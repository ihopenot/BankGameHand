from component.ledger_component import LedgerComponent
from core.entity import Entity


class Bank(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.init_component(LedgerComponent)
