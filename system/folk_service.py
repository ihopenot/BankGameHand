from __future__ import annotations

import math
from typing import Dict, List

from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.storage_component import StorageComponent
from entity.folk import Folk
from entity.goods import GoodsType
from system.market_service import MarketService, SellOrder, TradeRecord


class FolkService:
    """居民部门服务：管理所有居民群体的采购行为。"""

    def __init__(self, folks: List[Folk] | None = None) -> None:
        self.folks: List[Folk] = folks if folks is not None else []

    def load_folks_from_config(self, folk_initial_cash: int) -> List[Folk]:
        """从配置加载居民并设置初始资金。"""
        from entity.folk import load_folks
        self.folks = load_folks()
        for folk in self.folks:
            folk_ledger = folk.get_component(LedgerComponent)
            folk_ledger.cash = folk_initial_cash
        return self.folks

    def compute_demands(self, economy_cycle_index: float) -> Dict[Folk, Dict[GoodsType, int]]:
        """计算每个 Folk 对每种终端消费品的需求量。

        公式：population * per_capita * (1 + economy_cycle_index * sensitivity)
        """
        result: Dict[Folk, Dict[GoodsType, int]] = {}
        for folk in self.folks:
            folk_demands: Dict[GoodsType, int] = {}
            for goods_type, params in folk.base_demands.items():
                per_capita = params["per_capita"]
                sensitivity = params["sensitivity"]
                if per_capita == 0:
                    folk_demands[goods_type] = 0
                    continue
                raw = folk.population * per_capita * (1 + economy_cycle_index * sensitivity)
                folk_demands[goods_type] = int(raw)
            result[folk] = folk_demands
        return result

    @staticmethod
    def _price_attractiveness(price: int, avg_price: float) -> float:
        """用 sigmoid 计算价格吸引力，范围 [-1, 1]。

        价格低于均价 → 正值（有吸引力），高于均价 → 负值。
        """
        if avg_price <= 0:
            return 0.0
        k = 5.0
        x = k * (avg_price - price) / avg_price
        x = max(-500, min(500, x))  # 防止 math.exp 溢出
        return 2.0 / (1.0 + math.exp(-x)) - 1.0

    @staticmethod
    def _score_order(
        order: SellOrder,
        w_quality: float,
        w_brand: float,
        w_price: float,
        avg_price: float,
    ) -> float:
        """计算卖方挂单的竞争力评分（三维加权：品质+品牌+价格吸引力）。"""
        if order.price <= 0:
            return 0.0
        quality_score = order.batch.quality
        brand_score = order.batch.brand_value
        price_score = FolkService._price_attractiveness(order.price, avg_price)
        return w_quality * quality_score + w_brand * brand_score + w_price * price_score

    @staticmethod
    def _softmax_weights(scores: List[float]) -> List[float]:
        """对评分列表做 softmax 归一化，返回权重列表。"""
        if not scores:
            return []
        max_score = max(scores)
        exps = [math.exp(s - max_score) for s in scores]
        total = sum(exps)
        if total == 0:
            n = len(scores)
            return [1.0 / n] * n
        return [e / total for e in exps]

    def allocate_and_trade(
        self,
        folk: Folk,
        goods_type: GoodsType,
        demand: int,
        market: MarketService,
    ) -> List[TradeRecord]:
        """对单个 Folk 的单种商品执行加权均分采购。

        1. 获取所有该商品的 SellOrder
        2. 计算评分 → softmax 归一化
        3. 按权重分配需求量
        4. 库存不足时迭代重分配
        """
        if demand <= 0:
            return []

        orders = [o for o in market.get_sell_orders(goods_type) if o.remaining > 0]
        if not orders:
            return []

        trades: List[TradeRecord] = []
        remaining_demand = demand

        while remaining_demand > 0 and orders:
            folk_mc = folk.get_component(MetricComponent)
            avg_price = folk_mc.last_avg_buy_prices.get(goods_type, 0.0) if folk_mc else 0.0
            if avg_price <= 0:
                avg_price = goods_type.base_price
            scores = [self._score_order(o, folk.w_quality, folk.w_brand, folk.w_price, avg_price) for o in orders]
            weights = self._softmax_weights(scores)

            # 最大余数法分配，避免 int 截断丢失需求
            raw_allocs = [remaining_demand * w for w in weights]
            floor_allocs = [int(a) for a in raw_allocs]
            remainders = [a - f for a, f in zip(raw_allocs, floor_allocs)]
            deficit = remaining_demand - sum(floor_allocs)
            # 按余数从大到小补 1
            indices = sorted(range(len(remainders)), key=lambda i: remainders[i], reverse=True)
            for i in indices[:deficit]:
                floor_allocs[i] += 1

            round_traded = 0
            next_orders: List[SellOrder] = []

            for order, alloc in zip(orders, floor_allocs):
                if alloc <= 0:
                    next_orders.append(order)
                    continue
                actual = min(alloc, order.remaining)
                if actual > 0:
                    trades.append(TradeRecord(
                        seller=order.seller,
                        buyer=folk,
                        goods_type=goods_type,
                        quantity=actual,
                        price=order.price,
                    ))
                    order.remaining -= actual
                    round_traded += actual
                if order.remaining > 0:
                    next_orders.append(order)

            remaining_demand -= round_traded

            if round_traded == 0 or not next_orders:
                break
            orders = next_orders

        return trades

    def settle_trades(self, trades: List[TradeRecord]) -> None:
        """处理成交记录：商品转移 + 现金支付（居民无赊账）+ 更新卖方指标。"""
        for trade in trades:
            seller = trade.seller
            buyer = trade.buyer

            # 商品转移：卖方扣减 → 买方入库
            seller_storage = seller.get_component(StorageComponent)
            buyer_storage = buyer.get_component(StorageComponent)
            transferred = seller_storage.require_goods(trade.goods_type, trade.quantity, base=0)
            if transferred.quantity > 0:
                buyer_storage.add_batch(transferred)

            # 现金支付（居民目前无限现金，不做赊账）
            total_cost = trade.total
            buyer_ledger = buyer.get_component(LedgerComponent)
            seller_ledger = seller.get_component(LedgerComponent)
            buyer_ledger.cash -= total_cost
            seller_ledger.cash += total_cost

            # 更新卖方指标
            seller_mc = seller.get_component(MetricComponent)
            if seller_mc is not None:
                seller_mc.last_sold_quantities[trade.goods_type] = (
                    seller_mc.last_sold_quantities.get(trade.goods_type, 0) + trade.quantity
                )
                seller_mc.last_revenue += trade.total

    def buy_phase(self, market: MarketService, economy_cycle_index: float) -> List[TradeRecord]:
        """居民采购阶段：计算需求 → 按商品类型公平分配 → 结算 → 更新购买均价。

        按商品类型遍历，对每种商品将所有居民组的需求汇总后按比例公平分配供给，
        避免因迭代顺序导致后面的居民组买不到商品。
        """
        demands = self.compute_demands(economy_cycle_index)

        # 收集所有商品类型
        all_goods_types: set[GoodsType] = set()
        for folk_demands in demands.values():
            all_goods_types.update(folk_demands.keys())

        all_trades: List[TradeRecord] = []
        for goods_type in all_goods_types:
            # 收集对该商品有正需求的居民组
            folk_demands_for_good: List[tuple[Folk, int]] = []
            for folk in self.folks:
                d = demands[folk].get(goods_type, 0)
                if d > 0:
                    folk_demands_for_good.append((folk, d))
            if not folk_demands_for_good:
                continue

            total_demand = sum(d for _, d in folk_demands_for_good)
            total_supply = sum(
                o.remaining for o in market.get_sell_orders(goods_type) if o.remaining > 0
            )
            if total_supply <= 0:
                continue

            if total_supply >= total_demand:
                # 供给充足：每个居民组按原始需求购买
                for folk, demand in folk_demands_for_good:
                    trades = self.allocate_and_trade(folk, goods_type, demand, market)
                    all_trades.extend(trades)
            else:
                # 供不应求：按需求比例公平分配供给（最大余数法）
                raw_allocs = [total_supply * d / total_demand for _, d in folk_demands_for_good]
                floor_allocs = [int(a) for a in raw_allocs]
                remainders = [a - f for a, f in zip(raw_allocs, floor_allocs)]
                deficit = total_supply - sum(floor_allocs)
                indices = sorted(range(len(remainders)), key=lambda i: remainders[i], reverse=True)
                for i in indices[:deficit]:
                    floor_allocs[i] += 1

                for (folk, _demand), alloc in zip(folk_demands_for_good, floor_allocs):
                    if alloc > 0:
                        trades = self.allocate_and_trade(folk, goods_type, alloc, market)
                        all_trades.extend(trades)

        self.settle_trades(all_trades)
        self._update_avg_buy_prices(all_trades)
        return all_trades

    @staticmethod
    def _update_avg_buy_prices(trades: List[TradeRecord]) -> None:
        """按成交量加权更新每个 Folk 买方的 last_avg_buy_prices。"""
        from collections import defaultdict
        # 按 (buyer, goods_type) 聚合
        buyer_totals: Dict[tuple, list] = defaultdict(list)
        for trade in trades:
            if isinstance(trade.buyer, Folk):
                buyer_totals[(trade.buyer, trade.goods_type)].append(trade)

        for (folk, goods_type), folk_trades in buyer_totals.items():
            total_qty = sum(t.quantity for t in folk_trades)
            if total_qty > 0:
                weighted_price = sum(t.price * t.quantity for t in folk_trades)
                folk_mc = folk.get_component(MetricComponent)
                if folk_mc is not None:
                    folk_mc.last_avg_buy_prices[goods_type] = weighted_price / total_qty
