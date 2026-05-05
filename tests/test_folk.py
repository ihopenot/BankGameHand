"""Folk 实体测试。"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from component.ledger_component import LedgerComponent
from component.storage_component import StorageComponent
from entity.folk import DemandFeedbackParams
from entity.goods import GoodsType

_DEFAULT_DEMAND_FEEDBACK = DemandFeedbackParams(
    savings_target_ratio=5.0,
    max_adjustment=0.15,
    sensitivity=1.0,
    min_multiplier=0.3,
    max_multiplier=2.0,
)

_SPENDING_FLOW = {"tech": 1.0, "brand": 0.0, "maintenance": 0.0}


class TestFolkInit:
    """Folk 实体初始化测试。"""

    def test_folk_has_required_attributes(self) -> None:
        from entity.folk import Folk

        gt_food = GoodsType(name="食品", base_price=8000)
        base_demands = {
            gt_food: {"per_capita": 10, "sensitivity": 0.1},
        }
        folk = Folk(
            name="test_folk",
            population=6000,
            w_quality=0.95,
            w_brand=0.05,
            w_price=0.0,
            spending_flow=_SPENDING_FLOW,
            base_demands=base_demands,
            labor_participation_rate=0.6,
            labor_points_per_capita=1.0,
            demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
        )
        assert folk.population == 6000
        assert folk.w_quality == 0.95
        assert folk.w_brand == 0.05
        assert folk.base_demands is base_demands
        assert folk.labor_participation_rate == 0.6
        assert folk.labor_points_per_capita == 1.0

    def test_folk_labor_supply(self) -> None:
        """劳动力供给 = population * labor_participation_rate * labor_points_per_capita。"""
        from entity.folk import Folk

        folk = Folk(
            name="test_folk",
            population=6000,
            w_quality=0.95,
            w_brand=0.05,
            w_price=0.0,
            spending_flow=_SPENDING_FLOW,
            base_demands={},
            labor_participation_rate=0.6,
            labor_points_per_capita=1.0,
            demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
        )
        assert folk.labor_supply == int(6000 * 0.6 * 1.0)

    def test_folk_has_ledger_component(self) -> None:
        from entity.folk import Folk

        folk = Folk(name="test_folk", population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                     spending_flow=_SPENDING_FLOW, base_demands={},
                     labor_participation_rate=0.5, labor_points_per_capita=1.0,
                     demand_feedback=_DEFAULT_DEMAND_FEEDBACK)
        ledger = folk.get_component(LedgerComponent)
        assert ledger is not None

    def test_folk_has_storage_component(self) -> None:
        from entity.folk import Folk

        folk = Folk(name="test_folk", population=100, w_quality=0.5, w_brand=0.5, w_price=0.0,
                     spending_flow=_SPENDING_FLOW, base_demands={},
                     labor_participation_rate=0.5, labor_points_per_capita=1.0,
                     demand_feedback=_DEFAULT_DEMAND_FEEDBACK)
        storage = folk.get_component(StorageComponent)
        assert storage is not None

    def test_different_folk_have_different_demands(self) -> None:
        from entity.folk import Folk

        gt_food = GoodsType(name="食品", base_price=8000)
        gt_phone = GoodsType(name="手机", base_price=20000)

        folk_a = Folk(
            name="test_folk",
            population=6000,
            w_quality=0.95,
            w_brand=0.05,
            w_price=0.0,
            spending_flow=_SPENDING_FLOW,
            base_demands={
                gt_food: {"per_capita": 10, "sensitivity": 0.1},
                gt_phone: {"per_capita": 0, "sensitivity": 0.8},
            },
            labor_participation_rate=0.6,
            labor_points_per_capita=1.0,
            demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
        )
        folk_b = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.2,
            w_brand=0.8,
            w_price=0.0,
            spending_flow=_SPENDING_FLOW,
            base_demands={
                gt_food: {"per_capita": 10, "sensitivity": 0.05},
                gt_phone: {"per_capita": 8, "sensitivity": 0.4},
            },
            labor_participation_rate=0.7,
            labor_points_per_capita=1.5,
            demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
        )
        # folk_a 不需要手机
        assert folk_a.base_demands[gt_phone]["per_capita"] == 0
        # folk_b 需要手机
        assert folk_b.base_demands[gt_phone]["per_capita"] == 8


class TestLoadFolks:
    """从 ConfigManager 加载 Folk 列表的测试。"""

    def setup_method(self) -> None:
        GoodsType.types.clear()

    def teardown_method(self) -> None:
        GoodsType.types.clear()

    def test_load_folks_returns_list(self) -> None:
        from core.config import AttrDict
        from entity.folk import load_folks

        gt_food = GoodsType(name="食品", base_price=8000)
        GoodsType.types = {"食品": gt_food}

        config_data = AttrDict({
            "folks": [
                AttrDict({
                    "population": 6000,
                    "w_quality": 0.95,
                    "w_brand": 0.05,
                    "w_price": 0.0,
                    "labor_participation_rate": 0.6,
                    "labor_points_per_capita": 1.0,
                    "spending_flow": AttrDict({"tech": 0.6, "brand": 0.4, "maintenance": 0.5}),
                    "base_demands": AttrDict({
                        "食品": AttrDict({"per_capita": 10, "sensitivity": 0.1}),
                    }),
                    "demand_feedback": AttrDict({
                        "savings_target_ratio": 5.0,
                        "max_adjustment": 0.15,
                        "sensitivity": 1.0,
                        "min_multiplier": 0.3,
                        "max_multiplier": 2.0,
                    }),
                }),
                AttrDict({
                    "population": 1000,
                    "w_quality": 0.2,
                    "w_brand": 0.8,
                    "w_price": 0.0,
                    "labor_participation_rate": 0.7,
                    "labor_points_per_capita": 1.5,
                    "spending_flow": AttrDict({"tech": 0.4, "brand": 0.6, "maintenance": 0.5}),
                    "base_demands": AttrDict({
                        "食品": AttrDict({"per_capita": 5, "sensitivity": 0.05}),
                    }),
                    "demand_feedback": AttrDict({
                        "savings_target_ratio": 5.0,
                        "max_adjustment": 0.15,
                        "sensitivity": 1.0,
                        "min_multiplier": 0.3,
                        "max_multiplier": 2.0,
                    }),
                }),
            ],
        })

        with patch("entity.folk.ConfigManager") as mock_cm:
            mock_cm.return_value.section.return_value = config_data
            folks = load_folks()
        assert len(folks) == 2
        assert folks[0].population == 6000
        assert folks[0].labor_participation_rate == 0.6
        assert folks[0].labor_points_per_capita == 1.0
        assert folks[1].population == 1000
        assert folks[1].labor_participation_rate == 0.7

    def test_load_folks_maps_goods_types(self) -> None:
        from core.config import AttrDict
        from entity.folk import load_folks

        gt_food = GoodsType(name="食品", base_price=8000)
        gt_phone = GoodsType(name="手机", base_price=20000)
        GoodsType.types = {"食品": gt_food, "手机": gt_phone}

        config_data = AttrDict({
            "folks": [
                AttrDict({
                    "population": 3000,
                    "w_quality": 0.5,
                    "w_brand": 0.5,
                    "w_price": 0.0,
                    "labor_participation_rate": 0.6,
                    "labor_points_per_capita": 1.0,
                    "spending_flow": AttrDict({"tech": 1.0, "brand": 1.0, "maintenance": 1.0}),
                    "base_demands": AttrDict({
                        "食品": AttrDict({"per_capita": 10, "sensitivity": 0.2}),
                        "手机": AttrDict({"per_capita": 3, "sensitivity": 0.7}),
                    }),
                    "demand_feedback": AttrDict({
                        "savings_target_ratio": 5.0,
                        "max_adjustment": 0.15,
                        "sensitivity": 1.0,
                        "min_multiplier": 0.3,
                        "max_multiplier": 2.0,
                    }),
                }),
            ],
        })

        with patch("entity.folk.ConfigManager") as mock_cm:
            mock_cm.return_value.section.return_value = config_data
            folks = load_folks()
        folk = folks[0]
        # base_demands 的 key 应是 GoodsType 对象
        assert gt_food in folk.base_demands
        assert gt_phone in folk.base_demands
        assert folk.base_demands[gt_food]["per_capita"] == 10
        assert folk.base_demands[gt_phone]["per_capita"] == 3
