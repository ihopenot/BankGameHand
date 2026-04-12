from __future__ import annotations

from abc import ABC, abstractmethod


class PlayerInputController(ABC):
    """玩家输入控制器抽象基类。"""

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        """获取玩家输入。"""


class StdinInputController(PlayerInputController):
    """从标准输入读取玩家输入。"""

    def get_input(self, prompt: str) -> str:
        return input(prompt)
