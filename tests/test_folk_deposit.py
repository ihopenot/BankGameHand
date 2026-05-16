"""Tests for folk deposit and withdrawal logic."""
from __future__ import annotations

from component.ledger_component import LedgerComponent
from core.types import Loan, LoanType, RepaymentType
from entity.bank import Bank
from entity.folk import DemandFeedbackParams, Folk
from system.folk_service import FolkService


def _make_folk(last_spending: int = 1000, cash: int = 5000) -> Folk:
    """Create a test folk with known spending and cash."""
    folk = Folk(
        name="test_folk",
        population=100,
        w_quality=0.4,
        w_brand=0.3,
        w_price=0.3,
        spending_flow={},
        base_demands={},
        labor_participation_rate=0.7,
        labor_points_per_capita=1.0,
        demand_feedback=DemandFeedbackParams(
            savings_target_ratio=3.0,
            max_adjustment=0.2,
            sensitivity=1.0,
            min_multiplier=0.4,
            max_multiplier=1.8,
        ),
    )
    folk.last_spending = last_spending
    ledger = folk.get_component(LedgerComponent)
    ledger.cash = cash
    return folk


def _make_bank(name: str = "bank_A", cash: int = 100000, deposit_rate: int = 100) -> Bank:
    bank = Bank(name)
    bank.deposit_rate = deposit_rate
    ledger = bank.get_component(LedgerComponent)
    ledger.cash = cash
    return bank


class TestFolkDepositExcess:
    """When folk has more cash than reserve target, deposit excess."""

    def test_deposits_excess_into_bank(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        # reserve = 1000 * 3.0 = 3000, excess = 2000
        bank = _make_bank(deposit_rate=100)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank})

        folk_ledger = folk.get_component(LedgerComponent)
        assert folk_ledger.cash == 3000
        assert len(folk_ledger.receivables) == 1
        deposit = folk_ledger.receivables[0]
        assert deposit.loan_type == LoanType.DEPOSIT
        assert deposit.principal == 2000
        assert deposit.rate == 100
        assert deposit.term == 0

    def test_no_deposit_when_cash_equals_reserve(self):
        folk = _make_folk(last_spending=1000, cash=3000)
        bank = _make_bank(deposit_rate=100)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank})

        folk_ledger = folk.get_component(LedgerComponent)
        assert folk_ledger.cash == 3000
        assert len(folk_ledger.receivables) == 0

    def test_no_deposit_when_no_spending_history(self):
        folk = _make_folk(last_spending=0, cash=5000)
        bank = _make_bank(deposit_rate=100)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank})

        folk_ledger = folk.get_component(LedgerComponent)
        assert folk_ledger.cash == 5000
        assert len(folk_ledger.receivables) == 0


class TestFolkWithdrawShortfall:
    """When folk has less cash than reserve target, withdraw from deposits."""

    def test_withdraws_shortfall_from_existing_deposit(self):
        folk = _make_folk(last_spending=1000, cash=2000)
        bank = _make_bank(deposit_rate=100, cash=100000)
        # Pre-create a deposit: folk deposited 3000 earlier
        deposit = Loan(
            creditor=folk,
            debtor=bank,
            principal=3000,
            rate=100,
            term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger = folk.get_component(LedgerComponent)
        bank_ledger = bank.get_component(LedgerComponent)
        folk_ledger.receivables.append(deposit)
        bank_ledger.payables.append(deposit)

        service = FolkService(folks=[folk])
        service.folk_deposit_phase(banks={"bank_A": bank})

        # reserve = 3000, shortfall = 1000
        assert folk_ledger.cash == 3000
        assert deposit.remaining == 2000

    def test_no_withdraw_when_no_deposits(self):
        folk = _make_folk(last_spending=1000, cash=2000)
        bank = _make_bank(deposit_rate=100)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank})

        folk_ledger = folk.get_component(LedgerComponent)
        # Can't withdraw, cash stays as is
        assert folk_ledger.cash == 2000


