# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2024 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from contextlib import contextmanager
from logging import getLogger
from typing import TYPE_CHECKING, Dict, List, Optional

from anyblok.config import Configuration
from fastapi import FastAPI
from pkg_resources import iter_entry_points

from anyblok_fastapi.common import get_registry_for
from anyblok.registry import Registry, RegistryManager

if TYPE_CHECKING:
    from anyblok.registry import Registry
    from starlette.routing import BaseRoute


logger = getLogger(__name__)



def get_registry():
    """Facility to get anyblok registry in route method

    You (as a developer) have to manage committing transactions.
    **Warning** Avoid to use different SQL transaction in
    different async method as sqlAlchemy session are local to the current
    thread

        from fastapi import Depends
        from anyblok_fastapi.fastapi import get_registry

        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from anyblok.registry import Registry

        def my_route(anyblok_registry: "Registry" = Depends(get_registry):
            # do something with anyblok registry.
            # mind to commit your transaction
            ...
    """
    yield get_registry_for(Configuration.get("db_name"))


@contextmanager
def registry_transaction(registry: "Registry") -> "Registry":
    """A facility to commit transaction at the end of blok"""
    registry.System.Cache.clear_invalidate_cache()
    try:
        yield registry
        if registry.unittest:
            registry.flush()
        else:
            registry.commit()
    except Exception as ex:
        registry.rollback()
        raise ex

class FastAPIRegistry:
    asgi_routes = {}
    
    def declare_routes(self, routes: Optional[Dict[str, "BaseRoute"]] = None) -> None:
        if not routes:
            routes = {}
        self.asgi_routes.update(routes)


def register_anyblok_registry_mixin():
    RegistryManager.register_mixin("FastAPI", FastAPIRegistry)


def create_app(registry: "Registry") -> FastAPI:
    """Create FastAPI App

    At the time writting routes are declared on bloks and are dynamically
    loads according if blok is loaded or not at startup.

    You can setup an entry point to add new routes to your Starlette/FastAPI
    application using entry point ``anyblok_fastapi.routes``:

    method that return a BaseRoute List::

        from starlette.routing import Mount, Route
        from myapp import api
        ...

        def get_routes():
            return [
                Route("/", endpoint=home),
                Route("/api", endpoint=api, methods=["GET", "POST"]),
                Mount(
                    "/statics",
                    app=StaticFiles(directory="static_dir"),
                    name="Statics"
                ),
            ]

    We add the entry point in setup file::

        setup(
            ...,
            entry_points={
                "anyblok_fastapi.routes": [
                    "statics=path.to:get_routes",
                            ...
                ],
            },
            ...,
        )

    You can setup middlewares to your Starlette/FastAPI application using
    entry point ``anyblok_fastapi.middlewares``, first create a method
    that return a list of instantiated Middleware::


        from starlette.middleware import Middleware
        from starlette.middleware.base import BaseHTTPMiddleware

        class MyWonderHTTPMiddleware(BaseHTTPMiddleware):

            def __init__(self, app: "ASGIApp", my_extra_param: str = None):
                super().__init__(app)
                self.my_data = my_extra_param

            async def dispatch(
                self, request: "Request", call_next: "RequestResponseEndpoint"
            ) -> "Response":
                # do something before
                print(self.my_data)
                response = await call_next(request)
                # do something before


    method that instantiate the middleware

        def config_callable():
            return [
                Middleware(MyWonderHTTPMiddleware, my_extra_param="something")
            ]


    We add the entry point in setup file::

        setup(
            ...,
            entry_points={
                'anyblok_fastapi.middlewares': [
                    config_callable=path:config_callable,
                    ...
                ],
            },
            ...,
        )
    """
    routes: List["BaseRoute"] = list(registry.asgi_routes.values())
    # TODO gives a way to set other routes if python package is installed
    # declaring using a new entrypoint section like middlewares
    middlewares = []

    for method in iter_entry_points("anyblok_fastapi.middlewares"):
        logger.debug("Add FastAPI middlewares: %r" % method.name)
        middlewares.extend(method.load()())

    for method in iter_entry_points("anyblok_fastapi.routes"):
        logger.debug("Add FastAPI routes: %r" % method.name)
        routes.extend(method.load()())

    return FastAPI(routes=routes, middleware=middlewares)
