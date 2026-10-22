===============
AnyBlok FastAPI
===============

AnyBlok integration for the **FastAPI** ASGI framework, built on the **anyblok-starlette** foundation.

* License: Mozilla Public License Version 2.0 (MPL-2.0)
* Documentation: https://anyblok-fastapi.readthedocs.io

Overview
========

AnyBlok_FastAPI brings **FastAPI** support to the modular AnyBlok ecosystem.
Rather than enforcing a monolithic application, it allows Starlette to host one or multiple modular **FastAPI sub-applications**:

* **Unified Starlette ASGI Server**: Starlette handles the root server, AnyBlok lifecycle (**Lifespan**), and automatic transaction management (**AnyBlokTransactionMiddleware**).
* **Multi-API via Mounted Sub-Services**: Modular declaration of multiple FastAPI sub-apps (e.g. /api/v1, /api/partner, /admin/api) with complete route and documentation isolation.
* **Conditional Loading by Installed Bloks**: Sub-applications and endpoints are loaded if and only if their declaring Bloks are marked as installed in the database.
* **Dynamic Middlewares per Sub-App or Globally**: Declare ASGI middlewares conditionally loaded per sub-app via ``prepare_fastapi_middlewares(app, code)`` or globally on the root Starlette server via anyblok-starlette.
* **Strict Path Validation & Collision Surveillance**: Automatic detection and prevention of path collisions between sub-apps (FastAPIPathConflictError).
* **Dedicated OpenAPI / Swagger Documentation per Sub-App**: Each mounted sub-app serves its own interactive documentation (/path/docs, /path/redoc, /path/openapi.json) reflecting strictly the routes declared for its code by installed Bloks.
* **Native Dependency Injection**: Direct access to the current transaction's AnyBlok registry using Depends(get_registry).
* **Automatic REST CRUD Generator**: Fast scaffolding of full CRUD APIRouters with Pydantic v2 schemas (create_crud_router).

Installation
============

Production Installation
-----------------------

Install the package via pip:

.. code-block:: bash

    pip install anyblok-fastapi

Development Installation
------------------------

To install the repository in editable mode along with test and linting dependencies:

.. code-block:: bash

    git clone https://github.com/AnyBlok/AnyBlok_FastAPI.git
    cd AnyBlok_FastAPI
    python3 -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"

.. note::
   Always use quotes around the extra (e.g. ".[dev]") to prevent shell pattern-matching errors in shells like zsh.

Architecture & How It Works
===========================

1. Declaring FastAPI Sub-Applications (declare_fastapi_apps)
----------------------------------------------------------------

Any installed Blok can declare one or more FastAPI sub-applications using the declare_fastapi_apps class method:

.. code-block:: python

    from anyblok.blok import Blok
    from anyblok_fastapi import FastAPISubAppRegistry

    class PublicApiBlok(Blok):
        version = "0.1.0"

        @classmethod
        def declare_fastapi_apps(cls, reg: FastAPISubAppRegistry) -> None:
            reg.register(
                code="public",
                path="/api/v1",
                title="Public API v1",
                description="Public endpoints for mobile and web clients.",
                version="1.0.0",
            )

2. Modifying and Extending Sub-Apps from Other Bloks
----------------------------------------------------

The FastAPISubAppRegistry registry is designed to be easily modified. Another Blok can customize or enhance an already declared sub-app, or register additional ones:

.. code-block:: python

    class PartnerApiBlok(Blok):
        version = "0.1.0"

        @classmethod
        def declare_fastapi_apps(cls, reg: FastAPISubAppRegistry) -> None:
            # Update title or description of the existing 'public' sub-app
            reg.update(
                "public",
                title="Public API v1 (Extended)",
                description="Enhanced documentation provided by PartnerApiBlok.",
            )
            # Register a separate B2B partner sub-app
            reg.register(
                code="partner",
                path="/api/partner",
                title="Partner B2B API",
                version="2.0.0",
            )

3. Path Surveillance & Validation
---------------------------------

Mount paths undergo strict normalization and validation (normalize_path):

