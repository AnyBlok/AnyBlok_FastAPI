import pytest
from anyblok.blok import BlokManager
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse
from starlette.routing import Route

from anyblok_fastapi.fastapi import create_app
from anyblok_fastapi.test_bloks.test_blok1.api import (
    async_create_example,
    create_example,
    example,
    examples,
    homepage,
    other,
)
from anyblok_fastapi.test_bloks.test_blok1.schema import ExampleSchema


def _legacy_fastapi_routes(routes):
    routes.update(
        {
            "home": Route("/", homepage, methods=["GET"]),
            "GET/examples/": APIRoute(
                "/examples/",
                examples,
                methods=["GET"],
                response_model=list[ExampleSchema],
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


class TestFastApiUninstalled:
    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()

        def fin():
            if transaction.is_active:
                transaction.rollback()

        request.addfinalizer(fin)

    def test_home(self, registry_testblok):
        client = TestClient(create_app(registry_testblok))
        response = client.get("/")
        assert response.status_code == 404


class TestFastApiTestBlok:
    @pytest.fixture(scope="class")
    @classmethod
    def installed_blok(cls, registry_testblok):
        registry_testblok.upgrade(install=("test-fastapi-blok1",))
        return registry_testblok

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok, installed_blok):
        transaction = registry_testblok.begin_nested()

        def fin():
            if transaction.is_active:
                transaction.rollback()

        request.addfinalizer(fin)

    @pytest.fixture
    def webserver_test_blok(self, registry_testblok, installed_blok, monkeypatch):
        blok = BlokManager.get("test-fastapi-blok1")
        monkeypatch.setattr(
            blok, "fastapi_routes", _legacy_fastapi_routes, raising=False
        )
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("always")
            with pytest.deprecated_call():
                app = create_app(registry_testblok)
        return TestClient(app)

    def test_home_with_test_blok(self, webserver_test_blok):
        response = webserver_test_blok.get("/")
        assert response.status_code == 200
        assert "Hello, world!" in response.text

    def test_create_example(self, registry_testblok, webserver_test_blok):
        registry = registry_testblok

        count_before = registry.Example.query().count()
        rec_name = "test create example"
        response = webserver_test_blok.post("/examples/", json={"name": rec_name})
        assert response.status_code == 200
        assert count_before + 1 == registry.Example.query().count()
        assert registry.Example.query().get(response.json()["id"]).name == rec_name

    def test_async_create_example(self, registry_testblok, webserver_test_blok):
        registry = registry_testblok

        count_before = registry.Example.query().count()
        rec_name = "test create example"
        response = webserver_test_blok.post("/examples-async/", json={"name": rec_name})
        assert response.status_code == 200
        assert count_before + 1 == registry.Example.query().count()
        assert registry.Example.query().get(response.json()["id"]).name == rec_name

    def test_get_example(self, registry_testblok, webserver_test_blok):
        registry = registry_testblok

        example = registry.Example.insert(name="test get")
        example.refresh()
        response = webserver_test_blok.get(f"/examples/{example.id}")
        assert response.status_code == 200
        assert response.json() == {
            "id": example.id,
            "name": example.name,
        }
