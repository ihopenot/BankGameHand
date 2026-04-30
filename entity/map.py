from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Country:
    """国家数据模型。"""
    name: str
    description: str = ""


@dataclass
class Plot:
    """地块数据模型。"""
    name: str
    country: Country
    description: str = ""
    neighbors: List[Plot] = field(default_factory=list)
