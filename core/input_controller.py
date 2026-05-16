from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from core.types import LoanApprovalParam, PlayerAction, RepaymentType

if TYPE_CHECKING:
    from game.game import Game


class PlayerInputController(ABC):
    """玩家输入控制器抽象基类。"""

    def on_game_start(self, game: Game) -> None:
        """游戏循环开始前调用。子类可重写以执行初始化（如启动网络服务）。"""

    def on_game_end(self, game: Game) -> None:
        """游戏循环结束后调用。子类可重写以执行清理（如通知客户端）。"""

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        """获取玩家原始输入。"""

    def get_action(self, prompt: str) -> PlayerAction:
        """获取并解析玩家操作指令。

        输入格式：
            skip / 空行              → 跳过回合
            approve <银行名> <序号>:<金额>:<利率>:<期限>:<还款方式> [...]
                                     → 批量审批贷款
                还款方式: 1=等额本金, 2=先息后本, 3=到期一次性
            rate <银行名> <利率万分比> → 设置存款利率

        示例：
            approve 银行A 1:50000:500:5:1 2:30000:800:3:2
            rate 银行A 100
        """
        raw = self.get_input(prompt).strip()
        if not raw or raw.lower() == "skip":
            return PlayerAction(action_type="skip")

        parts = raw.split()
        if parts[0].lower() == "approve" and len(parts) >= 3:
            bank_name = parts[1]
            approvals = _parse_approvals(parts[2:])
            return PlayerAction(
                action_type="approve_loans",
                bank_name=bank_name,
                approvals=approvals,
            )

        if parts[0].lower() == "rate" and len(parts) >= 3:
            bank_name = parts[1]
            deposit_rate = int(parts[2])
            return PlayerAction(
                action_type="set_deposit_rate",
                bank_name=bank_name,
                deposit_rate=deposit_rate,
            )

        return PlayerAction(action_type="skip")


_REPAYMENT_MAP = {
    "1": RepaymentType.EQUAL_PRINCIPAL,
    "2": RepaymentType.INTEREST_FIRST,
    "3": RepaymentType.BULLET,
}


def _parse_approvals(tokens: List[str]) -> List[LoanApprovalParam]:
    """解析审批参数列表。每个 token 格式: 序号:金额:利率:期限:还款方式"""
    result: List[LoanApprovalParam] = []
    for token in tokens:
        fields = token.split(":")
        if len(fields) < 4:
            continue
        try:
            index = int(fields[0])
            amount = int(fields[1])
            rate = int(fields[2])
            term = int(fields[3])
            repayment_type = _REPAYMENT_MAP.get(
                fields[4] if len(fields) > 4 else "1",
                RepaymentType.EQUAL_PRINCIPAL,
            )
        except (ValueError, IndexError):
            continue
        result.append(LoanApprovalParam(
            application_index=index,
            amount=amount,
            rate=rate,
            term=term,
            repayment_type=repayment_type,
        ))
    return result


class StdinInputController(PlayerInputController):
    """从标准输入读取玩家输入。"""

    def get_input(self, prompt: str) -> str:
        return input(prompt)
