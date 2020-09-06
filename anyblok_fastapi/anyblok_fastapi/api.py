from typing import TYPE_CHECKING, Dict, List

from starlette.requests import Request
from starlette.responses import HTMLResponse

from .schema import ExampleCreateSchema

if TYPE_CHECKING:
    from anyblok import registry


async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse("<html><body><h1>Hello, world!</h1></body></html>")


def create_example(
    example: ExampleCreateSchema, request: "Request"
) -> "registry.Example":
    """Something useful to tell to API user"""
    registry = request.state.anyblok_registry
    db_ex = registry.Example.insert(name=example.name)
    db_ex.refresh()
    return db_ex


def examples(request: "Request") -> List["registry.Example"]:
    registry = request.state.anyblok_registry
    return registry.Example.query().all()


def example(id: int, request: "Request") -> "registry.Example":
    registry = request.state.anyblok_registry
    return registry.Example.query().filter(registry.Example.id == id).one()


def other() -> Dict[str, str]:
    return {"message": "hello world"}
