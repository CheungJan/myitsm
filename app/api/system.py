"""
系统管理 API（用户/部门/菜单/编码表）。

对应 PB base_sys.pbl 模块。
"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.extensions import db
from app.models.system import Department, Group, Menu, SysParm, User, UserGroup
from app.utils.response import error_response, success_response

__all__ = ["system_bp"]

system_bp = Blueprint("system", __name__)


# ---- 用户管理 ----


@system_bp.get("/users")
@login_required
def list_users():  # type: ignore[no-untyped-def]
    """获取用户列表。"""
    status = request.args.get("status")
    query = db.session.query(User)
    if status:
        query = query.filter(User.status == status)
    users = query.order_by(User.user_cd).all()
    return success_response(data=[u.to_dict() for u in users])


@system_bp.get("/users/<user_cd>")
@login_required
def get_user(user_cd: str):  # type: ignore[no-untyped-def]
    """获取用户详情。"""
    user = db.session.get(User, user_cd)
    if user is None:
        return error_response(message="用户不存在", code=404)
    return success_response(data=user.to_dict())


# ---- 部门管理 ----


@system_bp.get("/departments")
@login_required
def list_departments():  # type: ignore[no-untyped-def]
    """获取部门列表。"""
    depts = db.session.query(Department).order_by(Department.dept_cd).all()
    return success_response(data=[d.to_dict() for d in depts])


# ---- 用户组管理 ----


@system_bp.get("/groups")
@login_required
def list_groups():  # type: ignore[no-untyped-def]
    """获取用户组列表。"""
    groups = db.session.query(Group).order_by(Group.group_cd).all()
    return success_response(data=[g.to_dict() for g in groups])


@system_bp.get("/users/<user_cd>/groups")
@login_required
def get_user_groups(user_cd: str):  # type: ignore[no-untyped-def]
    """获取用户所属用户组。"""
    user_groups = db.session.query(UserGroup).filter(UserGroup.user_cd == user_cd).all()
    return success_response(
        data=[{"user_cd": ug.user_cd, "group_cd": ug.group_cd} for ug in user_groups]
    )


# ---- 菜单管理 ----


@system_bp.get("/menus")
@login_required
def list_menus():  # type: ignore[no-untyped-def]
    """获取菜单树。"""
    menus = db.session.query(Menu).filter(Menu.status == "1").order_by(Menu.menu_order).all()
    return success_response(data=[m.to_dict() for m in menus])


# ---- 系统参数 ----


@system_bp.get("/sysparms")
@login_required
def list_sysparms():  # type: ignore[no-untyped-def]
    """获取系统参数列表。"""
    parms = db.session.query(SysParm).order_by(SysParm.parm_cd).all()
    return success_response(data=[p.to_dict() for p in parms])


@system_bp.get("/sysparms/<parm_cd>")
@login_required
def get_sysparm(parm_cd: str):  # type: ignore[no-untyped-def]
    """获取指定系统参数。"""
    parm = db.session.get(SysParm, parm_cd)
    if parm is None:
        return error_response(message="参数不存在", code=404)
    return success_response(data=parm.to_dict())
