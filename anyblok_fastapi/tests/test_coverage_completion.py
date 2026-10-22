from datetime import date, datetime, time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    Time,
)
from sqlalchemy.orm import declarative_base
from starlette.requests import Request
from starlette.routing import Route

from anyblok_fastapi.crud import (
    _cast_pk,
    _sqla_to_py_type,
    create_crud_router,
    generate_pydantic_models,
)
from anyblok_fastapi.fastapi import (
    create_app,
    get_registry,
    registry_transaction,
)
from anyblok_fastapi.subapps import (
    FastAPISubAppRegistry,
    _declare_subapps_from_bloks,
    _populate_subapp_routes,
    mount_fastapi_apps,
)


def test_sqla_to_py_type_mapping():
    assert _sqla_to_py_type(Boolean()) is bool
    assert _sqla_to_py_type(Integer()) is int
    assert _sqla_to_py_type(Float()) is float
    assert _sqla_to_py_type(Numeric()) is float
    assert _sqla_to_py_type(DateTime()) is datetime
    assert _sqla_to_py_type(Date()) is date
    assert _sqla_to_py_type(Time()) is time
    assert _sqla_to_py_type(String()) is str


def test_cast_pk_branches():
    mock_model = MagicMock()

    # 1. No primary key
    with patch("anyblok_fastapi.crud.inspect") as mock_inspect:
        mock_inspect.return_value.primary_key = []
        assert _cast_pk(mock_model, "123") == "123"

    # 2. Integer primary key valid cast
    with patch("anyblok_fastapi.crud.inspect") as mock_inspect:
        pk_col = MagicMock()
        pk_col.type = Integer()
        mock_inspect.return_value.primary_key = [pk_col]
        assert _cast_pk(mock_model, "42") == 42
        assert _cast_pk(mock_model, "not_an_int") == "not_an_int"

    # 3. String primary key
    with patch("anyblok_fastapi.crud.inspect") as mock_inspect:
        pk_col = MagicMock()
        pk_col.type = String()
        mock_inspect.return_value.primary_key = [pk_col]
        assert _cast_pk(mock_model, "abc") == "abc"


def test_generate_pydantic_models_options():
    Base = declarative_base()

    class ComplexModel(Base):
        __tablename__ = "test_complex"
        id = Column(Integer, primary_key=True)
        optional_col = Column(String, nullable=True)
        default_col = Column(Integer, default=10, nullable=False)
        server_def_col = Column(Float, server_default="1.0", nullable=False)
        excluded_col = Column(String)

    models = generate_pydantic_models(ComplexModel, exclude_columns=["excluded_col"])
    assert "excluded_col" not in models["read"].model_fields
    assert "optional_col" in models["create"].model_fields
    assert "default_col" in models["create"].model_fields
    assert "server_def_col" in models["create"].model_fields


@pytest.mark.asyncio
async def test_crud_router_404_and_unknown_fields(registry_testblok):
    registry_testblok.upgrade(install=("test-fastapi-blok1",))
    app = FastAPI()
    router = create_crud_router("Example", prefix="/test-crud")
    app.include_router(router)
    client = TestClient(app)

    # 1. Update 404
    resp_up_404 = client.put("/test-crud/999999", json={"name": "fail"})
    assert resp_up_404.status_code == 404
    assert resp_up_404.json()["detail"] == "Record not found"

    # 2. Delete 404
    resp_del_404 = client.delete("/test-crud/999999")
    assert resp_del_404.status_code == 404
    assert resp_del_404.json()["detail"] == "Record not found"

    # 3. Create, then update with extra unknown field
    resp_create = client.post("/test-crud/", json={"name": "Valid Name"})
    assert resp_create.status_code == 201
    item_id = resp_create.json()["id"]

    resp_up = client.put(
        f"/test-crud/{item_id}", json={"name": "New Name", "non_existent_field": 123}
    )
    assert resp_up.status_code == 200
    assert resp_up.json()["name"] == "New Name"


