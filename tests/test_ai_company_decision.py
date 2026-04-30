"""AICompanyDecisionComponent AI 决策组件测试。"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from component.decision.company.ai import AICompanyDecisionComponent
from component.decision.company.base import BaseCompanyDecisionComponent
from component.decision.company.classic import ClassicCompanyDecisionComponent
from core.config import ConfigManager
from core.entity import Entity


# ── Fixtures ──


@pytest.fixture(autouse=True)
def _clear_components():
    AICompanyDecisionComponent.components.clear()
    yield
    AICompanyDecisionComponent.components.clear()


@pytest.fixture(autouse=True)
def _load_config():
    cm = ConfigManager()
    try:
        cm.section("decision")
    except KeyError:
        cm.load()


@pytest.fixture()
def comp() -> AICompanyDecisionComponent:
    entity = Entity()
    return entity.init_component(AICompanyDecisionComponent)


def _make_context(cash: int = 100000, last_revenue: int = 10000) -> dict:
    return {
        "company": {
            "name": "TestAI",
            "ceo_traits": {
                "business_acumen": 0.5,
                "risk_appetite": 0.5,
                "profit_focus": 0.5,
                "marketing_awareness": 0.5,
                "tech_focus": 0.5,
                "price_sensitivity": 0.5,
            },
        },
        "ledger": {"cash": cash, "revenue": 5000, "expense": 1000, "receivables": 0, "payables": 0},
        "productor": {"factories": {}, "tech_levels": {}, "brand_values": {}, "current_prices": {}},
        "metric": {"my_sell_orders": {}, "my_sold_quantities": {}, "last_revenue": last_revenue, "my_avg_buy_prices": {}},
        "market": {"economy_index": 1.0, "sell_orders": [], "trades": []},
    }


def _mock_ai_result(pricing=None, investment_plan=None, loan_needs=None):
    """构造一个 AI 返回的 JSON 字符串。"""
    data = {
        "pricing": pricing or {"食品": 120},
        "investment_plan": investment_plan or {"expansion": 0, "brand": 500, "tech": 300},
        "loan_needs": loan_needs or {"amount": 0, "max_rate": 10},
    }
    return json.dumps(data)


# ── 5.1: AI 决策核心逻辑 ──


class TestAIInheritsClassic:
    """AICompanyDecisionComponent 应继承 ClassicCompanyDecisionComponent。"""

    def test_inherits_classic(self) -> None:
        assert issubclass(AICompanyDecisionComponent, ClassicCompanyDecisionComponent)

    def test_inherits_base(self) -> None:
        assert issubclass(AICompanyDecisionComponent, BaseCompanyDecisionComponent)


class TestAISetContext:
    """5.1: set_context 调用 MCPAgentSDK 并缓存结果。"""

    def test_set_context_calls_sdk(self, comp) -> None:
        """set_context 应调用 MCPAgentSDK.run_agent。"""
        ctx = _make_context()

        with patch("component.decision.company.ai.MCPAgentSDK") as mock_sdk_cls:
            mock_sdk = MagicMock()
            mock_sdk_cls.return_value = mock_sdk
            mock_sdk.init = AsyncMock()

            # Mock async run_agent to return an AgentResult
            async def mock_run(config):
                from mcp_agent_sdk import AgentResult
                yield AgentResult(status="completed", message=_mock_ai_result())

            mock_sdk.run_agent = mock_run

            comp.set_context(ctx)

    def test_set_context_caches_ai_decisions(self, comp) -> None:
        """set_context 应将 AI 结果缓存到 _ai_decisions。"""
        ctx = _make_context()

        with patch("component.decision.company.ai.MCPAgentSDK") as mock_sdk_cls:
            mock_sdk = MagicMock()
            mock_sdk_cls.return_value = mock_sdk
            mock_sdk.init = AsyncMock()

            async def mock_run(config):
                from mcp_agent_sdk import AgentResult
                yield AgentResult(status="completed", message=_mock_ai_result())

            mock_sdk.run_agent = mock_run

            comp.set_context(ctx)
            assert hasattr(comp, "_ai_decisions")
            assert "pricing" in comp._ai_decisions


class TestAIDecisions:
    """5.1: AI 决策方法读取缓存。"""

    def test_decide_pricing_reads_cache(self, comp) -> None:
        """decide_pricing 应返回缓存的 AI 定价。"""
        ctx = _make_context()
        comp._ai_decisions = {"pricing": {"食品": 120}, "investment_plan": {"expansion": 0, "brand": 500, "tech": 300}, "loan_needs": {"amount": 0, "max_rate": 10}}
        comp._context = ctx

        result = comp.decide_pricing()
        assert result == {"食品": 120}

    def test_decide_investment_plan_reads_cache(self, comp) -> None:
        """decide_investment_plan 应返回缓存的 AI 投资计划。"""
        ctx = _make_context()
        comp._ai_decisions = {"pricing": {}, "investment_plan": {"expansion": 1000, "brand": 500, "tech": 300}, "loan_needs": {"amount": 0, "max_rate": 10}}
        comp._context = ctx

        result = comp.decide_investment_plan()
        assert result == {"expansion": 1000, "brand": 500, "tech": 300}

    def test_decide_loan_needs_reads_cache(self, comp) -> None:
        """decide_loan_needs 应返回缓存的 AI 贷款需求。"""
        ctx = _make_context()
        comp._ai_decisions = {"pricing": {}, "investment_plan": {"expansion": 0, "brand": 0, "tech": 0}, "loan_needs": {"amount": 5000, "max_rate": 8}}
        comp._context = ctx

        result = comp.decide_loan_needs()
        assert result == (5000, 8)


# ── 5.2: JSON 验证 ──


class TestAIValidation:
    """5.2: validate_fn 验证 AI 返回的 JSON。"""

    def test_valid_json_passes(self, comp) -> None:
        """合法 JSON 应通过验证。"""
        result = comp._validate_fn(_mock_ai_result())
        is_valid, msg = result
        assert is_valid is True

    def test_missing_pricing_fails(self, comp) -> None:
        """缺少 pricing 应验证失败。"""
        data = json.dumps({"investment_plan": {"expansion": 0, "brand": 0, "tech": 0}, "loan_needs": {"amount": 0, "max_rate": 0}})
        is_valid, msg = comp._validate_fn(data)
        assert is_valid is False
        assert "pricing" in msg.lower()

    def test_missing_investment_plan_fails(self, comp) -> None:
        """缺少 investment_plan 应验证失败。"""
        data = json.dumps({"pricing": {"食品": 100}, "loan_needs": {"amount": 0, "max_rate": 0}})
        is_valid, msg = comp._validate_fn(data)
        assert is_valid is False

    def test_missing_loan_needs_fails(self, comp) -> None:
        """缺少 loan_needs 应验证失败。"""
        data = json.dumps({"pricing": {"食品": 100}, "investment_plan": {"expansion": 0, "brand": 0, "tech": 0}})
        is_valid, msg = comp._validate_fn(data)
        assert is_valid is False

    def test_invalid_json_fails(self, comp) -> None:
        """非法 JSON 应验证失败。"""
        is_valid, msg = comp._validate_fn("not valid json{{{")
        assert is_valid is False

    def test_negative_pricing_fails(self, comp) -> None:
        """定价为负应验证失败。"""
        data = json.dumps({"pricing": {"食品": -10}, "investment_plan": {"expansion": 0, "brand": 0, "tech": 0}, "loan_needs": {"amount": 0, "max_rate": 0}})
        is_valid, msg = comp._validate_fn(data)
        assert is_valid is False

    def test_negative_investment_fails(self, comp) -> None:
        """投资为负应验证失败。"""
        data = json.dumps({"pricing": {"食品": 100}, "investment_plan": {"expansion": -1, "brand": 0, "tech": 0}, "loan_needs": {"amount": 0, "max_rate": 0}})
        is_valid, msg = comp._validate_fn(data)
        assert is_valid is False


class TestAIPromptTemplate:
    """5.2: prompt 模板包含完整 context。"""

    def test_prompt_contains_company_name(self, comp) -> None:
        ctx = _make_context()
        prompt = comp._build_prompt(ctx)
        assert "TestAI" in prompt

    def test_prompt_contains_context_json(self, comp) -> None:
        ctx = _make_context()
        prompt = comp._build_prompt(ctx)
        assert "ceo_traits" in prompt
        assert "cash" in prompt

    def test_prompt_asks_for_three_decisions(self, comp) -> None:
        ctx = _make_context()
        prompt = comp._build_prompt(ctx)
        assert "pricing" in prompt.lower()
        assert "investment_plan" in prompt.lower()
        assert "loan_needs" in prompt.lower()
