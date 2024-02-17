from anyblok.tests.conftest import *  # noqa
from anyblok_fastapi.fastapi import register_anyblok_registry_mixin

@pytest.fixture(scope="class")
def registry_testblok(request, testbloks_loaded, reload_registry_with_fastapi_mixin):
    registry = init_registry_with_bloks([], None)
    request.addfinalizer(registry.close)
    return registry
