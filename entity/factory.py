from __future__ import annotations

from typing import Dict, List, Optional

from core.config import ConfigManager
from core.types import Money
from entity.goods import GoodsBatch, GoodsType


class Recipe:
    """配方定义：描述输入输出转化关系。"""

    def __init__(
        self,
        input_goods_type: Optional[GoodsType],
        input_quantity: int,
        output_goods_type: GoodsType,
        output_quantity: int,
    ) -> None:
        self.input_goods_type = input_goods_type
        self.input_quantity = input_quantity
        self.output_goods_type = output_goods_type
        self.output_quantity = output_quantity


class FactoryType:
    """工厂类型定义：产能和经济属性。"""

    def __init__(
        self,
        recipe: Recipe,
        base_production: int,
        build_cost: Money,
        maintenance_cost: Money,
        build_time: int,
    ) -> None:
        self.recipe = recipe
        self.base_production = base_production
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

    def produce(self, supply: GoodsBatch) -> GoodsBatch:
        """计算一回合产出。

        Args:
            supply: 输入原料批次（原料层传 quantity=0 的空批次）。

        Returns:
            产出 GoodsBatch，品质和品牌留空（0.0, 0）。
        """
        if not self.is_built:
            raise RuntimeError("Factory is not built yet")

        recipe = self.factory_type.recipe
        base = self.factory_type.base_production
        output_type = recipe.output_goods_type

        if recipe.input_goods_type is None:
            # 原料层：无需输入，直接按基础产能生产
            return GoodsBatch(
                goods_type=output_type,
                quantity=base * recipe.output_quantity,
                quality=0.0,
                brand_value=0,
            )

        if supply.quantity <= 0:
            return GoodsBatch(
                goods_type=output_type, quantity=0, quality=0.0, brand_value=0
            )

        # 满产需求量 = recipe.input_quantity * base_production
        full_demand = recipe.input_quantity * base
        sufficiency = min(supply.quantity / full_demand, 1.0)

        # 良品率加成：1.0 + 原料品质 × 原料商品的加成上限
        quality_bonus = 1.0 + supply.quality * recipe.input_goods_type.bonus_ceiling

        output_qty = int(base * recipe.output_quantity * sufficiency * quality_bonus)

        return GoodsBatch(
            goods_type=output_type, quantity=output_qty, quality=0.0, brand_value=0
        )


def load_recipes(config: ConfigManager, goods_types: Dict[str, GoodsType]) -> Dict[str, Recipe]:
    """从配置加载所有配方，返回 {name: Recipe} 字典。"""
    section = config.section("goods")
    result: Dict[str, Recipe] = {}
    for item in section.recipes:
        input_gt = goods_types[item.input] if item.input is not None else None
        recipe = Recipe(
            input_goods_type=input_gt,
            input_quantity=item.input_quantity,
            output_goods_type=goods_types[item.output],
            output_quantity=item.output_quantity,
        )
        result[item.name] = recipe
    return result


def load_factory_types(config: ConfigManager, recipes: Dict[str, Recipe]) -> Dict[str, FactoryType]:
    """从配置加载所有工厂类型，返回 {name: FactoryType} 字典。"""
    section = config.section("goods")
    result: Dict[str, FactoryType] = {}
    for item in section.factory_types:
        ft = FactoryType(
            recipe=recipes[item.recipe],
            base_production=item.base_production,
            build_cost=item.build_cost,
            maintenance_cost=item.maintenance_cost,
            build_time=item.build_time,
        )
        result[item.name] = ft
    return result
