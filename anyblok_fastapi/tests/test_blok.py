import json

import pytest


class TestFastApiTestBlok:
    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_home(self, registry_testblok, webserver):
        registry = registry_testblok

        response = webserver.get("/")
        assert response.status_code == 404

        registry.upgrade(install=("test-fastapi-blok1",))

        response = webserver.get("/")
        assert response.status_code == 200
        assert "Hello, world!" in response.text

    def test_create_example(self, registry_testblok, webserver):
        registry = registry_testblok

        registry.upgrade(install=("test-fastapi-blok1",))
        count_before = registry.Example.query().count()
        rec_name = "test create example"
        response = webserver.post("/examples/", data=json.dumps({"name": rec_name}))
        assert response.status_code == 200
        assert count_before + 1 == registry.Example.query().count()
        assert registry.Example.query().get(response.json()["id"]).name == rec_name

    def test_get_example(self, registry_testblok, webserver):
        registry = registry_testblok

        registry.upgrade(install=("test-fastapi-blok1",))
        example = registry.Example.insert(name="test get")
        example.refresh()
        response = webserver.get(f"/examples/{example.id}")
        assert response.status_code == 200
        assert response.json() == {
            "id": example.id,
            "name": example.name,
        }
