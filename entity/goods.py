from __future__ import annotations

from typing import ClassVar, Dict

from core.config import ConfigManager
from core.types import Money, Radio


class GoodsType:
    """商品种类定义（静态配置数据）。"""

    types: ClassVar[Dict[str, "GoodsType"]] = {}

    def __init__(self, name: str, base_price: Money) -> None:
        self.name = name
        self.base_price = base_price


class GoodsBatch:
    """商品批次（运行时实例）。"""

    def __init__(self, goods_type: GoodsType, quantity: int, quality: Radio, brand_value: int) -> None:
        self.goods_type = goods_type
        self.quantity = quantity
        self.quality = quality
        self.brand_value = brand_value


def load_goods_types() -> Dict[str, GoodsType]:
    """从配置加载所有商品种类，返回 {name: GoodsType} 字典。"""
    config = ConfigManager()
    section = config.section("goods")
    result: Dict[str, GoodsType] = {}
    for item in section.goods_types:
        gt = GoodsType(
            name=item.name,
            base_price=item.base_price,
        )
        result[gt.name] = gt
    GoodsType.types = result
    return result
