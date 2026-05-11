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
    """获取用户列表，支持多条件筛选。"""
    status = request.args.get("status")
    user_cd = request.args.get("user_cd")
    user_nm = request.args.get("user_nm")
    dept_cd = request.args.get("dept_cd")
    users = _service.list_users(status=status, user_cd=user_cd, user_nm=user_nm, dept_cd=dept_cd)
    return success_response(data=users)


@system_bp.get("/users/<user_cd>")
@login_required
def get_user(user_cd: str):  # type: ignore[no-untyped-def]
    """获取用户详情。"""
    user = _service.get_user(user_cd)
    if user is None:
        return error_response(message="用户不存在", code=404)
    return success_response(data=user)


@system_bp.post("/users")
@login_required
def create_user():  # type: ignore[no-untyped-def]
    """新增用户。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_user(body), code=201)


@system_bp.put("/users/<user_cd>")
@login_required
def update_user(user_cd: str):  # type: ignore[no-untyped-def]
    """更新用户。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_user(user_cd, body)
    return success_response(data=r) if r else error_response("用户不存在", 404)


@system_bp.delete("/users/<user_cd>")
@login_required
def delete_user(user_cd: str):  # type: ignore[no-untyped-def]
    """删除用户。"""
    return success_response() if _service.delete_user(user_cd) else error_response("用户不存在", 404)


# ---- 部门管理 ----


@system_bp.get("/departments")
@login_required
def list_departments():  # type: ignore[no-untyped-def]
    """获取部门列表。"""
    return success_response(data=_service.list_departments())


@system_bp.post("/departments")
@login_required
def create_department():  # type: ignore[no-untyped-def]
    """新增部门。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_department(body), code=201)


@system_bp.put("/departments/<dept_cd>")
@login_required
def update_department(dept_cd: str):  # type: ignore[no-untyped-def]
    """更新部门。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_department(dept_cd, body)
    return success_response(data=r) if r else error_response("部门不存在", 404)


@system_bp.delete("/departments/<dept_cd>")
@login_required
def delete_department(dept_cd: str):  # type: ignore[no-untyped-def]
    """删除部门。"""
    return success_response() if _service.delete_department(dept_cd) else error_response("部门不存在", 404)


# ---- 用户组管理 ----


@system_bp.get("/groups")
@login_required
def list_groups():  # type: ignore[no-untyped-def]
    """获取用户组列表。"""
    return success_response(data=_service.list_groups())


@system_bp.post("/groups")
@login_required
def create_group():  # type: ignore[no-untyped-def]
    """新增用户组。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_group(body), code=201)


@system_bp.put("/groups/<group_cd>")
@login_required
def update_group(group_cd: str):  # type: ignore[no-untyped-def]
    """更新用户组。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_group(group_cd, body)
    return success_response(data=r) if r else error_response("用户组不存在", 404)


@system_bp.delete("/groups/<group_cd>")
@login_required
def delete_group(group_cd: str):  # type: ignore[no-untyped-def]
    """删除用户组。"""
    return success_response() if _service.delete_group(group_cd) else error_response("用户组不存在", 404)


@system_bp.get("/groups/<group_cd>/members")
@login_required
def get_group_members(group_cd: str):  # type: ignore[no-untyped-def]
    """获取用户组成员列表。"""
    return success_response(data=_service.get_group_members(group_cd))


@system_bp.post("/groups/<group_cd>/members")
@login_required
def add_group_member(group_cd: str):  # type: ignore[no-untyped-def]
    """添加用户组成员。"""
    body = request.get_json(silent=True) or {}
    user_cd = body.get("user_cd", "")
    if not user_cd:
        return error_response("缺少 user_cd", 400)
    return success_response() if _service.add_group_member(user_cd, group_cd) else error_response("添加失败", 400)


@system_bp.delete("/groups/<group_cd>/members/<user_cd>")
@login_required
def remove_group_member(group_cd: str, user_cd: str):  # type: ignore[no-untyped-def]
    """移除用户组成员。"""
    return success_response() if _service.remove_group_member(user_cd, group_cd) else error_response("成员不存在", 404)


@system_bp.get("/users/<user_cd>/groups")
@login_required
def get_user_groups(user_cd: str):  # type: ignore[no-untyped-def]
    """获取用户所属用户组。"""
    return success_response(data=_service.get_user_groups(user_cd))


# ---- 权限管理 ----


@system_bp.get("/groups/<group_cd>/rights")
@login_required
def get_group_rights(group_cd: str):  # type: ignore[no-untyped-def]
    """获取用户组权限。"""
    return success_response(data=_service.get_group_rights(group_cd))


@system_bp.put("/groups/<group_cd>/rights")
@login_required
def set_group_rights(group_cd: str):  # type: ignore[no-untyped-def]
    """设置用户组权限（全量替换）。"""
    body = request.get_json(silent=True) or {}
    rights = body.get("rights", [])
    _service.set_group_rights(group_cd, rights)
    return success_response(message="权限设置成功")


