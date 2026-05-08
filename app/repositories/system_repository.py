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
    def get_items(page: int = 1, per_page: int = 20) -> tuple[list[Item], int]:
        q = db.session.query(Item).order_by(Item.item_cd)
        total = q.count()
        return q.offset((page - 1) * per_page).limit(per_page).all(), total

    @staticmethod
    def get_item(item_cd: str) -> Item | None:
        return db.session.get(Item, item_cd)

    @staticmethod
    def create_item(data: dict[str, Any]) -> Item:
        item = Item(**data)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def update_item(record: Item, data: dict[str, Any]) -> Item:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_item(record: Item) -> None:
        db.session.delete(record)
        db.session.commit()

    @staticmethod
    def get_customers(page: int = 1, per_page: int = 20) -> tuple[list[Customer], int]:
        q = db.session.query(Customer).order_by(Customer.cust_cd)
        total = q.count()
        return q.offset((page - 1) * per_page).limit(per_page).all(), total

    @staticmethod
    def get_customer(cust_cd: str) -> Customer | None:
        return db.session.get(Customer, cust_cd)

    @staticmethod
    def create_customer(data: dict[str, Any]) -> Customer:
        c = Customer(**data)
        db.session.add(c)
        db.session.commit()
        return c

    @staticmethod
    def update_customer(record: Customer, data: dict[str, Any]) -> Customer:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_customer(record: Customer) -> None:
        db.session.delete(record)
        db.session.commit()

    @staticmethod
    def get_eid_list(page: int = 1, per_page: int = 20) -> tuple[list[Eid], int]:
        q = db.session.query(Eid).order_by(Eid.eid)
        total = q.count()
        return q.offset((page - 1) * per_page).limit(per_page).all(), total

    @staticmethod
    def get_eid(itemcd: str, eid_val: str) -> Eid | None:
        return db.session.get(Eid, (itemcd, eid_val))

    @staticmethod
    def create_eid(data: dict[str, Any]) -> Eid:
        e = Eid(**data)
        db.session.add(e)
        db.session.commit()
        return e

    @staticmethod
    def update_eid(itemcd: str, eid_val: str, data: dict[str, Any]) -> Eid | None:
        r = db.session.get(Eid, (itemcd, eid_val))
        if r:
            for k, v in data.items():
                setattr(r, k, v)
            db.session.commit()
        return r

    @staticmethod
    def delete_eid(itemcd: str, eid_val: str) -> bool:
        r = db.session.get(Eid, (itemcd, eid_val))
        if r:
            db.session.delete(r)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_cust_pos_rl(page: int = 1, per_page: int = 20) -> tuple[list[CustPosRl], int]:
        q = db.session.query(CustPosRl).order_by(CustPosRl.eid)
        total = q.count()
        return q.offset((page - 1) * per_page).limit(per_page).all(), total
