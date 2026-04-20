"""ServerInputController：服务端模式的玩家输入控制器，通过 WebSocket 与远程客户端通信。"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import TYPE_CHECKING, Optional, Set

import websockets

from core.input_controller import PlayerInputController
from core.types import (
    LoanApprovalParam,
    PlayerAction,
    RepaymentType,
)

if TYPE_CHECKING:
    from game.game import Game

logger = logging.getLogger(__name__)

_REPAYMENT_MAP = {
    "equal_principal": RepaymentType.EQUAL_PRINCIPAL,
    "interest_first": RepaymentType.INTEREST_FIRST,
    "bullet": RepaymentType.BULLET,
}


class ServerInputController(PlayerInputController):
    """服务端模式的输入控制器：内部运行 WebSocket server，
    get_action() 阻塞等待远程客户端提交操作。"""

    def __init__(self, host: str = "0.0.0.0", port: int = 9000) -> None:
        self._host = host
        self._port = port
        self._clients: Set[websockets.WebSocketServerProtocol] = set()
        self._action_event = threading.Event()
        self._pending_action: Optional[PlayerAction] = None
        self._game: Optional[Game] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._current_state: Optional[dict] = None  # 当前等待操作时的状态，供后连客户端获取
        self._waiting_for_action = False

    # ─── PlayerInputController 生命周期钩子 ───

    def on_game_start(self, game: Game) -> None:
        """游戏开始前：保存 Game 引用，启动 WebSocket server。"""
        self._game = game
        ready = threading.Event()
        t = threading.Thread(target=self._run_server, args=(ready,), daemon=True)
        t.start()
        ready.wait(timeout=5.0)
        logger.info("WebSocket server ready, waiting for clients on ws://%s:%d", self._host, self._port)

    def on_game_end(self, game: Game) -> None:
        """游戏结束后：通知所有客户端。"""
        self._broadcast_sync({"type": "game_end", "total_rounds": game.round})

    # ─── PlayerInputController 接口 ───

    def get_input(self, prompt: str) -> str:
        return "skip"

    def get_action(self, prompt: str) -> PlayerAction:
        """游戏主线程调用：推送状态给所有 WS 客户端，阻塞等待操作。"""
        self._current_state = self._build_game_state()
        self._waiting_for_action = True
        self._broadcast_sync({"type": "game_state", **self._current_state})

        self._action_event.clear()
        self._pending_action = None
        while not self._action_event.wait(timeout=0.5):
            pass
        self._waiting_for_action = False
        return self._pending_action  # type: ignore[return-value]

    # ─── 内部实现 ───

    def _run_server(self, ready: threading.Event) -> None:
        asyncio.run(self._serve(ready))

    async def _serve(self, ready: threading.Event) -> None:
        self._loop = asyncio.get_running_loop()
        async with websockets.serve(self._handler, self._host, self._port):
            ready.set()
            await asyncio.Future()  # run forever

    async def _handler(self, ws: websockets.WebSocketServerProtocol) -> None:
        self._clients.add(ws)
        logger.info("Client connected (%d total)", len(self._clients))
        # 如果当前正在等待操作，立即推送状态给新客户端
        if self._waiting_for_action and self._current_state:
            await ws.send(json.dumps({"type": "game_state", **self._current_state}, ensure_ascii=False))
        try:
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("type") == "player_action":
                    action = self._parse_action(msg.get("action", {}))
                    self._pending_action = action
                    self._action_event.set()
        except websockets.ConnectionClosed:
            pass
        finally:
            self._clients.discard(ws)
            logger.info("Client disconnected (%d remaining)", len(self._clients))

    def _build_game_state(self) -> dict:
        game = self._game
        ps = game.player_service
        applications = game.bank_service.get_applications()
        company_names = game.company_service.companies
        return {
            "economy": ps.economy_summary_dict(),
            "companies": ps.company_table_dict(),
            "folks": ps.folk_table_dict(),
            "banks": ps.bank_summary_dict(game.bank_service.banks),
            "loan_applications": ps.loan_applications_dict(applications, company_names),
            "metrics": ps.metrics_entities_dict(),
        }

    def _broadcast_sync(self, msg: dict) -> None:
        if not self._clients or not self._loop:
            return
        data = json.dumps(msg, ensure_ascii=False)
        future = asyncio.run_coroutine_threadsafe(
            self._async_broadcast(data), self._loop,
        )
        try:
            future.result(timeout=5.0)
        except Exception:
            logger.exception("Broadcast failed")

    async def _async_broadcast(self, data: str) -> None:
        if not self._clients:
            return
        await asyncio.gather(
            *(ws.send(data) for ws in self._clients),
            return_exceptions=True,
        )

    @staticmethod
    def _parse_action(action_data: dict) -> PlayerAction:
        action_type = action_data.get("action_type", "skip")
        if action_type == "skip":
            return PlayerAction(action_type="skip")

        bank_name = action_data.get("bank_name", "")
        approvals = []
        for item in action_data.get("approvals", []):
            repayment_str = item.get("repayment_type", "equal_principal")
            approvals.append(LoanApprovalParam(
                application_index=item.get("application_index", 0),
                amount=item.get("amount", 0),
                rate=item.get("rate", 0),
                term=item.get("term", 0),
                repayment_type=_REPAYMENT_MAP.get(repayment_str, RepaymentType.EQUAL_PRINCIPAL),
            ))
        return PlayerAction(
            action_type="approve_loans",
            bank_name=bank_name,
            approvals=approvals,
        )
