"""Tests for ProductorComponent.prices attribute."""

from __future__ import annotations

from component.productor_component import ProductorComponent
from core.entity import Entity
from entity.goods import GoodsType
from entity.factory import Factory, FactoryType, Recipe


class TestProductorPrices:
    """ProductorComponent should expose a prices dict mapping output GoodsType to Money."""

    def _make_entity_with_factory(self) -> tuple[Entity, GoodsType, FactoryType]:
        """Helper: create entity with one factory type producing one goods type."""
        gt = GoodsType(name="chip", base_price=500)
        recipe = Recipe(
            input_goods_type=None,
            input_quantity=0,
            output_goods_type=gt,
            output_quantity=10,
            tech_quality_weight=1.0,
        )
        ft = FactoryType(
            recipe=recipe,
            labor_demand=50,
            build_cost=1000,
            maintenance_cost=50,
            build_time=1,
        )
        entity = Entity()
        pc = entity.init_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        return entity, gt, ft

    def test_prices_attribute_exists(self) -> None:
        entity = Entity()
        pc = entity.init_component(ProductorComponent)
        assert hasattr(pc, "prices")
        assert isinstance(pc.prices, dict)

    def test_prices_empty_when_no_factories(self) -> None:
        entity = Entity()
        pc = entity.init_component(ProductorComponent)
        assert pc.prices == {}

    def test_prices_initialized_after_register_factory(self) -> None:
        """After adding a factory, calling init_prices populates prices from base_price."""
        entity, gt, ft = self._make_entity_with_factory()
        pc: ProductorComponent = entity.get_component(ProductorComponent)
        pc.init_prices()
        assert gt in pc.prices
        assert pc.prices[gt] == gt.base_price

    def test_prices_multiple_factory_types(self) -> None:
        """Multiple factory types -> each output goods type gets its own price."""
        gt_a = GoodsType(name="silicon", base_price=100)
        gt_b = GoodsType(name="chip", base_price=500)
        recipe_a = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt_a, output_quantity=10, tech_quality_weight=1.0)
        recipe_b = Recipe(input_goods_type=gt_a, input_quantity=5, output_goods_type=gt_b, output_quantity=2, tech_quality_weight=0.6)
        ft_a = FactoryType(recipe=recipe_a, labor_demand=50, build_cost=500, maintenance_cost=20, build_time=1)
        ft_b = FactoryType(recipe=recipe_b, labor_demand=50, build_cost=2000, maintenance_cost=100, build_time=2)

        entity = Entity()
        pc = entity.init_component(ProductorComponent)
        pc.factories[ft_a] = [Factory(ft_a, build_remaining=0)]
        pc.factories[ft_b] = [Factory(ft_b, build_remaining=0)]
        pc.init_prices()

        assert pc.prices[gt_a] == 100
        assert pc.prices[gt_b] == 500

    def test_prices_value_is_money_type(self) -> None:
        entity, gt, ft = self._make_entity_with_factory()
        pc: ProductorComponent = entity.get_component(ProductorComponent)
        pc.init_prices()
        assert isinstance(pc.prices[gt], int)  # Money = int
