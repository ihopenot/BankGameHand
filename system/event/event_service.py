from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from system.event.context import EventContext
from system.event.event_loader import Event, load_events

if TYPE_CHECKING:
    from game.game import Game

logger = logging.getLogger(__name__)


class EventService:
    """事件服务：加载事件定义，每回合扫描执行。"""

    def __init__(self, game: "Game", events_path: str | None = None) -> None:
        self.game = game
        if events_path is None:
            events_path = str(Path(__file__).resolve().parent.parent.parent / "config" / "events")
        self.events: List[Event] = load_events(events_path)
        logger.info(f"EventService loaded {len(self.events)} events from {events_path}")

    def build_global_context(self) -> Dict[str, Any]:
        """构建全局状态对象 _G，供事件表达式访问。"""
        from component.productor_component import ProductorComponent
        from entity.company.company import Company

        g: Dict[str, Any] = {
            "current_round": self.game.round,
        }

        # 收集所有公司
        all_companies = [
            comp.outer for comp in ProductorComponent.components
            if isinstance(comp.outer, Company)
        ]
        g["all_companies"] = all_companies

        # 收集所有国家
        if hasattr(self.game, "map_service"):
            g["all_countries"] = self.game.map_service.countries
            g["all_plots"] = self.game.map_service.plots
        else:
            g["all_countries"] = []
            g["all_plots"] = []

        return g

    def evaluate_events(self) -> None:
        """遍历所有事件定义，逐个求值。"""
        global_state = self.build_global_context()

        for event in self.events:
            try:
                context = EventContext(global_state)
                event.expr.evaluate(context)
            except Exception as e:
                logger.warning(f"Event '{event.id}' evaluation failed: {e}")
