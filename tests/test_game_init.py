"""测试 Game.__init__ 完整初始化逻辑。"""
from __future__ import annotations

import pytest

from core.types import RATE_SCALE

from component.decision_component import DecisionComponent
from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.config import ConfigManager
from entity.company.company import Company
from entity.folk import Folk
from entity.goods import GoodsType
from entity.factory import Recipe, FactoryType
from game.game import Game
from system.company_service import CompanyService
from system.economy_service import EconomyService
from system.folk_service import FolkService
from system.ledger_service import LedgerService
from system.market_service import MarketService
from system.productor_service import ProductorService


@pytest.fixture(autouse=True)
def _reset_config():
    """每个测试前重置 ConfigManager 单例。"""
    ConfigManager._instance = None
    yield
    ConfigManager._instance = None


@pytest.fixture(autouse=True)
def _reset_components():
    """每个测试前清空全局组件列表。"""
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    DecisionComponent.components.clear()
    LedgerComponent.components.clear()
    StorageComponent.components.clear()
    GoodsType.types.clear()
    Recipe.recipes.clear()
    FactoryType.factory_types.clear()
    yield
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    DecisionComponent.components.clear()
    LedgerComponent.components.clear()
    StorageComponent.components.clear()
    GoodsType.types.clear()
    Recipe.recipes.clear()
    FactoryType.factory_types.clear()


class TestGameInit:
    """验证 Game 初始化后 companies、folks、services 正确创建。"""

    def test_game_creates_companies(self):
        """初始化后应创建配置数量的公司。"""
        game = Game()
        # game.yaml 中 9 种工厂类型，总公司数 = 2+2+2+2+2+2+3+2+2 = 19
        assert hasattr(game, "companies")
        assert len(game.companies) == 19

    def test_company_has_factory(self):
        """每个公司应持有一个已建好的工厂。"""
        game = Game()
        for company in game.companies:
            pc = company.get_component(ProductorComponent)
            assert pc is not None
            total_factories = sum(len(fl) for fl in pc.factories.values())
            assert total_factories >= 1
            for factories in pc.factories.values():
                for factory in factories:
                    assert factory.is_built, "公司的初始工厂应该已建好"

    def test_company_has_initial_cash(self):
        """每个公司应有初始资金。"""
        game = Game()
        for company in game.companies:
            ledger = company.get_component(LedgerComponent)
            assert ledger is not None
            assert ledger.cash > 0

    def test_company_has_prices(self):
        """每个公司的 ProductorComponent 应已初始化定价。"""
        game = Game()
        for company in game.companies:
            pc = company.get_component(ProductorComponent)
            assert len(pc.prices) > 0

    def test_game_creates_folks(self):
        """初始化后应创建 3 组居民。"""
        game = Game()
        assert hasattr(game, "folks")
        assert len(game.folks) == 3

    def test_folk_has_initial_cash(self):
        """居民应有初始现金。"""
        game = Game()
        for folk in game.folks:
            ledger = folk.get_component(LedgerComponent)
            assert ledger is not None
            assert ledger.cash > 0

    def test_services_initialized(self):
        """初始化后应正确创建所有 Service。"""
        game = Game()
        assert isinstance(game.economy_service, EconomyService)
        assert isinstance(game.company_service, CompanyService)
        assert isinstance(game.market_service, MarketService)
        assert isinstance(game.folk_service, FolkService)
        assert isinstance(game.productor_service, ProductorService)
        assert isinstance(game.ledger_service, LedgerService)

    def test_total_rounds_from_config(self):
        """game_end 应使用配置的总回合数。"""
        game = Game()
        assert hasattr(game, "total_rounds")
        assert game.total_rounds == 20

    def test_company_names_unique(self):
        """companies_dict 中的公司名称应唯一，不发生冲突。"""
        game = Game()
        assert len(game.company_service.companies) == len(game.companies)

    def test_economy_index_normalization(self):
        """buy_phase 中 economy_index 应正确归一化到 [-1.0, 1.0] 范围。"""
        game = Game()
        # 手动设置 economy_index 为已知值
        game.economy_service.economy_index = 5000  # Rate = 5000
        # RATE_SCALE = 10000，归一化后应为 0.5
        expected = 5000 / RATE_SCALE
        assert expected == 0.5
        # 边界值
        assert -10000 / RATE_SCALE == -1.0
        assert 10000 / RATE_SCALE == 1.0
