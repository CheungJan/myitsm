"""
主框架菜单服务。
作者：Cascade
创建时间：2026-03-24
变更时间：2026-03-24
注意事项：事务边界在服务层管理，当前为只读场景。
"""

from __future__ import annotations

from typing import Any

from app.repositories.menu_repository import MenuRepository
from app.repositories.opened_modules_repository import OpenedModulesRepository

__all__ = ["ShellService"]


class ShellService:
    """
    主框架菜单业务服务。

    功能概述：
        对菜单数据进行业务编排并返回 API 友好结构；
        管理已打开模块的生命周期。
    """

    def __init__(
        self,
        menu_repository: MenuRepository | None = None,
        opened_modules_repository: OpenedModulesRepository | None = None,
    ) -> None:
        """
        初始化菜单服务。

        参数：
            menu_repository: 菜单仓储实例，默认自动创建。
            opened_modules_repository: 已开模块仓储实例，默认自动创建。
        """
        self._menu_repository = menu_repository or MenuRepository()
        self._opened_modules_repository = opened_modules_repository or OpenedModulesRepository()

    def list_menus(self, user_id: str) -> dict[str, list[dict[str, Any]]]:
        """
        获取菜单列表。

        参数：
            user_id: 用户编码。

        返回值：
            dict[str, list[dict[str, Any]]]: 菜单与常用菜单结构。
        """
        rows = self._menu_repository.fetch_menus(user_id=user_id)
        user_menu_rows = self._menu_repository.fetch_user_menus(user_id=user_id)
        user_menu_codes = {row["MenuCd"] for row in user_menu_rows}

        all_menus = [
            {
                "menu_code": row["MenuCd"],
                "menu_name": row["MenuNm"],
                "parent_code": row["Parent"],
                "level_code": row["LevelCd"],
                "child_flag": row["ChildFlg"],
                "order_no": row["OrdNo"],
                "picture_name": row["PicName"],
                "exe_path": row["ExePath"],
                "open_flag": row["OpenFlg"],
            }
            for row in rows
        ]

        recent_menus = [item for item in all_menus if item["menu_code"] in user_menu_codes]
        return {"all_menus": all_menus, "recent_menus": recent_menus}

    def get_open_object_info(self, user_id: str, menu_code: str) -> dict[str, Any] | None:
        """
        根据菜单编码返回打开对象所需信息。

        参数：
            user_id: 用户编码。
            menu_code: 菜单编码。

        返回值：
            dict[str, Any] | None: 可打开对象信息，若不可打开返回空。
        """
        row = self._menu_repository.get_menu_by_code(menu_code=menu_code, user_id=user_id)
        if row is None:
            return None
        if row["ChildFlg"] != "0":
            return None
        exe_path = row["ExePath"]
        if exe_path is None or str(exe_path).strip() == "":
            return None

        return {
            "title": row["MenuNm"],
            "object": exe_path,
            "picture": row["PicName"],
            "multi_open": row["OpenFlg"] == "1",
        }

    def list_opened_modules(self, user_id: str) -> list[dict[str, Any]]:
        """
        获取用户已打开的模块列表。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 已开模块列表。
        """
        return self._opened_modules_repository.list_modules(user_id=user_id)

    def open_object(
        self,
        user_id: str,
        menu_code: str,
        multi_open: bool = False,
    ) -> dict[str, Any] | None:
        """
        打开对象并记录到已开模块列表。

        参数：
            user_id: 用户编码。
            menu_code: 菜单编码。
            multi_open: 是否允许多开。

        返回值：
            dict[str, Any] | None: 打开的对象信息或空（若不可打开）。
        """
        info = self.get_open_object_info(user_id=user_id, menu_code=menu_code)
        if info is None:
            return None

        object_name = info["object"]
        opened = self._opened_modules_repository.list_modules(user_id=user_id)
        existing = next((m for m in opened if m["object"] == object_name), None)

        if existing and not multi_open:
            return {
                "action": "activated",
                "object": existing["object"],
                "title": existing["title"],
                "object_index": existing["object_index"],
            }

        new_module = self._opened_modules_repository.add_module(
            user_id=user_id,
            object_name=object_name,
            title=info["title"],
        )
        return {
            "action": "opened",
            "object": new_module["object"],
            "title": new_module["title"],
            "object_index": new_module["object_index"],
            "picture": info["picture"],
            "multi_open": info["multi_open"],
        }

    def close_object(self, user_id: str, object_name: str) -> bool:
        """
        关闭指定对象。

        参数：
            user_id: 用户编码。
            object_name: 对象名称。

        返回值：
            bool: 是否成功关闭。
        """
        return self._opened_modules_repository.remove_module(
            user_id=user_id,
            object_name=object_name,
        )

    def close_active_object(self, user_id: str) -> dict[str, Any] | None:
        """
        关闭当前活动对象（最后打开的模块）。

        参数：
            user_id: 用户编码。

        返回值：
            dict[str, Any] | None: 被关闭的模块信息或空。
        """
        return self._opened_modules_repository.remove_active(user_id=user_id)
