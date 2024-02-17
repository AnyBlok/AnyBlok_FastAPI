#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup script for anyblok-fastapi"""

import os
from typing import List

from setuptools import find_packages, setup

version = "0.1.0"
here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.rst"), "r", encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open(os.path.join(here, "CHANGELOG.rst"), "r", encoding="utf-8") as changelog_file:
    changelog = changelog_file.read()

requirements = [
    "anyblok",
    "fastapi",
    "gunicorn",
    "sqlalchemy",
    "uvicorn[standard]",
]

test_requirements: List[str] = [
    # TODO: put package test requirements here
]

setup(
    name="anyblok_fastapi",
    version=version,
    description="Use AnyBlok with FastAPI",
    long_description=readme + "\n\n" + changelog,
    author="Pierre Verkest",
    author_email="pierreverkest84@gmail.com",
    url="https://github.com/AnyBlok/AnyBlok_FastAPI",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "anyblok_uvicorn=anyblok_fastapi.scripts:asgi",
            "gunicorn_anyblok_uvicorn=anyblok_fastapi.scripts:gunicorn_asgi",
        ],
        "bloks": [],
        "anyblok.init": [
            "anyblok_fastapi_config=anyblok_fastapi:anyblok_init_config",
        ],
        "anyblok.registry.mixin": [
            "fastapi=anyblok_fastapi.fastapi:FastAPIRegistry",
        ],
        "test_bloks": [
            "test-fastapi-blok1=anyblok_fastapi.test_bloks.test_blok1:TestBlok",
        ],
    },
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords="anyblok-fastapi",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    test_suite="tests",
    tests_require=test_requirements,
)
