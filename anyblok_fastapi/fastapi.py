# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2024 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2026 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from importlib.metadata import entry_points
from logging import getLogger
from typing import TYPE_CHECKING, Any

from anyblok.blok import BlokManager
from anyblok.config import Configuration
from anyblok.registry import Registry
from anyblok_starlette.common import get_registry_for
from anyblok_starlette.lifespan import default_lifespan as anyblok_lifespan
from anyblok_starlette.middleware import AnyBlokTransactionMiddleware
from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.requests import Request

from anyblok_fastapi.subapps import (
    FastAPIPathConflictError,
    FastAPISubAppDefinition,
    FastAPISubAppRegistry,
    mount_fastapi_apps,
    normalize_path,
)

if TYPE_CHECKING:
    from starlette.routing import BaseRoute

logger = getLogger(__name__)

__all__ = [
    "FastAPIPathConflictError",
    "FastAPISubAppDefinition",
    "FastAPISubAppRegistry",
    "create_app",
    "get_blok_routes",
    "get_registry",
    "mount_fastapi_apps",
    "normalize_path",
    "prepare_fastapi_from_installed_bloks",
    "registry_transaction",
]


def get_registry(request: Request) -> Generator[Registry, None, None]:
    """Facility to get anyblok registry in route method.

    Can be used with FastAPI Depends:
        def my_route(anyblok_registry: Registry = Depends(get_registry)):
            ...
    """
    if hasattr(request, "state") and hasattr(request.state, "anyblok_registry"):
        yield request.state.anyblok_registry
    else:
        yield get_registry_for(Configuration.get("db_name"))


@contextmanager
def registry_transaction(registry: Registry) -> Generator[Registry, None, None]:
    """A facility to commit transaction at the end of block."""
    registry.System.Cache.clear_invalidate_cache()
    try:
        yield registry
        if registry.unittest:
            registry.flush()
        else:
            registry.commit()
    except Exception:
        registry.rollback()
        raise


def get_blok_routes(registry: Registry) -> list["BaseRoute"]:
    """Loop on each installed blok to load routes."""
    routes: dict[str, Any] = {}
    for blok_name in registry.System.Blok.list_by_state("installed"):
        Blok = BlokManager.get(blok_name)
        if hasattr(Blok, "fastapi_routes"):
            logger.debug("Load configuration from: %r", blok_name)
            Blok.fastapi_routes(routes)
            warnings.warn(
                f"Using 'fastapi_routes' method on Blok {blok_name} is deprecated. "
                "You should use prepare_fastapi instead",
                DeprecationWarning,
                stacklevel=2,
            )
    return list(routes.values())


def prepare_fastapi_from_installed_bloks(
    registry: Registry, fastapi_app: FastAPI
) -> None:
    for blok_name in registry.System.Blok.list_by_state("installed"):
        Blok = BlokManager.get(blok_name)
        if hasattr(Blok, "prepare_fastapi"):
            logger.debug("Prepare fastapi from blok: %r", blok_name)
            Blok.prepare_fastapi(fastapi_app)


def create_app(
    registry: Registry,
    subapp_registry: FastAPISubAppRegistry | None = None,
) -> FastAPI:
    """Create FastAPI App delegating lifespan and transaction, mounting sub-apps."""
    routes: list[BaseRoute] = get_blok_routes(registry)
    middlewares = [
        Middleware(AnyBlokTransactionMiddleware, default_registry=registry),
    ]

    for method in entry_points(group="anyblok_fastapi.middlewares"):
        logger.debug("Add FastAPI middlewares: %r", method.name)
        middlewares.extend(method.load()())

    for method in entry_points(group="anyblok_fastapi.routes"):
        logger.debug("Add FastAPI routes: %r", method.name)
        routes.extend(method.load()())

    app = FastAPI(routes=routes, middleware=middlewares, lifespan=anyblok_lifespan)
    prepare_fastapi_from_installed_bloks(registry, app)
    mount_fastapi_apps(app, registry, subapp_registry=subapp_registry)

    return app
