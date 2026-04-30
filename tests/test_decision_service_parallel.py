"""DecisionService 并行化与 prepare_next_round 测试。"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from component.decision.company.ai import AICompanyDecisionComponent
from core.config import ConfigManager
from core.entity import Entity
from entity.company.company import Company
from system.decision_service import DecisionService


# ── Fixtures ──


@pytest.fixture(autouse=True)
def _reset_config():
    ConfigManager._instance = None
    ConfigManager().load()
    yield
    ConfigManager._instance = None


@pytest.fixture(autouse=True)
def _clear_ai_class_state():
    """每个测试前后清理 AICompanyDecisionComponent 的类级别状态。"""
    AICompanyDecisionComponent._sessions.clear()
    AICompanyDecisionComponent._sdk = None
    AICompanyDecisionComponent._sdk_initialized = False
    AICompanyDecisionComponent._loop = None
    AICompanyDecisionComponent._loop_thread = None
    yield
    AICompanyDecisionComponent._sessions.clear()
    AICompanyDecisionComponent._sdk = None
    AICompanyDecisionComponent._sdk_initialized = False
    if AICompanyDecisionComponent._loop and not AICompanyDecisionComponent._loop.is_closed():
        AICompanyDecisionComponent._loop.call_soon_threadsafe(AICompanyDecisionComponent._loop.stop)
    AICompanyDecisionComponent._loop = None
    AICompanyDecisionComponent._loop_thread = None


def _make_ai_company(name: str) -> Company:
    """创建一个使用 AI 决策组件的公司。"""
    company = Company(name=name)
    company.init_component(AICompanyDecisionComponent)
    from component.ledger_component import LedgerComponent
    company.get_component(LedgerComponent).cash = 100_000
    company.initial_wage = 10
    company.wage = 10
    return company


def _mock_ai_result_json() -> str:
    return json.dumps({
        "pricing": {"食品": 120},
        "investment_plan": {"expansion": 0, "brand": 500, "tech": 300},
        "loan_needs": {"amount": 0, "max_rate": 10},
    })


# ── 2.1: prepare_next_round 与并行 plan_phase ──


class TestPrepareNextRound:
    """prepare_next_round 为所有 AI 公司 prepare session。"""

    def test_prepare_next_round_calls_prepare_next_sessions_for_ai_companies(self) -> None:
        """prepare_next_round 应为所有 AI 公司调用 prepare_next_sessions。"""
        companies = [_make_ai_company("company_A"), _make_ai_company("company_B")]

        with patch.object(AICompanyDecisionComponent, "prepare_next_sessions") as mock_prepare:
            svc = DecisionService()
            svc.prepare_next_round(companies)

            mock_prepare.assert_called_once()
            called_names = mock_prepare.call_args[0][0]
            assert set(called_names) == {"company_A", "company_B"}

    def test_prepare_next_round_skips_non_ai_companies(self) -> None:
        """prepare_next_round 应跳过非 AI 决策组件的公司。"""
        from component.decision.company.classic import ClassicCompanyDecisionComponent
        ai_company = _make_ai_company("company_A")
        classic_company = Company(name="company_B")
        classic_company.init_component(ClassicCompanyDecisionComponent)

        with patch.object(AICompanyDecisionComponent, "prepare_next_sessions") as mock_prepare:
            svc = DecisionService()
            svc.prepare_next_round([ai_company, classic_company])

            mock_prepare.assert_called_once()
            called_names = mock_prepare.call_args[0][0]
            assert called_names == ["company_A"]


class TestParallelPlanPhase:
    """plan_phase 并行调用所有 AI 决策，完成后自动 prepare 下一轮。"""

    def test_plan_phase_calls_prepare_next_round_after_decisions(self) -> None:
        """plan_phase 完成后应调用 prepare_next_round。"""
        companies = [_make_ai_company("company_A")]

        with patch.object(AICompanyDecisionComponent, "query_all_parallel") as mock_query, \
             patch.object(DecisionService, "prepare_next_round") as mock_prepare_next:
            mock_query.return_value = [{"pricing": {"食品": 120}, "investment_plan": {"expansion": 0, "brand": 500, "tech": 300}, "loan_needs": {"amount": 0, "max_rate": 10}}]

            svc = DecisionService()
            svc.set_market_data(sell_orders=[], trades=[], economy_index=1.0)
            svc.plan_phase(companies)

            mock_prepare_next.assert_called_once_with(companies)

    def test_plan_phase_queries_all_ai_companies_in_parallel(self) -> None:
        """plan_phase 应将所有 AI 公司的 query 一次性并行提交。"""
        companies = [_make_ai_company("company_A"), _make_ai_company("company_B")]

        with patch.object(AICompanyDecisionComponent, "query_all_parallel") as mock_query, \
             patch.object(DecisionService, "prepare_next_round"):
            mock_query.return_value = [
                {"pricing": {"食品": 120}, "investment_plan": {"expansion": 0, "brand": 500, "tech": 300}, "loan_needs": {"amount": 0, "max_rate": 10}},
                {"pricing": {"食品": 100}, "investment_plan": {"expansion": 0, "brand": 0, "tech": 0}, "loan_needs": {"amount": 0, "max_rate": 0}},
            ]

            svc = DecisionService()
            svc.set_market_data(sell_orders=[], trades=[], economy_index=1.0)
            svc.plan_phase(companies)

            # query_all_parallel 应被调用一次，参数包含两个公司的 query
            mock_query.assert_called_once()
            queries = mock_query.call_args[0][0]
            assert len(queries) == 2
            company_names = {q[0] for q in queries}
            assert company_names == {"company_A", "company_B"}
