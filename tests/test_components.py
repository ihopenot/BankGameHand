import pytest

from component.base_component import BaseComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.entity import Entity
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsType, GoodsBatch


class TestStorageComponent:
    def test_inherits_base_component(self):
        assert issubclass(StorageComponent, BaseComponent)

    def test_init_via_entity(self):
        entity = Entity()
        storage = entity.init_component(StorageComponent)
        assert isinstance(storage, StorageComponent)
        assert storage.outer is entity

    def test_empty_inventory(self):
        entity = Entity()
        storage = entity.init_component(StorageComponent)
        gt = GoodsType(name="芯片", base_price=5000)
        assert storage.get_batches(gt) == []

    def test_add_batch(self):
        entity = Entity()
        storage = entity.init_component(StorageComponent)
        gt = GoodsType(name="芯片", base_price=5000)
        batch = GoodsBatch(goods_type=gt, quantity=100, quality=0.7, brand_value=10)
        storage.add_batch(batch)
        batches = storage.get_batches(gt)
        assert len(batches) == 1
        assert batches[0] is batch

    def test_add_multiple_batches(self):
        entity = Entity()
        storage = entity.init_component(StorageComponent)
        gt = GoodsType(name="芯片", base_price=5000)
        b1 = GoodsBatch(goods_type=gt, quantity=50, quality=0.6, brand_value=0)
        b2 = GoodsBatch(goods_type=gt, quantity=80, quality=0.9, brand_value=5)
        storage.add_batch(b1)
        storage.add_batch(b2)
        assert len(storage.get_batches(gt)) == 2

    def test_different_goods_types(self):
        entity = Entity()
        storage = entity.init_component(StorageComponent)
        gt1 = GoodsType(name="芯片", base_price=5000)
        gt2 = GoodsType(name="硅", base_price=1000)
        b1 = GoodsBatch(goods_type=gt1, quantity=50, quality=0.6, brand_value=0)
        b2 = GoodsBatch(goods_type=gt2, quantity=100, quality=0.8, brand_value=0)
        storage.add_batch(b1)
        storage.add_batch(b2)
        assert len(storage.get_batches(gt1)) == 1
        assert len(storage.get_batches(gt2)) == 1


class TestRequireGoods:
    def _make_storage(self) -> tuple[Entity, StorageComponent, GoodsType]:
        entity = Entity()
        storage = entity.init_component(StorageComponent)
        gt = GoodsType(name="硅", base_price=1000)
        return entity, storage, gt

    def test_exact_quantity(self):
        """库存刚好够，精确取出。"""
        _, storage, gt = self._make_storage()
        storage.add_batch(GoodsBatch(gt, 200, quality=0.8, brand_value=10))
        result = storage.require_goods(gt, 200, base=100)
        assert result.quantity == 200
        assert result.quality == pytest.approx(0.8)
        assert result.brand_value == 10
        assert storage.get_batches(gt) == []

    def test_surplus_inventory(self):
        """库存有余，取出精确数量，剩余保留。"""
        _, storage, gt = self._make_storage()
        storage.add_batch(GoodsBatch(gt, 500, quality=0.6, brand_value=5))
        result = storage.require_goods(gt, 200, base=100)
        assert result.quantity == 200
        remaining = storage.get_batches(gt)
        assert len(remaining) == 1
        assert remaining[0].quantity == 300

    def test_insufficient_round_down_to_base(self):
        """库存不足，base>0 时向下取整到 base 整数倍。"""
        _, storage, gt = self._make_storage()
        storage.add_batch(GoodsBatch(gt, 350, quality=0.5, brand_value=0))
        result = storage.require_goods(gt, 500, base=200)
        # 350 // 200 * 200 = 200
        assert result.quantity == 200
        remaining = storage.get_batches(gt)
        assert remaining[0].quantity == 150

    def test_insufficient_base_zero_take_all(self):
        """库存不足，base=0 时能取多少取多少。"""
        _, storage, gt = self._make_storage()
        storage.add_batch(GoodsBatch(gt, 150, quality=0.7, brand_value=3))
        result = storage.require_goods(gt, 500, base=0)
        assert result.quantity == 150
        assert storage.get_batches(gt) == []

    def test_quality_descending_order(self):
        """按品质从高到低取，优先取高品质。"""
        _, storage, gt = self._make_storage()
        storage.add_batch(GoodsBatch(gt, 100, quality=0.3, brand_value=0))
        storage.add_batch(GoodsBatch(gt, 100, quality=0.9, brand_value=0))
        storage.add_batch(GoodsBatch(gt, 100, quality=0.6, brand_value=0))
        result = storage.require_goods(gt, 150, base=50)
        # 先取 quality=0.9 的 100，再从 quality=0.6 的取 50
        assert result.quantity == 150
        expected_quality = (0.9 * 100 + 0.6 * 50) / 150
        assert result.quality == pytest.approx(expected_quality)

    def test_weighted_average_quality_and_brand(self):
        """加权平均品质和品牌值。"""
        _, storage, gt = self._make_storage()
        storage.add_batch(GoodsBatch(gt, 100, quality=0.4, brand_value=10))
        storage.add_batch(GoodsBatch(gt, 300, quality=0.8, brand_value=30))
        result = storage.require_goods(gt, 400, base=100)
        # 先取 quality=0.8 的 300，再取 quality=0.4 的 100
        assert result.quantity == 400
        expected_quality = (0.8 * 300 + 0.4 * 100) / 400
        assert result.quality == pytest.approx(expected_quality)
        expected_brand = int((30 * 300 + 10 * 100) / 400)
        assert result.brand_value == expected_brand

    def test_partial_batch_consumed(self):
        """部分取走时批次剩余正确。"""
        _, storage, gt = self._make_storage()
        storage.add_batch(GoodsBatch(gt, 500, quality=0.9, brand_value=0))
        result = storage.require_goods(gt, 200, base=100)
        assert result.quantity == 200
        remaining = storage.get_batches(gt)
        assert len(remaining) == 1
        assert remaining[0].quantity == 300
        assert remaining[0].quality == 0.9

    def test_empty_inventory_returns_zero(self):
        """空库存返回数量0。"""
        _, storage, gt = self._make_storage()
        result = storage.require_goods(gt, 100, base=50)
        assert result.quantity == 0
        assert result.quality == 0.0
        assert result.brand_value == 0

    def test_insufficient_less_than_base(self):
        """库存不足且不够一个 base 单位，返回0。"""
        _, storage, gt = self._make_storage()
        storage.add_batch(GoodsBatch(gt, 50, quality=0.5, brand_value=0))
        result = storage.require_goods(gt, 500, base=200)
        # 50 // 200 * 200 = 0
        assert result.quantity == 0
        # 库存未被扣减
        remaining = storage.get_batches(gt)
        assert remaining[0].quantity == 50


