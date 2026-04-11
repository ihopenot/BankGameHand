from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def _convert(value: Any) -> Any:
    """递归转换 dict 为 AttrDict，处理 list 中的嵌套。"""
    if isinstance(value, dict):
        return AttrDict(value)
    if isinstance(value, list):
        return [_convert(item) for item in value]
    return value


class AttrDict:
    """支持属性访问的字典，嵌套 dict 自动转为 AttrDict。"""

    def __init__(self, data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        raw = data or {}
        raw.update(kwargs)
        for key, value in raw.items():
            object.__setattr__(self, key, _convert(value))

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(f"No attribute '{name}'")

    def __getitem__(self, name: str) -> Any:
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            raise KeyError(name)

    def __setitem__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self.__dict__

    def __repr__(self) -> str:
        return f"AttrDict({self.__dict__})"


class ConfigManager:
    """单例配置管理器，读取 config 目录下所有 YAML 文件。"""

    _instance: Optional[ConfigManager] = None
    _sections: Dict[str, AttrDict]

    def __new__(cls) -> ConfigManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sections = {}
        return cls._instance

    def load(self, path: Optional[str] = None) -> None:
        """加载指定目录下所有 .yaml / .yml 文件。

        Args:
            path: 配置目录路径，默认为项目根目录下的 config/。
        """
        if path is None:
            path = str(Path(__file__).resolve().parent.parent / "config")

        config_dir = Path(path)
        if not config_dir.is_dir():
            raise FileNotFoundError(f"Config directory not found: {config_dir}")

        self._sections.clear()
        for file in sorted(config_dir.iterdir()):
            if file.suffix in (".yaml", ".yml"):
                with open(file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                section_name = file.stem
                self._sections[section_name] = AttrDict(data) if isinstance(data, dict) else AttrDict()

    def section(self, name: str) -> AttrDict:
        """获取指定名称的配置段。

        Args:
            name: 配置段名称（对应 yaml 文件名，不含扩展名）。

        Returns:
            对应的 AttrDict 配置对象。
        """
        if name not in self._sections:
            raise KeyError(f"Config section '{name}' not found")
        return self._sections[name]
