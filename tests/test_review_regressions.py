from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.entity import Entity
from core.types import Loan, LoanType, RepaymentType
from entity.company.company import Company
from core.config import ConfigManager
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsBatch, GoodsType
from game.game import Game
from system.company_service import CompanyService
from system.market_service import BuyIntent, MarketService, SellOrder
from system.productor_service import ProductorService


@pytest.fixture(autouse=True)
def clear_component_state() -> None:
    ConfigManager._instance = None
    ConfigManager().load()
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    StorageComponent.components.clear()
    LedgerComponent.components.clear()
    GoodsType.types.clear()
    Recipe.recipes.clear()
    FactoryType.factory_types.clear()
    yield
    ConfigManager._instance = None
    ProductorComponent.components.clear()
    ProductorComponent.max_tech.clear()
    StorageComponent.components.clear()
    LedgerComponent.components.clear()
    GoodsType.types.clear()
    Recipe.recipes.clear()
    FactoryType.factory_types.clear()


def _make_service_game() -> MagicMock:
    return MagicMock()


class _CompanyPlanStub:
    def __init__(self) -> None:
        self.called = False

    def plan_phase(self) -> None:
        self.called = True


class TestMarketRegressionCoverage:
    def test_proportional_match_does_not_drop_remainder_supply(self) -> None:
        goods_type = GoodsType(name='silicon', base_price=100)
        seller = Entity()
        seller.init_component(StorageComponent)
        batch = GoodsBatch(goods_type=goods_type, quantity=1, quality=0.5, brand_value=0)
        seller.get_component(StorageComponent).add_batch(batch)

        market = MarketService()
        order = SellOrder(seller=seller, batch=batch, price=100)
        market.add_sell_order(order)

        buyer_a = Entity()
        buyer_b = Entity()
        intents = [
            BuyIntent(buyer=buyer_a, goods_type=goods_type, quantity=1, sort_key=lambda o: o.price),
            BuyIntent(buyer=buyer_b, goods_type=goods_type, quantity=1, sort_key=lambda o: o.price),
        ]

        records = market.match(intents)

        assert len(records) == 1
        assert records[0].quantity == 1
        assert sorted(intent.remaining for intent in intents) == [0, 1]
        assert order.remaining == 0


class TestTradeSettlementRegressionCoverage:
    def test_settlement_uses_the_matched_batch_metadata(self) -> None:
        goods_type = GoodsType(name='silicon', base_price=100)
        seller = Company()
        buyer = Company()

        seller_storage = seller.get_component(StorageComponent)
        seller_productor = seller.get_component(ProductorComponent)
        seller_productor.prices[goods_type] = 100
        seller_storage.add_batch(GoodsBatch(goods_type=goods_type, quantity=50, quality=0.1, brand_value=1))
        seller_storage.add_batch(GoodsBatch(goods_type=goods_type, quantity=50, quality=0.9, brand_value=9))
        buyer.get_component(LedgerComponent).cash = 5000

        market = MarketService()
        service = CompanyService()
        service.companies = {'seller': seller}
        service.sell_phase(market)

        intent = BuyIntent(
            buyer=buyer,
            goods_type=goods_type,
            quantity=50,
            sort_key=lambda order: order.batch.quality,
        )
        trades = market.match([intent])

        service.settle_trades(trades)

        bought_batches = buyer.get_component(StorageComponent).get_batches(goods_type)
        assert len(bought_batches) == 1
        assert bought_batches[0].quantity == 50
        assert bought_batches[0].quality == pytest.approx(0.9)
        assert bought_batches[0].brand_value == 9

    def test_settlement_charges_only_for_delivered_quantity(self) -> None:
        goods_type = GoodsType(name='silicon', base_price=100)
        seller = Company()
        buyer = Company()

        seller_storage = seller.get_component(StorageComponent)
        seller_productor = seller.get_component(ProductorComponent)
        seller_productor.prices[goods_type] = 100
        seller_storage.add_batch(GoodsBatch(goods_type=goods_type, quantity=100, quality=0.5, brand_value=0))

        buyer_ledger = buyer.get_component(LedgerComponent)
        buyer_ledger.cash = 10000
        seller_ledger = seller.get_component(LedgerComponent)

        market = MarketService()
        service = CompanyService()
        service.companies = {'seller': seller}
        service.sell_phase(market)

        intent = BuyIntent(
            buyer=buyer,
            goods_type=goods_type,
            quantity=100,
            sort_key=lambda order: order.price,
        )
        trades = market.match([intent])

        seller_storage.get_batches(goods_type)[0].quantity = 30
        service.settle_trades(trades)

        buyer_batches = buyer.get_component(StorageComponent).get_batches(goods_type)
        assert len(buyer_batches) == 1
        assert buyer_batches[0].quantity == 30
        assert buyer_ledger.cash == 7000
        assert seller_ledger.cash == 3000
        assert buyer_ledger.payables == []
        assert seller_ledger.receivables == []


