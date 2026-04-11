from abc import abstractmethod

from core.base_model import BaseModel
from core.types import Rate


class EconomyModel(BaseModel):
    """经济周期模型抽象基类，继承自 BaseModel。"""

    @abstractmethod
    def calculate(self, t: int) -> Rate:
        """根据当前轮次计算经济周期指数。

        Args:
            t: 当前游戏轮次

        Returns:
            Rate 类型的经济周期指数
        """
        ...