class TestProductorComponent:
    def test_inherits_base_component(self):
        assert issubclass(ProductorComponent, BaseComponent)

    def test_auto_init_storage(self):
        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        storage = entity.get_component(StorageComponent)
        assert isinstance(storage, StorageComponent)
        assert prod.storage is storage

    def test_storage_already_exists(self):
        entity = Entity()
        storage = entity.init_component(StorageComponent)
        prod = entity.init_component(ProductorComponent)
        assert prod.storage is storage

    def test_tech_values(self):
        silicon = GoodsType(name="硅", base_price=1000)
        chip = GoodsType(name="芯片", base_price=5000)
        recipe = Recipe(input_goods_type=silicon, input_quantity=200,
                        output_goods_type=chip, output_quantity=100, tech_quality_weight=0.6)
        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        assert prod.tech_values == {}
        prod.tech_values[recipe] = 500
        assert prod.tech_values[recipe] == 500

    def test_brand_values(self):
        gt = GoodsType(name="芯片", base_price=5000)
        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        assert prod.brand_values == {}
        prod.brand_values[gt] = 100
        assert prod.brand_values[gt] == 100

    def test_factories_is_dict(self):
        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        assert isinstance(prod.factories, dict)
        assert len(prod.factories) == 0


# --- Helpers ---

def _make_goods() -> tuple[GoodsType, GoodsType]:
    silicon = GoodsType(name="硅", base_price=1000)
    chip = GoodsType(name="芯片", base_price=5000)
    return silicon, chip


def _make_factory_type(silicon: GoodsType, chip: GoodsType) -> FactoryType:
    recipe = Recipe(input_goods_type=silicon, input_quantity=200,
                    output_goods_type=chip, output_quantity=100, tech_quality_weight=0.6)
    return FactoryType(recipe=recipe, labor_demand=50,
                       build_cost=100000, maintenance_cost=5000, build_time=3)


def _make_raw_factory_type() -> tuple[GoodsType, FactoryType]:
    silicon = GoodsType(name="硅", base_price=1000)
    recipe = Recipe(input_goods_type=None, input_quantity=0,
                    output_goods_type=silicon, output_quantity=100, tech_quality_weight=1.0)
    ft = FactoryType(recipe=recipe, labor_demand=50,
                     build_cost=50000, maintenance_cost=3000, build_time=2)
    return silicon, ft


