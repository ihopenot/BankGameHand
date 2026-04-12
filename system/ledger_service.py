from __future__ import annotations

from component.ledger_component import LedgerComponent


class LedgerService:
    """账本服务：统一管理所有 LedgerComponent 的账单生成与结算。"""

    def generate_bills(self) -> None:
        """对所有存活的 LedgerComponent 生成账单。"""
        for ledger in LedgerComponent.components:
            ledger.generate_bills()

    def settle_all(self) -> None:
        """对所有存活的 LedgerComponent 执行结算。"""
        for ledger in LedgerComponent.components:
            ledger.settle_all()
