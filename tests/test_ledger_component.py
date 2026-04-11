from __future__ import annotations

from component.base_component import BaseComponent
from component.ledger_component import LedgerComponent
from core.entity import Entity
from core.types import Loan


class TestLedgerComponent:
    def test_inherits_base_component(self):
        assert issubclass(LedgerComponent, BaseComponent)

    def test_init_via_entity(self):
        entity = Entity()
        ledger = entity.init_component(LedgerComponent)
        assert isinstance(ledger, LedgerComponent)
        assert ledger.outer is entity

    def test_get_via_entity(self):
        entity = Entity()
        entity.init_component(LedgerComponent)
        ledger = entity.get_component(LedgerComponent)
        assert isinstance(ledger, LedgerComponent)

    def test_has_original_fields(self):
        entity = Entity()
        ledger = entity.init_component(LedgerComponent)
        assert hasattr(ledger, 'cash')
        assert hasattr(ledger, 'loans')
        assert hasattr(ledger, 'deposit')
        assert ledger.cash == 0
        assert ledger.loans == []
        assert ledger.deposit == []
