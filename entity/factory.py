from __future__ import annotations

from typing import ClassVar, Dict, List, Optional

from core.config import ConfigManager
from core.types import Money
from entity.goods import GoodsBatch, GoodsType


class Recipe:
    """配方定义：描述输入输出转化关系。"""

    recipes: ClassVar[Dict[str, "Recipe"]] = {}

    def __init__(
        self,
        input_goods_type: Optional[GoodsType],
        input_quantity: int,
        output_goods_type: GoodsType,
        output_quantity: int,
        tech_quality_weight: float,
    ) -> None:
        self.input_goods_type = input_goods_type
        self.input_quantity = input_quantity
        self.output_goods_type = output_goods_type
        self.output_quantity = output_quantity
        self.tech_quality_weight = tech_quality_weight


class FactoryType:
    """工厂类型定义：产能和经济属性。"""

    factory_types: ClassVar[Dict[str, "FactoryType"]] = {}

    def __init__(
        self,
        recipe: Recipe,
        labor_demand: int,
        build_cost: Money,
        maintenance_cost: Money,
        build_time: int,
    ) -> None:
        self.recipe = recipe
        self.labor_demand = labor_demand
        self.build_cost = build_cost
        self.maintenance_cost = maintenance_cost
        self.build_time = build_time


class Factory:
    """工厂运行时实例。"""

    def __init__(self, factory_type: FactoryType, build_remaining: int) -> None:
        self.factory_type = factory_type
        self.build_remaining = build_remaining

    @property
    def is_built(self) -> bool:
        return self.build_remaining <= 0

    def tick_build(self) -> None:
        """建造进度推进一回合。"""
        if self.build_remaining > 0:
            self.build_remaining -= 1

    def produce(self, supply: GoodsBatch, labor_points: int = 0) -> GoodsBatch:
        """计算一回合产出。

        Args:
            supply: 输入原料批次（原料层传 quantity=0 的空批次）。
            labor_points: 本台工厂分配到的劳动力点数。

        Returns:
            产出 GoodsBatch，品质为原材料品质（原料层为 0.0），品牌留空。
        """
        if not self.is_built:
            raise RuntimeError("Factory is not built yet")

        recipe = self.factory_type.recipe
        output_type = recipe.output_goods_type
        labor_demand = self.factory_type.labor_demand

        # 劳动力充足率
        if labor_demand <= 0:
            staffing_ratio = 1.0
        else:
            staffing_ratio = min(labor_points / labor_demand, 1.0)

        if recipe.input_goods_type is None:
            # 原料层：产出受 staffing 约束
            output_qty = int(recipe.output_quantity * staffing_ratio)
            return GoodsBatch(
                goods_type=output_type,
                quantity=output_qty,
                quality=0.0,
                brand_value=0,
            )

        if supply.quantity <= 0:
            return GoodsBatch(
                goods_type=output_type, quantity=0, quality=0.0, brand_value=0
            )

        # 木桶效应：取原料和劳动力的最小值
        material_ratio = min(supply.quantity / recipe.input_quantity, 1.0)
        effective_ratio = min(material_ratio, staffing_ratio)
        output_qty = int(recipe.output_quantity * effective_ratio)

        return GoodsBatch(
            goods_type=output_type, quantity=output_qty, quality=supply.quality, brand_value=0
        )


def load_recipes() -> Dict[str, Recipe]:
    """从配置加载所有配方，返回 {name: Recipe} 字典。"""
    config = ConfigManager()
    goods_types = GoodsType.types
    section = config.section("goods")
    result: Dict[str, Recipe] = {}
    for item in section.recipes:
        input_gt = goods_types[item.input] if item.input is not None else None
        recipe = Recipe(
            input_goods_type=input_gt,
            input_quantity=item.input_quantity,
            output_goods_type=goods_types[item.output],
            output_quantity=item.output_quantity,
            tech_quality_weight=item.tech_quality_weight,
        )
        result[item.name] = recipe
    Recipe.recipes = result
    return result


def load_factory_types() -> Dict[str, FactoryType]:
    """从配置加载所有工厂类型，返回 {name: FactoryType} 字典。"""
    config = ConfigManager()
    recipes = Recipe.recipes
    section = config.section("goods")
    result: Dict[str, FactoryType] = {}
    for item in section.factory_types:
        ft = FactoryType(
            recipe=recipes[item.recipe],
            labor_demand=item.labor_demand,
            build_cost=item.build_cost,
            maintenance_cost=item.maintenance_cost,
            build_time=item.build_time,
        )
        result[item.name] = ft
    FactoryType.factory_types = result
    return result
