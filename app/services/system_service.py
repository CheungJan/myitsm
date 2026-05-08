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

    # ——— 基础数据 ———

    def list_items(self, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = self._repo.get_items(page, per_page)
        return {"items": [i.to_dict() for i in items], "total": total}

    def list_customers(self, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = self._repo.get_customers(page, per_page)
        return {"items": [c.to_dict() for c in items], "total": total}

    def list_eid(self, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = self._repo.get_eid_list(page, per_page)
        return {"items": [e.to_dict() for e in items], "total": total}

    def list_assets(self, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = self._repo.get_cust_pos_rl(page, per_page)
        return {"items": [a.to_dict() for a in items], "total": total}

    # ——— CRUD ———

    def create_item(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_item(data).to_dict()

    def update_item(self, item_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_item(item_cd)
        return self._repo.update_item(r, data).to_dict() if r else None

    def delete_item(self, item_cd: str) -> bool:
        r = self._repo.get_item(item_cd)
        if r: self._repo.delete_item(r); return True
        return False

    def create_customer(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_customer(data).to_dict()

    def update_customer(self, cust_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_customer(cust_cd)
        return self._repo.update_customer(r, data).to_dict() if r else None

    def delete_customer(self, cust_cd: str) -> bool:
        r = self._repo.get_customer(cust_cd)
        if r: self._repo.delete_customer(r); return True
        return False

    def create_eid(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_eid(data).to_dict()

    def update_eid(self, eid_val: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_eid(eid_val)
        return self._repo.update_eid(r, data).to_dict() if r else None

    def delete_eid(self, eid_val: str) -> bool:
        r = self._repo.get_eid(eid_val)
        if r: self._repo.delete_eid(r); return True
        return False
