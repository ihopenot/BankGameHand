"""全流程集成测试：创建 Game，运行 game_loop，校验结尾状态。"""
from pathlib import Path
from unittest.mock import MagicMock

from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.config import ConfigManager
from core.entity import Entity
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsType
from game.game import Game
from system.economy_service import EconomyService
from system.economy_models.dual_cycle_model import DualCycleModel
from system.productor_service import ProductorService


INTEGRATION_CONFIG_DIR = str(Path(__file__).parent / "config_integration")


class _GameForTest(Game):
    """可测试的 Game 子类，stub 掉未实现的 service 和 phase。"""

    def __init__(self) -> None:
        super().__init__()
        self.economy_service = EconomyService(self)
        # 其他 service 尚未实现，用 MagicMock 代替
        self.company_service = MagicMock()
        self.market_service = MagicMock()
        self.folk_service = MagicMock()

    def player_act(self) -> None:
        """跳过玩家交互。"""
        pass


class TestGameLoopIntegration:
    def setup_method(self) -> None:
        ConfigManager().load(INTEGRATION_CONFIG_DIR)

    def test_game_loop_runs_to_completion(self):
        """game_loop 正常运行到 game_end 终止"""
        game = _GameForTest()
        game.game_loop()
        assert game.round == 21

    def test_economy_index_updated_each_round(self):
        """每轮 update_phase 后 economy_index 被更新"""
        game = _GameForTest()
        indices: list[int] = []

        original_update = game.update_phase

        def tracking_update() -> None:
            original_update()
            indices.append(game.economy_service.economy_index)

        game.update_phase = tracking_update
        game.game_loop()

        assert len(indices) == 21
        for idx in indices:
            assert isinstance(idx, int)
            assert -10000 <= idx <= 10000

    def test_economy_index_final_state(self):
        """game_loop 结束后 economy_index 与独立模型逐轮计算的第 21 轮一致"""
        game = _GameForTest()
        game.game_loop()

        # 创建独立模型，逐轮计算到第 21 轮（模拟相同的 RNG 状态推进）
        verify_model = DualCycleModel()
        for t in range(1, 22):
            verify_value = verify_model.calculate(t)

        assert game.economy_service.economy_index == verify_value

    def test_economy_model_state_matches_last_round(self):
        """game_loop 结束后模型内部状态对应最后一轮"""
        game = _GameForTest()
        game.game_loop()

        state = game.economy_service.model.get_state()
        assert state["last_t"] == 21

    def test_economy_index_not_all_same(self):
        """21 轮中 economy_index 不应全部相同（正弦波 + 噪声）"""
        game = _GameForTest()
        indices: list[int] = []

        original_update = game.update_phase

        def tracking_update() -> None:
            original_update()
            indices.append(game.economy_service.economy_index)

        game.update_phase = tracking_update
        game.game_loop()

        assert len(set(indices)) > 1

    def test_reproducible_with_fixed_seed(self):
        """固定种子下两次运行结果完全一致"""
        game1 = _GameForTest()
        game1.game_loop()
        idx1 = game1.economy_service.economy_index
        state1 = game1.economy_service.model.get_state()

        # 重新 load 配置，创建新 game
        ConfigManager().load(INTEGRATION_CONFIG_DIR)
        game2 = _GameForTest()
        game2.game_loop()
        idx2 = game2.economy_service.economy_index
        state2 = game2.economy_service.model.get_state()

        assert idx1 == idx2
        assert state1 == state2


class TestProductorServiceIntegration:
    """ProductorService 集成测试：验证多公司场景下的生产流程端到端正确。"""

    def setup_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()

    def teardown_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()

    def test_update_phase_reflects_highest_tech(self) -> None:
        """多个 Entity 拥有不同 tech_values，update_phase 后 max_tech 反映最高值。"""
        gt = GoodsType(name="硅", base_price=1000, bonus_ceiling=0.0)
        recipe = Recipe(input_goods_type=None, input_quantity=0,
                        output_goods_type=gt, output_quantity=10)
        ft = FactoryType(recipe=recipe, base_production=5,
                         build_cost=10000, maintenance_cost=500, build_time=0)

        e1 = Entity()
        p1 = e1.init_component(ProductorComponent)
        p1.tech_values[recipe] = 80
        p1.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        e2 = Entity()
        p2 = e2.init_component(ProductorComponent)
        p2.tech_values[recipe] = 200
        p2.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        game = Game()
        game.economy_service = MagicMock()
        game.company_service = MagicMock()
        game.market_service = MagicMock()
        game.folk_service = MagicMock()
        service = ProductorService(game)
        service.update_phase()

        assert ProductorComponent.max_tech[recipe] == 200

    def test_product_phase_end_to_end(self) -> None:
        """多公司场景下 product_phase 执行后各公司库存有产出。"""
        gt = GoodsType(name="硅", base_price=1000, bonus_ceiling=0.0)
        recipe = Recipe(input_goods_type=None, input_quantity=0,
                        output_goods_type=gt, output_quantity=10)
        ft = FactoryType(recipe=recipe, base_production=5,
                         build_cost=10000, maintenance_cost=500, build_time=0)

        entities: list[Entity] = []
        for tech in (100, 150):
            e = Entity()
            p = e.init_component(ProductorComponent)
            p.tech_values[recipe] = tech
            p.factories[ft].append(Factory(factory_type=ft, build_remaining=0))
            entities.append(e)

        game = Game()
        game.economy_service = MagicMock()
        game.company_service = MagicMock()
        game.market_service = MagicMock()
        game.folk_service = MagicMock()
        service = ProductorService(game)

        # 先更新 max_tech，再生产
        service.update_phase()
        service.product_phase()

        for e in entities:
            storage = e.get_component(StorageComponent)
            assert storage is not None
            batches = storage.get_batches(gt)
            assert len(batches) == 1
            assert batches[0].quantity == 50  # 5 * 10

    def test_destroy_entity_removes_from_service_scope(self) -> None:
        """Entity.destroy() 后，ProductorService 不再遍历该组件。"""
        gt = GoodsType(name="硅", base_price=1000, bonus_ceiling=0.0)
        recipe = Recipe(input_goods_type=None, input_quantity=0,
                        output_goods_type=gt, output_quantity=10)
        ft = FactoryType(recipe=recipe, base_production=5,
                         build_cost=10000, maintenance_cost=500, build_time=0)

        e1 = Entity()
        p1 = e1.init_component(ProductorComponent)
        p1.tech_values[recipe] = 100
        p1.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        e2 = Entity()
        p2 = e2.init_component(ProductorComponent)
        p2.tech_values[recipe] = 200
        p2.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        # destroy e2
        e2.destroy()

        game = Game()
        game.economy_service = MagicMock()
        game.company_service = MagicMock()
        game.market_service = MagicMock()
        game.folk_service = MagicMock()
        service = ProductorService(game)
        service.update_phase()

        # max_tech 只反映 e1 的值
        assert ProductorComponent.max_tech[recipe] == 100
        assert len(ProductorComponent.components) == 1
