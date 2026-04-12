"""全局 pytest 配置：防止测试中调用真实的 input()。"""
from __future__ import annotations

import pytest

from core.input_controller import StdinInputController


@pytest.fixture(autouse=True)
def _no_real_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    """将 StdinInputController.get_input 替换为直接返回 'skip'，
    避免测试环境中读取 stdin 导致 OSError。"""
    monkeypatch.setattr(StdinInputController, "get_input", lambda self, prompt: "skip")
