"""测试 Game.game_loop 能完整运行，各阶段按正确顺序调用。"""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.config import ConfigManager
from entity.factory import Recipe, FactoryType
from entity.goods import GoodsType
from game.game import Game


@pytest.fixture(autouse=True)
def _reset():
    ConfigManager._instance = None
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    LedgerComponent.components.clear()
    StorageComponent.components.clear()
    GoodsType.types.clear()
    Recipe.recipes.clear()
    FactoryType.factory_types.clear()
    yield
    ConfigManager._instance = None
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    LedgerComponent.components.clear()
    StorageComponent.components.clear()
    GoodsType.types.clear()
    Recipe.recipes.clear()
    FactoryType.factory_types.clear()


class TestGameLoop:
    """验证 game_loop 能完整运行若干回合无异常，各阶段按正确顺序调用。"""

    def test_game_loop_runs_to_completion(self):
        """game_loop 运行到 total_rounds 时停止。"""
        game = Game()
        game.game_loop()
        assert game.round == game.total_rounds

    def test_phase_order(self):
        """各阶段应按 update→sell→buy→product→plan→player_act→settlement→act 顺序调用。"""
        game = Game()
        game.total_rounds = 1
        phase_log = []

        original_update = game.update_phase
        original_sell = game.sell_phase
        original_buy = game.buy_phase
        original_product = game.product_phase
        original_plan = game.plan_phase
        original_player_act = game.player_act
        original_settlement = game.settlement_phase
        original_act = game.act_phase

        def log(name, fn):
            def wrapper():
                phase_log.append(name)
                fn()
            return wrapper

        game.update_phase = log("update", original_update)
        game.sell_phase = log("sell", original_sell)
        game.buy_phase = log("buy", original_buy)
        game.product_phase = log("product", original_product)
        game.plan_phase = log("plan", original_plan)
        game.player_act = log("player_act", original_player_act)
        game.settlement_phase = log("settlement", original_settlement)
        game.act_phase = log("act", original_act)

        game.game_loop()

        expected = ["update", "sell", "buy", "product", "plan", "player_act", "settlement", "act"]
        assert phase_log == expected

    def test_no_exception_full_loop(self):
        """完整运行不应抛出异常。"""
        game = Game()
        game.game_loop()
        assert game.round == game.total_rounds

    def test_round_increments_each_cycle(self):
        """每个循环 round 增加 1。"""
        game = Game()
        game.total_rounds = 3
        rounds_seen = []

        original_update = game.update_phase
        def tracking_update():
            original_update()
            rounds_seen.append(game.round)

        game.update_phase = tracking_update
        game.game_loop()

        assert rounds_seen == [1, 2, 3]

    def test_buy_phase_no_exception(self):
        """单轮 buy_phase 执行不应抛出异常。"""
        game = Game()
        game.update_phase()
        game.sell_phase()
        game.buy_phase()

    def test_settlement_phase_no_exception(self):
        """单轮 settlement_phase 执行不应抛出异常。"""
        game = Game()
        game.update_phase()
        game.sell_phase()
        game.buy_phase()
        game.product_phase()
        game.settlement_phase()
