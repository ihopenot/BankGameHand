"""tests/test_market_match.py — MarketService.match() 逐轮匹配算法测试。"""

from __future__ import annotations

import pytest

from core.entity import Entity
from component.storage_component import StorageComponent
from entity.goods import GoodsBatch, GoodsType
from system.market_service import BuyIntent, MarketService, SellOrder, TradeRecord


# ── Helpers ──


def _make_seller(goods_type: GoodsType, quantity: int, quality: float, brand: int = 0) -> tuple:
    """创建卖方 Entity + GoodsBatch，返回 (entity, batch)。"""
    e = Entity("test")
    e.init_component(StorageComponent)
    batch = GoodsBatch(goods_type=goods_type, quantity=quantity, quality=quality, brand_value=brand)
    e.get_component(StorageComponent).add_batch(batch)
    return e, batch


def _make_order(seller: Entity, batch: GoodsBatch, price: int) -> SellOrder:
    return SellOrder(seller=seller, batch=batch, price=price)


def _price_key(o: SellOrder) -> float:
    """按价格排序（价格高优先）。"""
    return o.price


def _quality_key(o: SellOrder) -> float:
    """按品质排序（品质高优先）。"""
    return o.batch.quality


# ── Fixtures ──


@pytest.fixture()
def gt() -> GoodsType:
    return GoodsType(name="硅", base_price=1000)


@pytest.fixture()
def market() -> MarketService:
    return MarketService()


# ── 供大于求：全部成交 ──


class TestSupplyExceedsDemand:
    def test_single_buyer_single_seller_full_match(self, gt: GoodsType, market: MarketService) -> None:
        seller, batch = _make_seller(gt, 100, 0.8)
        order = _make_order(seller, batch, 1000)
        market.add_sell_order(order)

        buyer = Entity("test")
        intent = BuyIntent(buyer=buyer, goods_type=gt, quantity=50, sort_key=_price_key)

        records = market.match([intent])

        assert len(records) == 1
        assert records[0].seller is seller
        assert records[0].buyer is buyer
        assert records[0].quantity == 50
        assert records[0].price == 1000
        assert records[0].total == 50000
        assert order.remaining == 50
        assert intent.remaining == 0

    def test_multiple_buyers_supply_enough(self, gt: GoodsType, market: MarketService) -> None:
        seller, batch = _make_seller(gt, 200, 0.8)
        order = _make_order(seller, batch, 1000)
        market.add_sell_order(order)

        buyer1 = Entity("test")
        buyer2 = Entity("test")
        intent1 = BuyIntent(buyer=buyer1, goods_type=gt, quantity=80, sort_key=_price_key)
        intent2 = BuyIntent(buyer=buyer2, goods_type=gt, quantity=60, sort_key=_price_key)

        records = market.match([intent1, intent2])

        total_bought = sum(r.quantity for r in records)
        assert total_bought == 140
        assert order.remaining == 60


# ── 供小于求：等比例分配 ──


class TestDemandExceedsSupply:
    def test_proportional_allocation(self, gt: GoodsType, market: MarketService) -> None:
        seller, batch = _make_seller(gt, 100, 0.8)
        order = _make_order(seller, batch, 1000)
        market.add_sell_order(order)

        buyer1 = Entity("test")
        buyer2 = Entity("test")
        intent1 = BuyIntent(buyer=buyer1, goods_type=gt, quantity=120, sort_key=_price_key)
        intent2 = BuyIntent(buyer=buyer2, goods_type=gt, quantity=80, sort_key=_price_key)

        records = market.match([intent1, intent2])

        total_bought = sum(r.quantity for r in records)
        assert total_bought == 100
        assert order.remaining == 0

        buyer1_bought = sum(r.quantity for r in records if r.buyer is buyer1)
        buyer2_bought = sum(r.quantity for r in records if r.buyer is buyer2)
        assert buyer1_bought == 60
        assert buyer2_bought == 40


# ── 多轮降级选择 ──


