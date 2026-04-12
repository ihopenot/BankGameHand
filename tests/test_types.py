"""LoanType / RepaymentType 枚举及 Loan / LoanBill 类型测试。"""

from __future__ import annotations

import pytest

from core.entity import Entity
from core.types import Loan, LoanBill, LoanType, RepaymentType


# ── LoanType 枚举 ──────────────────────────────────────────────


class TestLoanType:
    def test_members(self) -> None:
        assert LoanType.CORPORATE_LOAN.value == "corporate_loan"
        assert LoanType.DEPOSIT.value == "deposit"
        assert LoanType.INTERBANK.value == "interbank"
        assert LoanType.BOND.value == "bond"

    def test_settle_priority_order(self) -> None:
        """结算优先级：DEPOSIT(0) → INTERBANK(1) → CORPORATE_LOAN(2) → BOND(3)。"""
        assert LoanType.DEPOSIT.priority < LoanType.INTERBANK.priority
        assert LoanType.INTERBANK.priority < LoanType.CORPORATE_LOAN.priority
        assert LoanType.CORPORATE_LOAN.priority < LoanType.BOND.priority

    def test_sort_by_priority(self) -> None:
        types = [LoanType.BOND, LoanType.CORPORATE_LOAN, LoanType.DEPOSIT, LoanType.INTERBANK]
        sorted_types = sorted(types, key=lambda t: t.priority)
        assert sorted_types == [
            LoanType.DEPOSIT,
            LoanType.INTERBANK,
            LoanType.CORPORATE_LOAN,
            LoanType.BOND,
        ]


# ── RepaymentType 枚举 ─────────────────────────────────────────


class TestRepaymentType:
    def test_members(self) -> None:
        assert RepaymentType.EQUAL_PRINCIPAL.value == "equal_principal"
        assert RepaymentType.INTEREST_FIRST.value == "interest_first"
        assert RepaymentType.BULLET.value == "bullet"


# ── Loan 构造 ──────────────────────────────────────────────────


class TestLoanConstruction:
    def test_defaults(self) -> None:
        creditor = Entity()
        debtor = Entity()
        loan = Loan(
            creditor=creditor,
            debtor=debtor,
            principal=10000,
            rate=500,
            term=5,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        assert loan.remaining == 10000
        assert loan.elapsed == 0
        assert loan.accrued_interest == 0


# ── LoanBill 构造 ──────────────────────────────────────────────


class TestLoanBill:
    def test_fields(self) -> None:
        creditor = Entity()
        debtor = Entity()
        loan = Loan(
            creditor=creditor,
            debtor=debtor,
            principal=10000,
            rate=500,
            term=5,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        bill = LoanBill(
            loan=loan,
            principal_due=2000,
            interest_due=500,
            total_due=2500,
            total_paid=0,
            accrued_delta=0,
        )
        assert bill.total_due == bill.principal_due + bill.interest_due
        assert bill.total_paid == 0
        assert bill.accrued_delta == 0


# ── Loan.settle() 等额本金 ────────────────────────────────────


class TestSettleEqualPrincipal:
    def _make_loan(self, remaining: int = 10000, elapsed: int = 0) -> Loan:
        return Loan(
            creditor=Entity(),
            debtor=Entity(),
            principal=10000,
            rate=500,
            term=5,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.EQUAL_PRINCIPAL,
            remaining=remaining,
            elapsed=elapsed,
        )

    def test_first_period(self) -> None:
        loan = self._make_loan()
        bill = loan.settle()
        assert bill.principal_due == 2000       # 10000 / 5
        assert bill.interest_due == 500         # 10000 * 500 // 10000
        assert bill.total_due == 2500
        assert bill.total_paid == 0
        assert bill.accrued_delta == 0

    def test_mid_period(self) -> None:
        loan = self._make_loan(remaining=6000, elapsed=2)
        bill = loan.settle()
        assert bill.principal_due == 2000       # 10000 / 5 (固定)
        assert bill.interest_due == 300         # 6000 * 500 // 10000
        assert bill.total_due == 2300

    def test_settle_does_not_mutate(self) -> None:
        """settle() 不修改 Loan 状态。"""
        loan = self._make_loan()
        loan.settle()
        assert loan.remaining == 10000
        assert loan.elapsed == 0
        assert loan.accrued_interest == 0


# ── Loan.settle() 先息后本 ────────────────────────────────────


class TestSettleInterestFirst:
    def _make_loan(self, elapsed: int = 0) -> Loan:
        return Loan(
            creditor=Entity(),
            debtor=Entity(),
            principal=10000,
            rate=500,
            term=5,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.INTEREST_FIRST,
            remaining=10000,
            elapsed=elapsed,
        )

    def test_non_final_period(self) -> None:
        loan = self._make_loan(elapsed=0)
        bill = loan.settle()
        assert bill.principal_due == 0
        assert bill.interest_due == 500         # 10000 * 500 // 10000
        assert bill.total_due == 500
        assert bill.accrued_delta == 0

    def test_final_period(self) -> None:
        loan = self._make_loan(elapsed=4)       # term=5, 最后一期
        bill = loan.settle()
        assert bill.principal_due == 10000
        assert bill.interest_due == 500
        assert bill.total_due == 10500
        assert bill.accrued_delta == 0


# ── Loan.settle() 到期本息 ────────────────────────────────────


class TestSettleBullet:
    def _make_loan(self, elapsed: int = 0, accrued: int = 0) -> Loan:
        return Loan(
            creditor=Entity(),
            debtor=Entity(),
            principal=10000,
            rate=500,
            term=5,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.BULLET,
            remaining=10000,
            elapsed=elapsed,
            accrued_interest=accrued,
        )

    def test_non_final_period(self) -> None:
        loan = self._make_loan(elapsed=0)
        bill = loan.settle()
        assert bill.principal_due == 0
        assert bill.interest_due == 0
        assert bill.total_due == 0
        assert bill.accrued_delta == 500        # 10000 * 500 // 10000

    def test_final_period(self) -> None:
        loan = self._make_loan(elapsed=4, accrued=2000)
        bill = loan.settle()
        assert bill.principal_due == 10000
        assert bill.interest_due == 2500        # 2000 + 500(本期)
        assert bill.total_due == 12500
        assert bill.accrued_delta == 0


# ── Loan.settle() 活期存款 (term=0, BULLET 逻辑) ─────────────


class TestSettleDemandDeposit:
    def test_demand_deposit_generates_accrued_delta(self) -> None:
        loan = Loan(
            creditor=Entity(),
            debtor=Entity(),
            principal=10000,
            rate=500,
            term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
            remaining=10000,
        )
        bill = loan.settle()
        assert bill.principal_due == 0
        assert bill.interest_due == 0
        assert bill.total_due == 0
        assert bill.accrued_delta == 500
