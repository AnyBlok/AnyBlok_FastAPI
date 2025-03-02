# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2024 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Blok declaration example
"""
from typing import TYPE_CHECKING, Callable, List

from anyblok.blok import Blok
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.routing import Route

if TYPE_CHECKING:
    from types import ModuleType

    from anyblok.version import AnyBlokVersion


class TestBlok(Blok):
    """TestBlok's Blok class definition"""

    version = "0.1.0"
    author = "Pierre Verkest"
    required = [
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
        from . import schema  # noqa

        reload(model)
        reload(schema)

    def update(self, latest: "AnyBlokVersion") -> None:
        """Update blok"""
        # if we install this blok in the database we add a new record
        if not latest:
            self.anyblok.Example.insert(name="An example")

    @classmethod
    def fastapi_routes(cls, routes) -> None:
        from .api import (
            async_create_example,
            create_example,
            example,
            examples,
            homepage,
            other,
        )
        from .schema import ExampleSchema

        routes.update(
            {
                "home": Route("/", homepage, methods=["GET"]),
                "GET/examples/": APIRoute(
                    "/examples/",
                    examples,
                    methods=[
                        "GET",
                    ],
                    response_model=List[ExampleSchema],
                    response_class=JSONResponse,
                ),
                "POST/examples/": APIRoute(
                    "/examples/",
                    create_example,
                    methods=["POST"],
                    response_model=ExampleSchema,
                    response_class=JSONResponse,
                ),
                "POST/examples-async/": APIRoute(
                    "/examples-async/",
                    async_create_example,
                    methods=["POST"],
                    response_model=ExampleSchema,
                    response_class=JSONResponse,
                ),
                "GET/examples/{id}": APIRoute(
                    "/examples/{id}",
                    example,
                    methods=["GET"],
                    response_model=ExampleSchema,
                    response_class=JSONResponse,
                ),
                "other": APIRoute("/other", other, response_class=JSONResponse),
            }
        )

    @classmethod
    def prepare_fastapi(cls, app: FastAPI) -> None:
        from .apiv2 import router

        app.include_router(router)
