import pytest

from entity.factory import Recipe, FactoryType, Factory
from entity.goods import GoodsType, GoodsBatch


class TestRecipe:
    def test_intermediate_recipe(self):
        silicon = GoodsType(name="硅", base_price=1000)
        chip = GoodsType(name="芯片", base_price=5000)
        recipe = Recipe(
            input_goods_type=silicon,
            input_quantity=200,
            output_goods_type=chip,
            output_quantity=100,
            tech_quality_weight=0.6,
        )
        assert recipe.input_goods_type is silicon
        assert recipe.input_quantity == 200
        assert recipe.output_goods_type is chip
        assert recipe.output_quantity == 100
        assert recipe.tech_quality_weight == 0.6

    def test_raw_material_recipe(self):
        silicon = GoodsType(name="硅", base_price=1000)
        recipe = Recipe(
            input_goods_type=None,
            input_quantity=0,
            output_goods_type=silicon,
            output_quantity=100,
            tech_quality_weight=1.0,
        )
        assert recipe.input_goods_type is None
        assert recipe.input_quantity == 0
        assert recipe.tech_quality_weight == 1.0


class TestFactoryType:
    def test_attributes(self):
        silicon = GoodsType(name="硅", base_price=1000)
        chip = GoodsType(name="芯片", base_price=5000)
        recipe = Recipe(
            input_goods_type=silicon,
            input_quantity=200,
            output_goods_type=chip,
            output_quantity=100,
            tech_quality_weight=0.6,
        )
        ft = FactoryType(
            recipe=recipe,
            labor_demand=50,
            build_cost=100000,
            maintenance_cost=5000,
            build_time=3,
        )
        assert ft.recipe is recipe
        assert ft.labor_demand == 50
        assert ft.build_cost == 100000
        assert ft.maintenance_cost == 5000
        assert ft.build_time == 3

    def test_no_base_production(self):
        """FactoryType 不应再包含 base_production 字段。"""
        silicon = GoodsType(name="硅", base_price=1000)
        recipe = Recipe(
            input_goods_type=None,
            input_quantity=0,
            output_goods_type=silicon,
            output_quantity=100,
            tech_quality_weight=1.0,
        )
        ft = FactoryType(
            recipe=recipe,
            labor_demand=30,
            build_cost=50000,
            maintenance_cost=3000,
            build_time=2,
        )
        assert not hasattr(ft, "base_production")


# --- Fixtures ---

def _make_chip_factory(build_remaining: int = 0) -> Factory:
    """硅→芯片工厂。"""
    silicon = GoodsType(name="硅", base_price=1000)
    chip = GoodsType(name="芯片", base_price=5000)
    recipe = Recipe(
        input_goods_type=silicon,
        input_quantity=200,
        output_goods_type=chip,
        output_quantity=100,
        tech_quality_weight=0.6,
    )
    ft = FactoryType(
        recipe=recipe,
        labor_demand=50,
        build_cost=100000,
        maintenance_cost=5000,
        build_time=3,
    )
    return Factory(factory_type=ft, build_remaining=build_remaining)


def _make_raw_factory(build_remaining: int = 0) -> Factory:
    """→硅 原料工厂。"""
    silicon = GoodsType(name="硅", base_price=1000)
    recipe = Recipe(
        input_goods_type=None,
        input_quantity=0,
        output_goods_type=silicon,
        output_quantity=100,
        tech_quality_weight=1.0,
    )
    ft = FactoryType(
        recipe=recipe,
        labor_demand=30,
        build_cost=50000,
        maintenance_cost=3000,
        build_time=2,
    )
    return Factory(factory_type=ft, build_remaining=build_remaining)


