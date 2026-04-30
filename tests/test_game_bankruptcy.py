"""测试 Game.settlement_phase 集成破产清算与市场补充。"""
from __future__ import annotations

import pytest

from component.decision.company.classic import ClassicCompanyDecisionComponent
from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.config import ConfigManager
from core.types import Loan, LoanType, RepaymentType
from entity.factory import FactoryType, Recipe
from entity.goods import GoodsType
from game.game import Game


@pytest.fixture(autouse=True)
def _reset_config():
    ConfigManager._instance = None
    yield
    ConfigManager._instance = None


@pytest.fixture(autouse=True)
def _reset_components():
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    ClassicCompanyDecisionComponent.components.clear()
    LedgerComponent.components.clear()
    StorageComponent.components.clear()
    GoodsType.types.clear()
    Recipe.recipes.clear()
    FactoryType.factory_types.clear()
    yield
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    ClassicCompanyDecisionComponent.components.clear()
    LedgerComponent.components.clear()
    StorageComponent.components.clear()
    GoodsType.types.clear()
    Recipe.recipes.clear()
    FactoryType.factory_types.clear()


class TestSettlementBankruptcy:
    """Game.settlement_phase() 集成测试。"""

    def test_bankrupt_company_destroyed_after_settlement(self) -> None:
        """结算后破产公司应被清算销毁。"""
        game = Game()
        initial_count = len(game.companies)

        # 选一家公司，给它一笔还不起的贷款
        target = game.companies[0]
        target_ledger = target.get_component(LedgerComponent)
        target_ledger.cash = 0  # 没钱

        # 创建一个银行实体作为债权人
        bank = list(game.bank_service.banks.values())[0]
        bank_ledger = bank.get_component(LedgerComponent)

        loan = Loan(
            creditor=bank,
            debtor=target,
            principal=999999,
            rate=0,
            term=1,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.BULLET,
        )
        bank_ledger.receivables.append(loan)
        target_ledger.payables.append(loan)

        # 生成账单并执行结算
        target_ledger.generate_bills()
        game.settlement_phase()

        # 公司应被销毁
        assert target.get_component(LedgerComponent) is None

    def test_creditor_receives_partial_repayment(self) -> None:
        """破产清算后债权方应收到部分偿还。"""
        game = Game()

        target = game.companies[0]
        target_ledger = target.get_component(LedgerComponent)
        original_cash = target_ledger.cash
        target_ledger.cash = 100  # 只有 100 现金

        bank = list(game.bank_service.banks.values())[0]
        bank_ledger = bank.get_component(LedgerComponent)
        bank_cash_before = bank_ledger.cash

        loan = Loan(
            creditor=bank,
            debtor=target,
            principal=999999,
            rate=0,
            term=1,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.BULLET,
        )
        bank_ledger.receivables.append(loan)
        target_ledger.payables.append(loan)

        target_ledger.generate_bills()
        game.settlement_phase()

        # 银行应收到一些清算偿还（现金 + 工厂折价）
        assert bank_ledger.cash > bank_cash_before

    def test_market_replenishment_creates_company(self) -> None:
        """产业链生产者不足时应补充新公司。"""
        game = Game()

        # 找到某种商品的所有生产者，销毁到只剩 0 个
        # 找第一个公司的 output goods type
        first_company = game.companies[0]
        first_pc = first_company.get_component(ProductorComponent)
        target_ft = list(first_pc.factories.keys())[0]
        target_gt = target_ft.recipe.output_goods_type

        # 收集所有生产该商品的公司
        producers = []
        for c in game.companies:
            pc = c.get_component(ProductorComponent)
            for ft in pc.factories:
                if ft.recipe.output_goods_type is target_gt:
                    producers.append(c)
                    break

        # 给所有生产者制造破产条件
        for p in producers:
            p_ledger = p.get_component(LedgerComponent)
            p_ledger.cash = 0
            bank = list(game.bank_service.banks.values())[0]
            loan = Loan(
                creditor=bank,
                debtor=p,
                principal=999999,
                rate=0,
                term=1,
                loan_type=LoanType.CORPORATE_LOAN,
                repayment_type=RepaymentType.BULLET,
            )
            bank.get_component(LedgerComponent).receivables.append(loan)
            p_ledger.payables.append(loan)
            p_ledger.generate_bills()

        game.settlement_phase()

        # 市场补充应创建新公司来填补该商品的生产者空缺
        new_producers = []
        for pc in ProductorComponent.components:
            for ft in pc.factories:
                if ft.recipe.output_goods_type is target_gt and len(pc.factories[ft]) > 0:
                    new_producers.append(pc)
                    break

        assert len(new_producers) >= 2  # 至少达到最低阈值
