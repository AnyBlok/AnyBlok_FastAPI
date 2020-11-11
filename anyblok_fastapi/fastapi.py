import inspect
import threading
from logging import getLogger
from typing import TYPE_CHECKING, Any, Callable, Dict, List
from uuid import uuid4

from fastapi import FastAPI
from pkg_resources import iter_entry_points

from anyblok.config import Configuration
from anyblok.registry import Registry
from anyblok_fastapi.common import get_registry_for
from anyblok_fastapi.config import get_db_name as default_get_db_name
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

if TYPE_CHECKING:
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.responses import Response
    from starlette.routing import BaseRoute
    from starlette.types import ASGIApp


logger = getLogger(__name__)


class FastAPIRegistry(Registry):

    asgi_routes: Dict[str, "BaseRoute"] = {}

    def declare_routes(self, routes: Dict = None) -> None:
        if not routes:
            routes = {}
        self.asgi_routes.update(routes)


class RequestEnvironment:
    """ Use a request base, to get the environment """

    @classmethod
    def scoped_function_for_session(cls, *args, **kwargs):
        request = None
        for frame_info in inspect.stack():
            for arg in frame_info.frame.f_locals.values():
                if isinstance(arg, Request):
                    request = arg
                    break
        if request:
            return request.state.anyblok_fastapi_request_id

        return threading.get_ident()

    values: Dict[Any, Any] = {}

    @classmethod
    def setter(cls, key: Any, value: Any):
        """Save the value of the key in the environment

        :param key: the key of the value to save
        :param value: the value to save
        """
        if hash(cls.scoped_function_for_session()) not in cls.values:
            cls.values[hash(cls.scoped_function_for_session())] = {}

        cls.values[hash(cls.scoped_function_for_session())][key] = value

    @classmethod
    def getter(cls, key: Any, default: Any):
        """Get the value of the key in the environment

        :param key: the key of the value to retrieve
        :param default: return this value if no value loaded for the key
        :rtype: the value of the key
        """
        if str(hash(cls.scoped_function_for_session())) not in cls.values:
            return default

        return cls.values[hash(cls.scoped_function_for_session())].get(key, default)


class AnyblokRegistryMiddleware(BaseHTTPMiddleware):
    """This middleware setup anyblok registry on request object state

    Also it commit SQL transaction at the end of the http call
    """

    def __init__(self, app: "ASGIApp", get_db_name: Callable = default_get_db_name):
        super().__init__(app)
        self.get_db_name = get_db_name

    async def dispatch(
        self, request: "Request", call_next: "RequestResponseEndpoint"
    ) -> "Response":
        request.state.anyblok_fastapi_request_id = uuid4()
        dbname: str = self.get_db_name(request)
        if Configuration.get("Registry").db_exists(db_name=dbname):
            request.state.anyblok_registry = get_registry_for(dbname)
            request.state.anyblok_registry.System.Cache.clear_invalidate_cache()
        try:
            response = await call_next(request)
            if hasattr(request.state, "anyblok_registry"):
                if not request.state.anyblok_registry.unittest:
                    # TODO: we should do a two phase commit to make sure
                    # end users wait until the end that he receives all results
                    # if user get a timeout due a proxy we must rollback its
                    # transaction
                    request.state.anyblok_registry.commit()
        except Exception as ex:
            # TODO: not sure if it would conflict with exception handling
            # https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers
            # https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/#dependencies-with-yield-and-httpexception
            if hasattr(request.state, "anyblok_registry"):
                request.state.anyblok_registry.rollback()
            raise ex
        finally:
            if hasattr(request.state, "anyblok_registry"):
                if not request.state.anyblok_registry.unittest:
                    request.state.anyblok_registry.close()
        return response


def get_registry(request: "Request"):
    """Facility to get anyblok registry in route entry point
    from fastapi import Depends
    from anyblok_fastapi.fastapi import get_registry

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        # TODO: not sure about this import
        from anyblok.registry import Registry

    def my_route(anyblok_registry: "Registry" = Depends(get_registry):
        # do something with anyblok registry
        # do not commit in your code, commit is done by the middleware

    or using directly startlette Request (without this method)

    from starlette.requests import Request

    def my_route(request: "Request"):
        anyblok_registry = request.state.anyblok_registry
        # do something with anyblok registry
        # do not commit in your code, commit is done by the middleware
    """
    return request.state.anyblok_registry


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

    routes: List["BaseRoute"] = registry.asgi_routes.values()
    # TODO gives a way to set other routes if python package is installed
    # declaring using a new entrypoint section like middlewares
    middlewares = [
        Middleware(
            AnyblokRegistryMiddleware, get_db_name=Configuration.get("get_db_name")
        ),
    ]

    for method in iter_entry_points("anyblok_fastapi.middlewares"):
        logger.debug("Add FastAPI middlewares: %r" % method.name)
        middlewares.extend(method.load()())

    for method in iter_entry_points("anyblok_fastapi.routes"):
        logger.debug("Add FastAPI routes: %r" % method.name)
        routes.extend(method.load()())

    return FastAPI(routes=routes, middleware=middlewares)
