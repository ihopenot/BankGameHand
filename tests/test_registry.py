from core.registry import Registry
from core.base_model import BaseModel
import pytest


class TestRegistry:
    def test_register_and_create(self):
        """注册一个类后通过 model_name 创建实例"""
        registry = Registry()

        class Foo(BaseModel):
            model_name = "foo"

            def __init__(self, value: int) -> None:
                self.value = value

            def get_state(self) -> dict:
                return {}

        registry.register(Foo)
        instance = registry.create("foo", value=42)
        assert isinstance(instance, Foo)
        assert instance.value == 42

    def test_decorator_register(self):
        """使用装饰器注册类"""
        registry = Registry()

        @registry.register
        class Bar(BaseModel):
            model_name = "bar"

            def get_state(self) -> dict:
                return {}

        assert Bar is not None
        instance = registry.create("bar")
        assert isinstance(instance, Bar)

    def test_create_unregistered_raises_key_error(self):
        """创建未注册的名称抛出 KeyError"""
        registry = Registry()
        with pytest.raises(KeyError):
            registry.create("nonexistent")

    def test_available_returns_registered_names(self):
        """available() 返回所有已注册名称"""
        registry = Registry()

        class A(BaseModel):
            model_name = "alpha"

            def get_state(self) -> dict:
                return {}

        class B(BaseModel):
            model_name = "beta"

            def get_state(self) -> dict:
                return {}

        registry.register(A)
        registry.register(B)
        names = registry.available()
        assert sorted(names) == ["alpha", "beta"]

    def test_available_empty(self):
        """空注册表返回空列表"""
        registry = Registry()
        assert registry.available() == []

    def test_decorator_returns_original_class(self):
        """装饰器不修改原始类"""
        registry = Registry()

        @registry.register
        class Original(BaseModel):
            model_name = "original"
            class_attr = "hello"

            def get_state(self) -> dict:
                return {}

        assert Original.class_attr == "hello"
