import pytest
from fastapi.testclient import TestClient

from anyblok.config import Configuration
from anyblok.conftest import *  # noqa
from anyblok.registry import RegistryManager
from anyblok.testing import load_configuration
from anyblok_fastapi.fastapi import create_app


@pytest.fixture(scope="session")
def configuration_loaded(request):
    # TODO: find a nice way to avoid to overwrit this fixture
    # from anyblok.conftest

    # TODO: I'm wondering why while setting define_environment_cls
    # thing went wrong
    # from anyblok.environment import EnvironmentManager
    # EnvironmentManager.set("current_blok", "anyblok-core")
    # EnvironmentManager.define_environment_cls(RequestEnvironment)
    load_configuration()


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
