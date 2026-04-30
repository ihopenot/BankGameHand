from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from core.entity import Entity

if TYPE_CHECKING:
    from entity.map import Plot


class Company(Entity):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.plot: Optional[Plot] = None
        self.init_component(ProductorComponent)
        self.init_component(LedgerComponent)
        self.init_component(MetricComponent)
