# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.config import Configuration
from anyblok.conftest import *  # noqa
from anyblok.registry import RegistryManager
from fastapi.testclient import TestClient

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
