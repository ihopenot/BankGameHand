"""全局 pytest 配置：防止测试中调用真实的 input()，确保配置已加载。"""
from __future__ import annotations

import pytest

from core.config import ConfigManager
from core.input_controller import StdinInputController


@pytest.fixture(autouse=True)
def _no_real_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    """将 StdinInputController.get_input 替换为直接返回 'skip'，
    避免测试环境中读取 stdin 导致 OSError。"""
    monkeypatch.setattr(StdinInputController, "get_input", lambda self, prompt: "skip")


@pytest.fixture(autouse=True)
def _ensure_config_loaded() -> None:
    """确保 ConfigManager 在每个测试前已加载默认配置。"""
    config = ConfigManager()
    if not config._sections:
        config.load()


@pytest.fixture(autouse=True)
def _clear_component_registries() -> None:
    """清理 BaseComponent 子类的 class-level components 列表，防止跨测试污染。"""
    from component.base_component import BaseComponent
    yield
    for cls in BaseComponent.__subclasses__():
        cls.components.clear()
