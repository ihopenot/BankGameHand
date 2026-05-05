"""经济反馈机制集成测试：验证完整游戏循环中的资金流动反馈。"""

from pathlib import Path

import pytest

from core.config import ConfigManager
from entity.goods import GoodsType, load_goods_types
from entity.factory import load_recipes, load_factory_types, FactoryType


@pytest.fixture(autouse=True)
def _load_full_config():
    """加载完整配置。"""
    ConfigManager._instance = None
    ConfigManager().load(str(Path(__file__).parent.parent / "config"))
    GoodsType.types.clear()
    load_goods_types()
    load_recipes()
    load_factory_types()
    yield
    ConfigManager._instance = None
    FactoryType.factory_types.clear()


class TestEconomicFeedbackIntegration:
    """验证反馈机制在多回合中正常运作。"""

    def test_wage_evolves_over_rounds(self) -> None:
        """企业工资不再是固定值，应在多轮后变化。"""
        from system.company_service import CompanyService
        from system.decision_service import DecisionService

        company_service = CompanyService()
        ft = list(FactoryType.factory_types.values())[0]
        company = company_service.create_company(
            name="test_co",
            factory_type=ft,
            initial_cash=1000000,
            decision_component="classic",
            initial_wage=400,
        )

        decision_service = DecisionService()
        decision_service.set_market_data([], [], 0.0)

        initial_wage = company.wage
        # 模拟多轮决策
        for _ in range(5):
            decision_service.plan_phase(list(company_service.companies.values()))

        # 工资应该有变化（不再固定）
        assert company.wage != initial_wage

    def test_demand_multiplier_responds_to_spending(self) -> None:
        """居民 demand_multiplier 在有开销记录后应变化。"""
        from entity.folk import load_folks
        from component.ledger_component import LedgerComponent
        from component.decision.folk.classic import ClassicFolkDecisionComponent

        folks = load_folks()
        folk = folks[0]

        # 设置现金和开销
        ledger = folk.get_component(LedgerComponent)
        ledger.cash = 500000
        folk.last_spending = 10000  # R = 50, T = 3 → 非常充裕

        dc = folk.get_component(ClassicFolkDecisionComponent)

        # 从配置获取参数
        config = ConfigManager().section("folk")
        fb = config.folks[0].demand_feedback
        dc.update_demand_multiplier(
            savings_target_ratio=fb.savings_target_ratio,
            max_adjustment=fb.max_adjustment,
            sensitivity=fb.sensitivity,
            min_multiplier=fb.min_multiplier,
            max_multiplier=fb.max_multiplier,
        )

        # 因为 R >> T，demand_multiplier 应增加
        assert folk.demand_multiplier > 1.0

    def test_feedback_loop_stabilizes(self) -> None:
        """反馈循环：当 R = T 时，demand_multiplier 不再变化。"""
        from entity.folk import load_folks
        from component.ledger_component import LedgerComponent
        from component.decision.folk.classic import ClassicFolkDecisionComponent

        folks = load_folks()
        folk = folks[1]  # 中等收入，T=5.0

        ledger = folk.get_component(LedgerComponent)
        ledger.cash = 50000
        folk.last_spending = 10000  # R = 5.0 = T → 平衡

        dc = folk.get_component(ClassicFolkDecisionComponent)
        config = ConfigManager().section("folk")
        fb = config.folks[1].demand_feedback

        original = folk.demand_multiplier
        dc.update_demand_multiplier(
            savings_target_ratio=fb.savings_target_ratio,
            max_adjustment=fb.max_adjustment,
            sensitivity=fb.sensitivity,
            min_multiplier=fb.min_multiplier,
            max_multiplier=fb.max_multiplier,
        )

        # R == T → deviation == 0 → adjustment == 0 → no change
        assert folk.demand_multiplier == pytest.approx(original, abs=1e-10)

    def test_low_cash_decreases_demand(self) -> None:
        """居民现金不足时 demand_multiplier 下降。"""
        from entity.folk import load_folks
        from component.ledger_component import LedgerComponent
        from component.decision.folk.classic import ClassicFolkDecisionComponent

        folks = load_folks()
        folk = folks[2]  # 高收入，T=8.0

        ledger = folk.get_component(LedgerComponent)
        ledger.cash = 10000
        folk.last_spending = 10000  # R = 1.0, T = 8.0 → 严重不足

        dc = folk.get_component(ClassicFolkDecisionComponent)
        config = ConfigManager().section("folk")
        fb = config.folks[2].demand_feedback
        dc.update_demand_multiplier(
            savings_target_ratio=fb.savings_target_ratio,
            max_adjustment=fb.max_adjustment,
            sensitivity=fb.sensitivity,
            min_multiplier=fb.min_multiplier,
            max_multiplier=fb.max_multiplier,
        )

        # R << T → demand_multiplier 应下降
        assert folk.demand_multiplier < 1.0