class TestMultiRoundFallback:
    def test_buyer_falls_back_to_next_preference(self, gt: GoodsType, market: MarketService) -> None:
        """买方首选卖方售罄后，下一轮向次选卖方下单。"""
        seller_a, batch_a = _make_seller(gt, 50, 0.9)
        seller_b, batch_b = _make_seller(gt, 80, 0.6)
        order_a = _make_order(seller_a, batch_a, 1000)
        order_b = _make_order(seller_b, batch_b, 900)
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)

        buyer = Entity("test")
        # sort_key: 按品质降序 → A(0.9) > B(0.6)
        intent = BuyIntent(buyer=buyer, goods_type=gt, quantity=100, sort_key=_quality_key)

        records = market.match([intent])

        total_bought = sum(r.quantity for r in records)
        assert total_bought == 100  # 50 from A + 50 from B
        assert order_a.remaining == 0
        assert order_b.remaining == 30

    def test_design_doc_example(self, gt: GoodsType, market: MarketService) -> None:
        """MainLoop.md 中的匹配示例。

        卖方: A(100, price=800), B(80, price=1000), C(50, price=1200)
        甲偏好: A > B > C （按价格升序 → sort_key 取负价格）
        乙偏好: C > B > A （按品质降序）
        """
        seller_a, batch_a = _make_seller(gt, 100, 0.5)
        seller_b, batch_b = _make_seller(gt, 80, 0.7)
        seller_c, batch_c = _make_seller(gt, 50, 0.9)
        order_a = _make_order(seller_a, batch_a, 800)
        order_b = _make_order(seller_b, batch_b, 1000)
        order_c = _make_order(seller_c, batch_c, 1200)
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)
        market.add_sell_order(order_c)

        buyer_jia = Entity("test")
        buyer_yi = Entity("test")
        # 甲: 价格低优先 (A=800 > B=1000 > C=1200) → sort_key = -price
        intent_jia = BuyIntent(
            buyer=buyer_jia, goods_type=gt, quantity=90,
            sort_key=lambda o: -o.price,
        )
        # 乙: 品质高优先 (C=0.9 > B=0.7 > A=0.5)
        intent_yi = BuyIntent(
            buyer=buyer_yi, goods_type=gt, quantity=70,
            sort_key=_quality_key,
        )

        records = market.match([intent_jia, intent_yi])

        jia_bought = sum(r.quantity for r in records if r.buyer is buyer_jia)
        yi_bought = sum(r.quantity for r in records if r.buyer is buyer_yi)

        # 第一轮：甲→A(90), 乙→C(70)
        # A: 90≤100 → 甲全部满足, A剩余10
        # C: 70>50 → 等比分配, 乙买到50, C售罄, 乙剩余20
        # 第二轮：乙(剩余20)→B
        # B: 20≤80 → 乙全部满足
        assert jia_bought == 90
        assert yi_bought == 70
        assert order_a.remaining == 10
        assert order_b.remaining == 60
        assert order_c.remaining == 0


# ── 终止条件 ──


class TestTermination:
    def test_no_buyers(self, gt: GoodsType, market: MarketService) -> None:
        seller, batch = _make_seller(gt, 100, 0.8)
        order = _make_order(seller, batch, 1000)
        market.add_sell_order(order)

        records = market.match([])
        assert records == []

    def test_no_sellers(self, gt: GoodsType, market: MarketService) -> None:
        buyer = Entity("test")
        intent = BuyIntent(buyer=buyer, goods_type=gt, quantity=50, sort_key=_price_key)

        records = market.match([intent])
        assert records == []
        assert intent.remaining == 50

    def test_no_matching_goods(self, gt: GoodsType, market: MarketService) -> None:
        """买方偏好列表中无可用卖方。"""
        buyer = Entity("test")
        intent = BuyIntent(buyer=buyer, goods_type=gt, quantity=50, sort_key=_price_key)

        records = market.match([intent])
        assert records == []

    def test_all_sellers_exhausted(self, gt: GoodsType, market: MarketService) -> None:
        seller, batch = _make_seller(gt, 30, 0.8)
        order = _make_order(seller, batch, 1000)
        market.add_sell_order(order)

        buyer = Entity("test")
        intent = BuyIntent(buyer=buyer, goods_type=gt, quantity=100, sort_key=_price_key)

        records = market.match([intent])

        total_bought = sum(r.quantity for r in records)
        assert total_bought == 30
        assert intent.remaining == 70
        assert order.remaining == 0
