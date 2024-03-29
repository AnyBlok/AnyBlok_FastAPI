# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import argparse
from logging import getLogger
from typing import TYPE_CHECKING, Any, Optional

from anyblok import configuration_post_load, load_init_function_from_entry_points
from anyblok.blok import BlokManager
from anyblok.config import Configuration, getParser
from gunicorn import __version__
from gunicorn.app.base import Application
from gunicorn.config import Config as GunicornConfig

from anyblok_fastapi.common import preload_database
from anyblok_fastapi.fastapi import create_app

if TYPE_CHECKING:
    from anyblok.config import AnyBlokArgumentParser
    from fastapi import FastAPI


logger = getLogger(__name__)


class Config(GunicornConfig):
    def __init__(
        self,
        usage: Optional[str] = None,
        prog: Optional[str] = None,
        application: Optional[str] = None,
    ) -> None:
        super(Config, self).__init__(usage=usage, prog=prog)
        self.application = application

    def parser(self) -> "AnyBlokArgumentParser":
        # Don't call super to user the Parser of anyblok
        kwargs = {"usage": self.usage, "prog": self.prog}
        parser = getParser(**kwargs)
        parser.add_argument(
            "-v",
            "--version",
            action="version",
            default=argparse.SUPPRESS,
            version="%(prog)s (version " + __version__ + ")\n",
            help="show program's version number and exit",
        )
        parser.add_argument("args", nargs="*", help=argparse.SUPPRESS)

        keys = sorted(self.settings, key=self.settings.__getitem__)
        for k in keys:
            self.settings[k].add_option(parser)

        description = {}
        if self.application in Configuration.applications:
            description.update(Configuration.applications[self.application])
        else:
            description.update(Configuration.applications["default"])

        configuration_groups = description.pop(
            "configuration_groups", ["gunicorn", "database"]
        )
        if "plugins" not in configuration_groups:
            configuration_groups.append("plugins")

        Configuration._load(parser, configuration_groups)
        return parser

    def set(self, name: str, value: Any) -> None:
        if name not in self.settings:
            return  # certainly come from anyblok config

        self.settings[name].set(value)


class ASGIApplication(Application):
    def __init__(self, application: str) -> None:
        load_init_function_from_entry_points()
        conf = Configuration.applications.get(application, {})
        usage = conf.get("usage")
        prog = conf.get("prog")
        self.application = application
        super(ASGIApplication, self).__init__(usage=usage, prog=prog)

    def load_default_config(self) -> None:
        self.cfg = Config(self.usage, prog=self.prog, application=self.application)
        self.cfg.set("worker_class", "uvicorn.workers.UvicornWorker")

    def init(self, parser, opts, args) -> None:
        Configuration.parse_options(opts)

        # get the configuration save in AnyBlok configuration in
        # gunicorn configuration
        for name in Configuration.configuration.keys():
            if name in self.cfg.settings:
                value = Configuration.get(name)
                if value:
                    self.cfg.settings[name].set(value)

        configuration_post_load()

    def load(self) -> "FastAPI":
        BlokManager.load(entry_points=("bloks",))
        return create_app(preload_database())
