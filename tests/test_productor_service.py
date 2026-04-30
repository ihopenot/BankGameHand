"""ProductorService 单元测试。"""
from __future__ import annotations

import pytest
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
    return GoodsType(name=name, base_price=1000)


def _make_raw_recipe(output_gt: GoodsType) -> Recipe:
    return Recipe(
        input_goods_type=None,
        input_quantity=0,
        output_goods_type=output_gt,
        output_quantity=10,
        tech_quality_weight=1.0,
    )


def _make_intermediate_recipe(input_gt: GoodsType, output_gt: GoodsType,
                               tech_quality_weight: float = 0.6) -> Recipe:
    return Recipe(
        input_goods_type=input_gt,
        input_quantity=100,
        output_goods_type=output_gt,
        output_quantity=50,
        tech_quality_weight=tech_quality_weight,
    )


def _make_factory_type(recipe: Recipe) -> FactoryType:
    return FactoryType(
        recipe=recipe,
        labor_demand=25,
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
        """product_phase 遍历所有 ProductorComponent 执行生产（需要 hired_labor_points）。"""
        gt = _make_goods_type()
        recipe = _make_raw_recipe(gt)
        ft = _make_factory_type(recipe)  # labor_demand=25

        e1 = _make_entity_with_productor(recipe, ft, tech=100)
        e2 = _make_entity_with_productor(recipe, ft, tech=100)
        e1.get_component(ProductorComponent).hired_labor_points = 100
        e2.get_component(ProductorComponent).hired_labor_points = 100

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

    def test_quality_raw_layer_uses_tech_only(self) -> None:
        """原料层品质 = tech_rank_ratio（无原料品质混合）。"""
        gt = _make_goods_type()
        recipe = _make_raw_recipe(gt)
        ft = _make_factory_type(recipe)

        entity = _make_entity_with_productor(recipe, ft, tech=100)
        ProductorComponent.max_tech[recipe] = 200  # tech_rank_ratio = 0.5

        pc = entity.get_component(ProductorComponent)
        pc.hired_labor_points = 100  # 满员
        batch, _ = pc.produce(ft, remaining_labor=pc.hired_labor_points)
        assert batch.quality == pytest.approx(0.5)

    def test_quality_blended_with_material(self) -> None:
        """有原料输入时品质 = tech * weight + material * (1 - weight)。"""
        gt_in = _make_goods_type("硅")
        gt_out = _make_goods_type("芯片")
        recipe = _make_intermediate_recipe(gt_in, gt_out, tech_quality_weight=0.6)
        ft = _make_factory_type(recipe)

        entity = _make_entity_with_productor(recipe, ft, tech=100)
        ProductorComponent.max_tech[recipe] = 100  # tech_rank_ratio = 1.0

        # 给库存放入原料，品质 0.8
        storage = entity.get_component(StorageComponent)
        from entity.goods import GoodsBatch
        storage.add_batch(GoodsBatch(goods_type=gt_in, quantity=10000, quality=0.8, brand_value=0))

        pc = entity.get_component(ProductorComponent)
        pc.hired_labor_points = 100  # 满员
        batch, _ = pc.produce(ft, remaining_labor=pc.hired_labor_points)
        # quality = 1.0 * 0.6 + 0.8 * 0.4 = 0.92
        assert batch.quality == pytest.approx(0.92)

    def test_quality_blended_multiple_factories(self) -> None:
        """多工厂时原材料品质按产出加权平均后混合。"""
        gt_in = _make_goods_type("硅")
        gt_out = _make_goods_type("芯片")
        recipe = _make_intermediate_recipe(gt_in, gt_out, tech_quality_weight=0.5)
        ft = _make_factory_type(recipe)

        entity = Entity()
        pc = entity.init_component(ProductorComponent)
        pc.tech_values[recipe] = 100
        ProductorComponent.max_tech[recipe] = 100  # tech_rank_ratio = 1.0

        # 两个已建成工厂
        pc.factories[ft].append(Factory(factory_type=ft, build_remaining=0))
        pc.factories[ft].append(Factory(factory_type=ft, build_remaining=0))
        pc.hired_labor_points = 200  # 满员（两台各需 25）

        # 放入不同品质的原料批次
        storage = entity.get_component(StorageComponent)
        from entity.goods import GoodsBatch
        # 高品质批次（先被消耗）和低品质批次
        storage.add_batch(GoodsBatch(goods_type=gt_in, quantity=500, quality=0.9, brand_value=0))
        storage.add_batch(GoodsBatch(goods_type=gt_in, quantity=10000, quality=0.3, brand_value=0))

        batch, _ = pc.produce(ft, remaining_labor=pc.hired_labor_points)
        assert batch.quantity > 0
        # 品质应介于纯tech(1.0)和纯原料之间
        assert 0.0 < batch.quality < 1.0


class TestProductorServiceStaffing:
    def setup_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()

    def teardown_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()

    def test_product_phase_uses_hired_labor_points(self):
        """product_phase 应按工厂顺序分配 hired_labor_points。"""
        gt = _make_goods_type()
        recipe = _make_raw_recipe(gt)
        ft = _make_factory_type(recipe)  # labor_demand=25
        entity = _make_entity_with_productor(recipe, ft, tech=100)
        # 雇到了 12 个劳动力点，工厂需求 25，staffing_ratio = 12/25 = 0.48
        entity.get_component(ProductorComponent).hired_labor_points = 12

        game = _make_game()
        service = ProductorService(game)
        service.update_phase()
        service.product_phase()

        storage = entity.get_component(StorageComponent)
        batches = storage.get_batches(gt)
        total_qty = sum(b.quantity for b in batches)
        # output_quantity=10, staffing_ratio=12/25=0.48 → int(10*0.48)=4
        assert total_qty == 4

    def test_product_phase_full_staffing(self):
        """hired_labor_points 满足需求时产出不受约束。"""
        gt = _make_goods_type()
        recipe = _make_raw_recipe(gt)
        ft = _make_factory_type(recipe)  # labor_demand=25
        entity = _make_entity_with_productor(recipe, ft, tech=100)
        entity.get_component(ProductorComponent).hired_labor_points = 50  # 超过需求 25，staffing_ratio=1.0

        game = _make_game()
        service = ProductorService(game)
        service.update_phase()
        service.product_phase()

        storage = entity.get_component(StorageComponent)
        batches = storage.get_batches(gt)
        total_qty = sum(b.quantity for b in batches)
        # output_quantity=10, staffing_ratio=1.0 → 10
        assert total_qty == 10


class TestProductorServiceWageLiability:
    """工资负债现在在 labor_match_phase 生成，product_phase 不再生成工资负债。"""

    def setup_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()

    def teardown_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()

    def test_product_phase_does_not_create_wage_liability(self):
        """product_phase 不应再生成工资负债（已移至 labor_match_phase）。"""
        from component.ledger_component import LedgerComponent
        from core.types import LoanType

        gt = _make_goods_type()
        recipe = _make_raw_recipe(gt)
        ft = _make_factory_type(recipe)
        entity = _make_entity_with_productor(recipe, ft, tech=100)
        entity.init_component(LedgerComponent)
        entity.get_component(ProductorComponent).hired_labor_points = 50
        entity.wage = 10

        game = _make_game()
        service = ProductorService(game)
        service.update_phase()
        service.product_phase()

        # product_phase 后不应有工资负债
        ledger = entity.get_component(LedgerComponent)
        payables = ledger.filter_loans(LoanType.TRADE_PAYABLE)
        assert len(payables) == 0
