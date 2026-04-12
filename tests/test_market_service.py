"""tests/test_market_service.py — MarketService 数据结构与基础操作测试。"""

from __future__ import annotations

import pytest

from core.entity import Entity
from component.storage_component import StorageComponent
from entity.goods import GoodsBatch, GoodsType
from system.market_service import BuyIntent, MarketService, SellOrder, TradeRecord


# ── Fixtures ──


@pytest.fixture()
def goods_type_silicon() -> GoodsType:
    return GoodsType(name="硅", base_price=1000, bonus_ceiling=0.1)


@pytest.fixture()
def goods_type_chip() -> GoodsType:
    return GoodsType(name="芯片", base_price=5000, bonus_ceiling=0.1)


@pytest.fixture()
def seller(goods_type_silicon: GoodsType) -> Entity:
    e = Entity()
    e.init_component(StorageComponent)
    storage = e.get_component(StorageComponent)
    batch = GoodsBatch(goods_type=goods_type_silicon, quantity=100, quality=0.8, brand_value=10)
    storage.add_batch(batch)
    return e


@pytest.fixture()
def market() -> MarketService:
    return MarketService()


# ── SellOrder 创建 ──


class TestSellOrder:
    def test_create_sell_order(self, seller: Entity, goods_type_silicon: GoodsType) -> None:
        storage = seller.get_component(StorageComponent)
        batch = storage.get_batches(goods_type_silicon)[0]
        order = SellOrder(seller=seller, batch=batch, price=1000)
        assert order.seller is seller
        assert order.batch is batch
        assert order.price == 1000
        assert order.remaining == batch.quantity

    def test_sell_order_remaining_defaults_to_batch_quantity(
        self, seller: Entity, goods_type_silicon: GoodsType
    ) -> None:
        storage = seller.get_component(StorageComponent)
        batch = storage.get_batches(goods_type_silicon)[0]
        order = SellOrder(seller=seller, batch=batch, price=1000)
        assert order.remaining == 100


# ── MarketService 基础操作 ──


class TestMarketServiceBasic:
    def test_add_and_get_sell_orders(
        self, market: MarketService, seller: Entity, goods_type_silicon: GoodsType
    ) -> None:
        storage = seller.get_component(StorageComponent)
        batch = storage.get_batches(goods_type_silicon)[0]
        order = SellOrder(seller=seller, batch=batch, price=1000)
        market.add_sell_order(order)

        orders = market.get_sell_orders(goods_type_silicon)
        assert len(orders) == 1
        assert orders[0] is order

    def test_get_sell_orders_empty(
        self, market: MarketService, goods_type_chip: GoodsType
    ) -> None:
        orders = market.get_sell_orders(goods_type_chip)
        assert orders == []

    def test_clear(
        self, market: MarketService, seller: Entity, goods_type_silicon: GoodsType
    ) -> None:
        storage = seller.get_component(StorageComponent)
        batch = storage.get_batches(goods_type_silicon)[0]
        order = SellOrder(seller=seller, batch=batch, price=1000)
        market.add_sell_order(order)
        market.clear()

        orders = market.get_sell_orders(goods_type_silicon)
        assert orders == []

    def test_multiple_orders_same_goods(
        self, market: MarketService, goods_type_silicon: GoodsType
    ) -> None:
        seller1 = Entity()
        seller1.init_component(StorageComponent)
        s1 = seller1.get_component(StorageComponent)
        b1 = GoodsBatch(goods_type=goods_type_silicon, quantity=50, quality=0.9, brand_value=5)
        s1.add_batch(b1)

        seller2 = Entity()
        seller2.init_component(StorageComponent)
        s2 = seller2.get_component(StorageComponent)
        b2 = GoodsBatch(goods_type=goods_type_silicon, quantity=80, quality=0.6, brand_value=3)
        s2.add_batch(b2)

        market.add_sell_order(SellOrder(seller=seller1, batch=b1, price=1200))
        market.add_sell_order(SellOrder(seller=seller2, batch=b2, price=900))

        orders = market.get_sell_orders(goods_type_silicon)
        assert len(orders) == 2


# ── BuyIntent 创建 ──


def _price_key(o: SellOrder) -> float:
    return o.price


class TestBuyIntent:
    def test_create_buy_intent(self, goods_type_silicon: GoodsType) -> None:
        buyer = Entity()
        intent = BuyIntent(
            buyer=buyer,
            goods_type=goods_type_silicon,
            quantity=200,
            sort_key=_price_key,
        )
        assert intent.buyer is buyer
        assert intent.goods_type is goods_type_silicon
        assert intent.quantity == 200
        assert intent.remaining == 200
        assert intent.sort_key is _price_key


# ── TradeRecord 创建 ──


class TestTradeRecord:
    def test_create_trade_record(self, goods_type_silicon: GoodsType) -> None:
        seller = Entity()
        buyer = Entity()
        record = TradeRecord(
            seller=seller,
            buyer=buyer,
            goods_type=goods_type_silicon,
            quantity=50,
            price=1000,
        )
        assert record.seller is seller
        assert record.buyer is buyer
        assert record.goods_type is goods_type_silicon
        assert record.quantity == 50
        assert record.price == 1000
        assert record.total == 50 * 1000
