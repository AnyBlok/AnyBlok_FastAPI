import pytest
from fastapi.testclient import TestClient

from anyblok.config import Configuration
from anyblok.conftest import *  # noqa
from anyblok.registry import RegistryManager
from anyblok_fastapi.fastapi import create_app


@pytest.fixture(scope="session")
def webserver(request, configuration_loaded, init_session):
    with TestClient(
        create_app(
            RegistryManager.get(
                Configuration.get("db_name"),
                loadwithoutmigration=True,
            )
        )
    ) as client:
        yield client
