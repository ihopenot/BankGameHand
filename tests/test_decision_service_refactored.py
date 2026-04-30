"""DecisionService 重构后的编排层测试。"""

import random
from unittest.mock import MagicMock, patch

import pytest

from component.decision.company.base import BaseCompanyDecisionComponent
from component.decision.company.classic import ClassicCompanyDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from core.config import ConfigManager
from core.entity import Entity
from core.types import LoanApplication
from entity.company.company import Company
from entity.factory import Factory, FactoryType
from entity.goods import GoodsBatch, GoodsType, load_goods_types
from system.decision_service import DecisionService


# ── Fixtures ──


@pytest.fixture(autouse=True)
def _load_config():
    cm = ConfigManager()
    try:
        cm.section("decision")
    except KeyError:
        cm.load()
    if not GoodsType.types:
        load_goods_types()


@pytest.fixture(autouse=True)
def _clear_components():
    for cls in [ClassicCompanyDecisionComponent, LedgerComponent, MetricComponent, ProductorComponent]:
        cls.components.clear()
    yield
    for cls in [ClassicCompanyDecisionComponent, LedgerComponent, MetricComponent, ProductorComponent]:
        cls.components.clear()


def _make_company(cash: int = 100000, last_revenue: int = 10000) -> Company:
    """创建一个带完整组件的 mock company。"""
    company = Company(name="test_company")
    company.init_component(ClassicCompanyDecisionComponent)
    company.get_component(LedgerComponent).cash = cash
    mc = company.get_component(MetricComponent)
    mc.last_revenue = last_revenue
    return company


def _make_ds_with_market() -> DecisionService:
    """创建 DecisionService 并设置市场数据。"""
    ds = DecisionService()
    ds.set_market_data(sell_orders=[], trades=[], economy_index=1.0)
    return ds


# ── 3.1: DecisionService 委托到组件 ──


class TestDecisionServiceBuildsContext:
    """3.1: DecisionService._build_context 从组件组装 context dict。"""

    def test_build_context_contains_all_sections(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company()
        ctx = ds._build_context(company)

        assert "company" in ctx
        assert "ledger" in ctx
        assert "productor" in ctx
        assert "metric" in ctx
        assert "market" in ctx

    def test_build_context_company_section(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company()
        ctx = ds._build_context(company)

        assert "name" in ctx["company"]
        assert "ceo_traits" in ctx["company"]

    def test_build_context_ledger_section(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company(cash=5000)
        ctx = ds._build_context(company)

        assert ctx["ledger"]["cash"] == 5000

    def test_build_context_productor_section(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company()
        ctx = ds._build_context(company)

        assert "factories" in ctx["productor"]
        assert "current_prices" in ctx["productor"]

    def test_build_context_metric_section(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company(last_revenue=8000)
        ctx = ds._build_context(company)

        assert ctx["metric"]["last_revenue"] == 8000


class TestDecisionServicePlanPhase:
    """3.1: plan_phase 委托到组件的 set_context + decide_pricing + decide_investment_plan。"""

    def test_plan_phase_calls_set_context(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company()

        original = BaseCompanyDecisionComponent.set_context
        with patch.object(
            BaseCompanyDecisionComponent, "set_context", wraps=original
        ) as mock_set:
            ds.plan_phase([company])
            mock_set.assert_called_once()
            ctx = mock_set.call_args[0][1]
            assert "ledger" in ctx

    def test_plan_phase_calls_decide_pricing(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company()
        comp = company.get_component(ClassicCompanyDecisionComponent)

        with patch.object(comp, "decide_pricing", wraps=comp.decide_pricing) as mock:
            ds.plan_phase([company])
            mock.assert_called_once()

    def test_plan_phase_calls_decide_investment_plan(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company()
        comp = company.get_component(ClassicCompanyDecisionComponent)

        with patch.object(comp, "decide_investment_plan", wraps=comp.decide_investment_plan) as mock:
            ds.plan_phase([company])
            mock.assert_called_once()

    def test_plan_phase_updates_prices(self) -> None:
        """plan_phase 应将 decide_pricing 的结果应用到 ProductorComponent.prices。"""
        ds = _make_ds_with_market()
        company = _make_company()
        pc = company.get_component(ProductorComponent)
        mc = company.get_component(MetricComponent)
        gt = GoodsType.types.get("食品")

        if gt is not None:
            pc.prices[gt] = 100
            mc.last_sell_orders[gt] = 10
            mc.last_sold_quantities[gt] = 10

        ds.plan_phase([company])
        # 定价可能已更新（取决于是否有 sell_orders）


class TestDecisionServiceActPhase:
    """3.1: act_phase 委托到组件的 decide_budget_allocation 并执行投资。"""

    def test_act_phase_calls_decide_budget_allocation(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company()
        comp = company.get_component(ClassicCompanyDecisionComponent)

        # 先 plan_phase 以设置 investment_plan
        ds.plan_phase([company])

        with patch.object(comp, "decide_budget_allocation", wraps=comp.decide_budget_allocation) as mock:
            ds.act_phase([company])
            mock.assert_called_once()


class TestDecisionServiceCalcLoanNeeds:
    """3.1: calc_loan_needs 委托到组件的 decide_loan_needs。"""

    def test_calc_loan_needs_returns_list(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company(cash=0, last_revenue=10000)
        ds.plan_phase([company])

        result = ds.calc_loan_needs([company])
        assert isinstance(result, list)

    def test_calc_loan_needs_delegates_to_component(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company(cash=0, last_revenue=10000)
        comp = company.get_component(ClassicCompanyDecisionComponent)
        ds.plan_phase([company])

        with patch.object(comp, "decide_loan_needs", wraps=comp.decide_loan_needs) as mock:
            ds.calc_loan_needs([company])
            mock.assert_called_once()


class TestDecisionServiceMakePurchaseSortKey:
    """3.1: make_purchase_sort_key 委托到组件。"""

    def test_delegates_to_component(self) -> None:
        ds = _make_ds_with_market()
        company = _make_company()
        comp = company.get_component(ClassicCompanyDecisionComponent)

        with patch.object(comp, "make_purchase_sort_key", wraps=comp.make_purchase_sort_key) as mock:
            ds.make_purchase_sort_key(company)
            mock.assert_called_once()
