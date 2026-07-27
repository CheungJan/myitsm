"""事件总线（审核意见 13 采纳）。

轻量级进程内事件总线，用于解耦 Service 间直接调用。

使用方式：
    # 发事件
    EventBus.emit("d2d_leave_store", {
        "maintenance_id": "MD000001",
        "custcd": "C0001",
        "posstatus": "01",
        "posstatus1": "11",
    })

    # 监听事件（在 listeners 模块注册）
    @EventBus.on("d2d_leave_store")
    def on_d2d_leave_sync_pos(payload):
        PosSyncService.sync(...)

设计要点：
- 进程内同步执行（Flask 请求上下文内，事务一致）
- 监听器异常不阻断主流程（记录日志，继续执行）
- 支持多监听器（按注册顺序执行）
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EventBus:
    """进程内事件总线（同步执行）。"""

    _listeners: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

    @classmethod
    def on(cls, event: str) -> Callable[[Callable[[dict[str, Any]], None]], None]:
        """注册事件监听器（装饰器）。

        Args:
            event: 事件名（如 "d2d_leave_store"）

        Returns:
            装饰器函数
        """

        def decorator(
            handler: Callable[[dict[str, Any]], None],
        ) -> Callable[[dict[str, Any]], None]:
            cls._listeners.setdefault(event, []).append(handler)
            logger.debug("EventBus listener registered: %s -> %s", event, handler.__name__)
            return handler

        return decorator

    @classmethod
    def emit(cls, event: str, payload: dict[str, Any]) -> None:
        """触发事件（同步执行所有监听器）。

        监听器异常不阻断主流程，记录日志后继续。

        Args:
            event: 事件名
            payload: 事件数据 dict
        """
        handlers = cls._listeners.get(event, [])
        if not handlers:
            logger.debug("EventBus no listener for: %s", event)
            return
        for handler in handlers:
            try:
                handler(payload)
            except Exception as e:
                logger.exception(
                    "EventBus listener %s failed for event %s: %s",
                    handler.__name__,
                    event,
                    e,
                )

    @classmethod
    def clear(cls) -> None:
        """清空所有监听器（仅用于测试）。"""
        cls._listeners.clear()