def test_get_registry_branches():
    mock_reg = MagicMock()
    # Branch 1: request has state with anyblok_registry
    req_with_state = MagicMock(spec=Request)
    req_with_state.state.anyblok_registry = mock_reg
    gen1 = get_registry(req_with_state)
    assert next(gen1) is mock_reg

    # Branch 2: request has no state or no anyblok_registry
    req_without_state = object()
    with patch("anyblok_fastapi.fastapi.get_registry_for", return_value=mock_reg):
        gen2 = get_registry(req_without_state)
        assert next(gen2) is mock_reg


def test_registry_transaction_branches():
    mock_reg = MagicMock()

    # Branch 1: unittest=False -> commit()
    mock_reg.unittest = False
    with registry_transaction(mock_reg):
        pass
    mock_reg.commit.assert_called_once()
    mock_reg.flush.assert_not_called()

    # Branch 2: exception -> rollback()
    mock_reg.reset_mock()
    with (
        pytest.raises(ValueError, match="test error"),
        registry_transaction(mock_reg),
    ):
        raise ValueError("test error")
    mock_reg.rollback.assert_called_once()


def test_create_app_with_entrypoints():
    mock_reg = MagicMock()
    mock_reg.System.Blok.list_by_state.return_value = []

    mock_mw_ep = MagicMock()
    mock_mw_ep.name = "test_mw"
    mock_mw_ep.load().return_value = []

    mock_route_ep = MagicMock()
    mock_route_ep.name = "test_route"
    mock_route_ep.load().return_value = [Route("/custom", lambda r: None)]

    def mock_entry_points(group):
        if group == "anyblok_fastapi.middlewares":
            return [mock_mw_ep]
        if group == "anyblok_fastapi.routes":
            return [mock_route_ep]
        return []

    with patch("anyblok_fastapi.fastapi.entry_points", side_effect=mock_entry_points):
        app = create_app(mock_reg)
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/custom" in paths


def test_subapps_additional_branches():
    reg = FastAPISubAppRegistry()
    # 1. Register with title, description, version, docs_url, kwargs
    sub = reg.register(
        code="v1",
        path="/api/v1",
        title="V1",
        description="V1 desc",
        version="1.0.0",
        docs_url="/docs",
        custom_opt="hello",
    )
    assert sub.kwargs["custom_opt"] == "hello"

    # Update via register with description, version, kwargs
    sub_updated = reg.register(
        code="v1",
        path="/api/v1",
        title="V1 Updated",
        description="V1 new desc",
        version="2.0.0",
        extra_key="world",
    )
    assert sub_updated.title == "V1 Updated"
    assert sub_updated.description == "V1 new desc"
    assert sub_updated.version == "2.0.0"
    assert sub_updated.kwargs["extra_key"] == "world"

    # Update via register with title=None, description="", version=""
    sub_empty_branch = reg.register(
        code="v1",
        path="/api/v1",
        title=None,
        description="",
        version="",
    )
    assert sub_empty_branch.title == "V1 Updated"

    # Update via update() with path, title, and extra kwargs
    reg.update("v1", path="/api/v1-updated", title="Final Title", custom_attr="foo")
    assert reg.get("v1").path == "/api/v1-updated"
    assert reg.get("v1").title == "Final Title"
    assert reg.get("v1").kwargs["custom_attr"] == "foo"

    # Remove non-existing code does not fail
    reg.remove("non_existing")


