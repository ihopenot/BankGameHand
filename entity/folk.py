from __future__ import annotations

from typing import Dict, List

from component.ledger_component import LedgerComponent
from component.storage_component import StorageComponent
from core.config import AttrDict
from core.entity import Entity
from entity.goods import GoodsType


class Folk(Entity):
    """居民群体实体，由配置驱动，不硬编码阶层标识。"""

    def __init__(
        self,
        population: int,
        w_value_for_money: float,
        w_brand: float,
        base_demands: Dict[GoodsType, Dict[str, float]],
    ) -> None:
        super().__init__()
        self.population = population
        self.w_value_for_money = w_value_for_money
        self.w_brand = w_brand
        self.base_demands = base_demands
        self.init_component(LedgerComponent)
        self.init_component(StorageComponent)


def load_folks(config: AttrDict, goods_types: Dict[str, GoodsType]) -> List[Folk]:
    """从配置段加载 Folk 列表。

    Args:
        config: ConfigManager.section("folk") 返回的 AttrDict，包含 folks 列表。
        goods_types: 商品名称到 GoodsType 的映射。

    Returns:
        Folk 实体列表。
    """
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
            w_value_for_money=item.w_value_for_money,
            w_brand=item.w_brand,
            base_demands=base_demands,
        ))
    return folks