class TestDepositAllocation:
    """Deposits are allocated across banks based on rate attractiveness."""

    def test_all_to_highest_rate_when_spread_large(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        bank_a = _make_bank("bank_A", deposit_rate=300)
        bank_b = _make_bank("bank_B", deposit_rate=50)  # 300 - 50 = 250 > 200, so score = 0
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank_a, "bank_B": bank_b})

        folk_ledger = folk.get_component(LedgerComponent)
        deposits_a = [l for l in folk_ledger.receivables if l.debtor is bank_a]
        deposits_b = [l for l in folk_ledger.receivables if l.debtor is bank_b]
        assert sum(d.principal for d in deposits_a) == 2000
        assert len(deposits_b) == 0

    def test_split_proportionally_when_rates_close(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        bank_a = _make_bank("bank_A", deposit_rate=200)
        bank_b = _make_bank("bank_B", deposit_rate=100)
        # max_rate=200, threshold=0. bank_a score=(200-0)/100=2.0, bank_b=(100-0)/100=1.0
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank_a, "bank_B": bank_b})

        folk_ledger = folk.get_component(LedgerComponent)
        deposits_a = [l for l in folk_ledger.receivables if l.debtor is bank_a]
        deposits_b = [l for l in folk_ledger.receivables if l.debtor is bank_b]
        total_a = sum(d.principal for d in deposits_a)
        total_b = sum(d.principal for d in deposits_b)
        assert total_a + total_b == 2000
        # bank_a gets 2/3, bank_b gets 1/3
        assert total_a > total_b

    def test_no_deposit_when_all_rates_zero(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        bank_a = _make_bank("bank_A", deposit_rate=0)
        bank_b = _make_bank("bank_B", deposit_rate=0)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank_a, "bank_B": bank_b})

        folk_ledger = folk.get_component(LedgerComponent)
        assert len(folk_ledger.receivables) == 0
        assert folk_ledger.cash == 5000


class TestDepositAccumulation:
    """Deposits accumulate across rounds."""

    def test_adds_new_deposit_each_round(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        bank = _make_bank("bank_A", deposit_rate=100)
        # Pre-existing deposit
        existing = Loan(
            creditor=folk,
            debtor=bank,
            principal=1000,
            rate=100,
            term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger = folk.get_component(LedgerComponent)
        bank_ledger = bank.get_component(LedgerComponent)
        folk_ledger.receivables.append(existing)
        bank_ledger.payables.append(existing)

        service = FolkService(folks=[folk])
        service.folk_deposit_phase(banks={"bank_A": bank})

        # reserve=3000, excess=2000, new deposit created
        deposits = [l for l in folk_ledger.receivables if l.loan_type == LoanType.DEPOSIT]
        total_deposited = sum(d.remaining for d in deposits)
        assert total_deposited == 3000  # 1000 existing + 2000 new
        assert folk_ledger.cash == 3000


class TestEndToEnd:
    """Full deposit/withdraw cycle."""

    def test_deposit_then_withdraw(self):
        folk = _make_folk(last_spending=1000, cash=6000)
        bank = _make_bank("bank_A", deposit_rate=150, cash=100000)
        service = FolkService(folks=[folk])

        # Phase 1: deposit excess (reserve=3000, excess=3000)
        service.folk_deposit_phase(banks={"bank_A": bank})
        folk_ledger = folk.get_component(LedgerComponent)
        assert folk_ledger.cash == 3000

        # Simulate next round: higher spending, low cash
        folk.last_spending = 2000
        folk_ledger.cash = 1000

        # Phase 2: withdraw shortfall (reserve=6000, shortfall=5000, deposit has 3000)
        service.folk_deposit_phase(banks={"bank_A": bank})
        assert folk_ledger.cash == 4000  # 1000 + 3000 withdrawn
