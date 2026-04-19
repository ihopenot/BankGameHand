"""Tests for post-trade settlement: goods transfer + payment/credit."""

from __future__ import annotations

from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.types import LoanType
from entity.company.company import Company
from entity.goods import GoodsBatch, GoodsType
from entity.factory import Factory, FactoryType, Recipe
from system.company_service import CompanyService
from system.market_service import MarketService, TradeRecord


def _gt(name: str = "silicon", base_price: int = 100) -> GoodsType:
    return GoodsType(name=name, base_price=base_price)


def _setup_seller(gt: GoodsType, quantity: int = 200, quality: float = 0.5) -> Company:
    """Create a seller company with stock of gt."""
    seller = Company()
    pc = seller.get_component(ProductorComponent)
    ft = FactoryType(
        recipe=Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt, output_quantity=10, tech_quality_weight=1.0),
        base_production=100, build_cost=500, maintenance_cost=20, build_time=1,
    )
    pc.factories[ft] = [Factory(ft, build_remaining=0)]
    pc.init_prices()
    batch = GoodsBatch(goods_type=gt, quantity=quantity, quality=quality, brand_value=0)
    seller.get_component(StorageComponent).add_batch(batch)
    return seller


def _setup_buyer(gt_input: GoodsType, gt_output: GoodsType, cash: int = 100000) -> Company:
    """Create a buyer company needing gt_input."""
    buyer = Company()
    pc = buyer.get_component(ProductorComponent)
    recipe = Recipe(input_goods_type=gt_input, input_quantity=2, output_goods_type=gt_output, output_quantity=1, tech_quality_weight=0.6)
    ft = FactoryType(recipe=recipe, base_production=50, build_cost=1000, maintenance_cost=50, build_time=1)
    pc.factories[ft] = [Factory(ft, build_remaining=0)]
    pc.init_prices()
    buyer.get_component(LedgerComponent).cash = cash
    return buyer


class TestGoodsTransfer:
    """After settlement, goods move from seller to buyer."""

    def test_buyer_receives_goods(self) -> None:
        gt = _gt()
        gt_out = _gt("chip", 500)
        seller = _setup_seller(gt, quantity=200)
        buyer = _setup_buyer(gt, gt_out, cash=100000)

        market = MarketService()
        sell_svc = CompanyService()
        sell_svc.companies = {"seller": seller}
        sell_svc.sell_phase(market)

        buy_svc = CompanyService()
        buy_svc.companies = {"buyer": buyer}
        intents = buy_svc.buy_phase(market)
        trades = market.match(intents)

        buy_svc.settle_trades(trades)

        buyer_storage = buyer.get_component(StorageComponent)
        buyer_batches = buyer_storage.get_batches(gt)
        total_bought = sum(b.quantity for b in buyer_batches)
        assert total_bought == 100  # demand = 2*50 = 100

    def test_seller_batch_quantity_reduced(self) -> None:
        gt = _gt()
        gt_out = _gt("chip", 500)
        seller = _setup_seller(gt, quantity=200)
        buyer = _setup_buyer(gt, gt_out, cash=100000)

        market = MarketService()
        sell_svc = CompanyService()
        sell_svc.companies = {"seller": seller}
        sell_svc.sell_phase(market)

        buy_svc = CompanyService()
        buy_svc.companies = {"buyer": buyer}
        intents = buy_svc.buy_phase(market)
        trades = market.match(intents)

        buy_svc.settle_trades(trades)

        seller_storage = seller.get_component(StorageComponent)
        seller_batches = seller_storage.get_batches(gt)
        total_remaining = sum(b.quantity for b in seller_batches)
        assert total_remaining == 100  # 200 - 100 = 100


