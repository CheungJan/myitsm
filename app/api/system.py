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


@system_bp.get("/items")
@login_required
def list_items():  # type: ignore[no-untyped-def]
    """物料列表（分页）。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    result = _service.list_items(page=page, per_page=per_page)
    return success_response(data={"items": result["items"], "total": result["total"]})


@system_bp.post("/items")
@login_required
def create_item():  # type: ignore[no-untyped-def]
    """新增物料。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_item(body), code=201)


@system_bp.put("/items/<item_cd>")
@login_required
def update_item(item_cd: str):  # type: ignore[no-untyped-def]
    """更新物料。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_item(item_cd, body)
    return success_response(data=r) if r else error_response("不存在", 404)


@system_bp.delete("/items/<item_cd>")
@login_required
def delete_item(item_cd: str):  # type: ignore[no-untyped-def]
    """删除物料。"""
    return success_response() if _service.delete_item(item_cd) else error_response("不存在", 404)


@system_bp.get("/customers")
@login_required
def list_customers():  # type: ignore[no-untyped-def]
    """客户列表（分页）。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    result = _service.list_customers(page=page, per_page=per_page)
    return success_response(data={"items": result["items"], "total": result["total"]})


@system_bp.post("/customers")
@login_required
def create_customer():  # type: ignore[no-untyped-def]
    """新增客户。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_customer(body), code=201)


@system_bp.put("/customers/<cust_cd>")
@login_required
def update_customer(cust_cd: str):  # type: ignore[no-untyped-def]
    """更新客户。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_customer(cust_cd, body)
    return success_response(data=r) if r else error_response("不存在", 404)


@system_bp.delete("/customers/<cust_cd>")
@login_required
def delete_customer(cust_cd: str):  # type: ignore[no-untyped-def]
    """删除客户。"""
    return success_response() if _service.delete_customer(cust_cd) else error_response("不存在", 404)


@system_bp.get("/eid")
@login_required
def list_eid():  # type: ignore[no-untyped-def]
    """EID 设备列表（分页）。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    result = _service.list_eid(page=page, per_page=per_page)
    return success_response(data={"items": result["items"], "total": result["total"]})


@system_bp.post("/eid")
@login_required
def create_eid():  # type: ignore[no-untyped-def]
    """新增 EID。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_eid(body), code=201)


@system_bp.put("/eid/<itemcd>/<eid_val>")
@login_required
def update_eid(itemcd: str, eid_val: str):  # type: ignore[no-untyped-def]
    """更新 EID（复合主键 itemcd+eid）。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_eid(itemcd, eid_val, body)
    return success_response(data=r) if r else error_response("不存在", 404)


@system_bp.delete("/eid/<itemcd>/<eid_val>")
@login_required
def delete_eid(itemcd: str, eid_val: str):  # type: ignore[no-untyped-def]
    """删除 EID（复合主键 itemcd+eid）。"""
    return success_response() if _service.delete_eid(itemcd, eid_val) else error_response("不存在", 404)


@system_bp.get("/assets")
@login_required
def list_assets():  # type: ignore[no-untyped-def]
    """资产台账列表（分页）。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    result = _service.list_assets(page=page, per_page=per_page)
    return success_response(data={"items": result["items"], "total": result["total"]})
