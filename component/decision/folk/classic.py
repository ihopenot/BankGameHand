from __future__ import annotations

import math
from typing import TYPE_CHECKING, Dict

from component.decision.folk.base import BaseFolkDecisionComponent, register_folk_decision_component
from component.ledger_component import LedgerComponent

if TYPE_CHECKING:
    from core.entity import Entity


@register_folk_decision_component("classic")
class ClassicFolkDecisionComponent(BaseFolkDecisionComponent):
    """经典公式驱动的居民决策组件。

    Context dict 约定：
    - economy_cycle_index: float — 经济周期指数（保留但不再用于需求计算）
    - reference_prices: Dict[str, int] — 各商品参考价格
    """

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)

    def update_demand_multiplier(
        self,
        savings_target_ratio: float,
        max_adjustment: float,
        sensitivity: float,
        min_multiplier: float,
        max_multiplier: float,
    ) -> None:
        """基于现金/开销比值更新 demand_multiplier。

        R = cash / last_spending
        deviation = (R - T) / T
        adjustment = max_adjustment * tanh(sensitivity * deviation)
        demand_multiplier *= (1 + adjustment)
        demand_multiplier = clamp(min_multiplier, max_multiplier)
        """
        folk = self.outer
        last_spending = folk.last_spending

        if last_spending <= 0:
            # 冷启动：无开销记录，不触发调整
            return

        ledger = folk.get_component(LedgerComponent)
        cash = ledger.cash
        R = cash / last_spending
        T = savings_target_ratio

        deviation = (R - T) / T
        adjustment = max_adjustment * math.tanh(sensitivity * deviation)

        folk.demand_multiplier *= (1 + adjustment)
        folk.demand_multiplier = max(min_multiplier, min(max_multiplier, folk.demand_multiplier))

    def decide_spending(self) -> Dict[str, Dict]:
        """计算每个商品类型的支出计划（预算 + 需求量）。

        demand = population * per_capita * demand_multiplier
        budget = demand * reference_price * spending_tendency
        """
        ctx = self._context
        reference_prices: Dict[str, int] = ctx.get("reference_prices", {})

        folk = self.outer
        spending_tendency = self._calc_spending_tendency()

        result: Dict[str, Dict] = {}
        for gt, demand_cfg in folk.base_demands.items():
            gt_name = gt.name
            per_capita = demand_cfg["per_capita"]

            if per_capita == 0:
                result[gt_name] = {"budget": 0, "demand": 0}
                continue

            demand = int(folk.population * per_capita * getattr(folk, 'demand_multiplier', 1.0))
            ref_price = reference_prices.get(gt_name, gt.base_price)
            budget = int(demand * ref_price * spending_tendency)

            result[gt_name] = {"budget": budget, "demand": demand}

        return result

    def _calc_spending_tendency(self) -> float:
        """根据 Folk 的 w_* 属性计算消费倾向。

        spending_tendency = w_quality + w_brand + w_price
        """
        folk = self.outer
        return folk.w_quality + folk.w_brand + folk.w_price
