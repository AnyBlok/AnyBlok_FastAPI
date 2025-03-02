# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#    Copyright (C) 2024 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import asyncio
from typing import Annotated, Dict, List

from anyblok.registry import Registry
from fastapi import APIRouter, Depends
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from anyblok_fastapi.fastapi import get_registry, registry_transaction

from .schema import ExampleCreateSchema, ExampleSchema

router = APIRouter(
    prefix="/v2",
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse("<html><body><h1>Hello, world!</h1></body></html>")


@router.post(
    "/examples",
    response_model=ExampleSchema,
    response_class=JSONResponse,
)
def create_example(
    example: ExampleCreateSchema,
    anyblok_registry: Annotated["Registry", Depends(get_registry)],
) -> "ExampleSchema":
    """Something useful to tell to API user"""
    with registry_transaction(anyblok_registry) as registry:
        return ExampleSchema.model_validate(registry.Example.insert(name=example.name))


@router.post(
    "/examples-async",
    response_model=ExampleSchema,
    response_class=JSONResponse,
)
async def async_create_example(
    example: ExampleCreateSchema,
    anyblok_registry: Annotated["Registry", Depends(get_registry)],
) -> "ExampleSchema":
    """Something useful to tell to API user"""
    with registry_transaction(anyblok_registry) as registry:
        db_ex = registry.Example.insert(name=example.name)
        await asyncio.sleep(0.5)
        ExampleSchema.model_validate(db_ex)
    return db_ex


def examples(
    anyblok_registry: Annotated["Registry", Depends(get_registry)],
) -> List["ExampleSchema"]:
    with registry_transaction(anyblok_registry) as registry:
        return [
            ExampleSchema.model_validate(el) for el in registry.Example.query().all()
        ]


@router.get(
    "/examples/{id}",
    response_model=ExampleSchema,
    response_class=JSONResponse,
)
def example(
    id: int,
    registry: Annotated["Registry", Depends(get_registry)],
) -> "ExampleSchema":
    return ExampleSchema.model_validate(
        registry.Example.query().filter(registry.Example.id == id).one()
    )


@router.get("/other", response_class=JSONResponse)
def other() -> Dict[str, str]:
    return {"message": "hello world"}
