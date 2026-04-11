from core.config import ConfigManager
from entity.goods import GoodsType, load_goods_types
from entity.factory import Recipe, FactoryType, load_recipes, load_factory_types


class TestGoodsConfig:
    def setup_method(self):
        ConfigManager._instance = None
        self.config = ConfigManager()
        self.config.load()

    def test_load_goods_types(self):
        goods_types = load_goods_types(self.config)
        assert len(goods_types) == 9
        names = {gt.name for gt in goods_types.values()}
        assert "硅" in names
        assert "芯片" in names
        assert "手机" in names
        assert "棉花" in names
        assert "布料" in names
        assert "服装" in names
        assert "小麦" in names
        assert "面粉" in names
        assert "食品" in names

    def test_goods_type_attributes(self):
        goods_types = load_goods_types(self.config)
        chip = goods_types["芯片"]
        assert chip.base_price == 5000
        assert chip.bonus_ceiling == 0.1

    def test_load_recipes(self):
        goods_types = load_goods_types(self.config)
        recipes = load_recipes(self.config, goods_types)
        assert len(recipes) == 9

    def test_raw_recipe_has_no_input(self):
        goods_types = load_goods_types(self.config)
        recipes = load_recipes(self.config, goods_types)
        silicon_recipe = recipes["硅矿开采"]
        assert silicon_recipe.input_goods_type is None
        assert silicon_recipe.input_quantity == 0
        assert silicon_recipe.output_goods_type is goods_types["硅"]

    def test_intermediate_recipe(self):
        goods_types = load_goods_types(self.config)
        recipes = load_recipes(self.config, goods_types)
        chip_recipe = recipes["芯片制造"]
        assert chip_recipe.input_goods_type is goods_types["硅"]
        assert chip_recipe.input_quantity == 200
        assert chip_recipe.output_goods_type is goods_types["芯片"]
        assert chip_recipe.output_quantity == 100

    def test_load_factory_types(self):
        goods_types = load_goods_types(self.config)
        recipes = load_recipes(self.config, goods_types)
        factory_types = load_factory_types(self.config, recipes)
        assert len(factory_types) == 9

    def test_factory_type_attributes(self):
        goods_types = load_goods_types(self.config)
        recipes = load_recipes(self.config, goods_types)
        factory_types = load_factory_types(self.config, recipes)
        chip_factory = factory_types["芯片工厂"]
        assert chip_factory.recipe is recipes["芯片制造"]
        assert chip_factory.base_production == 10
        assert chip_factory.build_cost == 100000
        assert chip_factory.maintenance_cost == 5000
        assert chip_factory.build_time == 3
