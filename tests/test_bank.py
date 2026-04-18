"""Bank 实体单元测试。"""

from component.ledger_component import LedgerComponent
from entity.bank import Bank


class TestBank:
    def test_bank_has_ledger_component(self):
        bank = Bank()
        ledger = bank.get_component(LedgerComponent)
        assert ledger is not None

    def test_bank_initial_cash_is_zero(self):
        bank = Bank()
        ledger = bank.get_component(LedgerComponent)
        assert ledger.cash == 0

    def test_bank_set_initial_cash(self):
        bank = Bank()
        ledger = bank.get_component(LedgerComponent)
        ledger.cash = 1_000_000
        assert ledger.cash == 1_000_000

    def test_bank_is_entity(self):
        from core.entity import Entity
        bank = Bank()
        assert isinstance(bank, Entity)

    def test_bank_destroy_clears_components(self):
        bank = Bank()
        bank.destroy()
        assert bank.get_component(LedgerComponent) is None
