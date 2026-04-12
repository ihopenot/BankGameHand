"""Tests for CompanyService.sell_phase."""

from __future__ import annotations

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.entity import Entity
from entity.company.company import Company
from entity.goods import GoodsBatch, GoodsType
from entity.factory import Factory, FactoryType, Recipe
from system.company_service import CompanyService
from system.market_service import MarketService, SellOrder


def _make_goods_type(name: str = "chip", base_price: int = 500) -> GoodsType:
    return GoodsType(name=name, base_price=base_price, bonus_ceiling=0.3)


def _make_factory_type(gt: GoodsType) -> FactoryType:
    recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt, output_quantity=10)
    return FactoryType(recipe=recipe, base_production=100, build_cost=1000, maintenance_cost=50, build_time=1)


class TestSellPhase:
    """CompanyService.sell_phase should create SellOrders from company inventories."""

    def test_single_batch_creates_sell_order(self) -> None:
        gt = _make_goods_type()
        ft = _make_factory_type(gt)

        company = Company()
        pc = company.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        storage = company.get_component(StorageComponent)
        batch = GoodsBatch(goods_type=gt, quantity=100, quality=0.8, brand_value=10)
        storage.add_batch(batch)

        market = MarketService()
        service = CompanyService()
        service.companies = {"c1": company}
        service.sell_phase(market)

        orders = market.get_sell_orders(gt)
        assert len(orders) == 1
        assert orders[0].batch is batch
        assert orders[0].price == 500
        assert orders[0].seller is company

    def test_multiple_batches_create_multiple_orders(self) -> None:
        gt = _make_goods_type()
        ft = _make_factory_type(gt)

        company = Company()
        pc = company.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        storage = company.get_component(StorageComponent)
        b1 = GoodsBatch(goods_type=gt, quantity=50, quality=0.7, brand_value=5)
        b2 = GoodsBatch(goods_type=gt, quantity=30, quality=0.9, brand_value=8)
        storage.add_batch(b1)
        storage.add_batch(b2)

        market = MarketService()
        service = CompanyService()
        service.companies = {"c1": company}
        service.sell_phase(market)

        orders = market.get_sell_orders(gt)
        assert len(orders) == 2

    def test_zero_quantity_batch_not_listed(self) -> None:
        gt = _make_goods_type()
        ft = _make_factory_type(gt)

        company = Company()
        pc = company.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        storage = company.get_component(StorageComponent)
        batch = GoodsBatch(goods_type=gt, quantity=0, quality=0.5, brand_value=0)
        storage.add_batch(batch)

        market = MarketService()
        service = CompanyService()
        service.companies = {"c1": company}
        service.sell_phase(market)

        orders = market.get_sell_orders(gt)
        assert len(orders) == 0

    def test_no_inventory_no_orders(self) -> None:
        company = Company()
        market = MarketService()
        service = CompanyService()
        service.companies = {"c1": company}
        service.sell_phase(market)

        # Market should have no orders for any type
        assert market._orders == {}

    def test_price_from_productor_component(self) -> None:
        gt = _make_goods_type(base_price=1200)
        ft = _make_factory_type(gt)

        company = Company()
        pc = company.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        storage = company.get_component(StorageComponent)
        batch = GoodsBatch(goods_type=gt, quantity=10, quality=0.5, brand_value=0)
        storage.add_batch(batch)

        market = MarketService()
        service = CompanyService()
        service.companies = {"c1": company}
        service.sell_phase(market)

        orders = market.get_sell_orders(gt)
        assert orders[0].price == 1200

    def test_multiple_companies(self) -> None:
        gt = _make_goods_type()
        ft = _make_factory_type(gt)

        c1 = Company()
        pc1 = c1.get_component(ProductorComponent)
        pc1.factories[ft] = [Factory(ft, build_remaining=0)]
        pc1.init_prices()
        c1.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=gt, quantity=50, quality=0.6, brand_value=3)
        )

        c2 = Company()
        pc2 = c2.get_component(ProductorComponent)
        pc2.factories[ft] = [Factory(ft, build_remaining=0)]
        pc2.init_prices()
        c2.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=gt, quantity=80, quality=0.9, brand_value=7)
        )

        market = MarketService()
        service = CompanyService()
        service.companies = {"c1": c1, "c2": c2}
        service.sell_phase(market)

        orders = market.get_sell_orders(gt)
        assert len(orders) == 2
