"""
已开模块仓储。
作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08
注意事项：当前为内存实现；后续可按需扩展为 Redis/DB 持久化。
"""

from __future__ import annotations

import threading
import time
from typing import Any

__all__ = ["OpenedModulesRepository"]


class OpenedModulesRepository:
    """
    已开模块数据访问仓储。

    功能概述：
        跟踪用户当前打开的模块对象，支持增删查。
    """

    def __init__(self) -> None:
        """初始化内存存储与线程锁。"""
        self._lock = threading.Lock()
        self._modules: dict[str, list[dict[str, Any]]] = {}

    def list_modules(self, user_id: str) -> list[dict[str, Any]]:
        """
        获取用户已打开的模块列表。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 已开模块列表，按打开顺序排列。
        """
        with self._lock:
            modules = self._modules.get(user_id, [])
            return [
                {
                    "object": m["object"],
                    "object_index": m["object_index"],
                    "title": m["title"],
                    "opened_at": m["opened_at"],
                }
                for m in modules
            ]

    def add_module(
        self,
        user_id: str,
        object_name: str,
        title: str,
    ) -> dict[str, Any]:
        """
        添加已打开模块记录。

        参数：
            user_id: 用户编码。
            object_name: 对象名称（如 w_r_mc_user）。
            title: 窗口标题。

        返回值：
            dict[str, Any]: 添加后的模块信息，包含 object_index。
        """
        with self._lock:
            if user_id not in self._modules:
                self._modules[user_id] = []
            modules = self._modules[user_id]
            existing = next(
                (m for m in modules if m["object"] == object_name),
                None,
            )
            if existing:
                return {
                    "object": existing["object"],
                    "object_index": existing["object_index"],
                    "title": existing["title"],
                    "opened_at": existing["opened_at"],
                }
            new_index = len(modules) + 1
            new_module = {
                "object": object_name,
                "object_index": new_index,
                "title": title,
                "opened_at": time.time(),
            }
            modules.append(new_module)
            return {
                "object": new_module["object"],
                "object_index": new_module["object_index"],
                "title": new_module["title"],
                "opened_at": new_module["opened_at"],
            }

    def remove_module(self, user_id: str, object_name: str) -> bool:
        """
        移除已打开模块记录。

        参数：
            user_id: 用户编码。
            object_name: 对象名称。

        返回值：
            bool: 是否成功移除。
        """
        with self._lock:
            modules = self._modules.get(user_id, [])
            for i, m in enumerate(modules):
                if m["object"] == object_name:
                    modules.pop(i)
                    self._reindex(modules)
                    return True
            return False

    def remove_active(self, user_id: str) -> dict[str, Any] | None:
        """
        移除当前活动（最后打开）模块。

        参数：
            user_id: 用户编码。

        返回值：
            dict[str, Any] | None: 被移除的模块信息或空。
        """
        with self._lock:
            modules = self._modules.get(user_id, [])
            if not modules:
                return None
            removed = modules.pop()
            self._reindex(modules)
            return {
                "object": removed["object"],
                "object_index": removed["object_index"],
                "title": removed["title"],
                "opened_at": removed["opened_at"],
            }

    def _reindex(self, modules: list[dict[str, Any]]) -> None:
        """重新索引模块列表。"""
        for i, m in enumerate(modules, start=1):
            m["object_index"] = i
