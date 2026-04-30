from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Dict, Tuple, Type

from component.base_component import BaseComponent

if TYPE_CHECKING:
    from core.entity import Entity
    from system.market_service import SellOrder

# 决策组件注册表：name → subclass of BaseCompanyDecisionComponent
_DECISION_COMPONENT_REGISTRY: Dict[str, Type[BaseCompanyDecisionComponent]] = {}


def register_decision_component(name: str):
    """类装饰器：将决策组件类注册到全局注册表。"""
    def decorator(cls: Type[BaseCompanyDecisionComponent]) -> Type[BaseCompanyDecisionComponent]:
        _DECISION_COMPONENT_REGISTRY[name] = cls
        return cls
    return decorator


def get_decision_component_class(name: str) -> Type[BaseCompanyDecisionComponent]:
    """根据名称获取决策组件类。首次查询时自动导入子模块以触发注册。"""
    if not _DECISION_COMPONENT_REGISTRY:
        import component.decision.company.classic  # noqa: F401 — 触发 @register_decision_component
        import component.decision.company.ai  # noqa: F401
    return _DECISION_COMPONENT_REGISTRY[name]


class BaseCompanyDecisionComponent(BaseComponent, ABC):
    """企业决策抽象基类：定义 CEO 特质和 5 个决策 API。"""

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        # 6 维 CEO 特质，取值 [0, 1]
        self.business_acumen: float = random.random()
        self.risk_appetite: float = random.random()
        self.profit_focus: float = random.random()
        self.marketing_awareness: float = random.random()
        self.tech_focus: float = random.random()
        self.price_sensitivity: float = random.random()

        # 投资计划表（plan_phase 生成，act_phase 执行）
        self.investment_plan: Dict[str, int] = {}

        # 决策上下文（由 set_context 设置）
        self._context: dict = {}

    def set_context(self, context: dict) -> None:
        """接收并存储决策上下文数据。"""
        self._context = context

    @abstractmethod
    def decide_pricing(self) -> Dict[str, int]:
        """决策一：产品定价。返回 goods_type_name → new_price。"""

    @abstractmethod
    def decide_investment_plan(self) -> Dict[str, int]:
        """决策二：投资计划。返回 {"expansion": int, "brand": int, "tech": int}。"""

    @abstractmethod
    def decide_loan_needs(self) -> Tuple[int, int]:
        """决策三：贷款需求。返回 (amount, max_rate)。"""

    @abstractmethod
    def decide_budget_allocation(self) -> Dict[str, int]:
        """预算分配。返回实际分配金额。"""

    @abstractmethod
    def make_purchase_sort_key(self) -> Callable[[SellOrder], float]:
        """采购排序函数。"""

    @abstractmethod
    def decide_wage(self) -> int:
        """决策：工资定价。返回每劳动力点数的工资。"""
