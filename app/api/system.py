"""
系统管理 API（用户/部门/菜单/编码表）。

对应 PB base_sys.pbl 模块。
"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.services.system_service import SystemService
from app.utils.response import error_response, success_response

__all__ = ["system_bp"]

system_bp = Blueprint("system", __name__)
_service = SystemService()


# ---- 用户管理 ----


@system_bp.get("/users")
@login_required
def list_users():  # type: ignore[no-untyped-def]
    """获取用户列表。"""
    status = request.args.get("status")
    users = _service.list_users(status=status)
    return success_response(data=users)


@system_bp.get("/users/<user_cd>")
@login_required
def get_user(user_cd: str):  # type: ignore[no-untyped-def]
    """获取用户详情。"""
    user = _service.get_user(user_cd)
    if user is None:
        return error_response(message="用户不存在", code=404)
    return success_response(data=user)


# ---- 部门管理 ----


@system_bp.get("/departments")
@login_required
def list_departments():  # type: ignore[no-untyped-def]
    """获取部门列表。"""
    return success_response(data=_service.list_departments())


# ---- 用户组管理 ----


@system_bp.get("/groups")
@login_required
def list_groups():  # type: ignore[no-untyped-def]
    """获取用户组列表。"""
    return success_response(data=_service.list_groups())


@system_bp.get("/users/<user_cd>/groups")
@login_required
def get_user_groups(user_cd: str):  # type: ignore[no-untyped-def]
    """获取用户所属用户组。"""
    return success_response(data=_service.get_user_groups(user_cd))


# ---- 菜单管理 ----


@system_bp.get("/menus")
@login_required
def list_menus():  # type: ignore[no-untyped-def]
    """获取菜单树。"""
    return success_response(data=_service.list_menus())


# ---- 系统参数 ----


@system_bp.get("/sysparms")
@login_required
def list_sysparms():  # type: ignore[no-untyped-def]
    """获取系统参数列表。"""
    return success_response(data=_service.list_sysparms())


@system_bp.get("/sysparms/<parm_cd>")
@login_required
def get_sysparm(parm_cd: str):  # type: ignore[no-untyped-def]
    """获取指定系统参数。"""
    parm = _service.get_sysparm(parm_cd)
    if parm is None:
        return error_response(message="参数不存在", code=404)
    return success_response(data=parm)
