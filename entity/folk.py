from __future__ import annotations

from typing import Dict, List

from component.decision.folk.classic import ClassicFolkDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.storage_component import StorageComponent
from core.config import ConfigManager
from core.entity import Entity
from entity.goods import GoodsType


class Folk(Entity):
    """居民群体实体，由配置驱动，不硬编码阶层标识。"""

    def __init__(
        self,
        name: str,
        population: int,
        w_quality: float,
        w_brand: float,
        w_price: float,
        spending_flow: Dict[str, float],
        base_demands: Dict[GoodsType, Dict[str, float]],
        labor_participation_rate: float,
        labor_points_per_capita: float,
    ) -> None:
        super().__init__()
        self.name = name
        self.population = population
        self.w_quality = w_quality
        self.w_brand = w_brand
        self.w_price = w_price
        self.spending_flow = spending_flow
        self.base_demands = base_demands
        self.labor_participation_rate = labor_participation_rate
        self.labor_points_per_capita = labor_points_per_capita
        self.init_component(LedgerComponent)
        self.init_component(StorageComponent)
        self.init_component(MetricComponent)
        self.init_component(ClassicFolkDecisionComponent)

    @property
    def labor_supply(self) -> int:
        """劳动力供给 = 人口 × 参与率 × 人均劳动力点数（取整）。"""
        return int(self.population * self.labor_participation_rate * self.labor_points_per_capita)


def load_folks() -> List[Folk]:
    """从配置段加载 Folk 列表。

    使用 ConfigManager 单例获取配置，使用 GoodsType.types 获取商品类型。

    Returns:
        Folk 实体列表。
    """
    config = ConfigManager().section("folk")
    goods_types = GoodsType.types
    folks: List[Folk] = []

    for idx, item in enumerate(config.folks):
        base_demands: Dict[GoodsType, Dict[str, float]] = {}
        for goods_name in item.base_demands.__dict__:
            if goods_name.startswith("_"):
                continue
            gt = goods_types.get(goods_name)
            if gt is None:
                continue
            demand_cfg = getattr(item.base_demands, goods_name)
            base_demands[gt] = {
                "per_capita": demand_cfg.per_capita,
                "sensitivity": demand_cfg.sensitivity,
            }
        spending_flow: Dict[str, float] = {}
        if hasattr(item, "spending_flow"):
            for k, v in item.spending_flow.__dict__.items():
                if not k.startswith("_"):
                    spending_flow[k] = v

        folks.append(Folk(
            name=f"folk_{idx}",
            population=item.population,
            w_quality=item.w_quality,
            w_brand=item.w_brand,
            w_price=item.w_price,
            spending_flow=spending_flow,
            base_demands=base_demands,
            labor_participation_rate=item.labor_participation_rate,
            labor_points_per_capita=item.labor_points_per_capita,
        ))
    _validate_spending_flow(folks)
    return folks


def _validate_spending_flow(folks: List[Folk]) -> None:
    """校验 spending_flow 配置：每种支出类型的比例之和为 1.0（容差 0.01）。"""
    spending_types: Dict[str, float] = {}
    for folk in folks:
        for st, ratio in folk.spending_flow.items():
            spending_types[st] = spending_types.get(st, 0.0) + ratio
    for st, total in spending_types.items():
        if abs(total - 1.0) > 0.0001:
            raise ValueError(
                f"spending_flow.{st} 比例之和为 {total:.4f}，期望 1.0"
            )
