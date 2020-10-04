import inspect
import threading
from logging import getLogger
from typing import TYPE_CHECKING, Any, Callable, Dict
from uuid import uuid4

from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from anyblok.config import Configuration
from anyblok.registry import Registry, RegistryManager
from anyblok_fastapi.config import get_db_name as default_get_db_name

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
            request.scope["app"].router.routes.extend(
                request.state.anyblok_registry.asgi_routes.values()
            )
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
    from anyblok_fastapi.scripts import get_registry

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


def preload_databases(loadwithoutmigration: bool = True) -> None:
    # Methode copied from anyblok_pyramid.common"""
    dbnames = Configuration.get("db_names") or []
    dbname = Configuration.get("db_name")
    Registry = Configuration.get("Registry")
    if dbname not in dbnames:
        dbnames.append(dbname)

    # preload all db names
    dbnames = [x for x in dbnames if x]
    logger.info("Preload the databases : %s", ", ".join(dbnames))
    for dbname in dbnames:
        logger.info("Preload the database : %r", dbname)
        if Registry.db_exists(db_name=dbname):
            registry = get_registry_for(dbname, loadwithoutmigration, log_repeat=True)
            registry.commit()
            registry.session.close()
            logger.info("The database %r is preloaded", dbname)
        else:
            logger.warning("The database %r does not exist", dbname)


def get_registry_for(
    dbname: str, loadwithoutmigration: bool = True, log_repeat: bool = False
):
    # Methode copied from anyblok_pyramid.common"""
    settings: Dict[str, Any] = {}
    return RegistryManager.get(
        dbname,
        loadwithoutmigration=loadwithoutmigration,
        log_repeat=log_repeat,
        **settings,
    )


def create_app() -> FastAPI:
    """Create FastAPI App"""

    routes: Dict[str, "BaseRoute"] = {}
    # TODO gives a way to set other routes if python package is installed
    # declaring using a new entrypoint section
    # TODO gives a way to declare more middleware
    middlewares = [
        Middleware(
            AnyblokRegistryMiddleware, get_db_name=Configuration.get("get_db_name")
        ),
    ]
    return FastAPI(routes=routes, middleware=middlewares)
