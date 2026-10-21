import os
from pathlib import Path

if "ANYBLOK_CONFIG_FILE" not in os.environ:
    cfg = Path(__file__).resolve().parents[2] / "app.test.cfg"
    if cfg.exists():
        os.environ["ANYBLOK_CONFIG_FILE"] = str(cfg)

from anyblok.environment import ThreadEnvironment

ThreadEnvironment.scoped_function_for_session = lambda: 0

from anyblok.tests.conftest import *  # noqa: E402, F403
