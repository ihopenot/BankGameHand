"""FolkService 测试。"""
from __future__ import annotations

import math

from pathlib import Path

import pytest

from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.storage_component import StorageComponent
from core.config import ConfigManager
from core.entity import Entity
from entity.folk import Folk
from entity.goods import GoodsBatch, GoodsType
from system.folk_service import FolkService
from system.market_service import MarketService, SellOrder, TradeRecord

_TEST_CONFIG_DIR = str(Path(__file__).parent / "config_integration")


@pytest.fixture(autouse=True)
def _reset_config():
    ConfigManager._instance = None
    ConfigManager().load(_TEST_CONFIG_DIR)
    yield
    ConfigManager._instance = None


class TestFolkServiceInit:
    """FolkService 基础结构测试。"""

    def test_folk_service_holds_folks_list(self) -> None:
        gt_food = GoodsType(name="食品", base_price=8000)
        folk_a = Folk(
            population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
            base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.1}},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        )
        folk_b = Folk(
            population=200, w_quality=0.8, w_brand=0.2, w_price=0.0,
            base_demands={gt_food: {"per_capita": 5, "sensitivity": 0.2}},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        )
        service = FolkService(folks=[folk_a, folk_b])
        assert len(service.folks) == 2
        assert service.folks[0] is folk_a
        assert service.folks[1] is folk_b