* Paths must start with / (raises ValueError otherwise).
* Consecutive slashes are collapsed and trailing slashes are trimmed (e.g. /api//v1/ becomes /api/v1).
* **Collision Detection**: If two sub-apps with different codes attempt to claim the same mount path, a FastAPIPathConflictError is immediately raised on startup.

4. Declaring Routes based on Installed Bloks (prepare_fastapi)
------------------------------------------------------------------

To register routes on a specific sub-app, implement the prepare_fastapi(app, code) class method. It receives the target FastAPI instance and its code:

.. code-block:: python

    from anyblok.blok import Blok
    from anyblok.registry import Registry
    from anyblok_fastapi import get_registry
    from fastapi import APIRouter, Depends, FastAPI

    router_v1 = APIRouter(prefix="/articles", tags=["Articles"])

    @router_v1.get("/")
    def list_articles(registry: Registry = Depends(get_registry)):
        return registry.Model.Article.query().all()

    class ArticleRoutesBlok(Blok):
        version = "0.1.0"

        @classmethod
        def prepare_fastapi(cls, app: FastAPI, code: str = "default") -> None:
            if code == "public":
                app.include_router(router_v1)
            elif code == "partner":
                # Routes dedicated exclusively to the partner API
                app.include_router(router_partner)

**Installation guarantee:**
If a Blok is not marked as installed in registry.System.Blok for the active database, its sub-apps are never mounted and its routes are never registered.

5. Declaring Middlewares on FastAPI Sub-Apps (prepare_fastapi_middlewares)
-------------------------------------------------------------------------

Installed Bloks can dynamically register ASGI middlewares loaded specifically on a target FastAPI sub-application:

.. code-block:: python

    from anyblok.blok import Blok
    from fastapi import FastAPI
    from starlette.middleware.base import BaseHTTPMiddleware


    class ApiAuditMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-API-Audit"] = "Passed"
            return response


    class ApiAuditBlok(Blok):
        version = "0.1.0"

        @classmethod
        def prepare_fastapi_middlewares(cls, app: FastAPI, code: str = "default") -> None:
            # Mount middleware on all sub-apps or target a specific sub-app code
            if code == "public":
                app.add_middleware(ApiAuditMiddleware)

.. note::
   When mounting without sub-apps (single default app), the signatures ``prepare_fastapi_middlewares(cls, app, registry)`` and ``prepare_fastapi_middlewares(cls, app)`` are also seamlessly supported.

6. Migrating from Deprecated fastapi_routes to prepare_fastapi
--------------------------------------------------------------

In earlier versions of **AnyBlok_FastAPI**, routes were declared by defining a fastapi_routes(routes) class method on the Blok class and mutating a dictionary of raw Starlette Route or FastAPI APIRoute objects:

.. code-block:: python

    # --- OLD DEPRECATED PATTERN (fastapi_routes) ---
    from anyblok.blok import Blok
    from fastapi.routing import APIRoute
    from starlette.routing import Route

    def homepage(request):
        ...

    def list_examples(registry):
        ...

    class OldBlok(Blok):
        version = 0.1.0

        @classmethod
        def fastapi_routes(cls, routes: dict):
            # Mutating a dictionary with manual string keys
            routes.update({
                "home": Route("/", homepage, methods=["GET"]),
                "GET/examples/": APIRoute(
                    "/examples/",
                    list_examples,
                    methods=["GET"],
                    response_model=list[ExampleSchema],
                ),
            })

Why this pattern is deprecated:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Fragile dictionary keys**: Requiring manual dictionary keys (like "GET/examples/") is awkward and error-prone.
2. **Missing FastAPI router features**: It bypasses standard FastAPI features like APIRouter tags, dependencies, lifespan, prefixing, and validation error handling.
3. **No multi-subapp awareness**: All endpoints were mixed into a single dictionary, preventing different endpoints from being mounted on separate sub-applications (e.g. /api/v1 vs /api/partner).

How to migrate to prepare_fastapi:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Use standard FastAPI APIRouter**: Group your endpoints using an APIRouter with standard decorators (@router.get, @router.post, etc.).
2. **Replace fastapi_routes with prepare_fastapi**: On your Blok class, replace fastapi_routes(routes) with prepare_fastapi(app, code="default").
3. **Call app.include_router(router)**: Attach your router to the target app. If you use sub-applications, inspect code to target specific APIs.

.. code-block:: python

    # --- NEW RECOMMENDED PATTERN (prepare_fastapi) ---
    from anyblok.blok import Blok
    from anyblok.registry import Registry
    from anyblok_fastapi import get_registry
    from fastapi import APIRouter, Depends, FastAPI
    from starlette.responses import HTMLResponse

    router = APIRouter(tags=["Examples"])

    @router.get("/")
    async def homepage() -> HTMLResponse:
        return HTMLResponse("<h1>Hello, world!</h1>")

    @router.get("/examples/", response_model=list[ExampleSchema])
    async def list_examples(registry: Registry = Depends(get_registry)):
        return registry.Example.query().all()

    class MigratedBlok(Blok):
        version = 0.2.0

        @classmethod
        def prepare_fastapi(cls, app: FastAPI, code: str = "default") -> None:
            # Mount onto the default app or target specific sub-applications
            if code in ("default", "public"):
                app.include_router(router)

7. Faithful OpenAPI / Swagger Documentation Isolation
-----------------------------------------------------

Each mounted FastAPI sub-application independently generates its own isolated API documentation:

* Interactive Swagger UI: /api/v1/docs, /api/partner/docs
* Alternative ReDoc documentation: /api/v1/redoc, /api/partner/redoc
* Raw OpenAPI JSON schema: /api/v1/openapi.json, /api/partner/openapi.json

Each schema contains **only the routes declared for its specific code by installed Bloks**.

8. AnyBlok Registry Dependency Injection (Depends(get_registry))
--------------------------------------------------------------------

In any route handler, use the get_registry helper with FastAPI dependency injection to obtain the AnyBlok registry bound to the current HTTP transaction:

.. code-block:: python

    from anyblok.registry import Registry
    from anyblok_fastapi import get_registry
    from fastapi import APIRouter, Depends, HTTPException

    router = APIRouter()

    @router.get("/users/{user_id}")
    def get_user(user_id: int, registry: Registry = Depends(get_registry)):
        user = registry.System.User.query().filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "login": user.login}