def test_subapps_declare_and_populate_error_branches():
    manager = FastAPISubAppRegistry()

    # 1. _declare_subapps_from_bloks with BlokManager error
    with patch(
        "anyblok_fastapi.subapps.BlokManager.get",
        side_effect=RuntimeError("Blok load error"),
    ):
        _declare_subapps_from_bloks(["failing_blok"], manager)

    # 2. _declare_subapps_from_bloks with Blok without declare_fastapi_apps
    mock_blok_no_declare = MagicMock(spec=[])
    with patch(
        "anyblok_fastapi.subapps.BlokManager.get", return_value=mock_blok_no_declare
    ):
        _declare_subapps_from_bloks(["no_declare_blok"], manager)

    # 3. _populate_subapp_routes with BlokManager error
    app = FastAPI()
    with patch(
        "anyblok_fastapi.subapps.BlokManager.get",
        side_effect=RuntimeError("Blok load error"),
    ):
        _populate_subapp_routes(app, "default", ["failing_blok"])

    # 4. _populate_subapp_routes with Blok without prepare_fastapi
    mock_blok_no_prepare = MagicMock(spec=[])
    with patch(
        "anyblok_fastapi.subapps.BlokManager.get", return_value=mock_blok_no_prepare
    ):
        _populate_subapp_routes(app, "default", ["no_prepare_blok"])

        # 5. _populate_subapp_routes with 1-arg prepare_fastapi: default vs custom

    class Blok1Arg:
        @classmethod
        def prepare_fastapi(cls, app: FastAPI) -> None:
            app.state.called = True

    with patch("anyblok_fastapi.subapps.BlokManager.get", return_value=Blok1Arg):
        app_default = FastAPI()
        _populate_subapp_routes(app_default, "default", ["blok1"])
        assert getattr(app_default.state, "called", False) is True

        app_custom = FastAPI()
        _populate_subapp_routes(app_custom, "custom_code", ["blok1"])
        assert getattr(app_custom.state, "called", False) is False


def test_mount_fastapi_apps_no_system_blok():
    parent = FastAPI()
    # Registry without System or Blok returns {}
    empty_reg = object()
    mounted = mount_fastapi_apps(parent, empty_reg)
    assert mounted == {}


def test_prepare_fastapi_middlewares():
    from anyblok_fastapi.fastapi import prepare_fastapi_from_installed_bloks

    mock_reg = MagicMock()
    mock_reg.System.Blok.list_by_state.return_value = ["blok_2params", "blok_1param"]

    class Blok2Params:
        @classmethod
        def prepare_fastapi_middlewares(cls, app: FastAPI, registry: object) -> None:
            app.state.mw_called_2 = True

    class Blok1Param:
        @classmethod
        def prepare_fastapi_middlewares(cls, app: FastAPI) -> None:
            app.state.mw_called_1 = True

    def mock_get(name):
        if name == "blok_2params":
            return Blok2Params
        return Blok1Param

    app = FastAPI()
    with patch("anyblok_fastapi.fastapi.BlokManager.get", side_effect=mock_get):
        prepare_fastapi_from_installed_bloks(mock_reg, app)

    assert getattr(app.state, "mw_called_2", False) is True
    assert getattr(app.state, "mw_called_1", False) is True


def test_subapps_prepare_fastapi_middlewares():
    class BlokSubappMW2:
        @classmethod
        def prepare_fastapi_middlewares(cls, app: FastAPI, code: str) -> None:
            app.state.subapp_mw_2 = code

    class BlokSubappMW1:
        @classmethod
        def prepare_fastapi_middlewares(cls, app: FastAPI) -> None:
            app.state.subapp_mw_1 = True

    def mock_get(name):
        if name == "mw2":
            return BlokSubappMW2
        return BlokSubappMW1

    with patch("anyblok_fastapi.subapps.BlokManager.get", side_effect=mock_get):
        app_custom = FastAPI()
        _populate_subapp_routes(app_custom, "custom", ["mw2", "mw1"])
        assert getattr(app_custom.state, "subapp_mw_2", None) == "custom"
        assert getattr(app_custom.state, "subapp_mw_1", False) is False

        app_default = FastAPI()
        _populate_subapp_routes(app_default, "default", ["mw2", "mw1"])
        assert getattr(app_default.state, "subapp_mw_2", None) == "default"
        assert getattr(app_default.state, "subapp_mw_1", False) is True
