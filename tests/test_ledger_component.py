"""LedgerComponent 测试。"""

from __future__ import annotations

import pytest

from component.base_component import BaseComponent
from component.ledger_component import LedgerComponent
from core.entity import Entity
from core.types import Loan, LoanBill, LoanType, RepaymentType


# ── 辅助工厂 ───────────────────────────────────────────────────


def _make_entity() -> tuple[Entity, LedgerComponent]:
    entity = Entity()
    ledger = entity.init_component(LedgerComponent)
    return entity, ledger


def _make_loan(
    creditor: Entity,
    debtor: Entity,
    principal: int = 10000,
    rate: int = 500,
    term: int = 5,
    loan_type: LoanType = LoanType.CORPORATE_LOAN,
    repayment_type: RepaymentType = RepaymentType.EQUAL_PRINCIPAL,
    remaining: int | None = None,
    elapsed: int = 0,
    accrued_interest: int = 0,
) -> Loan:
    return Loan(
        creditor=creditor,
        debtor=debtor,
        principal=principal,
        rate=rate,
        term=term,
        loan_type=loan_type,
        repayment_type=repayment_type,
        remaining=remaining,
        elapsed=elapsed,
        accrued_interest=accrued_interest,
    )


# ── 基础结构 ───────────────────────────────────────────────────


class TestLedgerComponentInit:
    def test_inherits_base_component(self) -> None:
        assert issubclass(LedgerComponent, BaseComponent)

    def test_init_via_entity(self) -> None:
        entity, ledger = _make_entity()
        assert isinstance(ledger, LedgerComponent)
        assert ledger.outer is entity

    def test_initial_state(self) -> None:
        _, ledger = _make_entity()
        assert ledger.cash == 0
        assert ledger.receivables == []
        assert ledger.payables == []
        assert ledger.bills == []


# ── 查询方法 ───────────────────────────────────────────────────


class TestLedgerQueries:
    def test_total_receivables(self) -> None:
        bank, bank_ledger = _make_entity()
        company, _ = _make_entity()
        loan_a = _make_loan(bank, company, principal=5000, remaining=5000)
        loan_b = _make_loan(bank, company, principal=3000, remaining=3000)
        bank_ledger.receivables.extend([loan_a, loan_b])
        assert bank_ledger.total_receivables() == 8000

    def test_total_payables(self) -> None:
        _, debtor_ledger = _make_entity()
        creditor, _ = _make_entity()
        loan = _make_loan(creditor, debtor_ledger.outer, principal=5000, remaining=5000)
        debtor_ledger.payables.append(loan)
        assert debtor_ledger.total_payables() == 5000

    def test_net_financial_assets(self) -> None:
        bank, bank_ledger = _make_entity()
        company, _ = _make_entity()
        bank_ledger.cash = 10000
        recv = _make_loan(bank, company, principal=8000, remaining=8000)
        bank_ledger.receivables.append(recv)
        pay = _make_loan(company, bank, principal=5000, remaining=5000)
        bank_ledger.payables.append(pay)
        assert bank_ledger.net_financial_assets() == 13000  # 10000 + 8000 - 5000

    def test_filter_loans_from_receivables(self) -> None:
        bank, bank_ledger = _make_entity()
        company, _ = _make_entity()
        corp_loan = _make_loan(bank, company, loan_type=LoanType.CORPORATE_LOAN)
        bond = _make_loan(bank, company, loan_type=LoanType.BOND)
        bank_ledger.receivables.extend([corp_loan, bond])
        assert bank_ledger.filter_loans(LoanType.CORPORATE_LOAN) == [corp_loan]
        assert bank_ledger.filter_loans(LoanType.BOND) == [bond]

    def test_filter_loans_from_payables(self) -> None:
        _, debtor_ledger = _make_entity()
        creditor, _ = _make_entity()
        deposit = _make_loan(creditor, debtor_ledger.outer, loan_type=LoanType.DEPOSIT)
        debtor_ledger.payables.append(deposit)
        assert debtor_ledger.filter_loans(LoanType.DEPOSIT) == [deposit]

    def test_filter_loans_combines_both_lists(self) -> None:
        entity, ledger = _make_entity()
        other, _ = _make_entity()
        recv = _make_loan(entity, other, loan_type=LoanType.CORPORATE_LOAN)
        pay = _make_loan(other, entity, loan_type=LoanType.CORPORATE_LOAN)
        ledger.receivables.append(recv)
        ledger.payables.append(pay)
        result = ledger.filter_loans(LoanType.CORPORATE_LOAN)
        assert recv in result
        assert pay in result
        assert len(result) == 2

    def test_empty_queries(self) -> None:
        _, ledger = _make_entity()
        assert ledger.total_receivables() == 0
        assert ledger.total_payables() == 0
        assert ledger.net_financial_assets() == 0
        assert ledger.filter_loans(LoanType.CORPORATE_LOAN) == []


