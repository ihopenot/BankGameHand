from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List

from component.base_component import BaseComponent
from entity.goods import GoodsType

if TYPE_CHECKING:
    from core.entity import Entity
    from entity.factory import Recipe


@dataclass
class RoundSnapshot:
    """单轮快照数据。"""

    round_number: int
    cash: int = 0
    revenue: int = 0
    sell_orders: Dict[GoodsType, int] = field(default_factory=dict)
    sold_quantities: Dict[GoodsType, int] = field(default_factory=dict)
    prices: Dict[GoodsType, int] = field(default_factory=dict)
    brand_values: Dict[GoodsType, int] = field(default_factory=dict)
    tech_values: Dict[Recipe, int] = field(default_factory=dict)
    investment_plan: Dict[str, int] = field(default_factory=dict)
    actual_investment: Dict[str, int] = field(default_factory=dict)


class MetricComponent(BaseComponent):
    """指标追踪组件：存储当前轮次指标和历史快照。"""

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        # 当轮指标（每轮开始时重置）
        self.last_sell_orders: Dict[GoodsType, int] = {}
        self.last_sold_quantities: Dict[GoodsType, int] = {}
        self.last_revenue: int = 0
        self.last_avg_buy_prices: Dict[GoodsType, float] = {}
        self.last_hired_workers: int = 0
        # 累计计数器
        self.cumulative_revenue: int = 0
        self.cumulative_brand_spend: int = 0
        self.cumulative_tech_spend: int = 0
        self.cumulative_expansion_spend: int = 0

        # 工厂统计
        self.factories_active: int = 0  # 开工（已建成且已维护）
        self.factories_idle: int = 0    # 停工（已建成但未维护）
        self.factories_building: int = 0  # 在建

        # 历史快照
        self.round_history: List[RoundSnapshot] = []

    def add_snapshot(self, snapshot: RoundSnapshot) -> None:
        """添加一份轮次快照到历史记录。"""
        self.round_history.append(snapshot)

    def reset_round(self) -> None:
        """重置当轮指标（每轮开始时调用）。"""
        self.last_sell_orders = {}
        self.last_sold_quantities = {}
        self.last_revenue = 0
        self.last_hired_labor_points = 0
        self.factories_active = 0
        self.factories_idle = 0
        self.factories_building = 0
