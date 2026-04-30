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
    def test_outer_reference(self) -> None:
        entity = Entity("test")
        comp = DummyComponent(entity)
        assert comp.outer is entity


class TestComponentTracking:
    """测试 BaseComponent 子类的 components 实例追踪。"""

    def setup_method(self) -> None:
        DummyComponent.components.clear()
        DependencyComponent.components.clear()
        DependentComponent.components.clear()

    def teardown_method(self) -> None:
        DummyComponent.components.clear()
        DependencyComponent.components.clear()
        DependentComponent.components.clear()

    def test_component_registered_on_creation(self) -> None:
        """创建组件后自动注册到子类的 components 列表。"""
        entity = Entity("test")
        comp = entity.init_component(DummyComponent)
        assert comp in DummyComponent.components

    def test_different_subclasses_isolated(self) -> None:
        """不同子类的 components 列表相互隔离。"""
        e1 = Entity("test")
        e2 = Entity("test")
        dummy = e1.init_component(DummyComponent)
        dep = e2.init_component(DependencyComponent)
        assert dummy in DummyComponent.components
        assert dep in DependencyComponent.components
        assert dummy not in DependencyComponent.components
        assert dep not in DummyComponent.components

    def test_base_component_does_not_collect_subclass_instances(self) -> None:
        """BaseComponent.components 不收集子类实例。"""
        entity = Entity("test")
        entity.init_component(DummyComponent)
        assert len(BaseComponent.components) == 0

    def test_multiple_instances_tracked(self) -> None:
        """多个实例都被追踪。"""
        e1 = Entity("test")
        e2 = Entity("test")
        c1 = e1.init_component(DummyComponent)
        c2 = e2.init_component(DummyComponent)
        assert c1 in DummyComponent.components
        assert c2 in DummyComponent.components
        assert len(DummyComponent.components) == 2


class TestEntity:
    def test_init_component(self):
        entity = Entity("test")
        comp = entity.init_component(DummyComponent)
        assert isinstance(comp, DummyComponent)
        assert comp.outer is entity

    def test_get_component(self):
        entity = Entity("test")
        entity.init_component(DummyComponent)
        comp = entity.get_component(DummyComponent)
        assert isinstance(comp, DummyComponent)

    def test_init_component_skip_if_exists(self):
        entity = Entity("test")
        first = entity.init_component(DummyComponent)
        second = entity.init_component(DummyComponent)
        assert first is second

    def test_get_component_not_found_returns_none(self):
        entity = Entity("test")
        assert entity.get_component(DummyComponent) is None

    def test_dependency_auto_init(self):
        entity = Entity("test")
        dep_comp = entity.init_component(DependentComponent)
        # DependencyComponent 应该被自动拉起
        auto_comp = entity.get_component(DependencyComponent)
        assert isinstance(auto_comp, DependencyComponent)
        assert dep_comp.dep is auto_comp

    def test_multiple_component_types(self):
        entity = Entity("test")
        entity.init_component(DummyComponent)
        entity.init_component(DependencyComponent)
        assert isinstance(entity.get_component(DummyComponent), DummyComponent)
        assert isinstance(entity.get_component(DependencyComponent), DependencyComponent)


class TestEntityDestroy:
    """测试 Entity.destroy() 注销机制。"""

    def setup_method(self) -> None:
        DummyComponent.components.clear()
        DependencyComponent.components.clear()
        DependentComponent.components.clear()

    def teardown_method(self) -> None:
        DummyComponent.components.clear()
        DependencyComponent.components.clear()
        DependentComponent.components.clear()

    def test_destroy_removes_from_components_list(self) -> None:
        """destroy 后组件从子类 components 列表中移除。"""
        entity = Entity("test")
        comp = entity.init_component(DummyComponent)
        assert comp in DummyComponent.components
        entity.destroy()
        assert comp not in DummyComponent.components

    def test_destroy_clears_entity_registry(self) -> None:
        """destroy 后 get_component 返回 None。"""
        entity = Entity("test")
        entity.init_component(DummyComponent)
        entity.destroy()
        assert entity.get_component(DummyComponent) is None

    def test_destroy_removes_all_components(self) -> None:
        """destroy 移除 Entity 持有的所有组件。"""
        entity = Entity("test")
        entity.init_component(DummyComponent)
        entity.init_component(DependencyComponent)
        entity.destroy()
        assert len(DummyComponent.components) == 0
        assert len(DependencyComponent.components) == 0
        assert entity.get_component(DummyComponent) is None
        assert entity.get_component(DependencyComponent) is None

    def test_destroy_idempotent(self) -> None:
        """连续调用两次 destroy 不报错。"""
        entity = Entity("test")
        entity.init_component(DummyComponent)
        entity.destroy()
        entity.destroy()  # 第二次不应报错

    def test_destroy_with_dependent_component(self) -> None:
        """destroy 带依赖链的 Entity，所有组件都被清理。"""
        entity = Entity("test")
        entity.init_component(DependentComponent)
        # DependentComponent 和 DependencyComponent 都被注册
        assert len(DependentComponent.components) == 1
        assert len(DependencyComponent.components) == 1
        entity.destroy()
        assert len(DependentComponent.components) == 0
        assert len(DependencyComponent.components) == 0

    def test_destroy_only_affects_target_entity(self) -> None:
        """destroy 一个 Entity 不影响其他 Entity 的组件。"""
        e1 = Entity("test")
        e2 = Entity("test")
        c1 = e1.init_component(DummyComponent)
        c2 = e2.init_component(DummyComponent)
        e1.destroy()
        assert c1 not in DummyComponent.components
        assert c2 in DummyComponent.components
        assert len(DummyComponent.components) == 1
