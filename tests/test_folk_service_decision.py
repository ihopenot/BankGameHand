"""FolkService 使用决策组件测试。"""

import pytest

from component.decision.folk.classic import ClassicFolkDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.storage_component import StorageComponent
from core.config import ConfigManager
from core.entity import Entity
from entity.folk import Folk
from entity.goods import GoodsBatch, GoodsType
from system.market_service import MarketService, SellOrder


GT_FOOD = GoodsType(name="食品", base_price=50)
GT_CLOTH = GoodsType(name="服装", base_price=200)


@pytest.fixture(autouse=True)
def _load_config():
    ConfigManager._instance = None
    ConfigManager().load()
    yield
    ConfigManager._instance = None


@pytest.fixture(autouse=True)
def _clear_components():
    ClassicFolkDecisionComponent.components.clear()
    yield
    ClassicFolkDecisionComponent.components.clear()


def _make_folk_with_decision(population=6000, w_quality=0.4, w_brand=0.05, w_price=0.55):
    """创建带决策组件的 Folk 实体。"""
    folk = Folk(
        name="test_folk",
        population=population,
        w_quality=w_quality,
        w_brand=w_brand,
        w_price=w_price,
        spending_flow={"tech": 0.5, "brand": 0.3, "maintenance": 0.2},
        base_demands={
            GT_FOOD: {"per_capita": 10, "sensitivity": 0.1},
            GT_CLOTH: {"per_capita": 1, "sensitivity": 0.5},
        },
    )
    return folk


class TestFolkServiceDecisionComponent:
    """FolkService 通过决策组件获取支出计划。"""

    def test_folk_has_decision_component(self) -> None:
        """Folk 实体创建时自动附加 ClassicFolkDecisionComponent。"""
        folk = _make_folk_with_decision()
        dc = folk.get_component(ClassicFolkDecisionComponent)
        assert dc is not None
        assert isinstance(dc, ClassicFolkDecisionComponent)

    def test_buy_phase_uses_decision_component_for_spending_plan(self) -> None:
        """FolkService.buy_phase() 通过决策组件获取支出计划。"""
        folk = _make_folk_with_decision()
        folk.get_component(LedgerComponent).cash = 1000000

        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.set_context({
            "economy_cycle_index": 1.0,
            "reference_prices": {"食品": 50, "服装": 200},
        })

        # 验证决策组件能正确生成支出计划
        spending = dc.decide_spending()
        assert "食品" in spending
        assert spending["食品"]["demand"] > 0
        assert spending["食品"]["budget"] > 0

    def test_purchase_respects_budget_constraint(self) -> None:
        """采购时预算耗尽则停止：budget 限制实际购买量。"""
        from system.folk_service import FolkService

        folk = _make_folk_with_decision(population=100, w_quality=0.2, w_brand=0.1, w_price=0.2)
        folk.get_component(LedgerComponent).cash = 1000

        # 创建卖方
        seller = Entity()
        seller.init_component(StorageComponent)
        seller.init_component(LedgerComponent)
        batch = GoodsBatch(goods_type=GT_FOOD, quantity=5000, quality=0.5, brand_value=5)
        seller.get_component(StorageComponent).add_batch(batch)
        order = SellOrder(seller=seller, batch=batch, price=50)

        market = MarketService()
        market.add_sell_order(order)

        fs = FolkService([folk])
        # spending_tendency = 0.2 + 0.1 + 0.2 = 0.5
        # 食品: demand = 100 * 10 * 1.1 = 1100, budget = 1100 * 50 * 0.5 = 27500
        # 但 cash = 1000 → budget = min(27500, 1000) = 1000
        # 按 price=50, 最多买 1000 // 50 = 20 件
        trades = fs.buy_phase(market, economy_cycle_index=1.0)

        total_bought = sum(t.quantity for t in trades)
        assert total_bought == 20
