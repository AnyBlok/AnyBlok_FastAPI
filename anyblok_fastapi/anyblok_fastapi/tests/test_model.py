from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anyblok.registry import Registry


class TestExample:
    """ Test python api on AnyBlok models"""

    def test_create_example(self, rollback_registry: "Registry") -> None:
        registry = rollback_registry
        ex = registry.Example.insert(name="plop")
        assert registry.Example.query().count() == 2
        assert ex.name == "plop"
