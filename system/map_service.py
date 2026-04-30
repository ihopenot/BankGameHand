from __future__ import annotations

from typing import Dict, List

from entity.map import Country, Plot


class MapService:
    """地图服务 - 管理国家、地块数据的加载和查询。"""

    def __init__(self) -> None:
        self.countries: Dict[str, Country] = {}
        self.plots: Dict[str, Plot] = {}

    def load_map(self, config: dict) -> None:
        """从配置字典加载国家和地块，校验相邻关系双向一致性。"""
        self.countries.clear()
        self.plots.clear()

        # 1. 创建 Country
        for item in config.get("countries", []):
            name = item["name"]
            self.countries[name] = Country(
                name=name,
                description=item.get("description", ""),
            )

        # 2. 创建 Plot（neighbors 暂存名称列表）
        neighbor_names: Dict[str, List[str]] = {}
        for item in config.get("plots", []):
            name = item["name"]
            country_name = item["country"]
            if country_name not in self.countries:
                raise ValueError(f"地块 '{name}' 引用了未定义的国家 '{country_name}'")
            country = self.countries[country_name]
            self.plots[name] = Plot(
                name=name,
                country=country,
                description=item.get("description", ""),
            )
            neighbor_names[name] = item.get("neighbors", [])

        # 3. 解析 neighbors 引用
        for plot_name, names in neighbor_names.items():
            plot = self.plots[plot_name]
            for n_name in names:
                if n_name not in self.plots:
                    raise ValueError(f"地块 '{plot_name}' 引用了未定义的相邻地块 '{n_name}'")
                plot.neighbors.append(self.plots[n_name])

        # 4. 校验双向一致性
        for plot_name, plot in self.plots.items():
            for neighbor in plot.neighbors:
                if plot not in neighbor.neighbors:
                    raise ValueError(
                        f"相邻关系不一致: '{plot_name}' 列出 '{neighbor.name}' 为邻居，"
                        f"但 '{neighbor.name}' 未列出 '{plot_name}'"
                    )

    def get_country(self, name: str) -> Country:
        """按名称获取国家。"""
        if name not in self.countries:
            raise KeyError(f"国家 '{name}' 不存在")
        return self.countries[name]

    def get_plot(self, name: str) -> Plot:
        """按名称获取地块。"""
        if name not in self.plots:
            raise KeyError(f"地块 '{name}' 不存在")
        return self.plots[name]

    def get_plots_by_country(self, country_name: str) -> List[Plot]:
        """获取某国家下所有地块。"""
        return [p for p in self.plots.values() if p.country.name == country_name]

    def get_neighbors(self, plot_name: str) -> List[Plot]:
        """获取地块的相邻地块列表。"""
        return self.get_plot(plot_name).neighbors

    def get_companies_in_plot(self, plot_name: str, companies: list) -> list:
        """获取某地块中所有公司。"""
        plot = self.get_plot(plot_name)
        return [c for c in companies if getattr(c, 'plot', None) is plot]

    def get_companies_in_country(self, country_name: str, companies: list) -> list:
        """获取某国家中所有公司。"""
        country_plots = self.get_plots_by_country(country_name)
        return [c for c in companies if getattr(c, 'plot', None) in country_plots]
