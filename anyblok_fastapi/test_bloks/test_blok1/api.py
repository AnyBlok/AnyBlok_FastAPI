# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2024 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import asyncio
from typing import Dict, List

from anyblok.registry import Registry
from fastapi import Depends
from starlette.requests import Request
from starlette.responses import HTMLResponse

from anyblok_fastapi.fastapi import get_registry, registry_transaction

from .schema import ExampleCreateSchema, ExampleSchema


async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse("<html><body><h1>Hello, world!</h1></body></html>")


def create_example(
    example: ExampleCreateSchema,
    anyblok_registry: "Registry" = Depends(get_registry),
) -> "ExampleSchema":
    """Something useful to tell to API user"""
    with registry_transaction(anyblok_registry) as registry:
        return ExampleSchema.from_orm(registry.Example.insert(name=example.name))


async def async_create_example(
    example: ExampleCreateSchema,
    anyblok_registry: "Registry" = Depends(get_registry),
) -> "ExampleSchema":
    """Something useful to tell to API user"""
    with registry_transaction(anyblok_registry) as registry:
        db_ex = registry.Example.insert(name=example.name)
        await asyncio.sleep(0.5)
        ExampleSchema.from_orm(db_ex)
    return db_ex


def examples(
    anyblok_registry: "Registry" = Depends(get_registry),
) -> List["ExampleSchema"]:
    with registry_transaction(anyblok_registry) as registry:
        return [ExampleSchema.from_orm(el) for el in registry.Example.query().all()]


def example(id: int, registry: "Registry" = Depends(get_registry)) -> "ExampleSchema":
    return ExampleSchema.from_orm(
        registry.Example.query().filter(registry.Example.id == id).one()
    )


def other() -> Dict[str, str]:
    return {"message": "hello world"}
