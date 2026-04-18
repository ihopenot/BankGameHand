"""Game 集成测试：BankService 集成与贷款流程。"""

from pathlib import Path
from unittest.mock import patch

import pytest

from core.config import ConfigManager
from game.game import Game
from system.bank_service import BankService

_TEST_CONFIG_DIR = str(Path(__file__).parent / "config_integration")


@pytest.fixture(autouse=True)
def _reset_config():
    ConfigManager._instance = None
    yield
    ConfigManager._instance = None


class TestGameBankIntegration:
    def _make_game(self):
        """创建 Game 实例，使用测试配置。"""
        with patch("system.player_service.StdinInputController") as mock_ctrl:
            mock_ctrl.return_value.get_input.return_value = "skip"
            game = Game(_TEST_CONFIG_DIR)
        return game

    def test_game_has_bank_service(self):
        game = self._make_game()
        assert hasattr(game, "bank_service")
        assert isinstance(game.bank_service, BankService)

    def test_game_creates_banks_from_config(self):
        game = self._make_game()
        assert len(game.bank_service.banks) == 1
        assert "测试银行A" in game.bank_service.banks

    def test_bank_has_initial_cash(self):
        from component.ledger_component import LedgerComponent
        game = self._make_game()
        bank = game.bank_service.banks["测试银行A"]
        ledger = bank.get_component(LedgerComponent)
        assert ledger.cash == 1_000_000

    def test_game_loop_has_loan_phases(self):
        """验证 game_loop 包含贷款申请和贷款接受阶段。"""
        game = self._make_game()
        assert hasattr(game, "loan_application_phase")
        assert hasattr(game, "loan_acceptance_phase")
        assert callable(game.loan_application_phase)
        assert callable(game.loan_acceptance_phase)
