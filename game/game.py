from __future__ import annotations

from typing import Dict, List, Optional

from component.decision.company.ai import AICompanyDecisionComponent
from component.productor_component import ProductorComponent
from core.config import ConfigManager
from entity.company.company import Company
from entity.factory import FactoryType, load_factory_types, load_recipes
from entity.folk import Folk
from entity.goods import GoodsType, load_goods_types
from core.types import RATE_SCALE, Rate
from system.bank_service import BankService
from system.company_service import CompanyService
from system.decision_service import DecisionService
from system.economy_service import EconomyService
from system.folk_service import FolkService
from system.labor_service import LaborService
from system.ledger_service import LedgerService
from system.market_service import MarketService
from system.metric_service import MetricService
from system.player_service import PlayerService
from system.productor_service import ProductorService


class Game:

    def __init__(self, config_path: Optional[str] = None, input_controller=None) -> None:
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
        self.player_service = PlayerService(self, input_controller=input_controller)
        self.decision_service = DecisionService()
        self.bank_service = BankService()
        self.metric_service = MetricService()
        self.labor_service = LaborService()

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
            decision = item.decision_component
            for _ in range(item.count):
                name = f"company_{company_idx}"
                self.company_service.create_company(
                    name=name,
                    factory_type=ft,
                    initial_cash=item.initial_cash,
                    decision_component=decision,
                    initial_wage=item.initial_wage,
                )
                company_idx += 1

        self.companies: List[Company] = list(self.company_service.companies.values())

        # 通过 FolkService 创建居民
        folk_initial_cash = game_cfg.folk_initial_cash
        self.folk_service.load_folks_from_config(folk_initial_cash)
        self.folks: List[Folk] = self.folk_service.folks

        # 通过 BankService 创建银行
        for item in game_cfg.banks:
            self.bank_service.create_bank(
                name=item.name,
                initial_cash=item.initial_cash,
            )

    def game_end(self) -> bool:
        return self.round >= self.total_rounds

    def game_loop(self) -> None:
        self.player_service.input_controller.on_game_start(self)
        # 首轮预热：为所有 AI 公司 prepare session
        self.decision_service.prepare_next_round(self.companies)
        while not self.game_end():
            self.update_phase()
            self.sell_phase()
            self.buy_phase()
            self.plan_phase()
            self.maintenance_phase()
            self.labor_match_phase()
            self.product_phase()
            self.loan_application_phase()
            self.player_act()
            self.loan_acceptance_phase()
            self.settlement_phase()
            self.act_phase()
            self.snapshot_phase()
        # 游戏结束清理：关闭所有 prepared session
        AICompanyDecisionComponent.cleanup_sessions()
        self.player_service.input_controller.on_game_end(self)

    def update_phase(self) -> None:
        self.round += 1
        self.metric_service.reset_all()
        self.economy_service.update_phase()
        self.productor_service.update_phase()
        self.market_service.update_phase()
        self.ledger_service.generate_bills()

    def sell_phase(self) -> None:
        self.company_service.sell_phase(self.market_service)

    def buy_phase(self) -> None:
        economy_index = self.economy_service.economy_index / RATE_SCALE
        self.folk_service.buy_phase(self.market_service, economy_index)
        buy_intents = self.company_service.buy_phase(self.market_service, self.decision_service)
        trades = self.market_service.match(buy_intents)
        self.company_service.settle_trades(trades)

    def product_phase(self) -> None:
        self.productor_service.product_phase()

    def plan_phase(self) -> None:
        # 传递市场数据给 DecisionService
        economy_index = self.economy_service.economy_index / RATE_SCALE
        all_sell_orders = [
            order for orders in self.market_service._orders.values() for order in orders
        ]
        self.decision_service.set_market_data(
            sell_orders=all_sell_orders,
            trades=self.market_service.last_trades,
            economy_index=economy_index,
        )
        self.decision_service.plan_phase(self.companies)

    def maintenance_phase(self) -> None:
        """维护阶段：扣维护费，标记未维护工厂。"""
        self.decision_service.maintenance_phase(self.companies, self.folks)

    def labor_match_phase(self) -> None:
        """劳动力匹配阶段：匹配岗位与劳动力，生成工资负债。"""
        hire_records = self.labor_service.match(self.companies, self.folks)
        self.labor_service.apply(self.companies, hire_records)

    def loan_application_phase(self) -> None:
        """贷款申请阶段：收集企业贷款申请。"""
        self.bank_service.clear_applications()
        applications = self.decision_service.calc_loan_needs(self.companies)
        self.bank_service.collect_applications(applications)

    def player_act(self) -> None:
        """玩家操作阶段：展示信息，获取 PlayerAction 处理贷款审批。"""
        self.player_service.player_act_phase(self.bank_service)

    def loan_acceptance_phase(self) -> None:
        """贷款接受阶段：企业按利率排序接受贷款。"""
        self.bank_service.accept_loans()
        self.bank_service.clear_offers()

    def settlement_phase(self) -> None:
        self.ledger_service.settle_all()
        self.company_service.process_bankruptcies()
        self.company_service.replenish_market()
        self.companies = list(self.company_service.companies.values())

    def act_phase(self) -> None:
        self.decision_service.act_phase(self.companies, self.folks)

    def snapshot_phase(self) -> None:
        self.metric_service.snapshot_phase(self.round)
