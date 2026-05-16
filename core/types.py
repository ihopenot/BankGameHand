from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.entity import Entity

Radio = float   # 0.0 ~ 1.0
Rate = int      # unit: 1/10000 bias count
RATE_SCALE = 10000  # 1 Rate unit = 1/RATE_SCALE
Money = int     # unit: 1/100 yuan


class LoanType(Enum):
    """贷款类型，value 附带结算优先级（数值越小越优先）。"""

    TRADE_PAYABLE = "trade_payable"
    CORPORATE_LOAN = "corporate_loan"
    DEPOSIT = "deposit"
    INTERBANK = "interbank"
    BOND = "bond"

    @property
    def priority(self) -> int:
        return _LOAN_TYPE_PRIORITY[self]


_LOAN_TYPE_PRIORITY = {
    LoanType.TRADE_PAYABLE: -1,
    LoanType.DEPOSIT: 0,
    LoanType.INTERBANK: 1,
    LoanType.CORPORATE_LOAN: 2,
    LoanType.BOND: 3,
}


class RepaymentType(Enum):
    """偿付类型。"""

    EQUAL_PRINCIPAL = "equal_principal"  # 等额本金
    INTEREST_FIRST = "interest_first"   # 先息后本
    BULLET = "bullet"                   # 到期本息


class Loan:
    """统一表达所有双边金融关系（贷款、存款、拆借、债券）。"""

    def __init__(
        self,
        creditor: Entity,
        debtor: Entity,
        principal: int,
        rate: int,
        term: int,
        loan_type: LoanType,
        repayment_type: RepaymentType,
        remaining: int | None = None,
        elapsed: int = 0,
        accrued_interest: int = 0,
    ) -> None:
        self.creditor = creditor
        self.debtor = debtor
        self.principal = principal
        self.remaining = remaining if remaining is not None else principal
        self.rate = rate
        self.term = term
        self.elapsed = elapsed
        self.loan_type = loan_type
        self.repayment_type = repayment_type
        self.accrued_interest = accrued_interest

    def settle(self) -> LoanBill:
        """根据偿付类型计算本期账单，不修改自身状态。"""
        interest = self.remaining * self.rate // 10000

        if self.term == 0:
            # 活期：走 BULLET 非末期逻辑，永远不到期
            return LoanBill(
                loan=self,
                principal_due=0,
                interest_due=0,
                total_due=0,
                total_paid=0,
                accrued_delta=interest,
            )

        if self.repayment_type == RepaymentType.EQUAL_PRINCIPAL:
            is_final = self.elapsed >= self.term - 1
            if is_final:
                principal_due = self.remaining
            else:
                principal_due = self.principal // self.term
            return LoanBill(
                loan=self,
                principal_due=principal_due,
                interest_due=interest,
                total_due=principal_due + interest,
                total_paid=0,
                accrued_delta=0,
            )

        if self.repayment_type == RepaymentType.INTEREST_FIRST:
            is_final = self.elapsed >= self.term - 1
            principal_due = self.remaining if is_final else 0
            return LoanBill(
                loan=self,
                principal_due=principal_due,
                interest_due=interest,
                total_due=principal_due + interest,
                total_paid=0,
                accrued_delta=0,
            )

        # BULLET
        is_final = self.elapsed >= self.term - 1
        if is_final:
            total_interest = self.accrued_interest + interest
            return LoanBill(
                loan=self,
                principal_due=self.remaining,
                interest_due=total_interest,
                total_due=self.remaining + total_interest,
                total_paid=0,
                accrued_delta=0,
            )
        return LoanBill(
            loan=self,
            principal_due=0,
            interest_due=0,
            total_due=0,
            total_paid=0,
            accrued_delta=interest,
        )


class LoanBill:
    """结算账单。"""

    def __init__(
        self,
        loan: Loan,
        principal_due: int,
        interest_due: int,
        total_due: int,
        total_paid: int,
        accrued_delta: int,
    ) -> None:
        self.loan = loan
        self.principal_due = principal_due
        self.interest_due = interest_due
        self.total_due = total_due
        self.total_paid = total_paid
        self.accrued_delta = accrued_delta


class LoanApplication:
    """企业贷款申请。"""

    def __init__(self, applicant: Entity, amount: int) -> None:
        self.applicant = applicant
        self.amount = amount


class LoanApprovalParam:
    """单条贷款审批参数。"""

    def __init__(
        self,
        application_index: int,
        amount: int,
        rate: int,
        term: int,
        repayment_type: RepaymentType,
    ) -> None:
        self.application_index = application_index
        self.amount = amount
        self.rate = rate
        self.term = term
        self.repayment_type = repayment_type


class PlayerAction:
    """玩家操作指令。

    action_type:
        "skip"              — 跳过回合
        "approve_loans"     — 批量审批贷款，approvals 列表包含各条审批参数
        "set_deposit_rate"  — 设置银行存款利率
    """

    def __init__(
        self,
        action_type: str = "skip",
        bank_name: str = "",
        approvals: list | None = None,
        deposit_rate: int = 0,
    ) -> None:
        self.action_type = action_type
        self.bank_name = bank_name
        self.approvals: list[LoanApprovalParam] = approvals or []
        self.deposit_rate = deposit_rate