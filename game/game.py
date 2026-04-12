from __future__ import annotations

from typing import Dict, List, Optional

from core.config import ConfigManager
from entity.company.company import Company
from entity.factory import FactoryType, load_factory_types, load_recipes
from entity.folk import Folk
from entity.goods import GoodsType, load_goods_types
from core.types import RATE_SCALE, Rate
from system.company_service import CompanyService
from system.economy_service import EconomyService
from system.folk_service import FolkService
from system.ledger_service import LedgerService
from system.market_service import MarketService
from system.player_service import PlayerService
from system.productor_service import ProductorService


class Game:

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.round = 0

        # 加载配置
        config = ConfigManager()
        config.load(config_path)

        game_cfg = config.section("game")
        self.total_rounds: int = game_cfg.total_rounds

        # 加载类型注册表（类级别）
        load_goods_types()
        load_recipes()
        load_factory_types()

        # 初始化所有服务
        self.economy_service = EconomyService(self)
        self.market_service = MarketService()
        self.company_service = CompanyService()
        self.folk_service = FolkService()
        self.productor_service = ProductorService(self)
        self.ledger_service = LedgerService()
        self.player_service = PlayerService(self)

        # 业务逻辑初始化
        self.init_game()

    def init_game(self) -> None:
        """业务逻辑初始化：通过服务接口创建实体。"""
        config = ConfigManager()
        game_cfg = config.section("game")

        # 通过 CompanyService 创建公司
        factory_types = FactoryType.factory_types
        company_idx = 0
        for item in game_cfg.companies:
            ft = factory_types[item.factory_type]
            for _ in range(item.count):
                name = f"company_{company_idx}"
                self.company_service.create_company(
                    name=name,
                    factory_type=ft,
                    initial_cash=item.initial_cash,
                )
                company_idx += 1

        self.companies: List[Company] = list(self.company_service.companies.values())

        # 通过 FolkService 创建居民
        folk_initial_cash = game_cfg.folk_initial_cash
        self.folk_service.load_folks_from_config(folk_initial_cash)
        self.folks: List[Folk] = self.folk_service.folks

    def game_end(self) -> bool:
        return self.round >= self.total_rounds

    def game_loop(self) -> None:
        while not self.game_end():
            self.update_phase()
            self.sell_phase()
            self.buy_phase()
            self.product_phase()
            self.plan_phase()
            self.player_act()
            self.settlement_phase()
            self.act_phase()

    def update_phase(self) -> None:
        self.round += 1
        self.economy_service.update_phase()
        self.productor_service.update_phase()
        self.market_service.update_phase()
        self.ledger_service.generate_bills()

    def sell_phase(self) -> None:
        self.company_service.sell_phase(self.market_service)

    def buy_phase(self) -> None:
        # economy_index 是 Rate 类型（10000 = 100%），转为比率供 FolkService 使用
        economy_index = self.economy_service.economy_index / RATE_SCALE
        self.folk_service.buy_phase(self.market_service, economy_index)
        buy_intents = self.company_service.buy_phase(self.market_service)
        trades = self.market_service.match(buy_intents)
        self.company_service.settle_trades(trades)

    def product_phase(self) -> None:
        self.productor_service.product_phase()

    def plan_phase(self) -> None:
        pass  # 跳过：当前无公司 AI 决策

    def player_act(self) -> None:
        self.player_service.player_act_phase()

    def settlement_phase(self) -> None:
        self.ledger_service.settle_all()

    def act_phase(self) -> None:
        pass  # 跳过：当前无公司后决策
