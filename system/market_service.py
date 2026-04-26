from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Dict, List

from core.types import Money
from entity.goods import GoodsBatch, GoodsType

if TYPE_CHECKING:
    from core.entity import Entity


class SellOrder:
    """卖方挂单。"""

    def __init__(self, seller: Entity, batch: GoodsBatch, price: Money) -> None:
        self.seller = seller
        self.batch = batch
        self.price = price
        self.remaining: int = batch.quantity


class BuyIntent:
    """买方采购意向。

    sort_key: 排序函数，输入 SellOrder，返回排序键（值越大优先级越高）。
    MarketService.match 内部用 sort_key 对同商品类型的卖单进行降序排序。
    """

    def __init__(
        self,
        buyer: Entity,
        goods_type: GoodsType,
        quantity: int,
        sort_key: Callable[[SellOrder], Any],
    ) -> None:
        self.buyer = buyer
        self.goods_type = goods_type
        self.quantity = quantity
        self.remaining: int = quantity
        self.sort_key = sort_key


class TradeRecord:
    """成交记录。"""

    def __init__(
        self,
        seller: Entity,
        buyer: Entity,
        goods_type: GoodsType,
        quantity: int,
        price: Money,
    ) -> None:
        self.seller = seller
        self.buyer = buyer
        self.goods_type = goods_type
        self.quantity = quantity
        self.price = price
        self.total: Money = quantity * price


class MarketService:
    """市场撮合引擎。"""

    def __init__(self) -> None:
        self._orders: Dict[GoodsType, List[SellOrder]] = defaultdict(list)
        self._last_trades: List[TradeRecord] = []

    @property
    def last_trades(self) -> List[TradeRecord]:
        return self._last_trades

    def add_sell_order(self, order: SellOrder) -> None:
        self._orders[order.batch.goods_type].append(order)

    def get_sell_orders(self, goods_type: GoodsType) -> List[SellOrder]:
        return list(self._orders.get(goods_type, []))

    def clear(self) -> None:
        self._orders.clear()

    def update_phase(self) -> None:
        self.clear()
        self._last_trades = []

    def match(self, buy_intents: List[BuyIntent]) -> List[TradeRecord]:
        """逐轮匹配算法。

        每轮：
        1. 按 goods_type 分组买方
        2. 对每组，用买方的 sort_key 对有剩余的卖单排序（降序）
        3. 每个买方向排名最高的卖方下单
        4. 卖方汇总：供≥求全部成交，供<求等比分配
        终止：无剩余买方 / 本轮无成交
        """
        records: List[TradeRecord] = []
        # 每个买方维护一个偏好指针（指向自己排序后列表的当前位置）
        # buyer_id -> (sorted_orders, idx)
        buyer_state: Dict[int, tuple[List[SellOrder], int]] = {}

        active_buyers = [bi for bi in buy_intents if bi.remaining > 0]
        if not active_buyers:
            return records

        # 初始化：为每个买方按 sort_key 对其 goods_type 的卖单排序
        for bi in active_buyers:
            orders = self._orders.get(bi.goods_type, [])
            sorted_orders = sorted(orders, key=bi.sort_key, reverse=True)
            buyer_state[id(bi)] = (sorted_orders, 0)

        while active_buyers:
            # 收集本轮订单：sell_order_id -> [(buyer_intent, order_qty)]
            round_orders: Dict[int, List[tuple[BuyIntent, int]]] = defaultdict(list)
            # 本轮有目标卖方的买方
            round_buyers: List[BuyIntent] = []

            for bi in active_buyers:
                sorted_orders, idx = buyer_state[id(bi)]
                # 跳过已售罄的卖方
                while idx < len(sorted_orders) and sorted_orders[idx].remaining <= 0:
                    idx += 1
                buyer_state[id(bi)] = (sorted_orders, idx)

                if idx >= len(sorted_orders):
                    continue

                target = sorted_orders[idx]
                round_orders[id(target)].append((bi, bi.remaining))
                round_buyers.append(bi)

            if not round_orders:
                break

            any_trade = False
            next_active: List[BuyIntent] = []
            processed: set[int] = set()

            for bi in round_buyers:
                sorted_orders, idx = buyer_state[id(bi)]
                if idx >= len(sorted_orders):
                    continue
                target = sorted_orders[idx]
                order_key = id(target)

                if order_key in processed:
                    # 已处理过此卖方，检查买方是否仍有剩余
                    if bi.remaining > 0:
                        # 推进指针（该卖方已售罄或本轮已处理）
                        buyer_state[id(bi)] = (sorted_orders, idx + 1)
                        next_active.append(bi)
                    continue
                processed.add(order_key)

                buyers_for_order = round_orders[order_key]
                total_demand = sum(qty for _, qty in buyers_for_order)

                if total_demand <= target.remaining:
                    # 供≥求：全部成交
                    for buyer_intent, qty in buyers_for_order:
                        records.append(TradeRecord(
                            seller=target.seller,
                            buyer=buyer_intent.buyer,
                            goods_type=buyer_intent.goods_type,
                            quantity=qty,
                            price=target.price,
                        ))
                        target.remaining -= qty
                        buyer_intent.remaining -= qty
                        any_trade = True
                else:
                    # 供<求：等比分配（向上取整，min 保证不超卖）
                    available = target.remaining
                    remaining_supply = available
                    for buyer_intent, qty in buyers_for_order:
                        alloc = -(-(qty * available) // total_demand)
                        alloc = min(alloc, buyer_intent.remaining, remaining_supply)
                        if alloc > 0:
                            records.append(TradeRecord(
                                seller=target.seller,
                                buyer=buyer_intent.buyer,
                                goods_type=buyer_intent.goods_type,
                                quantity=alloc,
                                price=target.price,
                            ))
                            buyer_intent.remaining -= alloc
                            remaining_supply -= alloc
                            any_trade = True
                    target.remaining = 0
                    # 推进指针，仍有需求的买方进入下一轮
                    for buyer_intent, _ in buyers_for_order:
                        if buyer_intent.remaining > 0:
                            so, si = buyer_state[id(buyer_intent)]
                            buyer_state[id(buyer_intent)] = (so, si + 1)
                            next_active.append(buyer_intent)

            if not any_trade:
                break

            active_buyers = [bi for bi in next_active if bi.remaining > 0]

        self._last_trades = records
        return records
