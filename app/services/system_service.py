"""系统管理业务服务。"""

from __future__ import annotations

from typing import Any

from app.repositories.system_repository import SystemRepository


class SystemService:
    """系统管理 Service。"""

    def __init__(self, repo: SystemRepository | None = None) -> None:
        self._repo = repo or SystemRepository()

    def list_users(self, status: str | None = None) -> list[dict[str, Any]]:
        """获取用户列表。"""
        users = self._repo.get_users(status=status)
        return [u.to_dict() for u in users]

    def get_user(self, user_cd: str) -> dict[str, Any] | None:
        """获取用户详情。"""
        user = self._repo.get_user_by_cd(user_cd)
        return user.to_dict() if user else None

    def list_departments(self) -> list[dict[str, Any]]:
        """获取部门列表。"""
        depts = self._repo.get_departments()
        return [d.to_dict() for d in depts]

    def list_groups(self) -> list[dict[str, Any]]:
        """获取用户组列表。"""
        groups = self._repo.get_groups()
        return [grp.to_dict() for grp in groups]

    def get_user_groups(self, user_cd: str) -> list[dict[str, Any]]:
        """获取用户所属用户组。"""
        return self._repo.get_user_groups(user_cd)

    def list_menus(self) -> list[dict[str, Any]]:
        """获取菜单列表。"""
        menus = self._repo.get_menus()
        return [m.to_dict() for m in menus]

    def list_sysparms(self) -> list[dict[str, Any]]:
        """获取系统参数列表。"""
        parms = self._repo.get_sysparms()
        return [p.to_dict() for p in parms]

    def get_sysparm(self, parm_cd: str) -> dict[str, Any] | None:
        """获取指定系统参数。"""
        parm = self._repo.get_sysparm_by_cd(parm_cd)
        return parm.to_dict() if parm else None
