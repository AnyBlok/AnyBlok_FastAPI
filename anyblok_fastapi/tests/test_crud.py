import pytest
from fastapi.testclient import TestClient

from anyblok_fastapi.crud import create_crud_router, generate_pydantic_models
from anyblok_fastapi.fastapi import create_app


class TestFastApiCRUD:
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
    def crud_app(self, registry_testblok, installed_blok):
        app = create_app(registry_testblok)
        crud_router = create_crud_router("Example", prefix="/crud/examples")
        app.include_router(crud_router)
        return TestClient(app)

    def test_schema_generation(self, registry_testblok, installed_blok):
        schemas = generate_pydantic_models(registry_testblok.Example)
        assert "read" in schemas
        assert "create" in schemas
        assert "update" in schemas
        ReadModel = schemas["read"]
        assert "name" in ReadModel.model_fields
        assert "id" in ReadModel.model_fields

    def test_crud_endpoints(self, crud_app, registry_testblok):
        # 1. Create
        res_post = crud_app.post("/crud/examples/", json={"name": "CRUD Test Item"})
        assert res_post.status_code == 201
        created_id = res_post.json()["id"]
        assert res_post.json()["name"] == "CRUD Test Item"

        # 2. Get list
        res_list = crud_app.get("/crud/examples/")
        assert res_list.status_code == 200
        items = res_list.json()
        assert any(item["id"] == created_id for item in items)

        # 3. Get one
        res_get = crud_app.get(f"/crud/examples/{created_id}")
        assert res_get.status_code == 200
        assert res_get.json()["name"] == "CRUD Test Item"

        # 4. Put update
        res_put = crud_app.put(
            f"/crud/examples/{created_id}", json={"name": "Updated Item"}
        )
        assert res_put.status_code == 200
        assert res_put.json()["name"] == "Updated Item"

        # 5. Delete
        res_del = crud_app.delete(f"/crud/examples/{created_id}")
        assert res_del.status_code == 204

        # 6. Verify 404
        res_404 = crud_app.get(f"/crud/examples/{created_id}")
        assert res_404.status_code == 404
