"""系统管理数据访问层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.master import CustPosRl, Customer, Eid, Item
from app.models.system import Department, Group, Menu, SysParm, User, UserGroup


class SystemRepository:
    """系统管理 Repository。"""

    @staticmethod
    def get_users(status: str | None = None) -> list[User]:
        """获取用户列表。"""
        query = db.session.query(User)
        if status:
            query = query.filter(User.status == status)
        return list(query.order_by(User.user_cd).all())

    @staticmethod
    def get_user_by_cd(user_cd: str) -> User | None:
        """按编码获取用户。"""
        return db.session.get(User, user_cd)

    @staticmethod
    def get_departments() -> list[Department]:
        """获取部门列表。"""
        return list(db.session.query(Department).order_by(Department.dept_cd).all())

    @staticmethod
    def get_groups() -> list[Group]:
        """获取用户组列表。"""
        return list(db.session.query(Group).order_by(Group.group_cd).all())

    @staticmethod
    def get_user_groups(user_cd: str) -> list[dict[str, Any]]:
        """获取用户所属用户组。"""
        user_groups = db.session.query(UserGroup).filter(UserGroup.user_cd == user_cd).all()
        return [{"user_cd": ug.user_cd, "group_cd": ug.group_cd} for ug in user_groups]

    @staticmethod
    def get_menus() -> list[Menu]:
        """获取有效菜单列表。"""
        return list(
            db.session.query(Menu).filter(Menu.status == "1").order_by(Menu.menu_order).all()
        )

    @staticmethod
    def get_sysparms() -> list[SysParm]:
        """获取系统参数列表。"""
        return list(db.session.query(SysParm).order_by(SysParm.parm_cd).all())

    @staticmethod
    def get_sysparm_by_cd(parm_cd: str) -> SysParm | None:
        """按编码获取系统参数。"""
        return db.session.get(SysParm, parm_cd)

    # ——— 基础数据查询 ———

    @staticmethod
    def get_items(page: int = 1, per_page: int = 20) -> list[Item]:
        q = db.session.query(Item).order_by(Item.item_cd)
        return q.offset((page - 1) * per_page).limit(per_page).all()

    @staticmethod
    def get_customers(page: int = 1, per_page: int = 20) -> list[Customer]:
        q = db.session.query(Customer).order_by(Customer.cust_cd)
        return q.offset((page - 1) * per_page).limit(per_page).all()

    @staticmethod
    def get_eid_list(page: int = 1, per_page: int = 20) -> list[Eid]:
        q = db.session.query(Eid).order_by(Eid.eid)
        return q.offset((page - 1) * per_page).limit(per_page).all()

    @staticmethod
    def get_cust_pos_rl(page: int = 1, per_page: int = 20) -> list[CustPosRl]:
        q = db.session.query(CustPosRl).order_by(CustPosRl.eid)
        return q.offset((page - 1) * per_page).limit(per_page).all()
