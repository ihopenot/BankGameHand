"""破产标记测试：LedgerComponent.settle_all() 在有未全额结算账单时标记破产。"""
from __future__ import annotations

from component.ledger_component import LedgerComponent
from core.entity import Entity
from core.types import Loan, LoanType, RepaymentType


def _make_entity(cash: int = 0) -> Entity:
    """创建带 LedgerComponent 的测试实体。"""
    e = Entity("test")
    e.init_component(LedgerComponent)
    e.get_component(LedgerComponent).cash = cash
    return e


class TestBankruptcyMarking:
    """LedgerComponent 破产标记测试。"""

    def test_no_bankruptcy_when_all_bills_settled(self) -> None:
        """所有账单正常结算时 is_bankrupt 应为 False。"""
        creditor = _make_entity(cash=0)
        debtor = _make_entity(cash=10000)

        loan = Loan(
            creditor=creditor,
            debtor=debtor,
            principal=1000,
            rate=1000,  # 10%
            term=1,
            loan_type=LoanType.TRADE_PAYABLE,
            repayment_type=RepaymentType.BULLET,
        )
        debtor_ledger = debtor.get_component(LedgerComponent)
        creditor_ledger = creditor.get_component(LedgerComponent)
        creditor_ledger.receivables.append(loan)
        debtor_ledger.payables.append(loan)

        debtor_ledger.generate_bills()
        debtor_ledger.settle_all()

        assert debtor_ledger.is_bankrupt is False

    def test_bankruptcy_when_bill_not_fully_settled(self) -> None:
        """有未全额结算账单时 is_bankrupt 应为 True。"""
        creditor = _make_entity(cash=0)
        debtor = _make_entity(cash=500)  # 不够偿还 1000 本金 + 100 利息

        loan = Loan(
            creditor=creditor,
            debtor=debtor,
            principal=1000,
            rate=1000,  # 10%
            term=1,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.BULLET,
        )
        debtor_ledger = debtor.get_component(LedgerComponent)
        creditor_ledger = creditor.get_component(LedgerComponent)
        creditor_ledger.receivables.append(loan)
        debtor_ledger.payables.append(loan)

        debtor_ledger.generate_bills()
        debtor_ledger.settle_all()

        assert debtor_ledger.is_bankrupt is True

    def test_bankruptcy_flag_resets_each_round(self) -> None:
        """破产标记应在每次 settle_all 时重新判断，不保留上一回合状态。"""
        creditor = _make_entity(cash=0)
        debtor = _make_entity(cash=500)

        loan = Loan(
            creditor=creditor,
            debtor=debtor,
            principal=1000,
            rate=0,
            term=2,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        debtor_ledger = debtor.get_component(LedgerComponent)
        creditor_ledger = creditor.get_component(LedgerComponent)
        creditor_ledger.receivables.append(loan)
        debtor_ledger.payables.append(loan)

        # 第一回合：本金 500，现金 500，刚好够 → 不破产
        debtor_ledger.generate_bills()
        debtor_ledger.settle_all()
        assert debtor_ledger.is_bankrupt is False

    def test_bankruptcy_with_partial_loan_payment(self) -> None:
        """贷款部分偿还（现金不足以全额结清）应标记破产。"""
        creditor = _make_entity(cash=0)
        debtor = _make_entity(cash=300)

        loan = Loan(
            creditor=creditor,
            debtor=debtor,
            principal=1000,
            rate=0,
            term=1,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.BULLET,
        )
        debtor_ledger = debtor.get_component(LedgerComponent)
        creditor_ledger = creditor.get_component(LedgerComponent)
        creditor_ledger.receivables.append(loan)
        debtor_ledger.payables.append(loan)

        debtor_ledger.generate_bills()
        debtor_ledger.settle_all()

        assert debtor_ledger.is_bankrupt is True
        # 确认部分偿还发生
        assert debtor_ledger.cash == 0
