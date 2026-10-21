# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2026 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from anyblok.blok import BlokManager
from anyblok.registry import Registry
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from anyblok_fastapi.fastapi import (
    FastAPIPathConflictError,
    FastAPISubAppRegistry,
    create_app,
    get_registry,
    normalize_path,
)


class TestFastAPISubAppPathValidation:
    def test_normalize_path_valid(self):
        assert normalize_path("/api/v1") == "/api/v1"
        assert normalize_path("/api/v1/") == "/api/v1"
        assert normalize_path("/") == "/"
        assert normalize_path("/api//v1///test/") == "/api/v1/test"

    def test_normalize_path_invalid(self):
        with pytest.raises(ValueError, match="non-empty string"):
            normalize_path("")

        with pytest.raises(ValueError, match="non-empty string"):
            normalize_path("   ")

        with pytest.raises(ValueError, match="must start with '/'"):
            normalize_path("api/v1")


class TestFastAPISubAppRegistry:
    def test_register_and_get(self):
        reg = FastAPISubAppRegistry()
        app_def = reg.register(code="v1", path="/api/v1", title="API V1")
        assert app_def.code == "v1"
        assert app_def.path == "/api/v1"
        assert app_def.title == "API V1"
        assert reg.get("v1") == app_def
        assert "v1" in reg.all()

    def test_register_invalid_code(self):
        reg = FastAPISubAppRegistry()
        with pytest.raises(ValueError, match="non-empty string"):
            reg.register(code="", path="/api")

    def test_modify_existing_declaration(self):
        reg = FastAPISubAppRegistry()
        reg.register(code="v1", path="/api/v1", title="Old Title")
        updated = reg.register(code="v1", path="/api/v1-new", title="New Title")
        assert updated.path == "/api/v1-new"
        assert updated.title == "New Title"

    def test_update_method(self):
        reg = FastAPISubAppRegistry()
        reg.register(code="v1", path="/api/v1", title="API V1")
        reg.update("v1", title="Updated Title", description="New Desc")
        app_def = reg.get("v1")
        assert app_def.title == "Updated Title"
        assert app_def.description == "New Desc"

    def test_update_non_existing_raises(self):
        reg = FastAPISubAppRegistry()
        with pytest.raises(KeyError, match="not registered"):
            reg.update("unknown", title="Test")

    def test_path_conflict_between_different_codes(self):
        reg = FastAPISubAppRegistry()
        reg.register(code="v1", path="/api/v1")
        with pytest.raises(FastAPIPathConflictError, match="Path conflict"):
            reg.register(code="v2", path="/api/v1")

        with pytest.raises(FastAPIPathConflictError, match="Path conflict"):
            reg.register(code="v2", path="/api/v1/")

    def test_update_path_conflict_raises(self):
        reg = FastAPISubAppRegistry()
        reg.register(code="v1", path="/api/v1")
        reg.register(code="v2", path="/api/v2")
        with pytest.raises(FastAPIPathConflictError, match="Path conflict"):
            reg.update("v2", path="/api/v1")

    def test_remove_and_clear(self):
        reg = FastAPISubAppRegistry()
        reg.register(code="v1", path="/api/v1")
        reg.register(code="v2", path="/api/v2")
        reg.remove("v1")
        assert reg.get("v1") is None
        assert "v2" in reg.all()
        reg.clear()
        assert len(reg.all()) == 0


class MockBlokPublic:
    @classmethod
    def declare_fastapi_apps(cls, reg: FastAPISubAppRegistry) -> None:
        reg.register(
            code="public",
            path="/api/v1",
            title="Public API v1",
            description="Public endpoints",
        )

    @classmethod
    def prepare_fastapi(cls, app: FastAPI, code: str = "default") -> None:
        if code == "public":
            r = APIRouter()

            @r.get("/ping")
            def ping():
                return {"status": "ok", "api": "public"}

            @r.get("/db-check")
            async def db_check(reg: Registry = Depends(get_registry)):  # noqa: B008
                count = reg.Example.query().count()
                return {"example_count": count}

            app.include_router(r)


