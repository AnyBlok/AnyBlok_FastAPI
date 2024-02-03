from logging import getLogger
from typing import Any, Dict

from anyblok.config import Configuration
from anyblok.registry import Registry, RegistryManager

logger = getLogger(__name__)


def preload_database(loadwithoutmigration: bool = True) -> "Registry":
    # Methode copied from anyblok_pyramid.common"""
    dbname = Configuration.get("db_name")
    logger.info("Preload the database : %r", dbname)
    if Registry.db_exists(db_name=dbname):
        registry = get_registry_for(dbname, loadwithoutmigration, log_repeat=True)
        registry.commit()
        registry.session.close()
        logger.info("The database %r is preloaded", dbname)
    else:
        raise RuntimeError(f"The database {dbname} does not exist")

    return registry


def get_registry_for(
    dbname: str, loadwithoutmigration: bool = True, log_repeat: bool = False
):
    # Methode copied from anyblok_pyramid.common"""
    settings: Dict[str, Any] = {}
    return RegistryManager.get(
        dbname,
        loadwithoutmigration=loadwithoutmigration,
        log_repeat=log_repeat,
        **settings,
    )
