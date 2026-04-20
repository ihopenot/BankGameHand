"""WebClient 单元测试。"""
from __future__ import annotations

from starlette.testclient import TestClient


class TestWebClientHTTP:
    def test_get_root_returns_html(self):
        from web.web_controller import WebClient
        client = WebClient(server_url="ws://localhost:9999")
        tc = TestClient(client.app)
        resp = tc.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "BankGameHand" in resp.text


class TestServerInputController:
    def test_parse_action_skip(self):
        from web.server_input_controller import ServerInputController
        action = ServerInputController._parse_action({"action_type": "skip"})
        assert action.action_type == "skip"
        assert action.approvals == []

    def test_parse_action_approve(self):
        from web.server_input_controller import ServerInputController
        action = ServerInputController._parse_action({
            "action_type": "approve_loans",
            "bank_name": "银行A",
            "approvals": [{
                "application_index": 1,
                "amount": 50000,
                "rate": 500,
                "term": 5,
                "repayment_type": "equal_principal",
            }],
        })
        assert action.action_type == "approve_loans"
        assert action.bank_name == "银行A"
        assert len(action.approvals) == 1
        assert action.approvals[0].amount == 50000

    def test_parse_action_empty(self):
        from web.server_input_controller import ServerInputController
        action = ServerInputController._parse_action({})
        assert action.action_type == "skip"

    def test_on_game_start_creates_server(self):
        from web.server_input_controller import ServerInputController
        from unittest.mock import MagicMock
        import socket
        # Find a free port
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        ctrl = ServerInputController("127.0.0.1", port)
        mock_game = MagicMock()
        ctrl.on_game_start(mock_game)
        # Verify the server is listening
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass  # connection succeeded

    def test_submit_action_unblocks_get_action(self):
        import threading
        import time
        from web.server_input_controller import ServerInputController
        from core.types import PlayerAction
        import socket

        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]

        ctrl = ServerInputController("127.0.0.1", port)
        # Don't start WS server; directly test the event mechanism
        result = []

        def bg():
            # Simulate get_action without broadcast (no game set)
            ctrl._action_event.clear()
            ctrl._pending_action = None
            ctrl._action_event.wait(timeout=2)
            result.append(ctrl._pending_action)

        t = threading.Thread(target=bg)
        t.start()
        time.sleep(0.05)

        ctrl._pending_action = PlayerAction(action_type="skip")
        ctrl._action_event.set()

        t.join(timeout=2)
        assert len(result) == 1
        assert result[0].action_type == "skip"
