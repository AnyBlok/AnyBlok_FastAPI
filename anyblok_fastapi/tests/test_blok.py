import json

import pytest
from fastapi.testclient import TestClient

from anyblok_fastapi.fastapi import create_app


class TestFastApiTestBlok:
    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)

    @pytest.fixture
    def webserver(self, registry_testblok):
        with TestClient(create_app(registry_testblok)) as client:
            yield client

    @pytest.fixture
    def webserver_test_blok(self, registry_testblok):
        registry_testblok.upgrade(install=("test-fastapi-blok1",))
        with TestClient(create_app(registry_testblok)) as client:
            yield client

    def test_home(self, webserver):
        response = webserver.get("/")
        assert response.status_code == 404

    def test_home_with_test_blok(self, webserver_test_blok):
        response = webserver_test_blok.get("/")
        assert response.status_code == 200
        assert "Hello, world!" in response.text

    def test_create_example(self, registry_testblok, webserver_test_blok):
        registry = registry_testblok

        count_before = registry.Example.query().count()
        rec_name = "test create example"
        response = webserver_test_blok.post(
            "/examples/", data=json.dumps({"name": rec_name})
        )
        assert response.status_code == 200
        assert count_before + 1 == registry.Example.query().count()
        assert registry.Example.query().get(response.json()["id"]).name == rec_name

    def test_async_create_example(self, registry_testblok, webserver_test_blok):
        registry = registry_testblok

        count_before = registry.Example.query().count()
        rec_name = "test create example"
        response = webserver_test_blok.post(
            "/examples-async/", data=json.dumps({"name": rec_name})
        )
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