class TestComputeDemands:
    """需求计算测试。"""

    def test_basic_demand_calculation(self) -> None:
        """验证公式：population * per_capita * (1 + economy_cycle_index * sensitivity)"""
        gt_food = GoodsType(name="食品", base_price=8000)
        folk = Folk(
            population=1000, w_quality=0.5, w_brand=0.5, w_price=0.0,
            base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.2}},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        )
        service = FolkService(folks=[folk])
        demands = service.compute_demands(economy_cycle_index=0.5)
        # 1000 * 10 * (1 + 0.5 * 0.2) = 1000 * 10 * 1.1 = 11000
        assert demands[folk][gt_food] == 11000

    def test_zero_per_capita_returns_zero(self) -> None:
        """per_capita=0 的商品需求为 0。"""
        gt_phone = GoodsType(name="手机", base_price=20000)
        folk = Folk(
            population=6000, w_quality=0.95, w_brand=0.05, w_price=0.0,
            base_demands={gt_phone: {"per_capita": 0, "sensitivity": 0.8}},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        )
        service = FolkService(folks=[folk])
        demands = service.compute_demands(economy_cycle_index=0.3)
        assert demands[folk][gt_phone] == 0

    def test_different_folk_different_demands(self) -> None:
        """不同 Folk 对同一商品的需求量不同。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        folk_a = Folk(
            population=6000, w_quality=0.95, w_brand=0.05, w_price=0.0,
            base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.1}},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        )
        folk_b = Folk(
            population=1000, w_quality=0.2, w_brand=0.8, w_price=0.0,
            base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.05}},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        )
        service = FolkService(folks=[folk_a, folk_b])
        demands = service.compute_demands(economy_cycle_index=1.0)
        # folk_a: 6000 * 10 * (1 + 1.0 * 0.1) = 66000
        # folk_b: 1000 * 10 * (1 + 1.0 * 0.05) = 10500
        assert demands[folk_a][gt_food] == 66000
        assert demands[folk_b][gt_food] == 10500

    def test_negative_cycle_reduces_demand(self) -> None:
        """经济衰退（负周期指数）减少需求。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        folk = Folk(
            population=1000, w_quality=0.5, w_brand=0.5, w_price=0.0,
            base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.5}},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        )
        service = FolkService(folks=[folk])
        demands = service.compute_demands(economy_cycle_index=-0.4)
        # 1000 * 10 * (1 + (-0.4) * 0.5) = 1000 * 10 * 0.8 = 8000
        assert demands[folk][gt_food] == 8000

    def test_unconfigured_goods_not_in_demands(self) -> None:
        """Folk 未配置的商品不出现在 demands 中。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        gt_phone = GoodsType(name="手机", base_price=20000)
        folk = Folk(
            population=1000, w_quality=0.5, w_brand=0.5, w_price=0.0,
            base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.1}},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        )
        service = FolkService(folks=[folk])
        demands = service.compute_demands(economy_cycle_index=0.0)
        assert gt_food in demands[folk]
        assert gt_phone not in demands[folk]


def _make_seller(goods_type: GoodsType, quantity: int, quality: float, brand: int, price: int) -> tuple[Entity, SellOrder]:
    """辅助函数：创建卖方实体和 SellOrder。"""
    seller = Entity()
    seller.init_component(StorageComponent)
    seller.init_component(LedgerComponent)
    batch = GoodsBatch(goods_type=goods_type, quantity=quantity, quality=quality, brand_value=brand)
    seller.get_component(StorageComponent).add_batch(batch)
    order = SellOrder(seller=seller, batch=batch, price=price)
    return seller, order


class TestWeightedAllocation:
    """softmax 评分与加权分配测试。"""

    def test_single_seller_gets_all_demand(self) -> None:
        """只有一个卖方时，该卖方获得全部需求。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        market = MarketService()
        seller, order = _make_seller(gt_food, quantity=1000, quality=0.5, brand=10, price=100)
        market.add_sell_order(order)

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 5, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        service = FolkService(folks=[folk])
        trades = service.allocate_and_trade(folk, gt_food, demand=500, market=market)

        total_bought = sum(t.quantity for t in trades)
        assert total_bought == 500

    def test_two_sellers_higher_score_gets_more(self) -> None:
        """评分高的卖方分配到更多需求。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        market = MarketService()
        # 卖方A：高品质低价 → 高性价比
        _, order_a = _make_seller(gt_food, quantity=1000, quality=0.8, brand=5, price=100)
        # 卖方B：低品质高价 → 低性价比
        _, order_b = _make_seller(gt_food, quantity=1000, quality=0.2, brand=5, price=200)
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)

        # 价格敏感的 Folk
        folk = Folk(population=100, w_quality=0.9, w_brand=0.1, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 5, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        service = FolkService(folks=[folk])
        trades = service.allocate_and_trade(folk, gt_food, demand=500, market=market)

        qty_a = sum(t.quantity for t in trades if t.seller is order_a.seller)
        qty_b = sum(t.quantity for t in trades if t.seller is order_b.seller)
        # A 的评分更高（性价比高），应分配到更多
        assert qty_a > qty_b
        assert qty_a + qty_b == 500

    def test_all_sellers_get_some_demand(self) -> None:
        """softmax 保证所有卖方（包括低评分）都分到需求。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        market = MarketService()
        _, order_a = _make_seller(gt_food, quantity=1000, quality=0.9, brand=10, price=100)
        _, order_b = _make_seller(gt_food, quantity=1000, quality=0.1, brand=1, price=200)
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        service = FolkService(folks=[folk])
        trades = service.allocate_and_trade(folk, gt_food, demand=1000, market=market)

        qty_a = sum(t.quantity for t in trades if t.seller is order_a.seller)
        qty_b = sum(t.quantity for t in trades if t.seller is order_b.seller)
        # 两个卖方都应分到需求
        assert qty_a > 0
        assert qty_b > 0

    def test_sufficient_stock_one_pass(self) -> None:
        """所有卖方库存充足时一次分配完成。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        market = MarketService()
        _, order_a = _make_seller(gt_food, quantity=500, quality=0.5, brand=5, price=100)
        _, order_b = _make_seller(gt_food, quantity=500, quality=0.5, brand=5, price=100)
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 5, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        service = FolkService(folks=[folk])
        trades = service.allocate_and_trade(folk, gt_food, demand=400, market=market)

        total = sum(t.quantity for t in trades)
        assert total == 400


class TestIterativeReallocation:
    """迭代重分配测试。"""

    def test_seller_stock_insufficient_reallocates(self) -> None:
        """卖方A库存不足 → 只成交库存量 → 剩余重分配给卖方B。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        market = MarketService()
        # 卖方A：库存只有 30，评分相同
        _, order_a = _make_seller(gt_food, quantity=30, quality=0.5, brand=5, price=100)
        # 卖方B：库存充足 1000
        _, order_b = _make_seller(gt_food, quantity=1000, quality=0.5, brand=5, price=100)
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 5, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        service = FolkService(folks=[folk])
        trades = service.allocate_and_trade(folk, gt_food, demand=500, market=market)

        total = sum(t.quantity for t in trades)
        # 卖方A只能提供30，剩余应重新分配给B
        qty_a = sum(t.quantity for t in trades if t.seller is order_a.seller)
        qty_b = sum(t.quantity for t in trades if t.seller is order_b.seller)
        assert qty_a == 30  # A售罄
        assert total == 500  # 总需求满足
        assert qty_b == 470  # B承接剩余

    def test_all_sellers_exhausted(self) -> None:
        """所有卖方售罄，剩余需求为缺货。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        market = MarketService()
        _, order_a = _make_seller(gt_food, quantity=100, quality=0.5, brand=5, price=100)
        _, order_b = _make_seller(gt_food, quantity=50, quality=0.5, brand=5, price=100)
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 5, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        service = FolkService(folks=[folk])
        trades = service.allocate_and_trade(folk, gt_food, demand=500, market=market)

        total = sum(t.quantity for t in trades)
        # 最多买到 100+50=150
        assert total == 150
        assert order_a.remaining == 0
        assert order_b.remaining == 0

    def test_multi_round_iteration_converges(self) -> None:
        """多轮迭代场景：三个卖方，库存递减。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        market = MarketService()
        _, order_a = _make_seller(gt_food, quantity=50, quality=0.5, brand=5, price=100)
        _, order_b = _make_seller(gt_food, quantity=100, quality=0.5, brand=5, price=100)
        _, order_c = _make_seller(gt_food, quantity=1000, quality=0.5, brand=5, price=100)
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)
        market.add_sell_order(order_c)

        folk = Folk(population=300, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 3, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        service = FolkService(folks=[folk])
        trades = service.allocate_and_trade(folk, gt_food, demand=900, market=market)

        total = sum(t.quantity for t in trades)
        assert total == 900  # 全部满足（总供给 1150 > 900）


class TestSettleTrades:
    """采购结算测试。"""

    def test_goods_transfer_to_folk(self) -> None:
        """商品从卖方扣减并入库到 Folk。"""
        gt_food = GoodsType(name="食品", base_price=8000)

        seller = Entity()
        seller.init_component(StorageComponent)
        seller.init_component(LedgerComponent)
        batch = GoodsBatch(goods_type=gt_food, quantity=100, quality=0.5, brand_value=10)
        seller.get_component(StorageComponent).add_batch(batch)

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 1, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        folk.get_component(LedgerComponent).cash = 1_000_000  # 充足现金

        trade = TradeRecord(seller=seller, buyer=folk, goods_type=gt_food, quantity=50, price=100)

        service = FolkService(folks=[folk])
        service.settle_trades([trade])

        # 卖方库存减少
        seller_batches = seller.get_component(StorageComponent).get_batches(gt_food)
        seller_qty = sum(b.quantity for b in seller_batches)
        assert seller_qty == 50

        # 买方（Folk）库存增加
        folk_batches = folk.get_component(StorageComponent).get_batches(gt_food)
        folk_qty = sum(b.quantity for b in folk_batches)
        assert folk_qty == 50

    def test_cash_payment(self) -> None:
        """现金从 Folk 支付到卖方。"""
        gt_food = GoodsType(name="食品", base_price=8000)

        seller = Entity()
        seller.init_component(StorageComponent)
        seller.init_component(LedgerComponent)
        batch = GoodsBatch(goods_type=gt_food, quantity=100, quality=0.5, brand_value=10)
        seller.get_component(StorageComponent).add_batch(batch)
        seller.get_component(LedgerComponent).cash = 0

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 1, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        folk.get_component(LedgerComponent).cash = 100_000

        trade = TradeRecord(seller=seller, buyer=folk, goods_type=gt_food, quantity=50, price=100)
        # total = 50 * 100 = 5000

        service = FolkService(folks=[folk])
        service.settle_trades([trade])

        assert folk.get_component(LedgerComponent).cash == 100_000 - 5000
        assert seller.get_component(LedgerComponent).cash == 5000


class TestBuyPhase:
    """buy_phase 端到端集成测试。"""

    def test_buy_phase_two_folks_two_sellers(self) -> None:
        """两个 Folk + 两个卖方，验证完整采购流程。"""
        gt_food = GoodsType(name="食品", base_price=8000)

        # 卖方A：高品质低价
        seller_a, order_a = _make_seller(gt_food, quantity=5000, quality=0.9, brand=8, price=50)
        seller_a.get_component(LedgerComponent).cash = 0
        # 卖方B：低品质高价
        seller_b, order_b = _make_seller(gt_food, quantity=5000, quality=0.3, brand=2, price=150)
        seller_b.get_component(LedgerComponent).cash = 0

        market = MarketService()
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)

        # Folk 1: 品质敏感（高 w_quality），100人，per_capita=10
        folk_1 = Folk(population=100, w_quality=0.95, w_brand=0.05, w_price=0.0,
                      base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.0}},
                      labor_participation_rate=0.6, labor_points_per_capita=1.0)
        folk_1.get_component(LedgerComponent).cash = 10_000_000

        # Folk 2: 品牌敏感（高 w_brand），50人，per_capita=10
        folk_2 = Folk(population=50, w_quality=0.1, w_brand=0.9, w_price=0.0,
                      base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.0}},
                      labor_participation_rate=0.6, labor_points_per_capita=1.0)
        folk_2.get_component(LedgerComponent).cash = 10_000_000

        service = FolkService(folks=[folk_1, folk_2])
        trades = service.buy_phase(market=market, economy_cycle_index=0.0)

        # folk_1 需求：100 * 10 * 1.0 = 1000
        # folk_2 需求：50 * 10 * 1.0 = 500
        total_traded = sum(t.quantity for t in trades)
        assert total_traded == 1500

        # folk_1 是价格敏感 → 卖方A（高性价比）应分到更多
        folk1_from_a = sum(t.quantity for t in trades if t.buyer is folk_1 and t.seller is seller_a)
        folk1_from_b = sum(t.quantity for t in trades if t.buyer is folk_1 and t.seller is seller_b)
        assert folk1_from_a > folk1_from_b

        # folk_2 是品牌敏感 → 卖方A（brand=8）应分到更多
        folk2_from_a = sum(t.quantity for t in trades if t.buyer is folk_2 and t.seller is seller_a)
        folk2_from_b = sum(t.quantity for t in trades if t.buyer is folk_2 and t.seller is seller_b)
        assert folk2_from_a > folk2_from_b

        # 验证结算：卖方现金增加
        assert seller_a.get_component(LedgerComponent).cash > 0
        assert seller_b.get_component(LedgerComponent).cash > 0

        # 验证结算：Folk 库存增加
        folk1_qty = sum(b.quantity for b in folk_1.get_component(StorageComponent).get_batches(gt_food))
        folk2_qty = sum(b.quantity for b in folk_2.get_component(StorageComponent).get_batches(gt_food))
        assert folk1_qty == 1000
        assert folk2_qty == 500

    def test_buy_phase_sell_order_remaining_decremented(self) -> None:
        """buy_phase 后 SellOrder.remaining 正确扣减。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        seller, order = _make_seller(gt_food, quantity=1000, quality=0.5, brand=5, price=100)

        market = MarketService()
        market.add_sell_order(order)

        folk = Folk(population=200, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 2, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        folk.get_component(LedgerComponent).cash = 10_000_000

        service = FolkService(folks=[folk])
        service.buy_phase(market=market, economy_cycle_index=0.0)

        # demand = 200 * 2 * 1.0 = 400
        assert order.remaining == 600

    def test_buy_phase_multiple_goods_types(self) -> None:
        """多种商品类型的 buy_phase。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        gt_cloth = GoodsType(name="服装", base_price=15000)

        seller_food, order_food = _make_seller(gt_food, quantity=5000, quality=0.5, brand=5, price=80)
        seller_cloth, order_cloth = _make_seller(gt_cloth, quantity=5000, quality=0.5, brand=5, price=200)

        market = MarketService()
        market.add_sell_order(order_food)
        market.add_sell_order(order_cloth)

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={
                        gt_food: {"per_capita": 10, "sensitivity": 0.0},
                        gt_cloth: {"per_capita": 5, "sensitivity": 0.0},
                    },
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        folk.get_component(LedgerComponent).cash = 10_000_000

        service = FolkService(folks=[folk])
        trades = service.buy_phase(market=market, economy_cycle_index=0.0)

        food_traded = sum(t.quantity for t in trades if t.goods_type is gt_food)
        cloth_traded = sum(t.quantity for t in trades if t.goods_type is gt_cloth)
        # food demand: 100 * 10 = 1000, cloth demand: 100 * 5 = 500
        assert food_traded == 1000
        assert cloth_traded == 500

    def test_buy_phase_updates_last_avg_buy_prices(self) -> None:
        """buy_phase 后 Folk 的 last_avg_buy_prices 按成交量加权均价更新。"""
        gt_food = GoodsType(name="食品", base_price=8000)
        seller_a, order_a = _make_seller(gt_food, quantity=5000, quality=0.5, brand=5, price=100)
        seller_b, order_b = _make_seller(gt_food, quantity=5000, quality=0.5, brand=5, price=200)

        market = MarketService()
        market.add_sell_order(order_a)
        market.add_sell_order(order_b)

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        folk.get_component(LedgerComponent).cash = 10_000_000

        service = FolkService(folks=[folk])
        trades = service.buy_phase(market=market, economy_cycle_index=0.0)

        # 应该有 last_avg_buy_prices 被更新
        mc = folk.get_component(MetricComponent)
        assert gt_food in mc.last_avg_buy_prices
        # 加权均价应介于 100 和 200 之间
        avg = mc.last_avg_buy_prices[gt_food]
        assert 100 <= avg <= 200

    def test_folk_buy_updates_seller_metrics(self) -> None:
        """居民购买后，卖方 Company 的 MetricComponent 记录成交量和收入。"""
        from component.metric_component import MetricComponent
        from entity.company.company import Company
        from component.productor_component import ProductorComponent
        from entity.factory import Factory, FactoryType, Recipe

        ConfigManager._instance = None
        ConfigManager().load(_TEST_CONFIG_DIR)

        gt_food = GoodsType(name="食品", base_price=8000)
        recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt_food, output_quantity=10, tech_quality_weight=1.0)
        ft = FactoryType(recipe=recipe, labor_demand=50, build_cost=1000, maintenance_cost=50, build_time=1)

        seller = Company(name="seller")
        pc = seller.get_component(ProductorComponent)
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        batch = GoodsBatch(goods_type=gt_food, quantity=5000, quality=0.5, brand_value=5)
        seller.get_component(StorageComponent).add_batch(batch)
        seller.get_component(LedgerComponent).cash = 0

        order = SellOrder(seller=seller, batch=batch, price=100)
        market = MarketService()
        market.add_sell_order(order)

        folk = Folk(population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                    base_demands={gt_food: {"per_capita": 10, "sensitivity": 0.0}},
                    labor_participation_rate=0.6, labor_points_per_capita=1.0)
        folk.get_component(LedgerComponent).cash = 10_000_000

        service = FolkService(folks=[folk])
        trades = service.buy_phase(market=market, economy_cycle_index=0.0)

        mc = seller.get_component(MetricComponent)
        total_sold = sum(t.quantity for t in trades if t.seller is seller)
        assert mc.last_sold_quantities[gt_food] == total_sold
        assert mc.last_revenue == total_sold * 100
