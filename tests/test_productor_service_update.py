"""测试 ProductorService.update_phase 推进工厂建造进度。"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.entity import Entity
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsType
from system.productor_service import ProductorService


@pytest.fixture(autouse=True)
def _reset_components():
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    StorageComponent.components.clear()
    GoodsType.types.clear()
    yield
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    StorageComponent.components.clear()
    GoodsType.types.clear()


class TestProductorServiceUpdatePhase:
    """验证 update_phase 推进工厂建造进度。"""

    @staticmethod
    def _make_entity_with_factory(build_remaining: int) -> tuple[Entity, Factory]:
        gt = GoodsType(name="硅", base_price=1000, bonus_ceiling=0.1)
        recipe = Recipe(input_goods_type=None, input_quantity=0,
                        output_goods_type=gt, output_quantity=10)
        ft = FactoryType(recipe=recipe, base_production=5,
                         build_cost=10000, maintenance_cost=500, build_time=2)
        entity = Entity()
        pc = entity.init_component(ProductorComponent)
        factory = Factory(ft, build_remaining=build_remaining)
        pc.factories[ft].append(factory)
        return entity, factory

    def test_tick_build_reduces_remaining(self):
        """update_phase 应将在建工厂的 build_remaining 减 1。"""
        _, factory = self._make_entity_with_factory(build_remaining=3)
        service = ProductorService(MagicMock())
        service.update_phase()
        assert factory.build_remaining == 2

    def test_tick_build_completes_factory(self):
        """build_remaining=1 的工厂执行 update_phase 后应变为已建好。"""
        _, factory = self._make_entity_with_factory(build_remaining=1)
        service = ProductorService(MagicMock())
        service.update_phase()
        assert factory.build_remaining == 0
        assert factory.is_built

    def test_built_factory_not_affected(self):
        """已建好的工厂 (build_remaining=0) 不应被影响。"""
        _, factory = self._make_entity_with_factory(build_remaining=0)
        service = ProductorService(MagicMock())
        service.update_phase()
        assert factory.build_remaining == 0

    def test_multiple_companies_all_ticked(self):
        """多个公司的工厂都应被推进。"""
        _, f1 = self._make_entity_with_factory(build_remaining=3)
        _, f2 = self._make_entity_with_factory(build_remaining=1)
        _, f3 = self._make_entity_with_factory(build_remaining=0)
        service = ProductorService(MagicMock())
        service.update_phase()
        assert f1.build_remaining == 2
        assert f2.build_remaining == 0
        assert f3.build_remaining == 0