@system_bp.get("/users/<user_cd>/permissions")
@login_required
def get_user_permissions(user_cd: str):  # type: ignore[no-untyped-def]
    """获取用户有效权限（通过用户组继承）。"""
    return success_response(data=_service.get_user_permissions(user_cd))


# ---- 菜单管理 ----


@system_bp.get("/menus")
@login_required
def list_menus():  # type: ignore[no-untyped-def]
    """获取菜单树。"""
    return success_response(data=_service.list_menus())


@system_bp.get("/menus/perm-tree")
@login_required
def get_perm_tree():  # type: ignore[no-untyped-def]
    """获取权限树（动态读取数据库菜单+功能定义）。"""
    return success_response(data=_service.get_perm_tree())


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


@system_bp.put("/sysparms/<parm_cd>")
@login_required
def update_sysparm(parm_cd: str):  # type: ignore[no-untyped-def]
    """更新系统参数（单例表）。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_sysparm(parm_cd, body)
    return success_response(data=r) if r else error_response("参数不存在", 404)


# ---- 码表查询 ----


@system_bp.get("/syscodes/all")
@login_required
def list_all_syscodes():  # type: ignore[no-untyped-def]
    """全部系统编码列表（字典管理用）。"""
    return success_response(data=_service.get_all_syscodes())


@system_bp.get("/syscodes")
@login_required
def list_syscodes():  # type: ignore[no-untyped-def]
    """按编码类型查询系统编码（如 BT/ZF/YB）。"""
    code_typ = request.args.get("code_typ", "")
    if not code_typ:
        return error_response("缺少 code_typ 参数", 400)
    return success_response(data=_service.get_syscodes(code_typ))


@system_bp.post("/syscodes")
@login_required
def create_syscode():  # type: ignore[no-untyped-def]
    """新增系统编码。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_syscode(body), code=201)


@system_bp.put("/syscodes/<int:code_id>")
@login_required
def update_syscode(code_id: int):  # type: ignore[no-untyped-def]
    """更新系统编码。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_syscode(code_id, body)
    return success_response(data=r) if r else error_response("编码不存在", 404)


@system_bp.delete("/syscodes/<int:code_id>")
@login_required
def delete_syscode(code_id: int):  # type: ignore[no-untyped-def]
    """删除系统编码。"""
    return success_response() if _service.delete_syscode(code_id) else error_response("编码不存在", 404)


@system_bp.get("/areas")
@login_required
def list_areas():  # type: ignore[no-untyped-def]
    """区域列表。"""
    return success_response(data=_service.get_areas())


@system_bp.get("/commodes")
@login_required
def list_commodes():  # type: ignore[no-untyped-def]
    """通讯方式列表。"""
    return success_response(data=_service.get_commodes())


@system_bp.get("/countries")
@login_required
def list_countries():  # type: ignore[no-untyped-def]
    """国家列表。"""
    return success_response(data=_service.get_countries())


@system_bp.get("/provinces")
@login_required
def list_provinces():  # type: ignore[no-untyped-def]
    """省份/直辖市列表。"""
    return success_response(data=_service.get_provinces())


@system_bp.get("/cities")
@login_required
def list_cities():  # type: ignore[no-untyped-def]
    """城市/区列表，可选按省份筛选。"""
    prvn_cd = request.args.get("prvn_cd")
    return success_response(data=_service.get_cities(prvn_cd))


@system_bp.get("/towns")
@login_required
def list_towns():  # type: ignore[no-untyped-def]
    """区县/街道列表，可选按城市筛选。"""
    city_cd = request.args.get("city_cd")
    return success_response(data=_service.get_towns(city_cd))


# ---- 物料分类 ----


@system_bp.get("/itemclasses/tree")
@login_required
def get_item_class_tree():  # type: ignore[no-untyped-def]
    """物料分类树（三级）。"""
    return success_response(data=_service.get_item_class_tree())


@system_bp.get("/itemclasses")
@login_required
def list_item_classes():  # type: ignore[no-untyped-def]
    """物料分类列表（扁平）。"""
    return success_response(data=_service.list_item_classes())


@system_bp.post("/itemclasses")
@login_required
def create_item_class():  # type: ignore[no-untyped-def]
    """新增物料分类。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_item_class(body), code=201)


@system_bp.put("/itemclasses/<class_cd>")
@login_required
def update_item_class(class_cd: str):  # type: ignore[no-untyped-def]
    """更新物料分类。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_item_class(class_cd, body)
    return success_response(data=r) if r else error_response("分类不存在", 404)


@system_bp.delete("/itemclasses/<class_cd>")
@login_required
def delete_item_class(class_cd: str):  # type: ignore[no-untyped-def]
    """删除物料分类。"""
    return success_response() if _service.delete_item_class(class_cd) else error_response("分类不存在", 404)


# ---- 物料 ----


@system_bp.get("/items")
@login_required
def list_items():  # type: ignore[no-untyped-def]
    """物料列表（分页），支持分类筛选、递归子分类、搜索。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    class_cd = request.args.get("class_cd")
    recursive = request.args.get("recursive", "1") == "1"
    search = request.args.get("search")
    result = _service.list_items(
        page=page, per_page=per_page,
        class_cd=class_cd, recursive=recursive, search=search,
    )
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


