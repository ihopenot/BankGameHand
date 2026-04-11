from abc import ABC, abstractmethod


class BaseModel(ABC):
    """所有模型（经济模型、未来其他模型）的通用抽象基类。

    子类必须定义类变量 model_name，用于注册表自动识别。
    """

    model_name: str

    @abstractmethod
    def get_state(self) -> dict:
        """返回模型内部状态，用于调试和存档。"""
        ...
