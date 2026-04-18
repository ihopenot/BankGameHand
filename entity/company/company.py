from component.decision_component import DecisionComponent
from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from core.entity import Entity


class Company(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.init_component(ProductorComponent)
        self.init_component(LedgerComponent)
        self.init_component(DecisionComponent)
