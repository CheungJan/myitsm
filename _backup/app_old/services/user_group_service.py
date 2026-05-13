"""
用户组与权限服务。
作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08
注意事项：整合分散的权限查询，提供统一权限服务；对应 PB app_system.pbl。
"""

from __future__ import annotations

from typing import Any

from app.repositories.user_group_repository import UserGroupRepository

__all__ = ["UserGroupService"]


class UserGroupService:
    """
    用户组与权限业务服务。

    功能概述：
        用户组管理、用户权限查询、菜单权限计算；
        对应 PB app_system.pbl 的 u_mc_groups, w_r_mc_groupright 等。
    """

    def __init__(self, user_group_repository: UserGroupRepository | None = None) -> None:
        """
        初始化服务。

        参数：
            user_group_repository: 用户组仓储实例，默认自动创建。
        """
        self._repo = user_group_repository or UserGroupRepository()

    def list_groups(self) -> list[dict[str, Any]]:
        """
        获取用户组列表。

        返回值：
            list[dict[str, Any]]: 用户组列表。
        """
        return self._repo.list_groups()

    def get_user_groups(self, user_id: str) -> list[dict[str, Any]]:
        """
        获取用户所属的用户组。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 用户组列表。
        """
        return self._repo.get_user_groups(user_id)

    def get_group_detail(self, group_cd: str) -> dict[str, Any] | None:
        """
        获取用户组详情（包含成员和权限）。

        参数：
            group_cd: 用户组编码。

        返回值：
            dict[str, Any] | None: 组详情或空。
        """
        groups = self._repo.list_groups()
        group = next((g for g in groups if g["group_code"] == group_cd), None)
        if group is None:
            return None

        users = self._repo.get_group_users(group_cd)
        rights = self._repo.get_group_rights(group_cd)

        return {
            "group_code": group["group_code"],
            "group_name": group["group_name"],
            "group_type": group["group_type"],
            "users": users,
            "rights": rights,
        }

    def get_user_menus_with_rights(self, user_id: str) -> list[dict[str, Any]]:
        """
        获取用户有权限的菜单列表（含权限级别）。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 菜单列表，含权限级别（scale）。
        """
        return self._repo.get_user_menu_rights(user_id)

    def check_menu_right(self, user_id: str, menu_code: str) -> dict[str, Any]:
        """
        检查用户对指定菜单的权限。

        参数：
            user_id: 用户编码。
            menu_code: 菜单编码。

        返回值：
            dict[str, Any]: 权限检查结果。
                - has_right: 是否有权限
                - scale: 权限级别（1-9，9最大）
        """
        menus = self._repo.get_user_menu_rights(user_id)
        menu = next((m for m in menus if m["menu_code"] == menu_code), None)

        if menu is None:
            return {"has_right": False, "scale": 0}

        return {"has_right": True, "scale": menu.get("scale", 1)}

    def build_user_menu_tree(self, user_id: str) -> list[dict[str, Any]]:
        """
        构建用户有权限的菜单树（层级结构）。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 菜单树结构。
        """
        menus = self._repo.get_user_menu_rights(user_id)

        # 构建层级结构
        menu_map: dict[str, dict[str, Any]] = {}
        for menu in menus:
            menu["children"] = []
            menu_map[menu["menu_code"]] = menu

        # 根节点列表
        roots: list[dict[str, Any]] = []

        for menu in menus:
            parent = menu.get("parent", "")
            if parent and parent in menu_map:
                menu_map[parent]["children"].append(menu)
            else:
                roots.append(menu)

        return roots
