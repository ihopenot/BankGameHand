from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from core.entity import Entity


class Bank(Entity):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.deposit_rate: int = 0  # 万分比，玩家设定的存款利率
        self.init_component(LedgerComponent)
        self.init_component(MetricComponent)
