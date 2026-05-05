from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Callable, Dict, List, Tuple

from component.decision.company.base import BaseCompanyDecisionComponent, register_decision_component
from core.config import ConfigManager
from entity.factory import Factory, FactoryType
from entity.goods import GoodsType

if TYPE_CHECKING:
    from core.entity import Entity
    from system.market_service import SellOrder


@register_decision_component("classic")
class ClassicCompanyDecisionComponent(BaseCompanyDecisionComponent):
    """经典公式驱动的企业决策组件。

    Context dict 约定（由 DecisionService._build_context 组装）：
    - productor.factories: Dict[FactoryType, List[Factory]] — 与 ProductorComponent.factories 格式一致
    - productor.current_prices: Dict[GoodsType, int] — GoodsType 对象为 key
    - metric.my_sell_orders: Dict[GoodsType, int]
    - metric.my_sold_quantities: Dict[GoodsType, int]
    - metric.my_avg_buy_prices: Dict[GoodsType, float]
    - metric.last_revenue: int
    - ledger.cash: int
    """

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        self.config = ConfigManager().section("decision")

    # ── 决策一：产品定价 ──

    def decide_pricing(self) -> Dict[str, int]:
        """根据上轮销售情况调整标价。返回 {goods_type_name: new_price}。"""
        ctx = self._context
        metric = ctx.get("metric", {})
        productor = ctx.get("productor", {})
        cfg = self.config.pricing

        sell_orders = metric.get("my_sell_orders", {})
        sold_quantities = metric.get("my_sold_quantities", {})
        current_prices = productor.get("current_prices", {})

        new_prices: Dict[str, int] = {}
        for gt, old_price in current_prices.items():
            listed = sell_orders.get(gt, 0)
            sold = sold_quantities.get(gt, 0)

            if listed == 0:
                continue

            if sold >= listed:
                raise_rate = cfg.base_raise_rate * (1 + self.risk_appetite * cfg.risk_raise_coeff)
                delta = old_price * raise_rate
            else:
                cut_rate = cfg.base_cut_rate * (1 + (1 - self.profit_focus) * cfg.concession_coeff)
                delta = -old_price * cut_rate

            acumen = max(self.business_acumen, 0.01)
            noise_scale = cfg.noise_coeff / acumen
            noise = random.gauss(0, noise_scale * old_price)

            new_price = old_price + delta + noise
            gt_name = gt.name if hasattr(gt, "name") else str(gt)
            new_prices[gt_name] = max(1, round(new_price))

        return new_prices

    # ── 决策二：投资计划 ──

    def decide_investment_plan(self) -> Dict[str, int]:
        """生成投资计划表。返回 {"expansion": int, "brand": int, "tech": int}。"""
        plan = {
            "expansion": self._plan_expansion(),
            "brand": self._plan_brand(),
            "tech": self._plan_tech(),
        }
        self.investment_plan = plan
        return plan

    def _plan_expansion(self) -> int:
        """计划扩产金额。"""
        ctx = self._context
        productor = ctx.get("productor", {})
        factories: Dict[FactoryType, List[Factory]] = productor.get("factories", {})

        if not factories:
            return 0

        cfg = self.config.investment
        acumen = max(self.business_acumen, 0.01)
        noise = random.gauss(0, cfg.perception_noise_coeff / acumen)
        perceived_ratio = 0.8 + noise

        market_outlook = max(0.0, 1.0 - perceived_ratio)

        ledger = ctx.get("ledger", {})
        cash = ledger.get("cash", 0)
        min_cost = min((ft.build_cost for ft in factories), default=0)
        cash_adequacy = min(cash / (min_cost * 2), 1.0) if min_cost > 0 else 0.0
        willingness = (self.risk_appetite + market_outlook + cash_adequacy) / 3.0

        if willingness <= cfg.investment_threshold:
            return 0

        cheapest = min(factories, key=lambda ft: ft.build_cost)
        return cheapest.build_cost

    def _plan_brand(self) -> int:
        """计划品牌支出金额。"""
        ctx = self._context
        metric = ctx.get("metric", {})
        last_revenue = metric.get("last_revenue", 0)
        cfg = self.config.brand
        return int(last_revenue * cfg.base_ratio * (1 + self.marketing_awareness * cfg.marketing_coeff))

    def _plan_tech(self) -> int:
        """计划科技支出金额。"""
        ctx = self._context
        metric = ctx.get("metric", {})
        last_revenue = metric.get("last_revenue", 0)
        cfg = self.config.tech
        return int(last_revenue * cfg.base_ratio * (1 + self.tech_focus * cfg.tech_coeff))

    # ── 决策三：贷款需求 ──

    def decide_loan_needs(self) -> Tuple[int, int]:
        """根据投资计划和保留金计算贷款需求。返回 (amount, max_rate)。"""
        ctx = self._context
        ledger = ctx.get("ledger", {})
        cash = ledger.get("cash", 0)

        plan_total = sum(self.investment_plan.values())
        if plan_total == 0:
            return (0, 0)

        reserved = self._calc_reserved_cash()
        loan_need = reserved + plan_total - cash
        amount = max(0, loan_need)
        max_rate = int((1 - self.risk_appetite) * 15) + 3
        return (amount, max_rate)

    # ── 预算分配 ──

    def decide_budget_allocation(self) -> Dict[str, int]:
        """根据投资计划和可用现金计算实际分配。"""
        ctx = self._context
        ledger = ctx.get("ledger", {})
        cash = ledger.get("cash", 0)

        plan = self.investment_plan
        plan_total = sum(plan.values())
        if plan_total == 0:
            return {"expansion": 0, "brand": 0, "tech": 0}

        reserved = self._calc_reserved_cash()
        budget = max(0, cash - reserved)

        if budget >= plan_total:
            return dict(plan)
        else:
            return {k: int(budget * v / plan_total) for k, v in plan.items()}

    # ── 采购排序 ──

    def make_purchase_sort_key(self) -> Callable[[SellOrder], float]:
        """生成带 CEO 特质的采购排序函数。"""
        ctx = self._context
        metric = ctx.get("metric", {})
        avg_prices = metric.get("my_avg_buy_prices", {})

        awareness = self.marketing_awareness
        price_sens = self.price_sensitivity

        def sort_key(order: SellOrder) -> float:
            gt = order.batch.goods_type
            avg_price = avg_prices.get(gt, 0.0)
            if avg_price <= 0:
                avg_price = gt.base_price
            return self._calculate_supplier_score(
                marketing_awareness=awareness,
                price_sensitivity=price_sens,
                quality=order.batch.quality,
                price=order.price,
                brand_value=order.batch.brand_value,
                avg_price=avg_price,
            )

        return sort_key

    @staticmethod
    def _price_attractiveness(price: int, avg_price: float) -> float:
        """用 sigmoid 计算价格吸引力，范围 [-1, 1]。"""
        if avg_price <= 0:
            return 0.0
        k = 5.0
        x = k * (avg_price - price) / avg_price
        x = max(-500, min(500, x))
        return 2.0 / (1.0 + math.exp(-x)) - 1.0

    def _calculate_supplier_score(
        self,
        marketing_awareness: float,
        price_sensitivity: float,
        quality: float,
        price: int,
        brand_value: int,
        avg_price: float,
    ) -> float:
        """计算供应商评分（三维加权：品质+品牌+价格吸引力）。"""
        cfg = self.config.purchase
        w_brand = marketing_awareness * cfg.brand_weight_coeff
        w_price = price_sensitivity * cfg.brand_weight_coeff
        w_quality = max(0.0, 1.0 - w_brand - w_price)
        price_score = self._price_attractiveness(price, avg_price)
        return w_quality * quality + w_brand * brand_value + w_price * price_score

    # ── 决策：工资定价 ──

    def decide_wage(self) -> int:
        """动态工资决策：利润优先 + 现金调节 + 增量逼近。

        1. 计算目标工资 = (售价 - 非工资单位成本 - 目标利润) × 产量 / 劳动力需求
        2. 现金调节因子 = clamp(企业现金 / 运营支出 / target_cash_ratio, min, max)
        3. new_wage = current + step_rate × (target × cash_factor - current)
        """
        ctx = self._context
        company_ctx = ctx.get("company", {})
        ledger = ctx.get("ledger", {})
        productor = ctx.get("productor", {})
        metric = ctx.get("metric", {})

        cfg = self.config.wage
        current_wage = company_ctx.get("current_wage", company_ctx.get("initial_wage", 10))
        cash = ledger.get("cash", 0)
        last_op_expense = company_ctx.get("last_operating_expense", 0)

        # 获取工厂信息计算目标工资
        factories = productor.get("factories", {})
        current_prices = productor.get("current_prices", {})
        avg_buy_prices = metric.get("my_avg_buy_prices", {})

        # 计算总劳动力需求和总产能
        total_labor_demand = 0
        total_output_capacity = 0
        total_maintenance = 0
        total_material_cost = 0

        for ft, factory_list in factories.items():
            built_count = sum(1 for f in factory_list if f.is_built)
            if built_count == 0:
                continue
            total_labor_demand += ft.labor_demand * built_count
            total_output_capacity += ft.recipe.output_quantity * built_count
            total_maintenance += ft.maintenance_cost * built_count

            # 原材料成本（基于上回合采购均价）
            if ft.recipe.input_goods_type is not None:
                input_price = avg_buy_prices.get(ft.recipe.input_goods_type, 0.0)
                if input_price <= 0:
                    input_price = ft.recipe.input_goods_type.base_price
                total_material_cost += input_price * ft.recipe.input_quantity * built_count

        if total_labor_demand <= 0 or total_output_capacity <= 0:
            return max(1, current_wage)

        # 加权平均售价计算总收入容量
        total_revenue_capacity = 0
        for ft, factory_list in factories.items():
            built_count = sum(1 for f in factory_list if f.is_built)
            if built_count == 0:
                continue
            gt = ft.recipe.output_goods_type
            price = current_prices.get(gt, gt.base_price)
            total_revenue_capacity += price * ft.recipe.output_quantity * built_count

        # target_profit_margin = profit_focus × base_profit_margin
        target_profit_margin = self.profit_focus * cfg.base_profit_margin

        # 总利润空间 = 总收入 - 总非工资成本 - 目标利润
        wage_budget = total_revenue_capacity - total_material_cost - total_maintenance - target_profit_margin * total_revenue_capacity
        target_wage = wage_budget / total_labor_demand if total_labor_demand > 0 else current_wage

        # 现金调节因子
        if last_op_expense > 0:
            cash_ratio = cash / last_op_expense
            cash_factor = max(cfg.cash_factor_min, min(cfg.cash_factor_max, cash_ratio / cfg.target_cash_ratio))
        else:
            cash_factor = 1.0  # 中性

        # 增量逼近
        adjusted_target = target_wage * cash_factor
        new_wage = current_wage + cfg.step_rate * (adjusted_target - current_wage)

        return max(1, int(round(new_wage)))

    # ── 内部方法 ──

    def _calc_operating_expense(self) -> int:
        """计算经营开销（维护费），按已建成工厂实例计数。"""
        ctx = self._context
        productor = ctx.get("productor", {})
        factories: Dict[FactoryType, List[Factory]] = productor.get("factories", {})
        return sum(
            ft.maintenance_cost
            for ft, factory_list in factories.items()
            for f in factory_list
            if f.is_built
        )

    def _calc_reserved_cash(self) -> int:
        """计算保留金 = 经营开销 × (1 + (1 - risk_appetite) × reserve_coeff)。"""
        expense = self._calc_operating_expense()
        coeff = self.config.investment.reserve_coeff
        return int(expense * (1 + (1 - self.risk_appetite) * coeff))
