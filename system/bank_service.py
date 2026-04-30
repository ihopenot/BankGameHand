from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List

from component.ledger_component import LedgerComponent
from core.types import Loan, LoanApplication, LoanType, RepaymentType
from entity.bank import Bank

if TYPE_CHECKING:
    from core.entity import Entity


class LoanOffer:
    """银行对企业贷款申请的报价。"""

    def __init__(
        self,
        bank: Bank,
        applicant: Entity,
        amount: int,
        rate: int,
        term: int,
        repayment_type: RepaymentType,
    ) -> None:
        self.bank = bank
        self.applicant = applicant
        self.amount = amount
        self.rate = rate
        self.term = term
        self.repayment_type = repayment_type


class BankService:
    def __init__(self) -> None:
        self.banks: Dict[str, Bank] = {}
        self._applications: List[LoanApplication] = []
        self._offers: List[LoanOffer] = []

    def create_bank(self, name: str, initial_cash: int) -> Bank:
        bank = Bank(name)
        ledger = bank.get_component(LedgerComponent)
        ledger.cash = initial_cash
        self.banks[name] = bank
        return bank

    # ── 贷款申请 ──

    def collect_applications(self, applications: List[LoanApplication]) -> None:
        self._applications.extend(applications)

    def get_applications(self) -> List[LoanApplication]:
        return list(self._applications)

    def clear_applications(self) -> None:
        self._applications.clear()

    # ── 贷款报价 ──

    def add_offer(self, offer: LoanOffer) -> None:
        self._offers.append(offer)

    def get_offers(self) -> List[LoanOffer]:
        return list(self._offers)

    def clear_offers(self) -> None:
        self._offers.clear()

    # ── 贷款接受 ──

    def accept_loans(self) -> None:
        """企业按利率从低到高接受报价，直到满足借款需求。"""
        # 按申请企业分组报价
        offers_by_applicant: Dict[Entity, List[LoanOffer]] = defaultdict(list)
        for offer in self._offers:
            offers_by_applicant[offer.applicant].append(offer)

        # 按申请企业分组申请
        app_by_applicant: Dict[Entity, LoanApplication] = {}
        for app in self._applications:
            app_by_applicant[app.applicant] = app

        for applicant, app in app_by_applicant.items():
            offers = offers_by_applicant.get(applicant, [])
            if not offers:
                continue
            # 按利率从低到高排序
            offers.sort(key=lambda o: o.rate)
            remaining_need = app.amount
            for offer in offers:
                if remaining_need <= 0:
                    break
                accept_amount = min(offer.amount, remaining_need)
                loan = Loan(
                    creditor=offer.bank,
                    debtor=applicant,
                    principal=accept_amount,
                    rate=offer.rate,
                    term=offer.term,
                    loan_type=LoanType.CORPORATE_LOAN,
                    repayment_type=offer.repayment_type,
                )
                ledger = applicant.get_component(LedgerComponent)
                ledger.issue_loan(loan)
                remaining_need -= accept_amount
