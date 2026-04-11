"""全流程集成测试：创建 Game，运行 game_loop，校验结尾状态。"""
from pathlib import Path
from unittest.mock import MagicMock

from core.config import ConfigManager
from game.game import Game
from system.economy_service import EconomyService
from system.economy_models.dual_cycle_model import DualCycleModel


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
