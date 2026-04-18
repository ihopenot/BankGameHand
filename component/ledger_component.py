from __future__ import annotations

from typing import TYPE_CHECKING, List

from component.base_component import BaseComponent
from core.types import Loan, LoanBill, LoanType

if TYPE_CHECKING:
    from core.entity import Entity


class LedgerComponent(BaseComponent):
    """金融账本组件：管理实体的金融资产和负债。"""

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        self.cash: int = 0
        self.receivables: List[Loan] = []
        self.payables: List[Loan] = []
        self.bills: List[LoanBill] = []
        self.is_bankrupt: bool = False

    # ── 查询 ──

    def total_receivables(self) -> int:
        return sum(loan.remaining for loan in self.receivables)

    def total_payables(self) -> int:
        return sum(loan.remaining for loan in self.payables)

    def net_financial_assets(self) -> int:
        return self.cash + self.total_receivables() - self.total_payables()

    def filter_loans(self, loan_type: LoanType) -> List[Loan]:
        return [
            loan
            for loan in self.receivables + self.payables
            if loan.loan_type == loan_type
        ]

    # ── 金融操作 ──

    def issue_loan(self, loan: Loan) -> None:
        """发放贷款：债权人出资，债务人收款，双边更新列表。"""
        creditor_ledger: LedgerComponent = loan.creditor.get_component(LedgerComponent)
        debtor_ledger: LedgerComponent = loan.debtor.get_component(LedgerComponent)
        creditor_ledger.cash -= loan.principal
        debtor_ledger.cash += loan.principal
        creditor_ledger.receivables.append(loan)
        debtor_ledger.payables.append(loan)

    # ── 账单生成 ──

    def generate_bills(self) -> List[LoanBill]:
        """遍历 payables 生成本期账单，按结算优先级排序。不修改 Loan 状态。"""
        sorted_payables = sorted(self.payables, key=lambda l: l.loan_type.priority)
        self.bills = [loan.settle() for loan in sorted_payables]
        return self.bills

    # ── 支付 ──

    def settle_all(self) -> List[LoanBill]:
        """按优先级遍历 bills 执行现金划转，更新 Loan 状态。"""
        for bill in self.bills:
            loan = bill.loan
            creditor_ledger: LedgerComponent = loan.creditor.get_component(LedgerComponent)

            # 处理 accrued_delta（BULLET 非末期 / 活期存款）
            if bill.accrued_delta > 0:
                loan.accrued_interest += bill.accrued_delta

            if bill.total_due > 0:
                paid = min(bill.total_due, self.cash)
                bill.total_paid = paid
                self.cash -= paid
                creditor_ledger.cash += paid

                # 优先偿还利息，剩余偿还本金
                interest_paid = min(bill.interest_due, paid)
                principal_paid = paid - interest_paid
                loan.remaining -= principal_paid

            if loan.term > 0:
                loan.elapsed += 1

            # 还清的 Loan 从双方列表移除
            if loan.remaining <= 0:
                self._remove_loan(loan)

        self.is_bankrupt = any(b.total_paid < b.total_due for b in self.bills)
        return self.bills

    def _remove_loan(self, loan: Loan) -> None:
        """从债权人 receivables 和债务人 payables 中移除 Loan。"""
        creditor_ledger: LedgerComponent = loan.creditor.get_component(LedgerComponent)
        debtor_ledger: LedgerComponent = loan.debtor.get_component(LedgerComponent)
        if loan in creditor_ledger.receivables:
            creditor_ledger.receivables.remove(loan)
        if loan in debtor_ledger.payables:
            debtor_ledger.payables.remove(loan)

    def withdraw(self, loan: Loan, amount: int) -> int:
        """活期存款取款，一并结清 accrued_interest。返回实际取出的本金。

        必须在债务方（吸储方）的 LedgerComponent 上调用。
        """
        assert loan.debtor.get_component(LedgerComponent) is self, \
            "withdraw() must be called on the debtor's LedgerComponent"
        creditor_ledger: LedgerComponent = loan.creditor.get_component(LedgerComponent)
        interest = loan.accrued_interest
        principal_want = min(amount, loan.remaining)
        total_need = interest + principal_want
        total_available = min(total_need, self.cash)

        # 优先支付利息
        interest_paid = min(interest, total_available)
        principal_paid = total_available - interest_paid

        self.cash -= total_available
        creditor_ledger.cash += total_available
        loan.remaining -= principal_paid
        loan.accrued_interest -= interest_paid

        if loan.remaining <= 0:
            self._remove_loan(loan)

        return principal_paid

    def unpaid_bills(self) -> List[LoanBill]:
        """返回未付清账单（total_paid < total_due）。"""
        return [bill for bill in self.bills if bill.total_paid < bill.total_due]

    def write_off(self, loan: Loan) -> None:
        """坏账核销：从双方列表移除 Loan，清除相关账单，不产生现金流。"""
        self.bills = [bill for bill in self.bills if bill.loan is not loan]
        self._remove_loan(loan)