class TestCashPayment:
    """When buyer has enough cash, full payment is made."""

    def test_full_cash_payment(self) -> None:
        gt = _gt(base_price=100)
        gt_out = _gt("chip", 500)
        seller = _setup_seller(gt, quantity=200)
        buyer = _setup_buyer(gt, gt_out, cash=100000)
        seller.get_component(LedgerComponent).cash = 0

        market = MarketService()
        sell_svc = CompanyService()
        sell_svc.companies = {"seller": seller}
        sell_svc.sell_phase(market)

        buy_svc = CompanyService()
        buy_svc.companies = {"buyer": buyer}
        intents = buy_svc.buy_phase(market)
        trades = market.match(intents)

        buy_svc.settle_trades(trades)

        # buyer pays 100 units * 100 price = 10000
        buyer_ledger = buyer.get_component(LedgerComponent)
        seller_ledger = seller.get_component(LedgerComponent)
        assert buyer_ledger.cash == 100000 - 10000
        assert seller_ledger.cash == 10000


class TestCreditPayment:
    """When buyer doesn't have enough cash, shortfall becomes TRADE_PAYABLE."""

    def test_partial_cash_creates_trade_payable(self) -> None:
        gt = _gt(base_price=100)
        gt_out = _gt("chip", 500)
        seller = _setup_seller(gt, quantity=200)
        buyer = _setup_buyer(gt, gt_out, cash=3000)  # Only 3000, needs 10000
        seller.get_component(LedgerComponent).cash = 0

        market = MarketService()
        sell_svc = CompanyService()
        sell_svc.companies = {"seller": seller}
        sell_svc.sell_phase(market)

        buy_svc = CompanyService()
        buy_svc.companies = {"buyer": buyer}
        intents = buy_svc.buy_phase(market)
        trades = market.match(intents)

        buy_svc.settle_trades(trades)

        buyer_ledger = buyer.get_component(LedgerComponent)
        seller_ledger = seller.get_component(LedgerComponent)

        # Buyer pays all cash
        assert buyer_ledger.cash == 0
        # Seller receives buyer's cash
        assert seller_ledger.cash == 3000

        # Shortfall = 10000 - 3000 = 7000 as TRADE_PAYABLE
        trade_payables = buyer_ledger.filter_loans(LoanType.TRADE_PAYABLE)
        assert len(trade_payables) > 0
        total_payable = sum(loan.remaining for loan in trade_payables)
        assert total_payable == 7000

    def test_zero_cash_all_credit(self) -> None:
        gt = _gt(base_price=100)
        gt_out = _gt("chip", 500)
        seller = _setup_seller(gt, quantity=200)
        buyer = _setup_buyer(gt, gt_out, cash=0)
        seller.get_component(LedgerComponent).cash = 0

        market = MarketService()
        sell_svc = CompanyService()
        sell_svc.companies = {"seller": seller}
        sell_svc.sell_phase(market)

        buy_svc = CompanyService()
        buy_svc.companies = {"buyer": buyer}
        intents = buy_svc.buy_phase(market)
        trades = market.match(intents)

        buy_svc.settle_trades(trades)

        buyer_ledger = buyer.get_component(LedgerComponent)
        trade_payables = buyer_ledger.filter_loans(LoanType.TRADE_PAYABLE)
        total_payable = sum(loan.remaining for loan in trade_payables)
        assert total_payable == 10000  # Full amount on credit

    def test_settle_trades_updates_seller_metrics(self) -> None:
        """企业间交易后，卖方 MetricComponent 记录成交量和收入。"""
        gt = _gt(base_price=100)
        gt_out = _gt("chip", 500)
        seller = _setup_seller(gt, quantity=200)
        buyer = _setup_buyer(gt, gt_out, cash=100000)
        seller.get_component(LedgerComponent).cash = 0

        market = MarketService()
        sell_svc = CompanyService()
        sell_svc.companies = {"seller": seller}
        sell_svc.sell_phase(market)

        buy_svc = CompanyService()
        buy_svc.companies = {"buyer": buyer}
        intents = buy_svc.buy_phase(market)
        trades = market.match(intents)

        buy_svc.settle_trades(trades)

        mc = seller.get_component(MetricComponent)
        total_sold = sum(t.quantity for t in trades if t.seller is seller)
        assert mc.last_sold_quantities[gt] == total_sold
        assert mc.last_revenue == total_sold * 100
