"""BankService 单元测试。"""

from component.ledger_component import LedgerComponent
from core.entity import Entity
from core.types import LoanApplication, LoanType, RepaymentType
from entity.bank import Bank
from entity.company.company import Company
from system.bank_service import BankService, LoanOffer


class TestBankServiceCreate:
    def test_create_bank(self):
        service = BankService()
        bank = service.create_bank("bank_0", 500_000)
        assert isinstance(bank, Bank)
        ledger = bank.get_component(LedgerComponent)
        assert ledger.cash == 500_000

    def test_create_bank_tracked(self):
        service = BankService()
        service.create_bank("bank_0", 500_000)
        assert "bank_0" in service.banks
        assert len(service.banks) == 1

    def test_create_multiple_banks(self):
        service = BankService()
        service.create_bank("bank_0", 500_000)
        service.create_bank("bank_1", 1_000_000)
        assert len(service.banks) == 2
        ledger_0 = service.banks["bank_0"].get_component(LedgerComponent)
        ledger_1 = service.banks["bank_1"].get_component(LedgerComponent)
        assert ledger_0.cash == 500_000
        assert ledger_1.cash == 1_000_000


class TestBankServiceApplications:
    def _make_service_with_app(self):
        service = BankService()
        applicant = Entity("test")
        app = LoanApplication(applicant=applicant, amount=50_000)
        return service, app

    def test_collect_applications(self):
        service, app = self._make_service_with_app()
        service.collect_applications([app])
        assert len(service.get_applications()) == 1
        assert service.get_applications()[0] is app

    def test_collect_multiple_applications(self):
        service = BankService()
        app1 = LoanApplication(applicant=Entity("test"), amount=50_000)
        app2 = LoanApplication(applicant=Entity("test"), amount=80_000)
        service.collect_applications([app1, app2])
        assert len(service.get_applications()) == 2

    def test_clear_applications(self):
        service, app = self._make_service_with_app()
        service.collect_applications([app])
        service.clear_applications()
        assert len(service.get_applications()) == 0

    def test_get_applications_returns_copy(self):
        service, app = self._make_service_with_app()
        service.collect_applications([app])
        apps = service.get_applications()
        apps.clear()
        assert len(service.get_applications()) == 1


class TestBankServiceOffers:
    def _setup(self):
        service = BankService()
        bank = service.create_bank("bank_0", 500_000)
        company = Company(name="applicant")
        company.get_component(LedgerComponent).cash = 10_000
        app = LoanApplication(applicant=company, amount=100_000)
        service.collect_applications([app])
        return service, bank, company, app

    def test_add_offer(self):
        service, bank, company, app = self._setup()
        offer = LoanOffer(
            bank=bank, applicant=company, amount=100_000,
            rate=500, term=5, repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        service.add_offer(offer)
        assert len(service.get_offers()) == 1

    def test_clear_offers(self):
        service, bank, company, app = self._setup()
        offer = LoanOffer(
            bank=bank, applicant=company, amount=50_000,
            rate=500, term=5, repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        service.add_offer(offer)
        service.clear_offers()
        assert len(service.get_offers()) == 0


class TestAcceptLoans:
    def _setup_two_banks(self):
        service = BankService()
        bank_a = service.create_bank("bank_a", 500_000)
        bank_b = service.create_bank("bank_b", 500_000)
        company = Company(name="applicant")
        company.get_component(LedgerComponent).cash = 10_000
        return service, bank_a, bank_b, company

    def test_accept_lowest_rate_first(self):
        service, bank_a, bank_b, company = self._setup_two_banks()
        app = LoanApplication(applicant=company, amount=100_000)
        service.collect_applications([app])
        # bank_b offers lower rate
        service.add_offer(LoanOffer(
            bank=bank_a, applicant=company, amount=100_000,
            rate=800, term=5, repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        ))
        service.add_offer(LoanOffer(
            bank=bank_b, applicant=company, amount=100_000,
            rate=300, term=5, repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        ))
        service.accept_loans()
        # Company should only accept bank_b's offer (lower rate, full amount)
        company_ledger = company.get_component(LedgerComponent)
        assert company_ledger.cash == 10_000 + 100_000
        bank_b_ledger = bank_b.get_component(LedgerComponent)
        assert bank_b_ledger.cash == 500_000 - 100_000

    def test_partial_accept_last_offer(self):
        service, bank_a, bank_b, company = self._setup_two_banks()
        app = LoanApplication(applicant=company, amount=80_000)
        service.collect_applications([app])
        # bank_a cheaper but only offers 50k
        service.add_offer(LoanOffer(
            bank=bank_a, applicant=company, amount=50_000,
            rate=300, term=5, repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        ))
        service.add_offer(LoanOffer(
            bank=bank_b, applicant=company, amount=60_000,
            rate=500, term=5, repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        ))
        service.accept_loans()
        # Accept all 50k from bank_a + 30k from bank_b
        company_ledger = company.get_component(LedgerComponent)
        assert company_ledger.cash == 10_000 + 80_000
        bank_a_ledger = bank_a.get_component(LedgerComponent)
        assert bank_a_ledger.cash == 500_000 - 50_000
        bank_b_ledger = bank_b.get_component(LedgerComponent)
        assert bank_b_ledger.cash == 500_000 - 30_000

    def test_no_offers_no_change(self):
        service, bank_a, bank_b, company = self._setup_two_banks()
        app = LoanApplication(applicant=company, amount=100_000)
        service.collect_applications([app])
        service.accept_loans()
        company_ledger = company.get_component(LedgerComponent)
        assert company_ledger.cash == 10_000

    def test_loan_created_via_issue_loan(self):
        service, bank_a, _, company = self._setup_two_banks()
        app = LoanApplication(applicant=company, amount=50_000)
        service.collect_applications([app])
        service.add_offer(LoanOffer(
            bank=bank_a, applicant=company, amount=50_000,
            rate=500, term=5, repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        ))
        service.accept_loans()
        # Check loan exists in both ledgers
        company_ledger = company.get_component(LedgerComponent)
        bank_ledger = bank_a.get_component(LedgerComponent)
        assert len(company_ledger.payables) == 1
        assert len(bank_ledger.receivables) == 1
        loan = company_ledger.payables[0]
        assert loan.principal == 50_000
        assert loan.rate == 500
        assert loan.term == 5
        assert loan.loan_type == LoanType.CORPORATE_LOAN


class TestBankDepositRate:
    def test_bank_has_deposit_rate_default_zero(self):
        bank = Bank("test_bank")
        assert bank.deposit_rate == 0

    def test_bank_deposit_rate_settable(self):
        bank = Bank("test_bank")
        bank.deposit_rate = 150
        assert bank.deposit_rate == 150