class TestLedgerRegressionCoverage:
    def test_unpaid_trade_payable_does_not_advance_term(self) -> None:
        creditor = Entity()
        creditor_ledger = creditor.init_component(LedgerComponent)
        debtor = Entity()
        debtor_ledger = debtor.init_component(LedgerComponent)
        creditor_ledger.cash = 5000

        loan = Loan(
            creditor=creditor,
            debtor=debtor,
            principal=5000,
            rate=0,
            term=1,
            loan_type=LoanType.TRADE_PAYABLE,
            repayment_type=RepaymentType.BULLET,
        )
        creditor_ledger.issue_loan(loan)
        debtor_ledger.cash = 0

        first_bill = debtor_ledger.generate_bills()[0]
        assert first_bill.total_due == 5000

        debtor_ledger.settle_all()

        assert loan.elapsed == 1

    def test_unpaid_trade_payable_stays_due_next_round(self) -> None:
        creditor = Entity()
        creditor_ledger = creditor.init_component(LedgerComponent)
        debtor = Entity()
        debtor_ledger = debtor.init_component(LedgerComponent)
        creditor_ledger.cash = 5000

        loan = Loan(
            creditor=creditor,
            debtor=debtor,
            principal=5000,
            rate=0,
            term=1,
            loan_type=LoanType.TRADE_PAYABLE,
            repayment_type=RepaymentType.BULLET,
        )
        creditor_ledger.issue_loan(loan)
        debtor_ledger.cash = 0

        debtor_ledger.generate_bills()
        debtor_ledger.settle_all()
        second_bill = debtor_ledger.generate_bills()[0]

        assert second_bill.principal_due == 5000
        assert second_bill.total_due == 5000
        assert loan.remaining == 5000


class TestProductorRegressionCoverage:
    def test_update_phase_recomputes_max_tech_after_highest_component_is_removed(self) -> None:
        goods_type = GoodsType(name='silicon', base_price=100)
        recipe = Recipe(
            input_goods_type=None,
            input_quantity=0,
            output_goods_type=goods_type,
            output_quantity=1,
            tech_quality_weight=1.0,
        )
        factory_type = FactoryType(
            recipe=recipe,
            base_production=1,
            build_cost=100,
            maintenance_cost=10,
            build_time=0,
        )

        low_entity = Entity()
        low_productor = low_entity.init_component(ProductorComponent)
        low_productor.tech_values[recipe] = 100
        low_productor.factories[factory_type].append(Factory(factory_type=factory_type, build_remaining=0))

        high_entity = Entity()
        high_productor = high_entity.init_component(ProductorComponent)
        high_productor.tech_values[recipe] = 200
        high_productor.factories[factory_type].append(Factory(factory_type=factory_type, build_remaining=0))

        service = ProductorService(_make_service_game())
        service.update_phase()
        assert ProductorComponent.max_tech[recipe] == 200

        high_entity.destroy()
        assert len(ProductorComponent.components) == 1
        service.update_phase()

        assert ProductorComponent.max_tech[recipe] == 100


class TestGameRegressionCoverage:
    def test_game_init_sets_up_required_services(self) -> None:
        game = Game()

        assert hasattr(game, 'economy_service')
        assert hasattr(game, 'company_service')
        assert hasattr(game, 'market_service')
        assert hasattr(game, 'folk_service')

    def test_plan_phase_is_noop(self) -> None:
        game = Game()
        # plan_phase 当前为跳过状态，不应报错
        game.plan_phase()
