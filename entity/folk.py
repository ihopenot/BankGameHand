from __future__ import annotations

from typing import Dict, List

from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.storage_component import StorageComponent
from core.config import AttrDict, ConfigManager
from core.entity import Entity
from entity.goods import GoodsType


class Folk(Entity):
    """居民群体实体，由配置驱动，不硬编码阶层标识。"""

    def __init__(
        self,
        population: int,
        w_quality: float,
        w_brand: float,
        w_price: float,
        base_demands: Dict[GoodsType, Dict[str, float]],
    ) -> None:
        super().__init__()
        self.population = population
        self.w_quality = w_quality
        self.w_brand = w_brand
        self.w_price = w_price
        self.base_demands = base_demands
        self.init_component(LedgerComponent)
        self.init_component(StorageComponent)
        self.init_component(MetricComponent)


def load_folks() -> List[Folk]:
    """从配置段加载 Folk 列表。

    使用 ConfigManager 单例获取配置，使用 GoodsType.types 获取商品类型。

    Returns:
        Folk 实体列表。
    """
    config = ConfigManager().section("folk")
    goods_types = GoodsType.types
    folks: List[Folk] = []
    for item in config.folks:
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
        folks.append(Folk(
            population=item.population,
            w_quality=item.w_quality,
            w_brand=item.w_brand,
            w_price=item.w_price,
            base_demands=base_demands,
        ))
    return folks
