"""tests/test_company_ledger.py — Company 初始化 LedgerComponent 测试。"""

from __future__ import annotations

from component.ledger_component import LedgerComponent
from entity.company.company import Company


class TestCompanyLedger:
    def test_company_has_ledger_component(self) -> None:
        company = Company(name="test_company")
        ledger = company.get_component(LedgerComponent)
        assert ledger is not None
        assert isinstance(ledger, LedgerComponent)

    def test_company_ledger_initial_cash_zero(self) -> None:
        company = Company(name="test_company")
        ledger = company.get_component(LedgerComponent)
        assert ledger.cash == 0
