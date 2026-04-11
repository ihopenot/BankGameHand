from __future__ import annotations

from typing import TYPE_CHECKING, List

from component.base_component import BaseComponent
from core.types import Loan

if TYPE_CHECKING:
    from core.entity import Entity


class LedgerComponent(BaseComponent):
    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        self.cash: int = 0
        self.loans: List[Loan] = []
        self.deposit: List[Loan] = []
