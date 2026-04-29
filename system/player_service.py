from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.input_controller import PlayerInputController, StdinInputController
from core.types import RATE_SCALE, Loan, LoanApplication, PlayerAction
from entity.bank import Bank
from system.bank_service import BankService, LoanOffer
from system.service import Service

if TYPE_CHECKING:
    from core.entity import Entity
    from game.game import Game

console = Console(width=200)


class PlayerService(Service):
    """玩家操作服务：展示经济数据，处理玩家输入。"""

    def __init__(self, game: Game, input_controller: PlayerInputController | None = None) -> None:
        super().__init__(game)
        self.input_controller = input_controller or StdinInputController()

    # ── 展示方法（返回 rich 对象） ──

    def render_economy_summary(self) -> Panel:
        index_ratio = self.game.economy_service.economy_index / RATE_SCALE
        text = f"经济指数: [bold cyan]{index_ratio:.4f}[/]"
        title = f"第 {self.game.round} / {self.game.total_rounds} 回合"
        return Panel(text, title=title, border_style="blue")

    def render_company_table(self) -> Table:
        table = Table(title="企业概览", show_lines=True)
        table.add_column("公司名", style="bold")
        table.add_column("工厂类型")
        table.add_column("工厂数", justify="right")
        table.add_column("现金", justify="right", style="green")
        table.add_column("工资", justify="right", style="yellow")
        table.add_column("雇佣劳动力", justify="right")
        table.add_column("科技", justify="right", style="cyan")
        table.add_column("品牌", justify="right", style="magenta")
        table.add_column("定价")
        table.add_column("库存")
        table.add_column("应收款", justify="right")
        table.add_column("应付款", justify="right", style="red")

        for name, company in self.game.company_service.companies.items():
            ledger = company.get_component(LedgerComponent)
            storage = company.get_component(StorageComponent)
            pc = company.get_component(ProductorComponent)

            cash = ledger.cash
            receivables = ledger.total_receivables()
            payables = ledger.total_payables()

            ft_parts: List[str] = []
            factory_count = 0
            total_tech = 0
            total_brand = 0
            for ft, factories in pc.factories.items():
                ft_parts.append(ft.recipe.output_goods_type.name)
                factory_count += len(factories)
            total_tech = sum(pc.tech_values.values())
            total_brand = sum(pc.brand_values.values())

            inv_parts: List[str] = []
            if storage:
                for gt, batches in storage.inventory.items():
                    total_qty = sum(b.quantity for b in batches)
                    if total_qty > 0:
                        inv_parts.append(f"{gt.name} x{total_qty}")

            price_parts: List[str] = []
            for gt, price in pc.prices.items():
                price_parts.append(f"{gt.name}:{price}")

            table.add_row(
                name,
                ", ".join(ft_parts) or "-",
                str(factory_count),
                str(cash),
                str(company.wage),
                str(pc.hired_labor_points),
                str(total_tech),
                str(total_brand),
                ", ".join(price_parts) or "-",
                ", ".join(inv_parts) or "-",
                str(receivables),
                str(payables),
            )

        return table

    def render_folk_table(self) -> Table:
        table = Table(title="居民概览", show_lines=True)
        table.add_column("群体", style="bold")
        table.add_column("人口", justify="right")
        table.add_column("现金", justify="right", style="green")
        table.add_column("品质偏好", justify="right")
        table.add_column("品牌偏好", justify="right")
        table.add_column("价格偏好", justify="right")
        table.add_column("库存")

        folk_labels = [f"居民组{i+1}" for i in range(len(self.game.folks))]
        for label, folk in zip(folk_labels, self.game.folks):
            ledger = folk.get_component(LedgerComponent)
            storage = folk.get_component(StorageComponent)

            inv_parts: List[str] = []
            if storage:
                for gt, batches in storage.inventory.items():
                    total_qty = sum(b.quantity for b in batches)
                    if total_qty > 0:
                        inv_parts.append(f"{gt.name} x{total_qty}")

            table.add_row(
                label,
                str(folk.population),
                str(ledger.cash),
                f"{folk.w_quality:.2f}",
                f"{folk.w_brand:.2f}",
                f"{folk.w_price:.2f}",
                ", ".join(inv_parts) or "-",
            )

        return table

    def render_bank_summary(self, banks: Dict[str, Bank]) -> Table:
        table = Table(title="银行概览", show_lines=True)
        table.add_column("银行名", style="bold")
        table.add_column("现金", justify="right", style="green")
        table.add_column("贷款总额", justify="right", style="yellow")
        table.add_column("本回合利息收入", justify="right", style="cyan")

        for name, bank in banks.items():
            ledger = bank.get_component(LedgerComponent)
            cash = ledger.cash
            total_loans = ledger.total_receivables()
            interest_income = sum(
                min(bill.interest_due, bill.total_paid)
                for bill in ledger.bills
            )
            table.add_row(name, str(cash), str(total_loans), str(interest_income))

        return table

    def render_active_loans(self, loans: List[Loan]) -> Table:
        table = Table(title="活跃贷款", show_lines=True)
        table.add_column("借款方")
        table.add_column("贷款方")
        table.add_column("剩余本金", justify="right", style="yellow")
        table.add_column("利率(万分比)", justify="right")
        table.add_column("剩余期限", justify="right")

        if not loans:
            table.add_row("暂无", "", "", "", "")
            return table

        for loan in loans:
            remaining_term = str(max(0, loan.term - loan.elapsed)) if loan.term > 0 else "永续"
            table.add_row("?", "?", str(loan.remaining), str(loan.rate), remaining_term)

        return table

    def render_loan_applications(
        self,
        applications: List[LoanApplication],
        company_names: Dict[str, Entity],
    ) -> Table:
        table = Table(title="贷款申请", show_lines=True)
        table.add_column("序号", justify="right")
        table.add_column("申请企业", style="bold")
        table.add_column("申请金额", justify="right", style="yellow")

        if not applications:
            table.add_row("", "暂无申请", "")
            return table

        entity_to_name: Dict[Entity, str] = {v: k for k, v in company_names.items()}
        for i, app in enumerate(applications, 1):
            name = entity_to_name.get(app.applicant, "未知")
            table.add_row(str(i), name, str(app.amount))

        return table

    # ── JSON 序列化方法（返回 dict，供 WebController 使用） ──

    def economy_summary_dict(self) -> dict:
        """返回经济概要的 dict 表示。"""
        return {
            "round": self.game.round,
            "total_rounds": self.game.total_rounds,
            "economy_index": round(self.game.economy_service.economy_index / RATE_SCALE, 4),
        }

    def company_table_dict(self) -> List[dict]:
        """返回企业概览的 dict 列表。"""
        result: List[dict] = []
        for name, company in self.game.company_service.companies.items():
            ledger = company.get_component(LedgerComponent)
            storage = company.get_component(StorageComponent)
            pc = company.get_component(ProductorComponent)

            ft_parts: List[str] = []
            factory_count = 0
            for ft, factories in pc.factories.items():
                ft_parts.append(ft.recipe.output_goods_type.name)
                factory_count += len(factories)

            inv_parts: List[str] = []
            if storage:
                for gt, batches in storage.inventory.items():
                    total_qty = sum(b.quantity for b in batches)
                    if total_qty > 0:
                        inv_parts.append(f"{gt.name} x{total_qty}")

            price_parts: List[str] = []
            for gt, price in pc.prices.items():
                price_parts.append(f"{gt.name}:{price}")

            result.append({
                "name": name,
                "factory_types": ", ".join(ft_parts) or "-",
                "factory_count": factory_count,
                "cash": ledger.cash,
                "wage": company.wage,
                "hired_labor_points": pc.hired_labor_points,
                "tech": sum(pc.tech_values.values()),
                "brand": sum(pc.brand_values.values()),
                "prices": ", ".join(price_parts) or "-",
                "inventory": ", ".join(inv_parts) or "-",
                "receivables": ledger.total_receivables(),
                "payables": ledger.total_payables(),
            })
        return result

    def folk_table_dict(self) -> List[dict]:
        """返回居民概览的 dict 列表。"""
        result: List[dict] = []
        for i, folk in enumerate(self.game.folks):
            ledger = folk.get_component(LedgerComponent)
            storage = folk.get_component(StorageComponent)

            inv_parts: List[str] = []
            if storage:
                for gt, batches in storage.inventory.items():
                    total_qty = sum(b.quantity for b in batches)
                    if total_qty > 0:
                        inv_parts.append(f"{gt.name} x{total_qty}")

            result.append({
                "name": f"居民组{i+1}",
                "population": folk.population,
                "cash": ledger.cash,
                "w_quality": round(folk.w_quality, 2),
                "w_brand": round(folk.w_brand, 2),
                "w_price": round(folk.w_price, 2),
                "inventory": ", ".join(inv_parts) or "-",
            })
        return result

    def bank_summary_dict(self, banks: Dict[str, Bank]) -> List[dict]:
        """返回银行概览的 dict 列表。"""
        result: List[dict] = []
        for name, bank in banks.items():
            ledger = bank.get_component(LedgerComponent)
            interest_income = sum(
                min(bill.interest_due, bill.total_paid)
                for bill in ledger.bills
            )
            result.append({
                "name": name,
                "cash": ledger.cash,
                "total_loans": ledger.total_receivables(),
                "interest_income": interest_income,
            })
        return result

    def loan_applications_dict(
        self,
        applications: List[LoanApplication],
        company_names: Dict[str, Entity],
    ) -> List[dict]:
        """返回贷款申请的 dict 列表。"""
        entity_to_name: Dict[Entity, str] = {v: k for k, v in company_names.items()}
        result: List[dict] = []
        for i, app in enumerate(applications, 1):
            name = entity_to_name.get(app.applicant, "未知")
            result.append({
                "index": i,
                "company_name": name,
                "amount": app.amount,
            })
        return result

    def metrics_entities_dict(self) -> dict:
        """返回所有可查看 metrics 的实体列表及其历史快照数据。

        返回结构:
        {
            "entities": [
                {"id": "company_0", "type": "company"},
                {"id": "银行A", "type": "bank"},
                {"id": "居民组1", "type": "folk"},
                ...
            ],
            "snapshots": {
                "company_0": [
                    {"round": 1, "cash": 100000, "revenue": 0, ...},
                    ...
                ],
                ...
            }
        }
        """
        entities: List[dict] = []
        snapshots: dict = {}

        # Companies
        for name, company in self.game.company_service.companies.items():
            entities.append({"id": name, "type": "company"})
            mc = company.get_component(MetricComponent)
            if mc:
                snapshots[name] = [
                    {
                        "round": s.round_number,
                        "cash": s.cash,
                        "revenue": s.revenue,
                        "sell_orders": {gt.name: qty for gt, qty in s.sell_orders.items()},
                        "sold_quantities": {gt.name: qty for gt, qty in s.sold_quantities.items()},
                        "prices": {gt.name: p for gt, p in s.prices.items()},
                        "brand_values": {gt.name: v for gt, v in s.brand_values.items()},
                        "tech_values": {str(r): v for r, v in s.tech_values.items()},
                        "investment_plan": dict(s.investment_plan),
                    }
                    for s in mc.round_history
                ]

        # Banks
        for name, bank in self.game.bank_service.banks.items():
            entities.append({"id": name, "type": "bank"})
            mc = bank.get_component(MetricComponent)
            if mc:
                snapshots[name] = [
                    {
                        "round": s.round_number,
                        "cash": s.cash,
                        "revenue": s.revenue,
                    }
                    for s in mc.round_history
                ]

        # Folks
        for i, folk in enumerate(self.game.folks):
            folk_id = f"居民组{i+1}"
            entities.append({"id": folk_id, "type": "folk"})
            mc = folk.get_component(MetricComponent)
            if mc:
                snapshots[folk_id] = [
                    {
                        "round": s.round_number,
                        "cash": s.cash,
                        "revenue": s.revenue,
                    }
                    for s in mc.round_history
                ]

        return {"entities": entities, "snapshots": snapshots}

    # ── 兼容旧测试的字符串方法 ──

    def format_company_table(self) -> str:
        """返回企业表格的纯文本表示（供测试用）。"""
        with console.capture() as capture:
            console.print(self.render_company_table())
        return capture.get()

    def format_bank_summary(self, banks: Dict[str, Bank]) -> str:
        with console.capture() as capture:
            console.print(self.render_bank_summary(banks))
        return capture.get()

    def format_active_loans(self, loans: List[Loan]) -> str:
        with console.capture() as capture:
            console.print(self.render_active_loans(loans))
        return capture.get()

    def format_loan_applications(
        self,
        applications: List[LoanApplication],
        company_names: Dict[str, Entity],
    ) -> str:
        with console.capture() as capture:
            console.print(self.render_loan_applications(applications, company_names))
        return capture.get()

    # ── 操作处理 ──

    def handle_loan_approval(
        self,
        action: PlayerAction,
        bank_service: BankService,
    ) -> None:
        """根据 PlayerAction 批量处理贷款审批。"""
        bank = bank_service.banks.get(action.bank_name)
        if bank is None:
            console.print(f"[red]银行 '{action.bank_name}' 不存在[/]")
            return

        applications = bank_service.get_applications()
        if not applications:
            return

        bank_ledger = bank.get_component(LedgerComponent)
        available_cash = bank_ledger.cash

        for param in action.approvals:
            idx = param.application_index - 1
            if idx < 0 or idx >= len(applications):
                console.print(f"[yellow]贷款申请序号 {param.application_index} 无效，跳过[/]")
                continue

            app = applications[idx]
            amount = min(param.amount, available_cash)
            if amount <= 0:
                console.print(f"[yellow]银行现金不足，跳过申请 {param.application_index}[/]")
                continue

            offer = LoanOffer(
                bank=bank,
                applicant=app.applicant,
                amount=amount,
                rate=param.rate,
                term=param.term,
                repayment_type=param.repayment_type,
            )
            bank_service.add_offer(offer)
            available_cash -= amount
            console.print(
                f"[green]已批准申请 {param.application_index}: "
                f"金额={amount}, 利率={param.rate}, 期限={param.term}[/]"
            )

    def player_act_phase(self, bank_service: BankService) -> None:
        """执行玩家操作阶段：展示数据，获取一次 PlayerAction 并处理。"""
        console.print(self.render_economy_summary())
        console.print(self.render_company_table())
        console.print(self.render_folk_table())
        console.print(self.render_bank_summary(bank_service.banks))

        applications = bank_service.get_applications()
        company_names = self.game.company_service.companies
        console.print(self.render_loan_applications(applications, company_names))
        console.print()

        action = self.input_controller.get_action(
            "输入操作 (skip=跳过, approve <银行名> <序号:金额:利率:期限:还款方式> ...): "
        )

        if action.action_type == "approve_loans":
            self.handle_loan_approval(action, bank_service)

    # ── Service 接口方法 ──

    def update_phase(self) -> None:
        pass

    def sell_phase(self) -> None:
        pass

    def buy_phase(self) -> None:
        pass

    def product_phase(self) -> None:
        pass

    def plan_phase(self) -> None:
        pass

    def settlement_phase(self) -> None:
        pass

    def act_phase(self) -> None:
        pass
