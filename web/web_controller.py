"""WebClient：Web 客户端，本地提供 HTTP 页面并代理 WebSocket 到游戏服务端。"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


class WebClient:
    """Web 客户端：本地 FastAPI 提供网页，WS /ws 双向代理到游戏服务端。"""

    def __init__(self, server_url: str) -> None:
        self.server_url = server_url
        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            html_path = STATIC_DIR / "index.html"
            if html_path.exists():
                return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
            return HTMLResponse(
                content="<h1>BankGameHand WebCli</h1><p>index.html not found</p>"
            )

        @self.app.websocket("/ws")
        async def websocket_proxy(client_ws: WebSocket):
            await client_ws.accept()
            try:
                async with websockets.connect(self.server_url) as server_ws:
                    await self._proxy(client_ws, server_ws)
            except websockets.ConnectionClosed:
                logger.info("Server connection closed")
            except WebSocketDisconnect:
                logger.info("Browser disconnected")
            except Exception:
                logger.exception("WebSocket proxy error")

    @staticmethod
    async def _proxy(
        client_ws: WebSocket,
        server_ws: websockets.WebSocketClientProtocol,
    ) -> None:
        """双向代理：浏览器 ↔ 游戏服务端。"""

        async def client_to_server():
            """浏览器 → 游戏服务端。"""
            try:
                while True:
                    data = await client_ws.receive_text()
                    await server_ws.send(data)
            except WebSocketDisconnect:
                pass

        async def server_to_client():
            """游戏服务端 → 浏览器。"""
            try:
                async for data in server_ws:
                    await client_ws.send_text(data)
            except websockets.ConnectionClosed:
                pass

        # 两个方向并行，任一结束则退出
        done, pending = await asyncio.wait(
            [
                asyncio.create_task(client_to_server()),
                asyncio.create_task(server_to_client()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """启动本地 HTTP + WS 代理服务。"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)
