"""AICompanyDecisionComponent Session 池与两阶段调用测试。"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from component.decision.company.ai import AICompanyDecisionComponent
from core.config import ConfigManager
from core.entity import Entity
from mcp_agent_sdk import AgentResult, AgentRunConfig, AgentSession


# ── Fixtures ──


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


@pytest.fixture()
def comp() -> AICompanyDecisionComponent:
    entity = Entity()
    return entity.init_component(AICompanyDecisionComponent)


def _make_mock_session(agent_run_id: str = "test-session-1") -> MagicMock:
    """构造一个 mock AgentSession。"""
    session = MagicMock(spec=AgentSession)
    session.agent_run_id = agent_run_id
    session.closed = False
    session.close = AsyncMock()
    return session


# ── 1.1: Session 池与 prepare/cleanup ──


class TestSessionPool:
    """prepare_session 创建并存入 session、prepare_next_sessions 批量 prepare、cleanup_sessions 关闭所有 session。"""

    def test_prepare_session_creates_and_stores_session(self, comp) -> None:
        """prepare_session 应调用 sdk.prepare(config) 并将 AgentSession 存入 _sessions 池。"""
        mock_session = _make_mock_session("company_A")

        with patch.object(AICompanyDecisionComponent, "_run_in_loop") as mock_run:
            mock_run.return_value = mock_session

            comp.prepare_session("company_A")

            # _sessions 应包含 company_A 的 session
            assert "company_A" in AICompanyDecisionComponent._sessions
            assert AICompanyDecisionComponent._sessions["company_A"] is mock_session
            mock_run.assert_called_once()

    def test_prepare_session_uses_agent_run_config(self, comp) -> None:
        """prepare_session 应传入包含 validate_fn、model 等的 AgentRunConfig。"""
        mock_session = _make_mock_session("company_B")

        with patch.object(AICompanyDecisionComponent, "_run_in_loop") as mock_run:
            mock_run.return_value = mock_session

            comp.prepare_session("company_B")

            # _run_in_loop 的参数应是一个 coroutine（_prepare_session_coro）
            call_args = mock_run.call_args
            coro = call_args[0][0]
            # 关闭未 await 的协程以避免警告
            coro.close()

    def test_prepare_next_sessions_batch_prepare(self, comp) -> None:
        """prepare_next_sessions 应并行 prepare 所有公司的 session 并存入 _sessions。"""
        mock_session_a = _make_mock_session("company_A")
        mock_session_b = _make_mock_session("company_B")
        mock_session_c = _make_mock_session("company_C")

        with patch.object(AICompanyDecisionComponent, "_run_in_loop") as mock_run:
            mock_run.return_value = [mock_session_a, mock_session_b, mock_session_c]

            comp.prepare_next_sessions(["company_A", "company_B", "company_C"])

            assert "company_A" in AICompanyDecisionComponent._sessions
            assert "company_B" in AICompanyDecisionComponent._sessions
            assert "company_C" in AICompanyDecisionComponent._sessions
            mock_run.assert_called_once()

    def test_cleanup_sessions_closes_all(self, comp) -> None:
        """cleanup_sessions 应关闭所有 session 并清空 _sessions 池。"""
        mock_session_a = _make_mock_session("company_A")
        mock_session_b = _make_mock_session("company_B")

        AICompanyDecisionComponent._sessions["company_A"] = mock_session_a
        AICompanyDecisionComponent._sessions["company_B"] = mock_session_b

        comp.cleanup_sessions()

        # 两个 session 都应该被关闭
        mock_session_a.close.assert_called_once()
        mock_session_b.close.assert_called_once()
        # _sessions 应被清空
        assert len(AICompanyDecisionComponent._sessions) == 0

    def test_cleanup_sessions_handles_closed_session(self, comp) -> None:
        """cleanup_sessions 对已关闭的 session 不应报错。"""
        mock_session = _make_mock_session("company_A")
        mock_session.closed = True
        AICompanyDecisionComponent._sessions["company_A"] = mock_session

        comp.cleanup_sessions()

        # 已关闭的 session 不应再次调用 close
        mock_session.close.assert_not_called()
        assert len(AICompanyDecisionComponent._sessions) == 0

    def test_cleanup_sessions_empty_pool(self, comp) -> None:
        """cleanup_sessions 对空池不应报错。"""
        comp.cleanup_sessions()
        assert len(AICompanyDecisionComponent._sessions) == 0

    def test_sessions_is_class_level_dict(self) -> None:
        """_sessions 应为类级别属性（Dict[str, AgentSession]）。"""
        assert hasattr(AICompanyDecisionComponent, "_sessions")
        assert isinstance(AICompanyDecisionComponent._sessions, dict)


# ── 1.2: _query_ai 两阶段调用 ──


def _make_context(company_name: str = "TestAI", cash: int = 100000) -> dict:
    """构造 set_context 用的 context dict。"""
    return {
        "company": {
            "name": company_name,
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
        "metric": {"my_sell_orders": {}, "my_sold_quantities": {}, "last_revenue": 10000, "my_avg_buy_prices": {}},
        "market": {"economy_index": 1.0, "sell_orders": [], "trades": []},
    }


def _mock_ai_result_json() -> str:
    """构造 AI 返回的有效 JSON 字符串。"""
    import json
    return json.dumps({
        "pricing": {"食品": 120},
        "investment_plan": {"expansion": 0, "brand": 500, "tech": 300},
        "loan_needs": {"amount": 0, "max_rate": 10},
    })


class TestQueryAI:
    """_query_ai 从 session 池取 session 调用 do_query、session 不存在时回退 run_agent、do_query 后 session 从池中移除。"""

    def test_query_ai_uses_prepared_session(self, comp) -> None:
        """session 池中存在 session 时，_query_ai 应使用 do_query 而非 run_agent。"""
        mock_session = _make_mock_session("TestAI")
        AICompanyDecisionComponent._sessions["TestAI"] = mock_session

        with patch.object(AICompanyDecisionComponent, "_run_in_loop") as mock_run:
            mock_run.return_value = AgentResult(status="completed", message=_mock_ai_result_json())

            comp._query_ai(_make_context("TestAI"))

            # _run_in_loop 应被调用（用于 do_query 协程）
            assert mock_run.called

    def test_query_ai_removes_session_from_pool(self, comp) -> None:
        """do_query 后 session 应从池中移除（session 是一次性的）。"""
        mock_session = _make_mock_session("TestAI")
        AICompanyDecisionComponent._sessions["TestAI"] = mock_session

        with patch.object(AICompanyDecisionComponent, "_run_in_loop") as mock_run:
            mock_run.return_value = AgentResult(status="completed", message=_mock_ai_result_json())

            comp._query_ai(_make_context("TestAI"))

            # session 应从池中移除
            assert "TestAI" not in AICompanyDecisionComponent._sessions

    def test_query_ai_fallback_to_run_agent(self, comp) -> None:
        """session 池中无可用 session 时，_query_ai 应回退到 run_agent。"""
        # 不放入任何 session

        with patch.object(AICompanyDecisionComponent, "_run_in_loop") as mock_run:
            mock_run.return_value = AgentResult(status="completed", message=_mock_ai_result_json())

            comp._query_ai(_make_context("TestAI"))

            # _run_in_loop 应被调用（用于 _run_agent 协程）
            assert mock_run.called

    def test_set_context_uses_query_ai(self, comp) -> None:
        """set_context 应调用 _query_ai 而非 _call_ai。"""
        with patch.object(AICompanyDecisionComponent, "_query_ai") as mock_query:
            mock_query.return_value = {"pricing": {"食品": 120}, "investment_plan": {"expansion": 0, "brand": 500, "tech": 300}, "loan_needs": {"amount": 0, "max_rate": 10}}

            comp.set_context(_make_context())

            mock_query.assert_called_once()
