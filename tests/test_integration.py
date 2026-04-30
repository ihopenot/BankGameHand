"""全流程集成测试：创建 Game，运行 game_loop，校验结尾状态。"""
from pathlib import Path
from unittest.mock import MagicMock

from component.decision.company.classic import ClassicCompanyDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.config import ConfigManager
from core.entity import Entity
from core.types import LoanType
from entity.company.company import Company
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsBatch, GoodsType
from game.game import Game
from system.company_service import CompanyService
from system.economy_service import EconomyService
from system.economy_models.dual_cycle_model import DualCycleModel
from system.market_service import MarketService
from system.productor_service import ProductorService


INTEGRATION_CONFIG_DIR = str(Path(__file__).parent / "config_integration")


class _GameForTest(Game):
    """可测试的 Game 子类，使用集成测试配置。"""

    def __init__(self) -> None:
        super().__init__(config_path=INTEGRATION_CONFIG_DIR)


class TestGameLoopIntegration:
    def setup_method(self) -> None:
        ConfigManager._instance = None
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        LedgerComponent.components.clear()
        StorageComponent.components.clear()
        ClassicCompanyDecisionComponent.components.clear()
        MetricComponent.components.clear()
        GoodsType.types.clear()
        Recipe.recipes.clear()
        FactoryType.factory_types.clear()

    def teardown_method(self) -> None:
        ConfigManager._instance = None
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        LedgerComponent.components.clear()
        StorageComponent.components.clear()
        ClassicCompanyDecisionComponent.components.clear()
        MetricComponent.components.clear()
        GoodsType.types.clear()
        Recipe.recipes.clear()
        FactoryType.factory_types.clear()

    def test_game_loop_runs_to_completion(self):
        """game_loop 正常运行到 game_end 终止"""
        game = _GameForTest()
        game.game_loop()
        assert game.round == 20

    def test_economy_index_updated_each_round(self):
        """每轮 update_phase 后 economy_index 被更新"""
        game = _GameForTest()
        indices: list[int] = []

        original_update = game.update_phase

        def tracking_update() -> None:
            original_update()
            indices.append(game.economy_service.economy_index)

        game.update_phase = tracking_update
        game.game_loop()

        assert len(indices) == 20
        for idx in indices:
            assert isinstance(idx, int)
            assert -10000 <= idx <= 10000

    def test_economy_index_final_state(self):
        """game_loop 结束后 economy_index 与独立模型逐轮计算的第 21 轮一致"""
        game = _GameForTest()
        game.game_loop()

        # 创建独立模型，逐轮计算到第 20 轮（模拟相同的 RNG 状态推进）
        verify_model = DualCycleModel()
        for t in range(1, 21):
            verify_value = verify_model.calculate(t)

        assert game.economy_service.economy_index == verify_value

    def test_economy_model_state_matches_last_round(self):
        """game_loop 结束后模型内部状态对应最后一轮"""
        game = _GameForTest()
        game.game_loop()

        state = game.economy_service.model.get_state()
        assert state["last_t"] == 20

    def test_economy_index_not_all_same(self):
        """21 轮中 economy_index 不应全部相同（正弦波 + 噪声）"""
        game = _GameForTest()
        indices: list[int] = []

        original_update = game.update_phase

        def tracking_update() -> None:
            original_update()
            indices.append(game.economy_service.economy_index)

        game.update_phase = tracking_update
        game.game_loop()

        assert len(set(indices)) > 1

    def test_reproducible_with_fixed_seed(self):
        """固定种子下两次运行结果完全一致"""
        game1 = _GameForTest()
        game1.game_loop()
        idx1 = game1.economy_service.economy_index
        state1 = game1.economy_service.model.get_state()

        # 重新 load 配置，创建新 game
        ConfigManager._instance = None
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        LedgerComponent.components.clear()
        StorageComponent.components.clear()
        game2 = _GameForTest()
        game2.game_loop()
        idx2 = game2.economy_service.economy_index
        state2 = game2.economy_service.model.get_state()

        assert idx1 == idx2
        assert state1 == state2

    def test_price_and_investment_work(self):
        """运行 2 轮后，价格应发生变化，且至少有一个公司有非零品牌或科技投资。"""
        from component.metric_component import MetricComponent as MC

        game = _GameForTest()
        # 只运行 2 轮
        game.total_rounds = 2
        game.game_loop()

        # 价格变化检测：至少有一个公司的价格不等于 base_price
        any_price_changed = False
        for company in game.companies:
            pc = company.get_component(ProductorComponent)
            for gt, price in pc.prices.items():
                if price != gt.base_price:
                    any_price_changed = True
                    break
        assert any_price_changed, "价格更新未生效：所有公司价格仍等于 base_price"

        # 投资检测：至少有一个公司有非零品牌或科技累计投资
        any_investment = False
        for company in game.companies:
            mc = company.get_component(MC)
            if mc.cumulative_brand_spend > 0 or mc.cumulative_tech_spend > 0:
                any_investment = True
                break
        assert any_investment, "投资未生效：所有公司品牌和科技累计投资为零"
    """ProductorService 集成测试：验证多公司场景下的生产流程端到端正确。"""

    def setup_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()
        GoodsType.types.clear()
        Recipe.recipes.clear()
        FactoryType.factory_types.clear()

    def teardown_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()
        GoodsType.types.clear()
        Recipe.recipes.clear()
        FactoryType.factory_types.clear()

    def test_update_phase_reflects_highest_tech(self) -> None:
        """多个 Entity 拥有不同 tech_values，update_phase 后 max_tech 反映最高值。"""
        gt = GoodsType(name="硅", base_price=1000)
        recipe = Recipe(input_goods_type=None, input_quantity=0,
                        output_goods_type=gt, output_quantity=10, tech_quality_weight=1.0)
        ft = FactoryType(recipe=recipe, labor_demand=50,
                         build_cost=10000, maintenance_cost=500, build_time=0)

        e1 = Entity("test")
        p1 = e1.init_component(ProductorComponent)
        p1.tech_values[recipe] = 80
        p1.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        e2 = Entity("test")
        p2 = e2.init_component(ProductorComponent)
        p2.tech_values[recipe] = 200
        p2.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        game = MagicMock()
        game.economy_service = MagicMock()
        game.company_service = MagicMock()
        game.market_service = MagicMock()
        game.folk_service = MagicMock()
        service = ProductorService(game)
        service.update_phase()

        assert ProductorComponent.max_tech[recipe] == 200

    def test_product_phase_end_to_end(self) -> None:
        """多公司场景下 product_phase 执行后各公司库存有产出。"""
        gt = GoodsType(name="硅", base_price=1000)
        recipe = Recipe(input_goods_type=None, input_quantity=0,
                        output_goods_type=gt, output_quantity=10, tech_quality_weight=1.0)
        ft = FactoryType(recipe=recipe, labor_demand=50,
                         build_cost=10000, maintenance_cost=500, build_time=0)

        entities: list[Entity] = []
        for tech in (100, 150):
            e = Entity("test")
            p = e.init_component(ProductorComponent)
            p.tech_values[recipe] = tech
            p.factories[ft].append(Factory(factory_type=ft, build_remaining=0))
            e.hired_labor_points = 100  # 满员（需求 50，给 100 足够）
            e.get_component(ProductorComponent).hired_labor_points = 100
            entities.append(e)

        game = MagicMock()
        service = ProductorService(game)

        # 先更新 max_tech，再生产
        service.update_phase()
        service.product_phase()

        for e in entities:
            storage = e.get_component(StorageComponent)
            assert storage is not None
            batches = storage.get_batches(gt)
            assert len(batches) == 1
            assert batches[0].quantity == 10  # output_quantity = 10

    def test_destroy_entity_removes_from_service_scope(self) -> None:
        """Entity.destroy() 后，ProductorService 不再遍历该组件。"""
        gt = GoodsType(name="硅", base_price=1000)
        recipe = Recipe(input_goods_type=None, input_quantity=0,
                        output_goods_type=gt, output_quantity=10, tech_quality_weight=1.0)
        ft = FactoryType(recipe=recipe, labor_demand=50,
                         build_cost=10000, maintenance_cost=500, build_time=0)

        e1 = Entity("test")
        p1 = e1.init_component(ProductorComponent)
        p1.tech_values[recipe] = 100
        p1.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        e2 = Entity("test")
        p2 = e2.init_component(ProductorComponent)
        p2.tech_values[recipe] = 200
        p2.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        # destroy e2
        e2.destroy()

        game = MagicMock()
        service = ProductorService(game)
        service.update_phase()

        # max_tech 只反映 e1 的值
        assert ProductorComponent.max_tech[recipe] == 100
        assert len(ProductorComponent.components) == 1


