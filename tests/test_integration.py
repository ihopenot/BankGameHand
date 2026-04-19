"""全流程集成测试：创建 Game，运行 game_loop，校验结尾状态。"""
from pathlib import Path
from unittest.mock import MagicMock

from component.ledger_component import LedgerComponent
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
        GoodsType.types.clear()
        Recipe.recipes.clear()
        FactoryType.factory_types.clear()

    def teardown_method(self) -> None:
        ConfigManager._instance = None
        ProductorComponent.components.clear()
        ProductorComponent.max_tech.clear()
        LedgerComponent.components.clear()
        StorageComponent.components.clear()
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


class TestProductorServiceIntegration:
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
        ft = FactoryType(recipe=recipe, base_production=5,
                         build_cost=10000, maintenance_cost=500, build_time=0)

        e1 = Entity()
        p1 = e1.init_component(ProductorComponent)
        p1.tech_values[recipe] = 80
        p1.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        e2 = Entity()
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
        ft = FactoryType(recipe=recipe, base_production=5,
                         build_cost=10000, maintenance_cost=500, build_time=0)

        entities: list[Entity] = []
        for tech in (100, 150):
            e = Entity()
            p = e.init_component(ProductorComponent)
            p.tech_values[recipe] = tech
            p.factories[ft].append(Factory(factory_type=ft, build_remaining=0))
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
            assert batches[0].quantity == 50  # 5 * 10

    def test_destroy_entity_removes_from_service_scope(self) -> None:
        """Entity.destroy() 后，ProductorService 不再遍历该组件。"""
        gt = GoodsType(name="硅", base_price=1000)
        recipe = Recipe(input_goods_type=None, input_quantity=0,
                        output_goods_type=gt, output_quantity=10, tech_quality_weight=1.0)
        ft = FactoryType(recipe=recipe, base_production=5,
                         build_cost=10000, maintenance_cost=500, build_time=0)

        e1 = Entity()
        p1 = e1.init_component(ProductorComponent)
        p1.tech_values[recipe] = 100
        p1.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        e2 = Entity()
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
            recipe=recipe, base_production=20,
            build_cost=5000, maintenance_cost=100, build_time=0,
        )
        company = Company()
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
            recipe=recipe, base_production=50,
            build_cost=10000, maintenance_cost=200, build_time=0,
        )
        company = Company()
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

        # 上游生产硅：20 * 10 = 200 units
        ProductorComponent.max_tech[up_ft.recipe] = 100
        upstream.get_component(ProductorComponent).produce_all()
        assert sum(b.quantity for b in upstream.get_component(StorageComponent).get_batches(silicon)) == 200

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
        # 需求 = input_quantity(2) * base_production(50) = 100
        buy_service = CompanyService()
        buy_service.companies = {"downstream": downstream}
        intents = buy_service.buy_phase(market)
        assert len(intents) == 1
        assert intents[0].quantity == 100

        # match
        trades = market.match(intents)
        assert len(trades) == 1
        assert trades[0].quantity == 100
        assert trades[0].price == 100
        assert trades[0].total == 10000

        # settle
        company_service.settle_trades(trades)

        # 验证：下游获得 100 硅
        down_batches = downstream.get_component(StorageComponent).get_batches(silicon)
        assert sum(b.quantity for b in down_batches) == 100

        # 验证：上游库存减少到 100
        up_batches = upstream.get_component(StorageComponent).get_batches(silicon)
        assert sum(b.quantity for b in up_batches) == 100

        # 验证：现金流转
        assert downstream.get_component(LedgerComponent).cash == 50000 - 10000
        assert upstream.get_component(LedgerComponent).cash == 10000

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
        assert total_traded == 60  # 全部售出

        sell_svc.settle_trades(trades)

        # 上游硅全部卖出
        up_remaining = sum(b.quantity for b in upstream.get_component(StorageComponent).get_batches(silicon))
        assert up_remaining == 0

    def test_credit_when_cash_insufficient(self) -> None:
        """买方现金不足时，差额创建 TRADE_PAYABLE 贷款。"""
        silicon, chip = self._make_goods()
        upstream, up_ft = self._make_upstream(silicon)

        upstream.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=silicon, quantity=200, quality=0.5, brand_value=0)
        )
        upstream.get_component(ProductorComponent).init_prices()

        downstream, _ = self._make_downstream(silicon, chip)
        # 只给 3000 现金，需求 100 * 100 = 10000
        downstream.get_component(LedgerComponent).cash = 3000

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
        # 上游收到 3000 现金
        assert upstream.get_component(LedgerComponent).cash == 3000
        # 差额 7000 作为 TRADE_PAYABLE
        payables = downstream.get_component(LedgerComponent).filter_loans(LoanType.TRADE_PAYABLE)
        assert sum(l.remaining for l in payables) == 7000
        # 上游应收
        receivables = upstream.get_component(LedgerComponent).filter_loans(LoanType.TRADE_PAYABLE)
        assert sum(l.remaining for l in receivables) == 7000

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
        upstream.get_component(ProductorComponent).produce_all()  # 200 硅

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

        # 下游现在有 100 硅
        down_silicon = sum(b.quantity for b in downstream.get_component(StorageComponent).get_batches(silicon))
        assert down_silicon == 100

        # ── 下游用硅生产芯片 ──
        downstream.get_component(ProductorComponent).produce_all()
        down_chips = sum(b.quantity for b in downstream.get_component(StorageComponent).get_batches(chip))
        # base_production=50, output_quantity=1, input_quantity=2
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

        # 下游已有足够硅 (需求=100, 库存=150)
        downstream.get_component(StorageComponent).add_batch(
            GoodsBatch(goods_type=silicon, quantity=150, quality=0.5, brand_value=0)
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
