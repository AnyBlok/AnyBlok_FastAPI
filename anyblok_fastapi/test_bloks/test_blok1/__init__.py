"""Blok declaration example
"""
from typing import TYPE_CHECKING, Callable, List

from fastapi.routing import APIRoute

from anyblok.blok import Blok
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
            self.registry.Example.insert(name="An example")

    def load(self) -> None:
        from .api import (
            async_create_example,
            create_example,
            example,
            examples,
            homepage,
            other,
        )
        from .schema import ExampleSchema

        self.registry.declare_routes(
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
