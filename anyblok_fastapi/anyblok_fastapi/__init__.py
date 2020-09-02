"""Blok declaration example
"""
from typing import TYPE_CHECKING, Callable

from anyblok.blok import Blok

if TYPE_CHECKING:
    from types import ModuleType

    from anyblok.version import AnyBlokVersion


class Anyblok_fastapi(Blok):
    """Anyblok_fastapi's Blok class definition"""

    version = "0.1.0"
    author = "Pierre Verkest"
    required = ["anyblok-core"]

    @classmethod
    def import_declaration_module(cls) -> None:
        """Python module to import in the given order at start-up"""
        from . import model  # noqa

    @classmethod
    def reload_declaration_module(cls, reload: Callable[["ModuleType"], None]) -> None:
        """Python module to import while reloading server (ie when
        adding Blok at runtime
        """
        import pdb

        pdb.set_trace()
        from . import model  # noqa

        reload(model)

    def update(self, latest: "AnyBlokVersion") -> None:
        """Update blok"""
        # if we install this blok in the database we add a new record
        if not latest:
            self.registry.Example.insert(name="An example")
