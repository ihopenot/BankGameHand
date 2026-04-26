from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple

from component.base_company_decision import BaseCompanyDecisionComponent, register_decision_component
from component.classic_company_decision import ClassicCompanyDecisionComponent
from mcp_agent_sdk import AgentResult, AgentRunConfig, AssistantMessage, MCPAgentSDK

if TYPE_CHECKING:
    from core.entity import Entity
    from system.market_service import SellOrder

logger = logging.getLogger(__name__)


_PROMPT_TEMPLATE = """你是 BankGameHand 游戏中的 CEO 决策 AI。

重要：请直接根据下方提供的上下文数据做出决策，不要读取任何文件，立即回答。
极其重要：任务完成务必调用Compelete返回任务结果！！！
极其重要：任务完成务必调用Compelete返回任务结果！！！
极其重要：任务完成务必调用Compelete返回任务结果！！！

## 你的公司：{company_name}

## 公司上下文
{context_json}

## 你需要做出以下 3 项决策：

### 1. 产品定价 (pricing)
对每种产品设定新标价（正整数）。键为商品类型名称，值为新标价。

### 2. 投资计划 (investment_plan)
- expansion: 扩产金额（整数 >= 0）
- brand: 品牌投入金额（整数 >= 0）
- tech: 科技投入金额（整数 >= 0）

### 3. 贷款需求 (loan_needs)
- amount: 需要贷款的金额（整数 >= 0）
- max_rate: 可接受的最大利率（整数 >= 0）

## 请严格按以下 JSON 格式返回，不要包含其他内容：
```json
{{
  "pricing": {{ "<商品名>": <价格>, ... }},
  "investment_plan": {{ "expansion": <int>, "brand": <int>, "tech": <int> }},
  "loan_needs": {{ "amount": <int>, "max_rate": <int> }}
}}
```"""


