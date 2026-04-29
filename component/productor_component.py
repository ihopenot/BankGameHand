from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, ClassVar, Dict, List

from component.base_component import BaseComponent
from component.storage_component import StorageComponent
from core.types import Money, Radio
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsBatch, GoodsType

if TYPE_CHECKING:
    from core.entity import Entity


class ProductorComponent(BaseComponent):
    """生产者组件：管理工厂列表，执行生产流程。依赖 StorageComponent。"""

    max_tech: ClassVar[Dict[Recipe, int]] = {}

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        outer.init_component(StorageComponent)
        self.storage: StorageComponent = outer.get_component(StorageComponent)
        self.tech_values: Dict[Recipe, int] = {}
        self.brand_values: Dict[GoodsType, int] = {}
        self.factories: Dict[FactoryType, List[Factory]] = defaultdict(list)
        self.prices: Dict[GoodsType, Money] = {}
        self.hired_labor_points: int = 0

    def update_max_tech(self) -> None:
        """用自身科技值更新全局 max_tech 表。"""
        for recipe, tech in self.tech_values.items():
            if tech > ProductorComponent.max_tech.get(recipe, 0):
                ProductorComponent.max_tech[recipe] = tech

    def init_prices(self) -> None:
        """根据已注册的工厂类型，用各产出 GoodsType.base_price 初始化定价表。"""
        for ft in self.factories:
            gt = ft.recipe.output_goods_type
            if gt not in self.prices:
                self.prices[gt] = gt.base_price

    def produce(self, factory_type: FactoryType) -> GoodsBatch:
        """对一个 FactoryType 下的所有工厂执行生产。

        每台工厂从 hired_labor_points 中取 labor_demand 点劳动力（先到先得），
        从 storage 取原料，调 factory.produce() 计算产出，合并后贴品质和品牌。
        """
        recipe = factory_type.recipe
        output_goods_type = recipe.output_goods_type

        # 科技品质比
        my_tech = self.tech_values.get(recipe, 0)
        global_max = ProductorComponent.max_tech.get(recipe, 0)
        tech_rank_ratio: Radio = my_tech / global_max if global_max > 0 else 0.0

        # 品牌
        brand = self.brand_values.get(output_goods_type, 0)

        total_quantity = 0
        weighted_material_quality = 0.0

        for factory in self.factories.get(factory_type, []):
            if not factory.is_built:
                continue

            # 取劳动力（先到先得）
            labor_demand = factory_type.labor_demand
            labor_points = min(self.hired_labor_points, labor_demand)
            self.hired_labor_points -= labor_points

            # 取原料
            if recipe.input_goods_type is not None:
                supply_batch = self.storage.require_goods(recipe.input_goods_type, recipe.input_quantity, 1)
            else:
                supply_batch = GoodsBatch(goods_type=output_goods_type, quantity=0, quality=0.0, brand_value=0)

            # 工厂自己算产出（含原料比和劳动力比）
            output_batch = factory.produce(supply_batch, labor_points=labor_points)
            total_quantity += output_batch.quantity
            weighted_material_quality += output_batch.quality * output_batch.quantity

        # 品质混合
        if recipe.input_goods_type is not None and total_quantity > 0:
            avg_material_quality = weighted_material_quality / total_quantity
            w = recipe.tech_quality_weight
            output_quality = tech_rank_ratio * w + avg_material_quality * (1 - w)
        else:
            output_quality = tech_rank_ratio

        return GoodsBatch(
            goods_type=output_goods_type,
            quantity=total_quantity,
            quality=output_quality,
            brand_value=brand,
        )

    def produce_all(self) -> None:
        """枚举所有 FactoryType，依次生产并将产出存入库存。"""
        for factory_type in self.factories:
            batch = self.produce(factory_type)
            if batch.quantity > 0:
                self.storage.add_batch(batch)
