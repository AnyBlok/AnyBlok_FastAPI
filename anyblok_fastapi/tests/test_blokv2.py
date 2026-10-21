import pytest
from fastapi.testclient import TestClient

from anyblok_fastapi.fastapi import create_app


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
    def webserver_test_blok(self, registry_testblok, installed_blok):
        return TestClient(create_app(registry_testblok))

    def test_home_with_test_blok(self, webserver_test_blok):
        response = webserver_test_blok.get("/v2/")
        assert response.status_code == 200
        assert "Hello, world!" in response.text

    def test_create_example(self, registry_testblok, webserver_test_blok):
        registry = registry_testblok

        count_before = registry.Example.query().count()
        rec_name = "test create example"
        response = webserver_test_blok.post("/v2/examples", json={"name": rec_name})
        assert response.status_code == 200
        assert count_before + 1 == registry.Example.query().count()
        assert registry.Example.query().get(response.json()["id"]).name == rec_name

    def test_async_create_example(self, registry_testblok, webserver_test_blok):
        registry = registry_testblok

        count_before = registry.Example.query().count()
        rec_name = "test create example"
        response = webserver_test_blok.post(
            "/v2/examples-async", json={"name": rec_name}
        )
        assert response.status_code == 200
        assert count_before + 1 == registry.Example.query().count()
        assert registry.Example.query().get(response.json()["id"]).name == rec_name

    def test_get_example(self, registry_testblok, webserver_test_blok):
        registry = registry_testblok

        example = registry.Example.insert(name="test get")
        example.refresh()
        response = webserver_test_blok.get(f"/v2/examples/{example.id}")
        assert response.status_code == 200
        assert response.json() == {
            "id": example.id,
            "name": example.name,
        }