class MockBlokPartner:
    @classmethod
    def declare_fastapi_apps(cls, reg: FastAPISubAppRegistry) -> None:
        reg.update("public", title="Public API v1 Extended")
        reg.register(
            code="partner",
            path="/api/partner",
            title="Partner B2B API",
            description="Partner only endpoints",
        )

    @classmethod
    def prepare_fastapi(cls, app: FastAPI, code: str = "default") -> None:
        if code == "partner":
            r = APIRouter()

            @r.get("/orders")
            def orders():
                return [{"order_id": 101}]

            app.include_router(r)


class MockUninstalledBlok:
    @classmethod
    def declare_fastapi_apps(cls, reg: FastAPISubAppRegistry) -> None:
        reg.register(code="secret", path="/api/secret", title="Secret API")

    @classmethod
    def prepare_fastapi(cls, app: FastAPI, code: str = "default") -> None:
        if code == "secret":
            r = APIRouter()

            @r.get("/leak")
            def leak():
                return {"secret": True}

            app.include_router(r)


class TestFastAPISubAppsIntegration:
    @pytest.fixture(scope="class")
    @classmethod
    def installed_blok(cls, registry_testblok):
        registry_testblok.upgrade(install=("test-fastapi-blok1",))
        return registry_testblok

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok, installed_blok):
        transaction = registry_testblok.begin_nested()

        def fin():
            if transaction.is_active and not any(
                getattr(t[1], "_deactivated_from_connection", False)
                or not getattr(t[1], "is_active", True)
                for t in transaction._connections.values()
            ):
                transaction.rollback()

        request.addfinalizer(fin)

    @pytest.fixture
    def setup_mock_bloks(self, monkeypatch, registry_testblok, installed_blok):
        registry = registry_testblok

        installed_map = {
            "test-fastapi-blok1": BlokManager.get("test-fastapi-blok1"),
            "blok_public": MockBlokPublic,
            "blok_partner": MockBlokPartner,
        }

        monkeypatch.setattr(
            registry.System.Blok,
            "list_by_state",
            lambda state: (
                ["test-fastapi-blok1", "blok_public", "blok_partner"]
                if state == "installed"
                else ["uninstalled_blok"]
            ),
        )

        def mock_get(name):
            if name in installed_map:
                return installed_map[name]
            if name == "uninstalled_blok":
                return MockUninstalledBlok
            raise KeyError(name)

        monkeypatch.setattr(BlokManager, "get", mock_get)
        app = create_app(registry)
        return TestClient(app)

    def test_subapps_routes(self, setup_mock_bloks):
        client = setup_mock_bloks

        resp_ping = client.get("/api/v1/ping")
        assert resp_ping.status_code == 200
        assert resp_ping.json() == {"status": "ok", "api": "public"}

        resp_db = client.get("/api/v1/db-check")
        assert resp_db.status_code == 200
        assert "example_count" in resp_db.json()

        resp_orders = client.get("/api/partner/orders")
        assert resp_orders.status_code == 200
        assert resp_orders.json() == [{"order_id": 101}]

        resp_secret = client.get("/api/secret/leak")
        assert resp_secret.status_code == 404

    def test_subapps_openapi_docs_reflection(self, setup_mock_bloks):
        client = setup_mock_bloks

        resp_pub = client.get("/api/v1/openapi.json")
        assert resp_pub.status_code == 200
        pub_schema = resp_pub.json()
        assert pub_schema["info"]["title"] == "Public API v1 Extended"
        assert "/ping" in pub_schema["paths"]
        assert "/orders" not in pub_schema["paths"]

        resp_docs = client.get("/api/v1/docs")
        assert resp_docs.status_code == 200
        assert "text/html" in resp_docs.headers["content-type"]

        resp_part = client.get("/api/partner/openapi.json")
        assert resp_part.status_code == 200
        part_schema = resp_part.json()
        assert part_schema["info"]["title"] == "Partner B2B API"
        assert "/orders" in part_schema["paths"]
        assert "/ping" not in part_schema["paths"]