@register_decision_component("ai")
class AICompanyDecisionComponent(ClassicCompanyDecisionComponent):
    """AI 驱动的企业决策组件：通过 MCPAgentSDK 调用 LLM 完成定价、投资、贷款决策。

    继承 Classic 以复用 decide_budget_allocation 和 make_purchase_sort_key。
    覆写 decide_pricing、decide_investment_plan、decide_loan_needs 读取 AI 缓存。
    """

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        self._ai_decisions: Dict[str, Any] = {}

    # ── 覆写 set_context：调用 AI ──

    def set_context(self, context: dict) -> None:
        """接收上下文并调用 AI 生成决策，结果缓存。"""
        super().set_context(context)
        self._ai_decisions = self._call_ai(context)

    # ── 覆写 3 个决策方法：读取缓存 ──

    def decide_pricing(self) -> Dict[str, int]:
        """从 AI 缓存读取定价结果。"""
        if self._ai_decisions:
            return self._ai_decisions.get("pricing", {})
        return super().decide_pricing()

    def decide_investment_plan(self) -> Dict[str, int]:
        """从 AI 缓存读取投资计划。"""
        if self._ai_decisions:
            plan = self._ai_decisions.get("investment_plan", {})
            self.investment_plan = plan
            return plan
        return super().decide_investment_plan()

    def decide_loan_needs(self) -> Tuple[int, int]:
        """从 AI 缓存读取贷款需求。"""
        if self._ai_decisions:
            loan = self._ai_decisions.get("loan_needs", {})
            return (loan.get("amount", 0), loan.get("max_rate", 0))
        return super().decide_loan_needs()

    # ── AI 调用 ──

    def _call_ai(self, context: dict) -> Dict[str, Any]:
        """通过 MCPAgentSDK 调用 AI agent，返回解析后的决策 dict。"""
        prompt = self._build_prompt(context)
        logger.info("[AI] Prompt:\n%s", prompt)
        sdk = MCPAgentSDK()
        config = AgentRunConfig(
            prompt=prompt,
            validate_fn=self._validate_fn,
            max_retries=3,
            model="glm-5.1",
            permission_mode="plan",
        )

        result = asyncio.run(self._run_agent(sdk, config))

        # 尝试从 result.message 解析 JSON
        decisions = self._parse_ai_result(result.message)
        logger.info("[AI] %s 决策结果: %s", self._context.get("company", {}).get("name", "?"),
                     json.dumps(decisions, ensure_ascii=False))
        return decisions

    @staticmethod
    async def _run_agent(sdk: MCPAgentSDK, config: AgentRunConfig) -> AgentResult:
        """运行 AI agent 并收集最终结果，同时输出所有事件。"""
        await sdk.init()
        final_result = None
        async for event in sdk.run_agent(config):
            if isinstance(event, AgentResult):
                final_result = event
                logger.info("[AI] AgentResult: status=%s message=%s", event.status, event.message[:500])
            elif isinstance(event, AssistantMessage):
                AICompanyDecisionComponent._log_assistant_message(event)
        if final_result is None:
            raise RuntimeError("AI agent did not return a result")
        return final_result

    @staticmethod
    def _log_assistant_message(msg: AssistantMessage) -> None:
        """输出 AssistantMessage 中的所有内容块（思考、文本、工具调用）。"""
        from mcp_agent_sdk import TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock
        for block in msg.content:
            if isinstance(block, ThinkingBlock):
                logger.info("[AI] 思考: %s", block.thinking)
            elif isinstance(block, TextBlock):
                logger.info("[AI] 文本: %s", block.text)
            elif isinstance(block, ToolUseBlock):
                logger.info("[AI] 工具调用: %s(%s)", block.name, json.dumps(block.input, ensure_ascii=False))
            elif isinstance(block, ToolResultBlock):
                status = "错误" if block.is_error else "成功"
                logger.info("[AI] 工具结果[%s]: %s", status, block.output[:500])

    @staticmethod
    def _parse_ai_result(message: str) -> Dict[str, Any]:
        """从 AI 返回的消息中提取 JSON。"""
        # 尝试直接解析
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 代码块
        import re
        match = re.search(r"```(?:json)?\s*(.*?)```", message, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Cannot parse AI result as JSON: {message[:200]}")

    # ── 验证函数 ──

    @staticmethod
    def _validate_fn(result_str: str) -> Tuple[bool, str]:
        """验证 AI 返回的 JSON 包含所有必需字段和正确类型。"""
        print(f"Validate: {result_str}")
        try:
            data = json.loads(result_str)
        except json.JSONDecodeError:
            # 尝试提取代码块
            import re
            match = re.search(r"```(?:json)?\s*(.*?)```", result_str, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    return (False, "Invalid JSON format")
            else:
                return (False, "Invalid JSON format")

        # 检查 3 个必需 key
        for key in ("pricing", "investment_plan", "loan_needs"):
            if key not in data:
                return (False, f"Missing required key: {key}")

        # 验证 pricing
        pricing = data["pricing"]
        if not isinstance(pricing, dict):
            return (False, "pricing must be a dict")
        for name, price in pricing.items():
            if not isinstance(price, (int, float)) or price <= 0:
                return (False, f"pricing[{name}] must be a positive number, got {price}")

        # 验证 investment_plan
        plan = data["investment_plan"]
        if not isinstance(plan, dict):
            return (False, "investment_plan must be a dict")
        for key in ("expansion", "brand", "tech"):
            if key not in plan:
                return (False, f"investment_plan missing key: {key}")
            if not isinstance(plan[key], (int, float)) or plan[key] < 0:
                return (False, f"investment_plan[{key}] must be >= 0, got {plan[key]}")

        # 验证 loan_needs
        loan = data["loan_needs"]
        if not isinstance(loan, dict):
            return (False, "loan_needs must be a dict")
        for key in ("amount", "max_rate"):
            if key not in loan:
                return (False, f"loan_needs missing key: {key}")
            if not isinstance(loan[key], (int, float)) or loan[key] < 0:
                return (False, f"loan_needs[{key}] must be >= 0, got {loan[key]}")

        return (True, "")

    # ── Prompt 构建 ──

    @staticmethod
    def _serialize_for_json(obj: Any) -> Any:
        """递归将 context 转为 JSON 可序列化结构，手动处理每种领域对象。"""
        from collections import Counter
        from core.entity import Entity
        from entity.company.company import Company
        from entity.factory import FactoryType, Recipe
        from entity.goods import GoodsBatch, GoodsType
        from system.market_service import SellOrder, TradeRecord

        # ── 标量直接返回 ──
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj

        # ── 领域对象逐一处理 ──
        if isinstance(obj, GoodsType):
            return obj.name

        if isinstance(obj, Company):
            return obj.name

        if isinstance(obj, Entity):
            return getattr(obj, "name", type(obj).__name__)

        if isinstance(obj, GoodsBatch):
            return {
                "goods_type": obj.goods_type.name,
                "quantity": obj.quantity,
                "quality": obj.quality,
                "brand_value": obj.brand_value,
            }

        if isinstance(obj, SellOrder):
            return {
                "seller": obj.seller.name if isinstance(obj.seller, Company) else type(obj.seller).__name__,
                "goods_type": obj.batch.goods_type.name,
                "quantity": obj.batch.quantity,
                "price": obj.price,
            }

        if isinstance(obj, TradeRecord):
            return {
                "seller": obj.seller.name if isinstance(obj.seller, Company) else type(obj.seller).__name__,
                "buyer": obj.buyer.name if isinstance(obj.buyer, Company) else type(obj.buyer).__name__,
                "goods_type": obj.goods_type.name,
                "quantity": obj.quantity,
                "price": obj.price,
                "total": obj.total,
            }

        if isinstance(obj, Recipe):
            return {
                "output": f"{obj.output_goods_type.name}x{obj.output_quantity}",
                "input": f"{obj.input_goods_type.name}x{obj.input_quantity}" if obj.input_goods_type else "无",
            }

        # ── dict: 特殊处理 factories，其余递归 value ──
        if isinstance(obj, dict):
            if obj and all(isinstance(k, FactoryType) and isinstance(v, list) for k, v in obj.items()):
                return AICompanyDecisionComponent._serialize_factories(obj)
            result = {}
            for k, v in obj.items():
                key = k.name if isinstance(k, GoodsType) else (
                    k.output_goods_type.name if isinstance(k, Recipe) else (
                        str(k) if not isinstance(k, (str, int, float, bool, type(None))) else k
                    )
                )
                result[key] = AICompanyDecisionComponent._serialize_for_json(v)
            return result

        # ── list / tuple ──
        if isinstance(obj, (list, tuple)):
            return [AICompanyDecisionComponent._serialize_for_json(item) for item in obj]

        # ── 兜底 ──
        return str(obj)

    @staticmethod
    def _serialize_factories(factories: dict) -> dict:
        """序列化 factories dict：按 FactoryType 输出类型信息 + 按 build_remaining 聚类实例数。"""
        from entity.factory import FactoryType
        result = {}
        # 反查 FactoryType 注册名
        name_map = {id(ft): name for name, ft in FactoryType.factory_types.items()}
        for ft, factory_list in factories.items():
            name = name_map.get(id(ft), ft.recipe.output_goods_type.name)
            recipe = ft.recipe
            type_info = {
                "output": f"{recipe.output_goods_type.name}x{recipe.output_quantity}",
                "input": f"{recipe.input_goods_type.name}x{recipe.input_quantity}" if recipe.input_goods_type else "无",
                "base_production": ft.base_production,
                "maintenance_cost": ft.maintenance_cost,
                "build_cost": ft.build_cost,
                "build_time": ft.build_time,
            }
            # 按 build_remaining 聚类
            from collections import Counter
            counter = Counter(f.build_remaining for f in factory_list)
            instances = {}
            for br, count in sorted(counter.items()):
                status = "已建成" if br == 0 else f"建造中(剩余{br}回合)"
                instances[status] = count
            result[name] = {"type_info": type_info, "instances": instances}
        return result

    @staticmethod
    def _build_prompt(context: dict) -> str:
        """构建 AI prompt，包含完整 context。"""
        company_name = context.get("company", {}).get("name", "Unknown")
        safe_context = AICompanyDecisionComponent._serialize_for_json(context)
        context_json = json.dumps(safe_context, ensure_ascii=False, indent=2)
        return _PROMPT_TEMPLATE.format(company_name=company_name, context_json=context_json)