# ── issue_loan ─────────────────────────────────────────────────


class TestIssueLoan:
    def test_issue_corporate_loan(self) -> None:
        """银行(cash=50000) 向公司(cash=0) 发放 10000 贷款。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000

        loan = _make_loan(bank, company, principal=10000)
        bank_ledger.issue_loan(loan)

        assert bank_ledger.cash == 40000
        assert company_ledger.cash == 10000
        assert loan in bank_ledger.receivables
        assert loan in company_ledger.payables

    def test_issue_deposit(self) -> None:
        """居民(cash=5000) 存款到银行。居民是债权人。"""
        folk, folk_ledger = _make_entity()
        bank, bank_ledger = _make_entity()
        folk_ledger.cash = 5000

        deposit = _make_loan(
            folk, bank, principal=5000, term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger.issue_loan(deposit)

        assert folk_ledger.cash == 0
        assert bank_ledger.cash == 5000
        assert deposit in folk_ledger.receivables
        assert deposit in bank_ledger.payables


# ── generate_bills ─────────────────────────────────────────────


class TestGenerateBills:
    def test_generates_bills_for_payables(self) -> None:
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000

        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)

        bills = company_ledger.generate_bills()
        assert len(bills) == 1
        assert bills[0].loan is loan
        assert bills[0].principal_due == 2000
        assert bills[0].interest_due == 500
        assert bills[0].total_due == 2500
        assert bills[0].total_paid == 0

    def test_bills_stored_in_component(self) -> None:
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000)
        bank_ledger.issue_loan(loan)

        bills = company_ledger.generate_bills()
        assert company_ledger.bills is bills

    def test_priority_order(self) -> None:
        """DEPOSIT 排在 CORPORATE_LOAN 前面。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 100000

        corp_loan = _make_loan(
            bank, company, principal=10000,
            loan_type=LoanType.CORPORATE_LOAN,
        )
        deposit = _make_loan(
            bank, company, principal=5000, term=3,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        bank_ledger.issue_loan(corp_loan)
        bank_ledger.issue_loan(deposit)

        bills = company_ledger.generate_bills()
        assert len(bills) == 2
        assert bills[0].loan.loan_type == LoanType.DEPOSIT
        assert bills[1].loan.loan_type == LoanType.CORPORATE_LOAN

    def test_demand_deposit_generates_zero_bill(self) -> None:
        """活期存款(term=0)生成 total_due=0 的账单，利息记入 accrued_delta。"""
        folk, folk_ledger = _make_entity()
        bank, bank_ledger = _make_entity()
        folk_ledger.cash = 10000

        deposit = _make_loan(
            folk, bank, principal=10000, rate=500, term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger.issue_loan(deposit)

        bills = bank_ledger.generate_bills()
        assert len(bills) == 1
        assert bills[0].total_due == 0
        assert bills[0].accrued_delta == 500  # 10000 * 500 // 10000

    def test_does_not_mutate_loan(self) -> None:
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)

        company_ledger.generate_bills()
        assert loan.remaining == 10000
        assert loan.elapsed == 0
        assert loan.accrued_interest == 0


# ── settle_all ─────────────────────────────────────────────────


class TestSettleAll:
    def test_full_payment(self) -> None:
        """足额支付：cash 充足时全额偿还。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)
        # company cash = 10000, due = 2500 (2000 principal + 500 interest)

        company_ledger.generate_bills()
        bills = company_ledger.settle_all()

        assert len(bills) == 1
        assert bills[0].total_paid == 2500
        assert company_ledger.cash == 10000 - 2500  # 7500
        assert bank_ledger.cash == 40000 + 2500      # 42500
        assert loan.remaining == 8000                 # 10000 - 2000
        assert loan.elapsed == 1

    def test_partial_payment_interest_first(self) -> None:
        """不足额支付：优先偿还利息再偿还本金。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)
        company_ledger.cash = 1000  # 只有 1000，不够 2500

        company_ledger.generate_bills()
        bills = company_ledger.settle_all()

        assert bills[0].total_paid == 1000
        assert company_ledger.cash == 0
        assert bank_ledger.cash == 40000 + 1000   # 41000
        # 先付利息 500，剩余 500 付本金
        assert loan.remaining == 10000 - 500       # 9500
        assert loan.elapsed == 1

    def test_settle_priority(self) -> None:
        """结算优先级：DEPOSIT 先于 CORPORATE_LOAN，cash 不足时先付 DEPOSIT。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 100000

        deposit = _make_loan(
            bank, company, principal=5000, rate=500, term=3,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        corp_loan = _make_loan(
            bank, company, principal=10000, rate=500, term=5,
            loan_type=LoanType.CORPORATE_LOAN,
        )
        bank_ledger.issue_loan(deposit)
        bank_ledger.issue_loan(corp_loan)
        # company cash = 15000
        # deposit due: 1666 + 250 = 1916 (5000//3=1666, 5000*500//10000=250)
        # corp due: 2000 + 500 = 2500
        company_ledger.cash = 3000  # 不够付全部 (1916 + 2500 = 4416)

        company_ledger.generate_bills()
        bills = company_ledger.settle_all()

        # DEPOSIT 先付完 1916，剩 1084 给 CORPORATE_LOAN
        assert bills[0].loan.loan_type == LoanType.DEPOSIT
        assert bills[0].total_paid == 1916
        assert bills[1].loan.loan_type == LoanType.CORPORATE_LOAN
        assert bills[1].total_paid == 1084
        assert company_ledger.cash == 0

    def test_loan_removed_when_repaid(self) -> None:
        """到期还清的 Loan 从双方列表移除。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(
            bank, company, principal=10000, rate=500, term=1,
            repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        bank_ledger.issue_loan(loan)
        # term=1, 一期还清: principal_due=10000, interest_due=500, total=10500
        company_ledger.cash = 10500  # 确保足额

        company_ledger.generate_bills()
        company_ledger.settle_all()

        assert loan not in company_ledger.payables
        assert loan not in bank_ledger.receivables

    def test_bullet_accrued_interest(self) -> None:
        """BULLET 非末期：accrued_interest 累加，不产生现金划转。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(
            bank, company, principal=10000, rate=500, term=5,
            repayment_type=RepaymentType.BULLET,
        )
        bank_ledger.issue_loan(loan)
        initial_company_cash = company_ledger.cash  # 10000
        initial_bank_cash = bank_ledger.cash         # 40000

        company_ledger.generate_bills()
        bills = company_ledger.settle_all()

        assert bills[0].total_due == 0
        assert bills[0].total_paid == 0
        assert bills[0].accrued_delta == 500
        assert loan.accrued_interest == 500
        assert company_ledger.cash == initial_company_cash
        assert bank_ledger.cash == initial_bank_cash
        assert loan.elapsed == 1

    def test_demand_deposit_no_cash_transfer(self) -> None:
        """活期存款(term=0)：total_due=0，不产生现金划转，利息累计。"""
        folk, folk_ledger = _make_entity()
        bank, bank_ledger = _make_entity()
        folk_ledger.cash = 10000
        deposit = _make_loan(
            folk, bank, principal=10000, rate=500, term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger.issue_loan(deposit)
        # folk cash=0, bank cash=10000

        bank_ledger.generate_bills()
        bills = bank_ledger.settle_all()

        assert len(bills) == 1
        assert bills[0].total_due == 0
        assert bills[0].total_paid == 0
        assert deposit.accrued_interest == 500
        assert bank_ledger.cash == 10000  # 不变
        assert folk_ledger.cash == 0       # 不变

    def test_multiple_rounds(self) -> None:
        """连续两个回合结算，验证状态正确累积。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)

        # 第一回合
        company_ledger.generate_bills()
        company_ledger.settle_all()
        assert loan.remaining == 8000
        assert loan.elapsed == 1

        # 第二回合
        company_ledger.generate_bills()
        company_ledger.settle_all()
        # principal_due = 10000 // 5 = 2000, interest_due = 8000 * 500 // 10000 = 400
        assert loan.remaining == 6000
        assert loan.elapsed == 2