# ---- 客户分类 ----


@system_bp.get("/custclasses/tree")
@login_required
def get_cust_class_tree():  # type: ignore[no-untyped-def]
    """客户分类树。"""
    return success_response(data=_service.get_cust_class_tree())


@system_bp.get("/custclasses")
@login_required
def list_cust_classes():  # type: ignore[no-untyped-def]
    """客户分类列表（扁平）。"""
    return success_response(data=_service.list_cust_classes())


@system_bp.post("/custclasses")
@login_required
def create_cust_class():  # type: ignore[no-untyped-def]
    """新增客户分类。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_cust_class(body), code=201)


@system_bp.put("/custclasses/<class_cd>")
@login_required
def update_cust_class(class_cd: str):  # type: ignore[no-untyped-def]
    """更新客户分类。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_cust_class(class_cd, body)
    return success_response(data=r) if r else error_response("分类不存在", 404)


@system_bp.delete("/custclasses/<class_cd>")
@login_required
def delete_cust_class(class_cd: str):  # type: ignore[no-untyped-def]
    """删除客户分类。"""
    return success_response() if _service.delete_cust_class(class_cd) else error_response("分类不存在", 404)


# ---- 客户 ----


@system_bp.get("/customers")
@login_required
def list_customers():  # type: ignore[no-untyped-def]
    """客户列表（分页），支持分类筛选和搜索。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    class_cd = request.args.get("class_cd")
    search = request.args.get("search")
    result = _service.list_customers(page=page, per_page=per_page, class_cd=class_cd, search=search)
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


@system_bp.get("/eid/tree")
@login_required
def get_eid_tree():  # type: ignore[no-untyped-def]
    """EID 物料分类树（含 EID 数量）。"""
    return success_response(data=_service.get_eid_itemcd_tree())


@system_bp.get("/eid")
@login_required
def list_eid():  # type: ignore[no-untyped-def]
    """EID 设备列表（分页），支持分类筛选和搜索。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    class_cd = request.args.get("class_cd")
    search = request.args.get("search")
    result = _service.list_eid(page=page, per_page=per_page, class_cd=class_cd, search=search)
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


@system_bp.get("/eid/<itemcd>/<eid_val>/tracks")
@login_required
def get_eid_tracks(itemcd: str, eid_val: str):  # type: ignore[no-untyped-def]
    """查询设备变更历史。"""
    return success_response(data=_service.get_eid_tracks(itemcd, eid_val))


@system_bp.delete("/eid/<itemcd>/<eid_val>")
@login_required
def delete_eid(itemcd: str, eid_val: str):  # type: ignore[no-untyped-def]
    """删除 EID（复合主键 itemcd+eid）。"""
    return success_response() if _service.delete_eid(itemcd, eid_val) else error_response("不存在", 404)


@system_bp.get("/warehouses")
@login_required
def list_warehouses():  # type: ignore[no-untyped-def]
    """仓库列表。"""
    return success_response(data=_service.get_warehouses())


@system_bp.get("/assets")
@login_required
def list_assets():  # type: ignore[no-untyped-def]
    """资产台账列表（分页），支持客户分类/搜索/资产类型筛选。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    class_cd = request.args.get("class_cd")
    search = request.args.get("search")
    asset_type = request.args.get("asset_type")
    asset_owner = request.args.get("asset_owner")
    useflg = request.args.get("useflg")
    result = _service.list_assets(page=page, per_page=per_page, class_cd=class_cd, search=search, asset_type=asset_type, asset_owner=asset_owner, useflg=useflg)
    return success_response(data={"items": result["items"], "total": result["total"]})


@system_bp.put("/assets/<int:asset_id>")
@login_required
def update_asset(asset_id: int):  # type: ignore[no-untyped-def]
    """更新资产属性（操作 tmm43_eid）。"""
    body = request.get_json(silent=True) or {}
    r = _service.get_asset(asset_id)
    if not r:
        return error_response("不存在", 404)
    itemcd, eid = r.get("item_cd"), r.get("eid")
    if not itemcd or not eid:
        return error_response("无法定位设备", 400)
    from app.models.master import Eid
    from app.extensions import db
    e = db.session.get(Eid, (itemcd, eid))
    if not e:
        return error_response("设备不存在", 404)
    for k, v in body.items():
        if hasattr(e, k):
            setattr(e, k, v)
    db.session.commit()
    return success_response(data=e.to_dict())