class TestUpdateMaxTech:
    def setup_method(self):
        ProductorComponent.max_tech = {}

    def test_update_from_empty(self):
        """从空 max_tech 更新。"""
        silicon, chip = _make_goods()
        recipe = Recipe(input_goods_type=silicon, input_quantity=200,
                        output_goods_type=chip, output_quantity=100, tech_quality_weight=0.6)
        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.tech_values[recipe] = 500
        prod.update_max_tech()
        assert ProductorComponent.max_tech[recipe] == 500

    def test_update_higher_value(self):
        """更高的科技值覆盖旧值。"""
        silicon, chip = _make_goods()
        recipe = Recipe(input_goods_type=silicon, input_quantity=200,
                        output_goods_type=chip, output_quantity=100, tech_quality_weight=0.6)
        ProductorComponent.max_tech[recipe] = 300

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.tech_values[recipe] = 500
        prod.update_max_tech()
        assert ProductorComponent.max_tech[recipe] == 500

    def test_no_update_lower_value(self):
        """更低的科技值不覆盖。"""
        silicon, chip = _make_goods()
        recipe = Recipe(input_goods_type=silicon, input_quantity=200,
                        output_goods_type=chip, output_quantity=100, tech_quality_weight=0.6)
        ProductorComponent.max_tech[recipe] = 800

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.tech_values[recipe] = 500
        prod.update_max_tech()
        assert ProductorComponent.max_tech[recipe] == 800

    def test_multiple_recipes(self):
        """多个 Recipe 各自更新。"""
        silicon, chip = _make_goods()
        r1 = Recipe(input_goods_type=silicon, input_quantity=200,
                    output_goods_type=chip, output_quantity=100, tech_quality_weight=0.6)
        r2 = Recipe(input_goods_type=None, input_quantity=0,
                    output_goods_type=silicon, output_quantity=100, tech_quality_weight=1.0)

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.tech_values[r1] = 600
        prod.tech_values[r2] = 400
        prod.update_max_tech()
        assert ProductorComponent.max_tech[r1] == 600
        assert ProductorComponent.max_tech[r2] == 400


class TestProduce:
    def setup_method(self):
        ProductorComponent.max_tech = {}

    def _set_tech(self, prod: ProductorComponent, recipe: Recipe, tech: int, max_tech: int) -> None:
        prod.tech_values[recipe] = tech
        ProductorComponent.max_tech[recipe] = max_tech

    def test_single_factory_full_supply(self):
        """单工厂满供给。"""
        silicon, chip = _make_goods()
        ft = _make_factory_type(silicon, chip)

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[ft].append(Factory(ft, build_remaining=0))
        self._set_tech(prod, ft.recipe, 600, 1000)  # ratio=0.6

        prod.storage.add_batch(GoodsBatch(silicon, 2000, quality=0.8, brand_value=0))
        prod.hired_labor_points = 200  # 满员

        result = prod.produce(ft)
        # Factory: input_quantity=200, supply=2000, material_ratio=1.0, output=100*1.0=100
        assert result.goods_type is chip
        assert result.quantity == 100
        # quality = tech_ratio * tech_quality_weight + material_quality * (1 - tech_quality_weight)
        # = 0.6 * 0.6 + 0.8 * 0.4 = 0.68
        assert result.quality == pytest.approx(0.68)
        assert result.brand_value == 0

    def test_single_factory_insufficient_round_down(self):
        """单工厂库存不足时按充足率缩减产出。"""
        silicon, chip = _make_goods()
        ft = _make_factory_type(silicon, chip)

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[ft].append(Factory(ft, build_remaining=0))
        self._set_tech(prod, ft.recipe, 500, 1000)  # ratio=0.5

        prod.storage.add_batch(GoodsBatch(silicon, 100, quality=0.5, brand_value=0))
        prod.hired_labor_points = 200  # 满员

        result = prod.produce(ft)
        # supply=100, input_quantity=200, material_ratio=0.5, output=int(100*0.5)=50
        assert result.quantity == 50

    def test_multi_factory_sequential_consume(self):
        """多工厂依次从库存取料。"""
        silicon, chip = _make_goods()
        ft = _make_factory_type(silicon, chip)

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[ft].append(Factory(ft, build_remaining=0))
        prod.factories[ft].append(Factory(ft, build_remaining=0))
        self._set_tech(prod, ft.recipe, 500, 1000)  # ratio=0.5

        prod.storage.add_batch(GoodsBatch(silicon, 300, quality=0.5, brand_value=0))
        prod.hired_labor_points = 200  # 满员（两台各 50）

        result = prod.produce(ft)
        # 工厂1: supply=200, material_ratio=1.0, output=100
        # 工厂2: supply=100, material_ratio=100/200=0.5, output=50
        # total=150
        assert result.quantity == 150

    def test_raw_factory_no_input_needed(self):
        """原料层工厂无需取料。"""
        silicon, raw_ft = _make_raw_factory_type()

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[raw_ft].append(Factory(raw_ft, build_remaining=0))
        self._set_tech(prod, raw_ft.recipe, 700, 1000)  # ratio=0.7
        prod.hired_labor_points = 200  # 满员

        result = prod.produce(raw_ft)
        assert result.quantity == 100  # output_quantity=100
        assert result.quality == pytest.approx(0.7)

    def test_brand_applied(self):
        """品牌值正确贴到产出。"""
        silicon, raw_ft = _make_raw_factory_type()

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[raw_ft].append(Factory(raw_ft, build_remaining=0))
        prod.brand_values[silicon] = 42
        self._set_tech(prod, raw_ft.recipe, 1000, 1000)  # ratio=1.0
        prod.hired_labor_points = 200  # 满员

        result = prod.produce(raw_ft)
        assert result.brand_value == 42

    def test_skip_unbuilt_factory(self):
        """跳过未建成的工厂。"""
        silicon, chip = _make_goods()
        ft = _make_factory_type(silicon, chip)

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[ft].append(Factory(ft, build_remaining=0))
        prod.factories[ft].append(Factory(ft, build_remaining=2))  # 未建成
        self._set_tech(prod, ft.recipe, 500, 1000)

        prod.storage.add_batch(GoodsBatch(silicon, 4000, quality=0.5, brand_value=0))
        prod.hired_labor_points = 200  # 满员（只有1台建成，50够用）

        result = prod.produce(ft)
        # 只有1台已建成工厂，output_quantity=100
        assert result.quantity == 100

    def test_no_inventory_returns_zero(self):
        """无库存时非原料层返回0。"""
        silicon, chip = _make_goods()
        ft = _make_factory_type(silicon, chip)

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[ft].append(Factory(ft, build_remaining=0))
        self._set_tech(prod, ft.recipe, 500, 1000)
        prod.hired_labor_points = 200  # 满员，但无库存

        result = prod.produce(ft)
        assert result.quantity == 0

    def test_zero_max_tech_quality_is_zero(self):
        """max_tech 为 0 时品质为 0。"""
        silicon, raw_ft = _make_raw_factory_type()

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[raw_ft].append(Factory(raw_ft, build_remaining=0))
        prod.hired_labor_points = 200  # 满员，但 max_tech=0
        # 不设置 max_tech

        result = prod.produce(raw_ft)
        assert result.quality == 0.0


