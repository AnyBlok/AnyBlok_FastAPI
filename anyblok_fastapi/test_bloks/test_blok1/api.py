import asyncio
from typing import TYPE_CHECKING, Dict, List

from fastapi import Depends

from anyblok.registry import Registry
from anyblok_fastapi.fastapi import get_registry, registry_transaction
from starlette.requests import Request
from starlette.responses import HTMLResponse

from .schema import ExampleCreateSchema

if TYPE_CHECKING:
    from anyblok import registry


async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse("<html><body><h1>Hello, world!</h1></body></html>")


def create_example(
    example: ExampleCreateSchema,
    request: "Request",
    anyblok_registry: "Registry" = Depends(get_registry),
) -> "registry.Example":
    """Something useful to tell to API user"""
    with registry_transaction(anyblok_registry) as registry:
        db_ex = registry.Example.insert(name=example.name)
        db_ex.refresh()
    return db_ex


async def async_create_example(
    example: ExampleCreateSchema,
    request: "Request",
    anyblok_registry: "Registry" = Depends(get_registry),
) -> "registry.Example":
    """Something useful to tell to API user"""
    with registry_transaction(anyblok_registry) as registry:
        db_ex = registry.Example.insert(name=example.name)
        await asyncio.sleep(0.5)
        db_ex.refresh()
    return db_ex


def examples(
    request: "Request", anyblok_registry: "Registry" = Depends(get_registry)
) -> List["registry.Example"]:
    with registry_transaction(anyblok_registry) as registry:
        return registry.Example.query().all()


def example(
    id: int, request: "Request", registry: "Registry" = Depends(get_registry)
) -> "registry.Example":
    return registry.Example.query().filter(registry.Example.id == id).one()


def other() -> Dict[str, str]:
    return {"message": "hello world"}
