from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List

from component.base_component import BaseComponent
from entity.goods import GoodsBatch, GoodsType

if TYPE_CHECKING:
    from core.entity import Entity


class StorageComponent(BaseComponent):
    """库存组件：管理实体的商品库存。"""

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        self.inventory: Dict[GoodsType, List[GoodsBatch]] = defaultdict(list)

    def add_batch(self, batch: GoodsBatch) -> None:
        self.inventory[batch.goods_type].append(batch)

    def get_batches(self, goods_type: GoodsType) -> List[GoodsBatch]:
        return self.inventory.get(goods_type, [])

    def require_goods(self, goods_type: GoodsType, quantity: int, base: int) -> GoodsBatch:
        """从库存中按品质从高到低取出原料，归一化为一个 GoodsBatch。

        Args:
            goods_type: 要取的商品类型。
            quantity: 期望取出的数量。
            base: 取整基数。库存不足时向下取整到 base 的整数倍；
                  base=0 时能取多少取多少。

        Returns:
            归一化后的 GoodsBatch（加权平均品质和品牌值）。
            取出量为 0 时返回数量 0 的 GoodsBatch。
        """
        batches = self.inventory.get(goods_type)
        if not batches:
            return GoodsBatch(goods_type=goods_type, quantity=0, quality=0.0, brand_value=0)

        # 按品质从高到低排序
        batches.sort(key=lambda b: b.quality, reverse=True)

        total_available = sum(b.quantity for b in batches)

        # 确定实际取出量
        if total_available >= quantity:
            take = quantity
        elif base > 0:
            take = (total_available // base) * base
        else:
            take = total_available

        if take <= 0:
            return GoodsBatch(goods_type=goods_type, quantity=0, quality=0.0, brand_value=0)

        # 逐批扣减，累计加权信息
        remaining = take
        weighted_quality = 0.0
        weighted_brand = 0.0

        i = 0
        while remaining > 0 and i < len(batches):
            batch = batches[i]
            taken = min(batch.quantity, remaining)
            weighted_quality += batch.quality * taken
            weighted_brand += batch.brand_value * taken
            batch.quantity -= taken
            remaining -= taken
            i += 1

        # 清理数量为 0 的批次
        self.inventory[goods_type] = [b for b in batches if b.quantity > 0]

        avg_quality = weighted_quality / take
        avg_brand = round(weighted_brand / take)

        return GoodsBatch(
            goods_type=goods_type,
            quantity=take,
            quality=avg_quality,
            brand_value=avg_brand,
        )