class TestProduceAll:
    def setup_method(self):
        ProductorComponent.max_tech = {}

    def test_multi_factory_types(self):
        """多 FactoryType 全部生产并入库。"""
        silicon, raw_ft = _make_raw_factory_type()
        chip = GoodsType(name="芯片", base_price=5000)
        chip_recipe = Recipe(input_goods_type=silicon, input_quantity=200,
                             output_goods_type=chip, output_quantity=100, tech_quality_weight=0.6)
        chip_ft = FactoryType(recipe=chip_recipe, labor_demand=50,
                              build_cost=100000, maintenance_cost=5000, build_time=3)

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[raw_ft].append(Factory(raw_ft, build_remaining=0))
        prod.factories[chip_ft].append(Factory(chip_ft, build_remaining=0))

        prod.tech_values[raw_ft.recipe] = 800
        prod.tech_values[chip_recipe] = 600
        ProductorComponent.max_tech[raw_ft.recipe] = 1000
        ProductorComponent.max_tech[chip_recipe] = 1000
        prod.hired_labor_points = 200  # 两台工厂各需 50，给 200 满员

        prod.produce_all()

        # 原料工厂先生产硅: output_quantity=100, quality=0.8
        # 芯片工厂从库存取硅: input_quantity=200, 库存只有100, suff=0.5, output=int(100*0.5)=50
        silicon_batches = prod.storage.get_batches(silicon)
        chip_batches = prod.storage.get_batches(chip)

        total_silicon = sum(b.quantity for b in silicon_batches)
        total_chip = sum(b.quantity for b in chip_batches)
        assert total_chip == 50
        assert total_silicon == 0

    def test_zero_production_not_stored(self):
        """产量为0不入库。"""
        silicon, chip = _make_goods()
        ft = _make_factory_type(silicon, chip)

        entity = Entity()
        prod = entity.init_component(ProductorComponent)
        prod.factories[ft].append(Factory(ft, build_remaining=0))
        ProductorComponent.max_tech[ft.recipe] = 1000
        prod.tech_values[ft.recipe] = 500
        # 不放入任何原料

        prod.produce_all()

        chip_batches = prod.storage.get_batches(chip)
        assert len(chip_batches) == 0
