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

        每个工厂各自从库存取料生产，产出合并后贴品质和品牌。
        品质 = tech_rank_ratio * tech_quality_weight + avg_material_quality * (1 - tech_quality_weight)

        Args:
            factory_type: 工厂类型。

        Returns:
            贴好品质和品牌的合并产出 GoodsBatch。
        """
        recipe = factory_type.recipe
        output_goods_type = recipe.output_goods_type

        # 1. 计算科技品质比
        my_tech = self.tech_values.get(recipe, 0)
        global_max = ProductorComponent.max_tech.get(recipe, 0)
        tech_rank_ratio: Radio = my_tech / global_max if global_max > 0 else 0.0

        # 2. 计算品牌
        brand = self.brand_values.get(output_goods_type, 0)

        # 3. 遍历工厂逐个生产，收集产出和原材料品质
        total_quantity = 0
        weighted_material_quality = 0.0
        for factory in self.factories.get(factory_type, []):
            if not factory.is_built:
                continue

            if recipe.input_goods_type is not None:
                demand = recipe.input_quantity * factory_type.base_production
                supply_batch = self.storage.require_goods(
                    recipe.input_goods_type, demand, recipe.input_quantity
                )
            else:
                # 原料层：传入空 GoodsBatch
                supply_batch = GoodsBatch(
                    goods_type=output_goods_type, quantity=0, quality=0.0, brand_value=0
                )

            output_batch = factory.produce(supply_batch)
            total_quantity += output_batch.quantity
            weighted_material_quality += output_batch.quality * output_batch.quantity

        # 4. 计算最终品质
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
