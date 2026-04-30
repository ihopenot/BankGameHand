"""ProductorComponent 测试：验证劳动力分配与生产。"""
from __future__ import annotations

from component.productor_component import ProductorComponent
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsBatch, GoodsType


def _make_chip_productor(labor_demand: int = 50) -> ProductorComponent:
    """创建一个带芯片工厂的 ProductorComponent（需要原料）。"""
    from core.entity import Entity

    silicon = GoodsType(name="硅", base_price=10)
    chip = GoodsType(name="芯片", base_price=50)
    recipe = Recipe(
        input_goods_type=silicon,
        input_quantity=200,
        output_goods_type=chip,
        output_quantity=100,
        tech_quality_weight=0.6,
    )
    ft = FactoryType(recipe=recipe, labor_demand=labor_demand, build_cost=100000, maintenance_cost=5000, build_time=3)

    entity = Entity("test")
    prod = ProductorComponent(entity)
    factory = Factory(factory_type=ft, build_remaining=0)
    prod.factories[ft] = [factory]
    prod.storage.add_batch(GoodsBatch(goods_type=silicon, quantity=500, quality=0.5, brand_value=0))
    return prod


def _make_raw_productor(labor_demand: int = 30) -> ProductorComponent:
    """创建一个带原料工厂的 ProductorComponent。"""
    from core.entity import Entity

    silicon = GoodsType(name="硅", base_price=10)
    recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=silicon, output_quantity=100, tech_quality_weight=1.0)
    ft = FactoryType(recipe=recipe, labor_demand=labor_demand, build_cost=50000, maintenance_cost=3000, build_time=2)

    entity = Entity("test")
    prod = ProductorComponent(entity)
    factory = Factory(factory_type=ft, build_remaining=0)
    prod.factories[ft] = [factory]
    return prod


class TestProductorComponentProduceAll:
    def test_full_staffing_produces_fully(self):
        """hired_labor_points 充足时满产。"""
        prod = _make_raw_productor(labor_demand=30)
        prod.hired_labor_points = 100  # 远超需求 30
        prod.produce_all()

        ft = list(prod.factories.keys())[0]
        batches = prod.storage.get_batches(ft.recipe.output_goods_type)
        assert sum(b.quantity for b in batches) == 100

    def test_partial_staffing_reduces_output(self):
        """hired_labor_points 不足时，staffing_ratio 缩减产出。"""
        prod = _make_raw_productor(labor_demand=100)
        prod.hired_labor_points = 60  # staffing_ratio = 60/100 = 0.6
        prod.produce_all()

        ft = list(prod.factories.keys())[0]
        batches = prod.storage.get_batches(ft.recipe.output_goods_type)
        # output_quantity=100, staffing_ratio=0.6 → int(100*0.6)=60
        assert sum(b.quantity for b in batches) == 60

    def test_zero_labor_no_output(self):
        """hired_labor_points = 0 时无产出。"""
        prod = _make_raw_productor(labor_demand=30)
        prod.hired_labor_points = 0
        prod.produce_all()

        ft = list(prod.factories.keys())[0]
        batches = prod.storage.get_batches(ft.recipe.output_goods_type)
        assert sum(b.quantity for b in batches) == 0

    def test_multi_factory_sequential_allocation(self):
        """多台工厂按顺序分配劳动力：第一台满员，第二台可能欠缺。"""
        from core.entity import Entity

        silicon = GoodsType(name="硅2", base_price=10)
        recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=silicon, output_quantity=100, tech_quality_weight=1.0)
        ft = FactoryType(recipe=recipe, labor_demand=50, build_cost=50000, maintenance_cost=3000, build_time=2)

        entity = Entity("test")
        prod = ProductorComponent(entity)
        prod.factories[ft] = [
            Factory(factory_type=ft, build_remaining=0),  # 第一台
            Factory(factory_type=ft, build_remaining=0),  # 第二台
        ]
        prod.hired_labor_points = 75  # 总需求 100，只有 75

        prod.produce_all()

        batches = prod.storage.get_batches(silicon)
        total = sum(b.quantity for b in batches)
        # 第一台：50/50=1.0 → 100；第二台：25/50=0.5 → 50；合计 150
        assert total == 150

    def test_produce_all_with_material_constraint(self):
        """原料不足时，材料约束与劳动力约束取最小（木桶效应）。"""
        prod = _make_chip_productor(labor_demand=50)
        prod.hired_labor_points = 100  # 满员，不受人力约束
        # 库存 500 个硅，input_quantity=200，material_ratio=min(500/200, 1.0)=1.0
        prod.produce_all()

        ft = list(prod.factories.keys())[0]
        batches = prod.storage.get_batches(ft.recipe.output_goods_type)
        assert sum(b.quantity for b in batches) == 100
