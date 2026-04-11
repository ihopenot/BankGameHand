from __future__ import annotations

import pytest

from component.base_component import BaseComponent
from core.entity import Entity


class DummyComponent(BaseComponent):
    """用于测试的简单组件。"""
    pass


class DependencyComponent(BaseComponent):
    """被依赖的组件。"""
    pass


class DependentComponent(BaseComponent):
    """依赖 DependencyComponent 的组件，init 时自动拉起依赖。"""

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        outer.init_component(DependencyComponent)
        self.dep = outer.get_component(DependencyComponent)


class TestBaseComponent:
    def test_outer_reference(self):
        entity = Entity()
        comp = DummyComponent(entity)
        assert comp.outer is entity


class TestEntity:
    def test_init_component(self):
        entity = Entity()
        comp = entity.init_component(DummyComponent)
        assert isinstance(comp, DummyComponent)
        assert comp.outer is entity

    def test_get_component(self):
        entity = Entity()
        entity.init_component(DummyComponent)
        comp = entity.get_component(DummyComponent)
        assert isinstance(comp, DummyComponent)

    def test_init_component_skip_if_exists(self):
        entity = Entity()
        first = entity.init_component(DummyComponent)
        second = entity.init_component(DummyComponent)
        assert first is second

    def test_get_component_not_found_raises(self):
        entity = Entity()
        with pytest.raises(KeyError):
            entity.get_component(DummyComponent)

    def test_dependency_auto_init(self):
        entity = Entity()
        dep_comp = entity.init_component(DependentComponent)
        # DependencyComponent 应该被自动拉起
        auto_comp = entity.get_component(DependencyComponent)
        assert isinstance(auto_comp, DependencyComponent)
        assert dep_comp.dep is auto_comp

    def test_multiple_component_types(self):
        entity = Entity()
        entity.init_component(DummyComponent)
        entity.init_component(DependencyComponent)
        assert isinstance(entity.get_component(DummyComponent), DummyComponent)
        assert isinstance(entity.get_component(DependencyComponent), DependencyComponent)
