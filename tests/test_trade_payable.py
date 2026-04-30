"""tests/test_trade_payable.py — TRADE_PAYABLE 贷款类型测试。"""

from __future__ import annotations

from core.entity import Entity
from component.ledger_component import LedgerComponent
from core.types import Loan, LoanType, RepaymentType


class TestTradePayableType:
    def test_trade_payable_exists(self) -> None:
        assert hasattr(LoanType, "TRADE_PAYABLE")

    def test_trade_payable_highest_priority(self) -> None:
        """TRADE_PAYABLE 优先级数值最小（最优先偿还）。"""
        tp_priority = LoanType.TRADE_PAYABLE.priority
        for lt in LoanType:
            if lt is not LoanType.TRADE_PAYABLE:
                assert tp_priority < lt.priority, (
                    f"TRADE_PAYABLE priority {tp_priority} should be < {lt.name} priority {lt.priority}"
                )


class TestTradePayableLoan:
    def test_create_trade_payable_loan(self) -> None:
        creditor = Entity("test")
        creditor.init_component(LedgerComponent)
        debtor = Entity("test")
        debtor.init_component(LedgerComponent)

        loan = Loan(
            creditor=creditor,
            debtor=debtor,
            principal=5000,
            rate=0,
            term=1,
            loan_type=LoanType.TRADE_PAYABLE,
            repayment_type=RepaymentType.BULLET,
        )
        assert loan.loan_type == LoanType.TRADE_PAYABLE
        assert loan.principal == 5000

    def test_trade_payable_settles_before_others(self) -> None:
        """生成账单时，TRADE_PAYABLE 排在其他类型之前。"""
        creditor = Entity("test")
        creditor.init_component(LedgerComponent)
        creditor_ledger = creditor.get_component(LedgerComponent)
        creditor_ledger.cash = 100000

        debtor = Entity("test")
        debtor.init_component(LedgerComponent)
        debtor_ledger = debtor.get_component(LedgerComponent)
        debtor_ledger.cash = 10000

        # 创建两笔贷款：一笔 TRADE_PAYABLE，一笔 CORPORATE_LOAN
        trade_loan = Loan(
            creditor=creditor, debtor=debtor, principal=3000, rate=0,
            term=1, loan_type=LoanType.TRADE_PAYABLE,
            repayment_type=RepaymentType.BULLET,
        )
        corp_loan = Loan(
            creditor=creditor, debtor=debtor, principal=2000, rate=0,
            term=1, loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.BULLET,
        )
        debtor_ledger.payables.extend([corp_loan, trade_loan])
        creditor_ledger.receivables.extend([corp_loan, trade_loan])

        bills = debtor_ledger.generate_bills()

        # TRADE_PAYABLE 应该排在 CORPORATE_LOAN 之前
        assert bills[0].loan.loan_type == LoanType.TRADE_PAYABLE
        assert bills[1].loan.loan_type == LoanType.CORPORATE_LOAN
