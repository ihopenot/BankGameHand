from __future__ import annotations

from typing import TYPE_CHECKING, List

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.input_controller import StdinInputController
from core.types import RATE_SCALE
from system.service import Service

if TYPE_CHECKING:
    from game.game import Game


class PlayerService(Service):
    """玩家操作服务：展示经济数据，处理玩家输入。"""

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.input_controller = StdinInputController()

    def format_economy_summary(self) -> str:
        """格式化宏观经济摘要。"""
        index_ratio = self.game.economy_service.economy_index / RATE_SCALE
        lines = [
            f"========== 第 {self.game.round} / {self.game.total_rounds} 回合 ==========",
            f"经济指数: {index_ratio:.4f}",
        ]
        return "\n".join(lines)

    def format_company_table(self) -> str:
        """格式化所有公司的财务概览表格。"""
        header = f"{'公司名':<16}{'工厂类型':<16}{'现金':>12}{'库存':<20}{'应收款':>12}{'应付款':>12}"
        sep = "-" * len(header)
        rows: List[str] = [header, sep]

        for name, company in self.game.company_service.companies.items():
            ledger = company.get_component(LedgerComponent)
            storage = company.get_component(StorageComponent)

            cash = ledger.cash if ledger else 0
            receivables = ledger.total_receivables() if ledger else 0
            payables = ledger.total_payables() if ledger else 0

            # 工厂类型
            pc = company.get_component(ProductorComponent)
            ft_parts: List[str] = []
            if pc:
                for ft in pc.factories:
                    ft_parts.append(ft.recipe.output_goods_type.name)
            ft_str = ", ".join(ft_parts) if ft_parts else "-"

            # 汇总库存信息
            inv_parts: List[str] = []
            if storage:
                for gt, batches in storage.inventory.items():
                    total_qty = sum(b.quantity for b in batches)
                    if total_qty > 0:
                        inv_parts.append(f"{gt.name} x{total_qty}")
            inv_str = ", ".join(inv_parts) if inv_parts else "-"

            rows.append(f"{name:<16}{ft_str:<16}{cash:>12}{inv_str:<20}{receivables:>12}{payables:>12}")

        return "\n".join(rows)

    def player_act_phase(self) -> None:
        """执行玩家操作阶段：展示数据，等待玩家输入。"""
        print(self.format_economy_summary())
        print()
        print(self.format_company_table())
        print()

        while True:
            cmd = self.input_controller.get_input("输入操作 (skip=跳过回合): ").strip().lower()
            if cmd in ("skip", ""):
                return
            print("无法识别的命令，请输入 skip 或直接回车跳过回合")

    # ── Service 接口方法（PlayerService 只在 player_act 阶段活跃）──

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
