"""ProductorService 单元测试。"""
from __future__ import annotations

from unittest.mock import MagicMock

from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.entity import Entity
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsType
from game.game import Game
from system.productor_service import ProductorService


# ── 测试用的数据工厂 ────────────────────────────────────────


def _make_goods_type(name: str = "硅") -> GoodsType:
    return GoodsType(name=name, base_price=1000, bonus_ceiling=0.0)


def _make_raw_recipe(output_gt: GoodsType) -> Recipe:
    return Recipe(
        input_goods_type=None,
        input_quantity=0,
        output_goods_type=output_gt,
        output_quantity=10,
    )


def _make_factory_type(recipe: Recipe) -> FactoryType:
    return FactoryType(
        recipe=recipe,
        base_production=5,
        build_cost=10000,
        maintenance_cost=500,
        build_time=0,
    )


def _make_entity_with_productor(
    recipe: Recipe, factory_type: FactoryType, tech: int = 100
) -> Entity:
    """创建持有 ProductorComponent 的 Entity，含一个已建成工厂。"""
    entity = Entity()
    prod = entity.init_component(ProductorComponent)
    prod.tech_values[recipe] = tech
    factory = Factory(factory_type=factory_type, build_remaining=0)
    prod.factories[factory_type].append(factory)
    return entity


def _make_game() -> Game:
    game = Game()
    game.economy_service = MagicMock()
    game.company_service = MagicMock()
    game.market_service = MagicMock()
    game.folk_service = MagicMock()
    return game


# ── 测试类 ───────────────────────────────────────────────────


class TestProductorService:
    def setup_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()

    def teardown_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()

    def test_update_phase_updates_max_tech(self) -> None:
        """update_phase 遍历所有 ProductorComponent 更新 max_tech。"""
        gt = _make_goods_type()
        recipe = _make_raw_recipe(gt)
        ft = _make_factory_type(recipe)

        _make_entity_with_productor(recipe, ft, tech=100)
        _make_entity_with_productor(recipe, ft, tech=200)

        game = _make_game()
        service = ProductorService(game)
        service.update_phase()

        assert ProductorComponent.max_tech[recipe] == 200

    def test_product_phase_produces_for_all(self) -> None:
        """product_phase 遍历所有 ProductorComponent 执行 produce_all。"""
        gt = _make_goods_type()
        recipe = _make_raw_recipe(gt)
        ft = _make_factory_type(recipe)

        e1 = _make_entity_with_productor(recipe, ft, tech=100)
        e2 = _make_entity_with_productor(recipe, ft, tech=100)

        # 先 update_phase 让 max_tech 有值
        game = _make_game()
        service = ProductorService(game)
        service.update_phase()
        service.product_phase()

        # 每个 Entity 的 storage 应该有产出
        s1 = e1.get_component(StorageComponent)
        s2 = e2.get_component(StorageComponent)
        assert s1 is not None
        assert s2 is not None
        assert len(s1.get_batches(gt)) > 0
        assert len(s2.get_batches(gt)) > 0

    def test_no_components_no_error(self) -> None:
        """无 ProductorComponent 时两个 phase 无异常。"""
        game = _make_game()
        service = ProductorService(game)
        service.update_phase()
        service.product_phase()

    def test_update_phase_multiple_recipes(self) -> None:
        """多种 recipe 的 max_tech 各自独立更新。"""
        gt1 = _make_goods_type("硅")
        gt2 = _make_goods_type("棉花")
        r1 = _make_raw_recipe(gt1)
        r2 = _make_raw_recipe(gt2)
        ft1 = _make_factory_type(r1)
        ft2 = _make_factory_type(r2)

        e1 = _make_entity_with_productor(r1, ft1, tech=150)
        e2 = Entity()
        prod2 = e2.init_component(ProductorComponent)
        prod2.tech_values[r2] = 300
        prod2.factories[ft2].append(Factory(factory_type=ft2, build_remaining=0))

        game = _make_game()
        service = ProductorService(game)
        service.update_phase()

        assert ProductorComponent.max_tech[r1] == 150
        assert ProductorComponent.max_tech[r2] == 300
