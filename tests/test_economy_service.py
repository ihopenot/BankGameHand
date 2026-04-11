from pathlib import Path
from unittest.mock import MagicMock
from core.config import ConfigManager
from system.economy_service import EconomyService
from system.service import Service

TEST_CONFIG_DIR = str(Path(__file__).parent / "config")


class TestEconomyService:
    def setup_method(self) -> None:
        ConfigManager().load(TEST_CONFIG_DIR)

    def _make_game(self, round_num: int = 1) -> MagicMock:
        game = MagicMock()
        game.round = round_num
        return game

    def test_inherits_from_service(self):
        """EconomyService 继承自 Service"""
        assert issubclass(EconomyService, Service)

    def test_init_loads_model_from_config(self):
        """初始化时从配置加载模型"""
        service = EconomyService(self._make_game())
        assert service.model is not None
        assert service.model.model_name == "dual_cycle"

    def test_economy_index_initial_value(self):
        """初始 economy_index 为 0"""
        service = EconomyService(self._make_game())
        assert service.economy_index == 0

    def test_update_phase_updates_economy_index(self):
        """update_phase 调用后 economy_index 被更新"""
        service = EconomyService(self._make_game(round_num=5))
        service.update_phase()
        assert isinstance(service.economy_index, int)
        assert -10000 <= service.economy_index <= 10000

    def test_update_phase_uses_game_round(self):
        """update_phase 使用 self.game.round 获取轮次"""
        service = EconomyService(self._make_game(round_num=10))
        service.update_phase()
        state = service.model.get_state()
        assert state["last_t"] == 10

    def test_update_phase_different_rounds(self):
        """不同轮次产生不同结果"""
        game = self._make_game(round_num=0)
        service = EconomyService(game)
        service.update_phase()
        idx0 = service.economy_index

        game.round = 10
        service.update_phase()
        idx10 = service.economy_index

        assert isinstance(idx0, int)
        assert isinstance(idx10, int)