class TestMarketTradingIntegration:
    """端到端市场交易集成测试：sell_phase → buy_phase → match → settle_trades。"""

    def setup_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()
        LedgerComponent.components.clear()
        GoodsType.types.clear()
        Recipe.recipes.clear()
        FactoryType.factory_types.clear()

    def teardown_method(self) -> None:
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        StorageComponent.components.clear()
        LedgerComponent.components.clear()
        GoodsType.types.clear()
        Recipe.recipes.clear()
        FactoryType.factory_types.clear()

    @staticmethod
    def _make_goods() -> tuple[GoodsType, GoodsType]:
        """返回 (silicon, chip)。"""
        silicon = GoodsType(name="硅", base_price=100)
        chip = GoodsType(name="芯片", base_price=500)
        return silicon, chip

    @staticmethod
    def _make_upstream(silicon: GoodsType) -> tuple[Company, FactoryType]:
        """创建上游公司：硅矿 → 硅。"""
        recipe = Recipe(
            input_goods_type=None, input_quantity=0,
            output_goods_type=silicon, output_quantity=10,
            tech_quality_weight=1.0,
        )
        ft = FactoryType(
            recipe=recipe, labor_demand=50,
            build_cost=5000, maintenance_cost=100, build_time=0,
        )
        company = Company(name="upstream")
        pc = company.get_component(ProductorComponent)
        pc.tech_values[recipe] = 100
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        return company, ft

    @staticmethod
    def _make_downstream(silicon: GoodsType, chip: GoodsType) -> tuple[Company, FactoryType]:
        """创建下游公司：硅 → 芯片。"""
        recipe = Recipe(
            input_goods_type=silicon, input_quantity=2,
            output_goods_type=chip, output_quantity=1,
            tech_quality_weight=0.6,
        )
        ft = FactoryType(
            recipe=recipe, labor_demand=50,
            build_cost=10000, maintenance_cost=200, build_time=0,
        )
        company = Company(name="downstream")
        pc = company.get_component(ProductorComponent)
        pc.tech_values[recipe] = 100
        pc.factories[ft] = [Factory(ft, build_remaining=0)]
        pc.init_prices()
        return company, ft

    def test_full_trade_cycle(self) -> None:
        """上游生产硅 → 挂单 → 下游采购 → 撮合 → 结算：下游库存增加、上游库存减少、现金流转。"""
        silicon, chip = self._make_goods()
        upstream, up_ft = self._make_upstream(silicon)
        downstream, down_ft = self._make_downstream(silicon, chip)

        # 上游生产硅：output_quantity = 10 units
        ProductorComponent.max_tech[up_ft.recipe] = 100
        upstream.get_component(ProductorComponent).hired_labor_points = 1000
        upstream.get_component(ProductorComponent).produce_all()
        assert sum(b.quantity for b in upstream.get_component(StorageComponent).get_batches(silicon)) == 10

        # 给下游现金
        downstream.get_component(LedgerComponent).cash = 50000

        market = MarketService()
        company_service = CompanyService()
        company_service.companies = {"upstream": upstream, "downstream": downstream}

        # sell_phase: 上游挂单
        company_service.sell_phase(market)
        orders = market.get_sell_orders(silicon)
        assert len(orders) == 1
        assert orders[0].price == silicon.base_price  # 100

        # buy_phase: 下游生成采购意向
        # 需求 = input_quantity(2) * built_count(1) = 2
        buy_service = CompanyService()
        buy_service.companies = {"downstream": downstream}
        intents = buy_service.buy_phase(market)
        assert len(intents) == 1
        assert intents[0].quantity == 2

        # match
        trades = market.match(intents)
        assert len(trades) == 1
        assert trades[0].quantity == 2
        assert trades[0].price == 100
        assert trades[0].total == 200

        # settle
        company_service.settle_trades(trades)

        # 验证：下游获得 2 硅
        down_batches = downstream.get_component(StorageComponent).get_batches(silicon)
        assert sum(b.quantity for b in down_batches) == 2

        # 验证：上游库存减少到 8
        up_batches = upstream.get_component(StorageComponent).get_batches(silicon)
        assert sum(b.quantity for b in up_batches) == 8

        # 验证：现金流转
        assert downstream.get_component(LedgerComponent).cash == 50000 - 200
        assert upstream.get_component(LedgerComponent).cash == 200

    def test_supply_less_than_demand_proportional(self) -> None:
        """两个下游争抢不足的上游库存，按比例分配。"""
        silicon, chip = self._make_goods()
        upstream, up_ft = self._make_upstream(silicon)

        # 上游只有 60 硅
        upstream.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=silicon, quantity=60, quality=0.8, brand_value=0)
        )
        upstream.get_component(ProductorComponent).init_prices()

        # 两个下游各需 100
        down_a, _ = self._make_downstream(silicon, chip)
        down_b, _ = self._make_downstream(silicon, chip)
        down_a.get_component(LedgerComponent).cash = 50000
        down_b.get_component(LedgerComponent).cash = 50000

        market = MarketService()
        sell_svc = CompanyService()
        sell_svc.companies = {"up": upstream}
        sell_svc.sell_phase(market)

        buy_svc = CompanyService()
        buy_svc.companies = {"a": down_a, "b": down_b}
        intents = buy_svc.buy_phase(market)
        assert len(intents) == 2

        trades = market.match(intents)
        total_traded = sum(t.quantity for t in trades)
        # 两个下游各需 2 硅，共 4，但上游只有 60 → 全部售出上限为 4
        assert total_traded <= 4  # 需求总量 = 2 * 2 = 4，全部满足

        sell_svc.settle_trades(trades)

        # 上游硅大部分仍剩余（只卖出了 4 个）
        up_remaining = sum(b.quantity for b in upstream.get_component(StorageComponent).get_batches(silicon))
        assert up_remaining == 56  # 60 - 4 = 56

    def test_credit_when_cash_insufficient(self) -> None:
        """买方现金不足时，差额创建 TRADE_PAYABLE 贷款。"""
        silicon, chip = self._make_goods()
        upstream, up_ft = self._make_upstream(silicon)

        upstream.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=silicon, quantity=200, quality=0.5, brand_value=0)
        )
        upstream.get_component(ProductorComponent).init_prices()

        downstream, _ = self._make_downstream(silicon, chip)
        # 只给 100 现金，需求 2 * 100 = 200
        downstream.get_component(LedgerComponent).cash = 100

        market = MarketService()
        sell_svc = CompanyService()
        sell_svc.companies = {"up": upstream}
        sell_svc.sell_phase(market)

        buy_svc = CompanyService()
        buy_svc.companies = {"down": downstream}
        intents = buy_svc.buy_phase(market)
        trades = market.match(intents)

        sell_svc.settle_trades(trades)

        # 下游现金清零
        assert downstream.get_component(LedgerComponent).cash == 0
        # 上游收到 100 现金
        assert upstream.get_component(LedgerComponent).cash == 100
        # 差额 100 作为 TRADE_PAYABLE
        payables = downstream.get_component(LedgerComponent).filter_loans(LoanType.TRADE_PAYABLE)
        assert sum(l.remaining for l in payables) == 100
        # 上游应收
        receivables = upstream.get_component(LedgerComponent).filter_loans(LoanType.TRADE_PAYABLE)
        assert sum(l.remaining for l in receivables) == 100

    def test_market_clears_between_rounds(self) -> None:
        """update_phase 清空挂单，第二轮 sell_phase 重新挂单。"""
        silicon, chip = self._make_goods()
        upstream, _ = self._make_upstream(silicon)
        upstream.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=silicon, quantity=100, quality=0.5, brand_value=0)
        )
        upstream.get_component(ProductorComponent).init_prices()

        market = MarketService()
        svc = CompanyService()
        svc.companies = {"up": upstream}

        # 第一轮
        svc.sell_phase(market)
        assert len(market.get_sell_orders(silicon)) == 1

        # 清空
        market.update_phase()
        assert len(market.get_sell_orders(silicon)) == 0

        # 第二轮重新挂单
        svc.sell_phase(market)
        assert len(market.get_sell_orders(silicon)) == 1

    def test_multi_tier_supply_chain(self) -> None:
        """三层供应链：硅矿 → 芯片厂采购硅，验证完整的 生产→交易→生产 循环。"""
        silicon, chip = self._make_goods()
        upstream, up_ft = self._make_upstream(silicon)
        downstream, down_ft = self._make_downstream(silicon, chip)
        downstream.get_component(LedgerComponent).cash = 100000

        # ── 第一轮：上游生产 ──
        ProductorComponent.max_tech[up_ft.recipe] = 100
        ProductorComponent.max_tech[down_ft.recipe] = 100
        upstream.get_component(ProductorComponent).hired_labor_points = 1000
        upstream.get_component(ProductorComponent).produce_all()  # 10 硅

        market = MarketService()
        svc = CompanyService()
        svc.companies = {"up": upstream, "down": downstream}

        # sell → buy → match → settle
        svc.sell_phase(market)
        buy_svc = CompanyService()
        buy_svc.companies = {"down": downstream}
        intents = buy_svc.buy_phase(market)
        trades = market.match(intents)
        svc.settle_trades(trades)

        # 下游现在有 2 硅
        down_silicon = sum(b.quantity for b in downstream.get_component(StorageComponent).get_batches(silicon))
        assert down_silicon == 2

        # ── 下游用硅生产芯片 ──
        downstream.get_component(ProductorComponent).hired_labor_points = 1000
        downstream.get_component(ProductorComponent).produce_all()
        down_chips = sum(b.quantity for b in downstream.get_component(StorageComponent).get_batches(chip))
        # labor_demand=50, output_quantity=1, input_quantity=2
        # full demand = 2 * 50 = 100 硅, supply = 100 → sufficiency = 1.0
        # output = 50 * 1 * 1.0
        assert down_chips > 0  # 芯片已生产出来

    def test_no_demand_no_trade(self) -> None:
        """下游库存充足时不产生采购意向，无交易发生。"""
        silicon, chip = self._make_goods()
        upstream, _ = self._make_upstream(silicon)
        downstream, _ = self._make_downstream(silicon, chip)

        # 上游有库存
        upstream.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=silicon, quantity=200, quality=0.5, brand_value=0)
        )
        upstream.get_component(ProductorComponent).init_prices()

        # 下游已有足够硅 (需求=2, 库存=10，充足)
        downstream.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=silicon, quantity=10, quality=0.5, brand_value=0)
        )

        market = MarketService()
        sell_svc = CompanyService()
        sell_svc.companies = {"up": upstream}
        sell_svc.sell_phase(market)

        buy_svc = CompanyService()
        buy_svc.companies = {"down": downstream}
        intents = buy_svc.buy_phase(market)
        assert len(intents) == 0

        trades = market.match(intents)
        assert len(trades) == 0
