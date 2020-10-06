from logging import getLogger
from typing import Any, Dict

from anyblok.config import Configuration
from anyblok.registry import RegistryManager

logger = getLogger(__name__)


def preload_databases(loadwithoutmigration: bool = True) -> None:
    # Methode copied from anyblok_pyramid.common"""
    dbnames = Configuration.get("db_names") or []
    dbname = Configuration.get("db_name")
    Registry = Configuration.get("Registry")
    if dbname not in dbnames:
        dbnames.append(dbname)

    # preload all db names
    dbnames = [x for x in dbnames if x]
    logger.info("Preload the databases : %s", ", ".join(dbnames))
    for dbname in dbnames:
        logger.info("Preload the database : %r", dbname)
        if Registry.db_exists(db_name=dbname):
            registry = get_registry_for(dbname, loadwithoutmigration, log_repeat=True)
            registry.commit()
            registry.session.close()
            logger.info("The database %r is preloaded", dbname)
        else:
            logger.warning("The database %r does not exist", dbname)


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
