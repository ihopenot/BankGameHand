from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from core.entity import Entity


class Company(Entity):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.init_component(ProductorComponent)
        self.init_component(LedgerComponent)
        self.init_component(MetricComponent)
