# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2024 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Blok declaration example"""

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

from anyblok.blok import Blok
from fastapi import FastAPI

if TYPE_CHECKING:
    from types import ModuleType

    from anyblok.version import AnyBlokVersion


class TestBlok(Blok):
    """TestBlok's Blok class definition"""

    version = "0.1.0"
    author = "Pierre Verkest"
    required: ClassVar[list[str]] = [
        "anyblok-core",
    ]

    @classmethod
    def import_declaration_module(cls) -> None:
        """Python module to import in the given order at start-up"""
        from . import model  # noqa
        from . import schema  # noqa

    @classmethod
    def reload_declaration_module(cls, reload: Callable[["ModuleType"], None]) -> None:
        """Python module to import while reloading server (ie when
        adding Blok at runtime
        """
        from . import model  # noqa
        from . import schema

        reload(model)
        reload(schema)

    def update(self, latest: "AnyBlokVersion") -> None:
        """Update blok"""
        if not latest:
            self.anyblok.Example.insert(name="An example")

    @classmethod
    def prepare_fastapi(cls, app: FastAPI) -> None:
        from .apiv2 import router

        app.include_router(router)
