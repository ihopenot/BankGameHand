from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from core.entity import Entity


class Bank(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.init_component(LedgerComponent)
        self.init_component(MetricComponent)