9. Automatic REST CRUD Generator (create_crud_router)
---------------------------------------------------------

Generate complete REST CRUD endpoints (GET list, GET item, POST create, PUT update, DELETE) with Pydantic v2 validation from any AnyBlok model:

.. code-block:: python

    from anyblok_fastapi import create_crud_router

    product_router = create_crud_router(
        model_name="Model.Product",
        prefix="/products",
        tags=["Products"],
        exclude_columns=["secret_token"],
    )

    app.include_router(product_router)

10. Mounting on a Custom Starlette Application
---------------------------------------------

Mount all declared FastAPI sub-apps onto any existing Starlette application using mount_fastapi_apps:

.. code-block:: python

    from anyblok_fastapi import mount_fastapi_apps
    from anyblok_starlette import create_app as create_starlette_app

    starlette_app = create_starlette_app(registry)
    mounted_apps = mount_fastapi_apps(starlette_app, registry)
    # mounted_apps contains {'public': <FastAPI>, 'partner': <FastAPI>}

Running Tests
=============

Test Database Setup
-------------------

The tests require an AnyBlok test database configuration file (app.test.cfg):

.. code-block:: ini

    [AnyBlok]
    extend = app.cfg
    db_name = anyblok_fastapi_test

Initialize the test database before running tests:

.. code-block:: bash

    anyblok_createdb -c app.test.cfg || anyblok_updatedb -c app.test.cfg

Running the Test Suite
----------------------

Execute the unit tests using pytest:

.. code-block:: bash

    ANYBLOK_CONFIG_FILE=app.test.cfg pytest -v anyblok_fastapi/tests

Running with Coverage
---------------------

Generate a coverage report:

.. code-block:: bash

    ANYBLOK_CONFIG_FILE=app.test.cfg pytest --cov=anyblok_fastapi --cov-report=term-missing anyblok_fastapi/tests

Code Formatting and Linting
---------------------------

Check and format code with Ruff, Mypy, and Pre-commit:

.. code-block:: bash

    pre-commit run --all-files
    ruff check .
    ruff format .
    mypy anyblok_fastapi

Roadmap & Historical TODO Status
================================

Below is the status of the original project TODO, detailing what is completed, what has been delegated to **anyblok-starlette**, and what remains to be done:

Completed (Implemented in AnyBlok_FastAPI)
------------------------------------------

* [x] **Validate SQLAlchemy & Schema classes (create / get)**:
  Fully validated with SQLAlchemy and Pydantic v2 schemas (see test_blok, test_blokv2, and anyblok_fastapi.crud).
* [x] **Dynamic route declaration based on installed Bloks**:
  Routes and sub-apps are loaded conditionally based on active installed Bloks in the registry (via prepare_fastapi(app, code) and declare_fastapi_apps(reg)).
* [x] **AnyBlok model as validation schema**:
  Solved through automatic Pydantic v2 schema generation from AnyBlok models (generate_pydantic_models and create_crud_router).
* [x] **Write unit tests**:
  Comprehensive test suite covering sub-app mounting, route isolation, CRUD generation, path validation, and OpenAPI documentation reflection.
* [x] **Package-level route registration hooks**:
  Implemented via Python entry points (anyblok_fastapi.routes) and Blok lifecycle hooks (prepare_fastapi).

Delegated to anyblok-starlette
------------------------------

* [x] **Gunicorn ASGI server integration**:
  ASGI process runners and CLI options (Uvicorn / Gunicorn) are handled by the ASGI core foundation in anyblok-starlette.
* [x] **Package-level Starlette middleware registration**:
  Managed centrally through anyblok-starlette.middlewares entry points.
* [x] **Debug mode and hot reload testing**:
  Handled by the anyblok-starlette CLI (--debug, --reload) through Uvicorn.
* [x] **Transaction rollback on failure**:
  Automated by AnyBlokTransactionMiddleware in anyblok-starlette (rolls back when unhandled exceptions or HTTP status >= 400 occur).

Remaining / Future Work
-----------------------

* [ ] **Dedicated Exception Handlers**:
    - [x] *Validation errors*: Handled natively by FastAPI (HTTP 422 Unprocessable Entity).
    - [x] *Rollback on critical error*: Managed by AnyBlokTransactionMiddleware.
    - [ ] *SQLAlchemy error mapping*: Provide standardized exception handlers for common SQLAlchemy errors (e.g. mapping NoResultFound to HTTP 404, or IntegrityError to HTTP 409).
* [ ] **Dynamic AnyBlok Schema type**:
  Permit declaring a new AnyBlok declaration type (e.g. Declarations.Schema) allowing Bloks to dynamically extend and override Pydantic validation schemas across modules.
