# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2026 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Management of FastAPI sub-applications mounted onto Starlette / FastAPI."""

import inspect
from dataclasses import dataclass, field
from logging import getLogger
from typing import TYPE_CHECKING, Any

from anyblok.blok import BlokManager
from fastapi import FastAPI

if TYPE_CHECKING:
    from anyblok.registry import Registry
    from starlette.applications import Starlette

logger = getLogger(__name__)


class FastAPIPathConflictError(ValueError):
    """Raised when a FastAPI sub-app path conflicts with an existing sub-app."""


def normalize_path(path: str) -> str:
    """Validate and normalize a sub-application mount path.

    Rules:
    - Path must be a non-empty string.
    - Path must start with '/'.
    - Consecutive slashes are collapsed.
    - Trailing slashes are stripped (unless path is '/').
    """
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Sub-app path must be a non-empty string.")
    clean = path.strip()
    if not clean.startswith("/"):
        raise ValueError(f"Sub-app path must start with '/': got '{path}'.")

    while "//" in clean:
        clean = clean.replace("//", "/")

    if len(clean) > 1 and clean.endswith("/"):
        clean = clean.rstrip("/")

    return clean


@dataclass
class FastAPISubAppDefinition:
    """Declaration of a FastAPI sub-application."""

    code: str
    path: str
    title: str = ""
    description: str = ""
    version: str = "0.1.0"
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"
    openapi_url: str | None = "/openapi.json"
    kwargs: dict[str, Any] = field(default_factory=dict)


class FastAPISubAppRegistry:
    """Registry holding FastAPI sub-application definitions.

    Allows Bloks to declare new sub-apps or easily modify existing ones.
    Strictly validates paths to prevent collisions between different sub-apps.
    """

    def __init__(self) -> None:
        self._apps: dict[str, FastAPISubAppDefinition] = {}

    def _check_path_collision(self, code: str, norm_path: str) -> None:
        for existing_code, existing_app in self._apps.items():
            if existing_code != code and existing_app.path == norm_path:
                msg = (
                    f"Path conflict: sub-app '{code}' declares path '{norm_path}' "
                    f"which is already used by sub-app '{existing_code}'."
                )
                raise FastAPIPathConflictError(msg)

    def register(
        self,
        code: str,
        path: str,
        title: str | None = None,
        description: str = "",
        version: str = "0.1.0",
        docs_url: str | None = "/docs",
        redoc_url: str | None = "/redoc",
        openapi_url: str | None = "/openapi.json",
        **kwargs: Any,
    ) -> FastAPISubAppDefinition:
        """Register a new sub-application or update an existing one by code.

        Raises FastAPIPathConflictError if another sub-app already uses this path.
        """
        if not code or not isinstance(code, str):
            raise ValueError("Sub-app code must be a non-empty string.")

        norm_path = normalize_path(path)
        self._check_path_collision(code, norm_path)

        if code in self._apps:
            sub_app = self._apps[code]
            sub_app.path = norm_path
            if title is not None:
                sub_app.title = title
            if description:
                sub_app.description = description
            if version:
                sub_app.version = version
            sub_app.docs_url = docs_url
            sub_app.redoc_url = redoc_url
            sub_app.openapi_url = openapi_url
            sub_app.kwargs.update(kwargs)
        else:
            sub_app = FastAPISubAppDefinition(
                code=code,
                path=norm_path,
                title=title or f"API {code}",
                description=description,
                version=version,
                docs_url=docs_url,
                redoc_url=redoc_url,
                openapi_url=openapi_url,
                kwargs=kwargs,
            )
            self._apps[code] = sub_app

        return sub_app

    def update(self, code: str, **kwargs: Any) -> FastAPISubAppDefinition:
        """Modify attributes of an existing sub-application declaration."""
        if code not in self._apps:
            raise KeyError(f"Sub-app '{code}' is not registered.")

        if "path" in kwargs:
            norm_path = normalize_path(kwargs.pop("path"))
            self._check_path_collision(code, norm_path)
            self._apps[code].path = norm_path

        sub_app = self._apps[code]
        for key, val in kwargs.items():
            if hasattr(sub_app, key):
                setattr(sub_app, key, val)
            else:
                sub_app.kwargs[key] = val

        return sub_app

    def get(self, code: str) -> FastAPISubAppDefinition | None:
        """Return definition for code or None."""
        return self._apps.get(code)

    def all(self) -> dict[str, FastAPISubAppDefinition]:
        """Return a copy of all registered sub-applications."""
        return dict(self._apps)

    def remove(self, code: str) -> None:
        """Remove a declared sub-app by code."""
        if code in self._apps:
            del self._apps[code]

    def clear(self) -> None:
        """Clear all declared sub-apps."""
        self._apps.clear()


def _declare_subapps_from_bloks(
    installed_bloks: list[str],
    manager: FastAPISubAppRegistry,
) -> None:
    for blok_name in installed_bloks:
        try:
            Blok = BlokManager.get(blok_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Cannot get Blok %r: %s", blok_name, exc)
            continue

        if hasattr(Blok, "declare_fastapi_apps"):
            logger.debug("Declare FastAPI apps from Blok: %r", blok_name)
            Blok.declare_fastapi_apps(manager)


def _populate_subapp_routes(
    sub_app: FastAPI,
    code: str,
    installed_bloks: list[str],
) -> None:
    for blok_name in installed_bloks:
        try:
            Blok = BlokManager.get(blok_name)
        except Exception:  # noqa: BLE001, S112
            continue

        if hasattr(Blok, "prepare_fastapi_middlewares"):
            sig = inspect.signature(Blok.prepare_fastapi_middlewares)
            params = [
                p for p in sig.parameters.values() if p.name not in ("cls", "self")
            ]
            if len(params) >= 2:
                Blok.prepare_fastapi_middlewares(sub_app, code)
            elif code == "default":
                Blok.prepare_fastapi_middlewares(sub_app)

        if hasattr(Blok, "prepare_fastapi"):
            sig = inspect.signature(Blok.prepare_fastapi)
            params = [
                p for p in sig.parameters.values() if p.name not in ("cls", "self")
            ]
            if len(params) >= 2:
                Blok.prepare_fastapi(sub_app, code)
            elif code == "default":
                Blok.prepare_fastapi(sub_app)


def mount_fastapi_apps(
    parent_app: "FastAPI | Starlette",
    registry: "Registry",
    subapp_registry: FastAPISubAppRegistry | None = None,
) -> dict[str, FastAPI]:
    """Discover, instantiate, populate, and mount FastAPI sub-apps onto parent_app."""
    manager = (
        subapp_registry if subapp_registry is not None else FastAPISubAppRegistry()
    )

    if not hasattr(registry, "System") or not hasattr(registry.System, "Blok"):
        return {}

    installed_bloks = registry.System.Blok.list_by_state("installed")
    _declare_subapps_from_bloks(installed_bloks, manager)

    mounted_instances: dict[str, FastAPI] = {}
    for code, defn in manager.all().items():
        sub_app = FastAPI(
            title=defn.title,
            description=defn.description,
            version=defn.version,
            docs_url=defn.docs_url,
            redoc_url=defn.redoc_url,
            openapi_url=defn.openapi_url,
            **defn.kwargs,
        )
        _populate_subapp_routes(sub_app, code, installed_bloks)
        parent_app.mount(defn.path, sub_app)
        mounted_instances[code] = sub_app

    return mounted_instances
