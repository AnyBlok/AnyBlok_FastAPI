# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import sys
from copy import copy
from logging import getLogger
from typing import List

from anyblok import configuration_post_load, load_init_function_from_entry_points
from anyblok.blok import BlokManager
from anyblok.config import Configuration
from uvicorn.main import run

from anyblok_fastapi.common import preload_database
from anyblok_fastapi.fastapi import create_app

logger = getLogger(__name__)


def asgi() -> None:
    """uvicorn ASGI dev server"""

    load_init_function_from_entry_points()
    argv: List[str] = copy(sys.argv)
    Configuration.load("uvicorn")
    sys.argv = argv
    configuration_post_load()
    BlokManager.load()
    kwargs = {
        "app": create_app(preload_database(loadwithoutmigration=False)),
        "host": Configuration.get("host"),
        "port": Configuration.get("port"),
        # "uds": uds,
        # "fd": fd,
        # "loop": loop,
        # "http": http,
        # "ws": ws,
        # "lifespan": lifespan,
        # "env_file": env_file,
        # "log_config": LOGGING_CONFIG if log_config is None else log_config,
        # "log_level": log_level,
        # "access_log": access_log,
        # "interface": interface,
        # "debug": debug,
        # "reload": reload,
        # "reload_dirs": reload_dirs if reload_dirs else None,
        # "workers": workers,
        # "proxy_headers": proxy_headers,
        # "forwarded_allow_ips": forwarded_allow_ips,
        # "root_path": root_path,
        # "limit_concurrency": limit_concurrency,
        # "backlog": backlog,
        # "limit_max_requests": limit_max_requests,
        # "timeout_keep_alive": timeout_keep_alive,
        # "ssl_keyfile": ssl_keyfile,
        # "ssl_certfile": ssl_certfile,
        # "ssl_version": ssl_version,
        # "ssl_cert_reqs": ssl_cert_reqs,
        # "ssl_ca_certs": ssl_ca_certs,
        # "ssl_ciphers": ssl_ciphers,
        # "headers": list([header.split(":") for header in headers]),
        # "use_colors": use_colors,
    }

    run(**kwargs)


def gunicorn_asgi():
    """console script function to run anyblok / pyramid with gunicorn"""
    try:
        import gunicorn  # noqa
    except ImportError:
        logger.error("Gunicorn is not installed. Try: pip install gunicorn")
        sys.exit(1)

    from .gunicorn import ASGIApplication

    ASGIApplication("gunicorn").run()
