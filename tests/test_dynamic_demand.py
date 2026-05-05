"""居民动态需求机制测试。"""

import math
from pathlib import Path
from unittest.mock import patch

import pytest

from core.config import ConfigManager
from entity.goods import GoodsType, load_goods_types


@pytest.fixture(autouse=True)
def _load_config():
    """确保配置和 GoodsType 已加载。"""
    ConfigManager._instance = None
    ConfigManager().load(str(Path(__file__).parent / "config_integration"))
    GoodsType.types.clear()
    load_goods_types()
    yield
    ConfigManager._instance = None


class TestFolkDemandAttributes:
    """Folk 实体应有 last_spending 和 demand_multiplier 属性。"""

    def test_folk_has_last_spending(self) -> None:
        from entity.folk import Folk
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
        )
        assert folk.last_spending == 0

    def test_folk_has_demand_multiplier(self) -> None:
        from entity.folk import Folk
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
        )
        assert folk.demand_multiplier == 1.0
