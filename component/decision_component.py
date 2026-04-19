from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict

from component.base_component import BaseComponent

if TYPE_CHECKING:
    from core.entity import Entity


class DecisionComponent(BaseComponent):
    """决策组件：存储 CEO 特质和决策中间状态。"""

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        # 6 维 CEO 特质，取值 [0, 1]
        self.business_acumen: float = random.random()
        self.risk_appetite: float = random.random()
        self.profit_focus: float = random.random()
        self.marketing_awareness: float = random.random()
        self.tech_focus: float = random.random()
        self.price_sensitivity: float = random.random()

        # 投资计划表（plan_phase 生成，act_phase 执行）
        # 键: "expansion" / "brand" / "tech"，值: 计划金额
        self.investment_plan: Dict[str, int] = {}
