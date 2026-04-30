from __future__ import annotations

from component.decision.company.base import BaseCompanyDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent, RoundSnapshot
from component.productor_component import ProductorComponent


class MetricService:
    """指标采集服务：每轮结束时为所有实体生成快照。"""

    @staticmethod
    def reset_all() -> None:
        """重置所有 MetricComponent 的当轮指标（每轮开始时调用）。"""
        for mc in MetricComponent.components:
            mc.reset_round()

    def snapshot_phase(self, round_number: int) -> None:
        """遍历所有 MetricComponent 实例，采集当轮快照。"""
        for mc in MetricComponent.components:
            entity = mc.outer

            # 基础数据
            ledger = entity.get_component(LedgerComponent)
            cash = ledger.cash if ledger is not None else 0

            # Company 特有数据
            pc = entity.get_component(ProductorComponent)
            dc = next(
                (c for c in entity._components.values() if isinstance(c, BaseCompanyDecisionComponent)),
                None,
            )

            snapshot = RoundSnapshot(
                round_number=round_number,
                cash=cash,
                revenue=mc.last_revenue,
                sell_orders=dict(mc.last_sell_orders),
                sold_quantities=dict(mc.last_sold_quantities),
                prices=dict(pc.prices) if pc is not None else {},
                brand_values=dict(pc.brand_values) if pc is not None else {},
                tech_values=dict(pc.tech_values) if pc is not None else {},
                investment_plan=dict(dc.investment_plan) if dc is not None else {},
            )
            mc.add_snapshot(snapshot)

            # 更新累计计数器
            mc.cumulative_revenue += mc.last_revenue
