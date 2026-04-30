"""Tests for CompanyService.buy_phase — demand calculation and preference sorting."""

from __future__ import annotations

from component.decision.company.classic import ClassicCompanyDecisionComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.entity import Entity
from entity.company.company import Company
from entity.goods import GoodsBatch, GoodsType
from entity.factory import Factory, FactoryType, Recipe
from system.company_service import CompanyService
from system.market_service import BuyIntent, MarketService, SellOrder


def _gt(name: str = "silicon", base_price: int = 100) -> GoodsType:
    return GoodsType(name=name, base_price=base_price)


class TestBuyPhaseDemand:
    """buy_phase should compute demand = sum(recipe.input_quantity * base_production) - existing stock, min 0."""

    def test_basic_demand_no_stock(self) -> None:
        """Demand = input_qty * base_production when no existing stock."""
        gt_input = _gt("silicon", 100)
        gt_output = _gt("chip", 500)
        recipe = Recipe(input_goods_type=gt_input, input_quantity=2, output_goods_type=gt_output, output_quantity=1, tech_quality_weight=0.6)
        ft = FactoryType(recipe=recipe, base_production=50, build_cost=1000, maintenance_cost=50, build_time=1)

        company = Company(name="buyer")
        pc = company.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()

        # Seller with silicon in stock
        seller = Company(name="seller")
        seller_pc = seller.get_component(ProductorComponent)
        seller_ft = FactoryType(
            recipe=Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt_input, output_quantity=10, tech_quality_weight=1.0),
            base_production=100, build_cost=500, maintenance_cost=20, build_time=1,
        )
        seller_pc.factories[seller_ft] = [Factory(seller_ft, build_remaining=0)]
        seller_pc.init_prices()
        seller_storage = seller.get_component(StorageComponent)
        seller_batch = GoodsBatch(goods_type=gt_input, quantity=200, quality=0.5, brand_value=0)
        seller_storage.add_batch(seller_batch)

        market = MarketService()
        seller_service = CompanyService()
        seller_service.companies = {"seller": seller}
        seller_service.sell_phase(market)

        service = CompanyService()
        service.companies = {"buyer": company}
        intents = service.buy_phase(market)

        # demand = 2 * 50 = 100
        assert len(intents) == 1
        assert intents[0].buyer is company
        assert intents[0].goods_type is gt_input
        assert intents[0].quantity == 100

    def test_demand_reduced_by_existing_stock(self) -> None:
        """Existing stock reduces demand."""
        gt_input = _gt("silicon", 100)
        gt_output = _gt("chip", 500)
        recipe = Recipe(input_goods_type=gt_input, input_quantity=2, output_goods_type=gt_output, output_quantity=1, tech_quality_weight=0.6)
        ft = FactoryType(recipe=recipe, base_production=50, build_cost=1000, maintenance_cost=50, build_time=1)

        company = Company(name="buyer")
        pc = company.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        storage = company.get_component(StorageComponent)
        storage.add_batch(GoodsBatch(goods_type=gt_input, quantity=30, quality=0.5, brand_value=0))

        seller = Company(name="seller")
        seller_pc = seller.get_component(ProductorComponent)
        seller_ft = FactoryType(
            recipe=Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt_input, output_quantity=10, tech_quality_weight=1.0),
            base_production=100, build_cost=500, maintenance_cost=20, build_time=1,
        )
        seller_pc.factories[seller_ft] = [Factory(seller_ft, build_remaining=0)]
        seller_pc.init_prices()
        seller.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=gt_input, quantity=200, quality=0.5, brand_value=0)
        )

        market = MarketService()
        s = CompanyService()
        s.companies = {"s": seller}
        s.sell_phase(market)

        service = CompanyService()
        service.companies = {"buyer": company}
        intents = service.buy_phase(market)

        # demand = 2 * 50 - 30 = 70
        assert intents[0].quantity == 70

    def test_demand_zero_when_stock_sufficient(self) -> None:
        """No BuyIntent when stock >= demand."""
        gt_input = _gt("silicon", 100)
        gt_output = _gt("chip", 500)
        recipe = Recipe(input_goods_type=gt_input, input_quantity=2, output_goods_type=gt_output, output_quantity=1, tech_quality_weight=0.6)
        ft = FactoryType(recipe=recipe, base_production=50, build_cost=1000, maintenance_cost=50, build_time=1)

        company = Company(name="buyer")
        pc = company.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        storage = company.get_component(StorageComponent)
        storage.add_batch(GoodsBatch(goods_type=gt_input, quantity=200, quality=0.5, brand_value=0))

        market = MarketService()
        service = CompanyService()
        service.companies = {"buyer": company}
        intents = service.buy_phase(market)

        assert len(intents) == 0

    def test_raw_material_factory_no_demand(self) -> None:
        """Factories with no input (raw material) don't generate BuyIntents."""
        gt_raw = _gt("silicon", 100)
        recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt_raw, output_quantity=10, tech_quality_weight=1.0)
        ft = FactoryType(recipe=recipe, base_production=100, build_cost=500, maintenance_cost=20, build_time=1)

        company = Company(name="raw_producer")
        pc = company.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()

        market = MarketService()
        service = CompanyService()
        service.companies = {"buyer": company}
        intents = service.buy_phase(market)

        assert len(intents) == 0