# ── withdraw ───────────────────────────────────────────────────


class TestWithdraw:
    def test_withdraw_with_accrued_interest(self) -> None:
        """取款时一并结清 accrued_interest。"""
        folk, folk_ledger = _make_entity()
        bank, bank_ledger = _make_entity()
        folk_ledger.cash = 10000
        deposit = _make_loan(
            folk, bank, principal=10000, rate=500, term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
            accrued_interest=200,
        )
        folk_ledger.issue_loan(deposit)
        # folk cash=0, bank cash=10000

        actual = bank_ledger.withdraw(deposit, 3000)
        # 本金取出 3000 + 利息结清 200 = 实际划转 3200
        assert actual == 3000   # 返回取出的本金
        assert folk_ledger.cash == 3200  # 本金 + 利息
        assert bank_ledger.cash == 10000 - 3200  # 6800
        assert deposit.remaining == 7000
        assert deposit.accrued_interest == 0

    def test_withdraw_limited_by_bank_cash(self) -> None:
        """受限于吸储方现金，优先支付利息。"""
        folk, folk_ledger = _make_entity()
        bank, bank_ledger = _make_entity()
        folk_ledger.cash = 10000
        deposit = _make_loan(
            folk, bank, principal=10000, rate=500, term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
            accrued_interest=200,
        )
        folk_ledger.issue_loan(deposit)
        bank_ledger.cash = 1000  # 限制

        actual = bank_ledger.withdraw(deposit, 3000)
        # 可用 1000，优先付利息 200，剩 800 付本金
        assert actual == 800    # 返回实际取出本金
        assert folk_ledger.cash == 1000  # 200 利息 + 800 本金
        assert bank_ledger.cash == 0
        assert deposit.remaining == 10000 - 800  # 9200
        assert deposit.accrued_interest == 0

    def test_withdraw_removes_when_fully_repaid(self) -> None:
        """取完后 remaining=0 且 accrued_interest=0，Loan 从双方移除。"""
        folk, folk_ledger = _make_entity()
        bank, bank_ledger = _make_entity()
        folk_ledger.cash = 5000
        deposit = _make_loan(
            folk, bank, principal=5000, rate=500, term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger.issue_loan(deposit)
        # folk cash=0, bank cash=5000

        actual = bank_ledger.withdraw(deposit, 5000)
        assert actual == 5000
        assert deposit not in folk_ledger.receivables
        assert deposit not in bank_ledger.payables

    def test_withdraw_limited_by_remaining(self) -> None:
        """取款金额大于 remaining 时，最多取 remaining。"""
        folk, folk_ledger = _make_entity()
        bank, bank_ledger = _make_entity()
        folk_ledger.cash = 3000
        deposit = _make_loan(
            folk, bank, principal=3000, rate=500, term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger.issue_loan(deposit)

        actual = bank_ledger.withdraw(deposit, 10000)
        assert actual == 3000
        assert deposit.remaining == 0


# ── unpaid_bills ──────────────────────────────────────────────


class TestUnpaidBills:
    def test_returns_unpaid_bills(self) -> None:
        """返回 total_paid < total_due 的未付清账单。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)
        company_ledger.cash = 1000  # 不够 2500

        company_ledger.generate_bills()
        company_ledger.settle_all()

        unpaid = company_ledger.unpaid_bills()
        assert len(unpaid) == 1
        assert unpaid[0].total_paid < unpaid[0].total_due

    def test_no_unpaid_when_fully_paid(self) -> None:
        """全部付清时返回空列表。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)

        company_ledger.generate_bills()
        company_ledger.settle_all()

        unpaid = company_ledger.unpaid_bills()
        assert unpaid == []

    def test_demand_deposit_not_unpaid(self) -> None:
        """活期存款(total_due=0)不算未付清。"""
        folk, folk_ledger = _make_entity()
        bank, bank_ledger = _make_entity()
        folk_ledger.cash = 10000
        deposit = _make_loan(
            folk, bank, principal=10000, rate=500, term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger.issue_loan(deposit)

        bank_ledger.generate_bills()
        bank_ledger.settle_all()

        unpaid = bank_ledger.unpaid_bills()
        assert unpaid == []


# ── write_off ─────────────────────────────────────────────────


class TestWriteOff:
    def test_write_off_removes_from_both(self) -> None:
        """核销后 Loan 从债权人 receivables 和债务人 payables 中移除。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)

        bank_ledger.write_off(loan)

        assert loan not in bank_ledger.receivables
        assert loan not in company_ledger.payables

    def test_write_off_no_cash_flow(self) -> None:
        """核销不产生现金流。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)
        bank_cash_before = bank_ledger.cash
        company_cash_before = company_ledger.cash

        bank_ledger.write_off(loan)

        assert bank_ledger.cash == bank_cash_before
        assert company_ledger.cash == company_cash_before

    def test_write_off_clears_related_bills(self) -> None:
        """核销时清除与该 Loan 相关的未付账单。"""
        bank, bank_ledger = _make_entity()
        company, company_ledger = _make_entity()
        bank_ledger.cash = 50000
        loan = _make_loan(bank, company, principal=10000, rate=500, term=5)
        bank_ledger.issue_loan(loan)
        company_ledger.cash = 0  # 无法支付

        company_ledger.generate_bills()
        company_ledger.settle_all()
        assert len(company_ledger.bills) == 1

        company_ledger.write_off(loan)

        assert loan not in company_ledger.payables
        assert loan not in bank_ledger.receivables
        # 相关账单也被清除
        related = [b for b in company_ledger.bills if b.loan is loan]
        assert related == []