class TestFactory:
    def test_is_built_when_zero(self):
        factory = _make_chip_factory(build_remaining=0)
        assert factory.is_built is True

    def test_is_not_built_when_positive(self):
        factory = _make_chip_factory(build_remaining=2)
        assert factory.is_built is False

    def test_tick_build(self):
        factory = _make_chip_factory(build_remaining=3)
        factory.tick_build()
        assert factory.build_remaining == 2
        factory.tick_build()
        assert factory.build_remaining == 1
        factory.tick_build()
        assert factory.build_remaining == 0
        assert factory.is_built is True

    def test_tick_build_already_built(self):
        factory = _make_chip_factory(build_remaining=0)
        factory.tick_build()
        assert factory.build_remaining == 0

    def test_produce_full_supply(self):
        """满原料供应，满劳动力，传递原料品质。"""
        factory = _make_chip_factory()  # labor_demand=50
        silicon = factory.factory_type.recipe.input_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=200, quality=0.8, brand_value=0)
        result = factory.produce(supply, labor_points=50)  # 满员
        assert result.quantity == 100
        assert result.quality == 0.8
        assert result.brand_value == 0

    def test_produce_partial_supply(self):
        """原料不足减产。"""
        factory = _make_chip_factory()
        silicon = factory.factory_type.recipe.input_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=100, quality=0.6, brand_value=0)
        result = factory.produce(supply, labor_points=50)  # 满员，原料 0.5
        # material_ratio=0.5, staffing=1.0 → output=50
        assert result.quantity == 50
        assert result.quality == 0.6

    def test_produce_raw_material(self):
        """原料层生产。"""
        factory = _make_raw_factory()  # labor_demand=30
        silicon = factory.factory_type.recipe.output_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=0, quality=0.0, brand_value=0)
        result = factory.produce(supply, labor_points=30)  # 满员
        assert result.quantity == 100
        assert result.quality == 0.0

    def test_produce_zero_supply_non_raw(self):
        """非原料层零供给返回0（无论劳动力多少）。"""
        factory = _make_chip_factory()
        silicon = factory.factory_type.recipe.input_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=0, quality=0.0, brand_value=0)
        result = factory.produce(supply, labor_points=50)
        assert result.quantity == 0

    def test_produce_oversupply_capped(self):
        """超额供给充足率上限1.0。"""
        factory = _make_chip_factory()
        silicon = factory.factory_type.recipe.input_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=400, quality=0.5, brand_value=0)
        result = factory.produce(supply, labor_points=50)
        assert result.quantity == 100
        assert result.quality == 0.5

    def test_produce_not_built_raises(self):
        """未建成的工厂不能生产。"""
        factory = _make_chip_factory(build_remaining=1)
        silicon = factory.factory_type.recipe.input_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=0, quality=0.0, brand_value=0)
        with pytest.raises(RuntimeError):
            factory.produce(supply, labor_points=50)

    def test_produce_with_full_labor(self):
        """满劳动力时，产出仅受原料约束。"""
        factory = _make_chip_factory()  # labor_demand=50
        silicon = factory.factory_type.recipe.input_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=200, quality=0.8, brand_value=0)
        result = factory.produce(supply, labor_points=50)
        assert result.quantity == 100

    def test_produce_with_partial_labor(self):
        """劳动力不足时按比例减产。"""
        factory = _make_chip_factory()  # labor_demand=50
        silicon = factory.factory_type.recipe.input_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=200, quality=0.8, brand_value=0)
        result = factory.produce(supply, labor_points=25)  # 25/50=0.5
        # material_ratio=1.0, staffing=0.5 → output=50
        assert result.quantity == 50

    def test_produce_labor_limits_output_below_material(self):
        """木桶效应：劳动力和原料取最小值。"""
        factory = _make_chip_factory()  # labor_demand=50
        silicon = factory.factory_type.recipe.input_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=100, quality=0.6, brand_value=0)
        result = factory.produce(supply, labor_points=15)  # 15/50=0.3
        # material_ratio=0.5, staffing=0.3 → min=0.3 → output=30
        assert result.quantity == 30

    def test_produce_raw_with_labor(self):
        """原料层也受劳动力约束。"""
        factory = _make_raw_factory()  # labor_demand=30
        silicon = factory.factory_type.recipe.output_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=0, quality=0.0, brand_value=0)
        result = factory.produce(supply, labor_points=18)  # 18/30=0.6
        assert result.quantity == 60

    def test_produce_zero_labor_no_output(self):
        """零劳动力时无产出。"""
        factory = _make_chip_factory()
        silicon = factory.factory_type.recipe.input_goods_type
        supply = GoodsBatch(goods_type=silicon, quantity=200, quality=0.8, brand_value=0)
        result = factory.produce(supply, labor_points=0)
        assert result.quantity == 0