class TestBuyPhasePreference:
    """buy_phase sort_key should order SellOrders by score (quality + brand + price attractiveness)."""

    def test_sort_key_prefers_better_cost_performance(self) -> None:
        """Verify sort_key produces correct ordering: cheaper seller with decent quality is preferred."""
        gt_input = _gt("silicon", 100)
        gt_output = _gt("chip", 500)
        recipe = Recipe(input_goods_type=gt_input, input_quantity=2, output_goods_type=gt_output, output_quantity=1, tech_quality_weight=0.6)
        ft = FactoryType(recipe=recipe, base_production=50, build_cost=1000, maintenance_cost=50, build_time=1)

        buyer = Company(name="buyer")
        pc = buyer.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        buyer.init_component(ClassicCompanyDecisionComponent)
        # Set traits so price sensitivity is high → cheaper seller wins
        dc = buyer.get_component(ClassicCompanyDecisionComponent)
        dc.marketing_awareness = 0.1
        dc.price_sensitivity = 0.8

        # seller_a: quality 0.8, price 100 (cheaper)
        seller_a = Company(name="seller_a")
        seller_a_pc = seller_a.get_component(ProductorComponent)
        seller_a_ft = FactoryType(
            recipe=Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt_input, output_quantity=10, tech_quality_weight=1.0),
            base_production=100, build_cost=500, maintenance_cost=20, build_time=1,
        )
        seller_a_pc.factories[seller_a_ft] = [Factory(seller_a_ft, build_remaining=0)]
        seller_a_pc.init_prices()
        batch_a = GoodsBatch(goods_type=gt_input, quantity=200, quality=0.8, brand_value=5)
        seller_a.get_component(StorageComponent).add_batch(batch_a)

        # seller_b: quality 0.9, price 200 (expensive)
        seller_b = Company(name="seller_b")
        seller_b_pc = seller_b.get_component(ProductorComponent)
        seller_b_ft = FactoryType(
            recipe=Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt_input, output_quantity=10, tech_quality_weight=1.0),
            base_production=100, build_cost=500, maintenance_cost=20, build_time=1,
        )
        seller_b_pc.factories[seller_b_ft] = [Factory(seller_b_ft, build_remaining=0)]
        seller_b_pc.prices[gt_input] = 200
        batch_b = GoodsBatch(goods_type=gt_input, quantity=200, quality=0.9, brand_value=10)
        seller_b.get_component(StorageComponent).add_batch(batch_b)

        market = MarketService()
        sell_service = CompanyService()
        sell_service.companies = {"a": seller_a, "b": seller_b}
        sell_service.sell_phase(market)

        from system.decision_service import DecisionService
        ds = DecisionService()

        buy_service = CompanyService()
        buy_service.companies = {"buyer": buyer}
        intents = buy_service.buy_phase(market, decision_service=ds)

        # Verify sort_key orders correctly
        assert len(intents) == 1
        orders = market.get_sell_orders(gt_input)
        sorted_orders = sorted(orders, key=intents[0].sort_key, reverse=True)
        assert sorted_orders[0].seller is seller_a  # cheaper price wins with high price_sensitivity
        assert sorted_orders[1].seller is seller_b
