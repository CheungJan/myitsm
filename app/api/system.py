"""
系统管理 API（用户/部门/菜单/编码表）。

对应 PB base_sys.pbl 模块。
"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.extensions import db
from app.models.master import CustItems, Supplier, SupplierClass
from sqlalchemy import func
from app.schemas.warehouse import TransferAccountCreate, TransferAccountUpdate
from app.services.system_service import SystemService
from app.services.warehouse_service import TransferAccountService
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
    """获取用户组成员列表。

    查询参数:
        active_only: 1 时仅返回 status='1' 的有效成员
    """
    active_only = request.args.get("active_only", "0") == "1"
    return success_response(data=_service.get_group_members(group_cd, active_only=active_only))


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
    """获取指定系统参数；不存在时返回 null 便于前端使用默认值。"""
    parm = _service.get_sysparm(parm_cd)
    return success_response(data=parm)


@system_bp.put("/sysparms/<parm_cd>")
@login_required
def update_sysparm(parm_cd: str):  # type: ignore[no-untyped-def]
    """更新或创建系统参数。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_sysparm(parm_cd, body)
    return success_response(data=r)


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


# ---- 国标地理表（geo_*，来源：province-city-china）----


@system_bp.get("/geo/provinces")
@login_required
def list_geo_provinces():  # type: ignore[no-untyped-def]
    """国标省级列表（31条，不含港澳台）。"""
    return success_response(data=_service.get_geo_provinces())


@system_bp.get("/geo/cities")
@login_required
def list_geo_cities():  # type: ignore[no-untyped-def]
    """国标地级市列表，可按省级代码筛选（?province_code=31）。"""
    province_code = request.args.get("province_code")
    return success_response(data=_service.get_geo_cities(province_code))


@system_bp.get("/geo/areas")
@login_required
def list_geo_areas():  # type: ignore[no-untyped-def]
    """国标区县列表，可按地级市代码筛选（?city_code=3101）。"""
    city_code = request.args.get("city_code")
    province_code = request.args.get("province_code")
    return success_response(data=_service.get_geo_areas(city_code, province_code))


@system_bp.get("/geo/streets")
@login_required
def list_geo_streets():  # type: ignore[no-untyped-def]
    """国标街道列表，可按区县代码筛选（?area_code=310101）。街道数据较多，建议必传 area_code。"""
    area_code = request.args.get("area_code")
    city_code = request.args.get("city_code")
    return success_response(data=_service.get_geo_streets(area_code, city_code))


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


@system_bp.get("/itemclasses/bom-tree")
@login_required
def get_bom_class_tree():  # type: ignore[no-untyped-def]
    """分类树（typflg=1 成品，typflg=0 配件）。"""
    typflg = request.args.get("typflg", "1")
    return success_response(data=_service.get_bom_class_tree(typflg))


@system_bp.post("/itemclasses")
@login_required
def create_item_class():  # type: ignore[no-untyped-def]
    """新增物料分类。"""
    body = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.create_item_class(body), code=201)
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.put("/itemclasses/<class_cd>")
@login_required
def update_item_class(class_cd: str):  # type: ignore[no-untyped-def]
    """更新物料分类。"""
    body = request.get_json(silent=True) or {}
    try:
        r = _service.update_item_class(class_cd, body)
        return success_response(data=r) if r else error_response("分类不存在", 404)
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.delete("/itemclasses/<class_cd>")
@login_required
def delete_item_class(class_cd: str):  # type: ignore[no-untyped-def]
    """删除物料分类。"""
    return success_response() if _service.delete_item_class(class_cd) else error_response("分类不存在", 404)


# ---- 物料 ----


@system_bp.get("/items")
@login_required
def list_items():  # type: ignore[no-untyped-def]
    """物料列表（分页），支持分类筛选、递归子分类、搜索、成品/配件过滤。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    class_cd = request.args.get("class_cd")
    recursive = request.args.get("recursive", "1") == "1"
    search = request.args.get("search")
    typflg = request.args.get("typflg")
    result = _service.list_items(
        page=page, per_page=per_page,
        class_cd=class_cd, recursive=recursive, search=search, typflg=typflg,
    )
    return success_response(data={"items": result["items"], "total": result["total"]})


@system_bp.get("/items/pos-models")
@login_required
def list_pos_models():  # type: ignore[no-untyped-def]
    """在产机型列表(整机成品 JOIN Bom useflg=1,带押金/售价)。

    供预计划机型下拉使用。对齐 PB 语义:Bom.useflg='1' 即在产可选。
    """
    return success_response(data=_service.list_pos_models())


@system_bp.post("/items")
@login_required
def create_item():  # type: ignore[no-untyped-def]
    """新增物料。"""
    body = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.create_item(body), code=201)
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.put("/items/<item_cd>")
@login_required
def update_item(item_cd: str):  # type: ignore[no-untyped-def]
    """更新物料。"""
    body = request.get_json(silent=True) or {}
    try:
        r = _service.update_item(item_cd, body)
        return success_response(data=r) if r else error_response("不存在", 404)
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.delete("/items/<item_cd>")
@login_required
def delete_item(item_cd: str):  # type: ignore[no-untyped-def]
    """删除物料。"""
    return success_response() if _service.delete_item(item_cd) else error_response("不存在", 404)


@system_bp.get("/suppliers")
@login_required
def list_suppliers():  # type: ignore[no-untyped-def]
    """供应商列表（分页 + 搜索 + 分类筛选）。"""
    keyword = request.args.get("keyword", "").strip()
    class_cd = request.args.get("class_cd", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return success_response(data=_service.list_suppliers(keyword, class_cd, page, per_page))


@system_bp.get("/suppliers/simple")
@login_required
def list_suppliers_simple():  # type: ignore[no-untyped-def]
    """供应商简表（全量，用于下拉选择）。"""
    return success_response(data=_service.list_suppliers_all())


@system_bp.get("/suppliers/<supp_cd>")
@login_required
def get_supplier(supp_cd: str):  # type: ignore[no-untyped-def]
    """供应商详情。"""
    data = _service.get_supplier(supp_cd)
    if not data:
        return error_response("供应商不存在", 404)
    return success_response(data=data)


@system_bp.get("/suppliers/by-requisition")
@login_required
def suppliers_by_requisition():  # type: ignore[no-untyped-def]
    """根据采购需求单查询可供应其物料的供应商列表（仅含仍有可用量的物料）。"""
    from app.models.procurement import PurchasePlanDt, RequisitionOrderLink

    pcplanid = request.args.get("pcplanid", "").strip()
    if not pcplanid:
        return error_response("pcplanid 不能为空", 400)

    # 子查询：仍有可用余额的需求行物料
    available_items = (
        db.session.query(PurchasePlanDt.itemcd)
        .filter(
            PurchasePlanDt.pcplanid == pcplanid,
            PurchasePlanDt.rgstqty
            > db.session.query(
                func.coalesce(func.sum(RequisitionOrderLink.linkqty), 0)
            )
            .filter(
                RequisitionOrderLink.pcplanid == PurchasePlanDt.pcplanid,
                RequisitionOrderLink.pclineno == PurchasePlanDt.lineno,
            )
            .correlate(PurchasePlanDt)
            .scalar_subquery(),
        )
    )

    rows = (
        db.session.query(Supplier.supp_cd, Supplier.supp_nm)
        .join(CustItems, Supplier.supp_cd == CustItems.custcd)
        .filter(
            CustItems.itemcd.in_(available_items),
            Supplier.useflg == "1",
        )
        .distinct()
        .all()
    )
    return success_response(data=[{"supp_cd": r.supp_cd, "supp_nm": r.supp_nm} for r in rows])


@system_bp.post("/suppliers")
@login_required
def create_supplier():  # type: ignore[no-untyped-def]
    """新增供应商。"""
    json_data = request.get_json(silent=True) or {}
    try:
        supp_cd = (json_data.get("supp_cd") or "").strip()
        if supp_cd:
            if db.session.get(Supplier, supp_cd):
                return error_response(f"供应商编码 {supp_cd} 已存在", 400)
        else:
            max_cd = (
                db.session.query(db.func.max(Supplier.supp_cd))
                .filter(Supplier.supp_cd.op("~")(r"^\d{8}$"))
                .scalar()
            )
            next_num = int(max_cd) + 1 if max_cd else 1
            supp_cd = str(next_num).zfill(8)
        if not json_data.get("supp_nm"):
            return error_response("供应商名称不能为空", 400)
        json_data["supp_cd"] = supp_cd
        obj = Supplier(**json_data)
        db.session.add(obj)
        db.session.commit()
        saved = db.session.get(Supplier, supp_cd)
        return success_response(data=saved.to_dict() if saved else obj.to_dict(), code=201)
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.put("/suppliers/<supp_cd>")
@login_required
def update_supplier(supp_cd: str):  # type: ignore[no-untyped-def]
    """编辑供应商。"""
    json_data = request.get_json(silent=True) or {}
    try:
        obj = db.session.get(Supplier, supp_cd)
        if obj is None:
            return error_response(f"供应商 {supp_cd} 不存在", 404)
        readonly = {"supp_cd", "custcd", "custnm", "opercd", "gendate", "upddate"}
        for field, value in json_data.items():
            if hasattr(obj, field) and field not in readonly:
                setattr(obj, field, value)
        db.session.commit()
        saved = db.session.get(Supplier, supp_cd)
        return success_response(data=saved.to_dict() if saved else obj.to_dict())
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.delete("/suppliers/<supp_cd>")
@login_required
def delete_supplier(supp_cd: str):  # type: ignore[no-untyped-def]
    """删除供应商（逻辑删除）。"""
    try:
        obj = db.session.get(Supplier, supp_cd)
        if obj is None:
            return error_response(f"供应商 {supp_cd} 不存在", 404)
        conflicts = _service._check_supplier_delete_conflicts(supp_cd)
        if conflicts:
            return error_response(f"该供应商存在以下关联：{'; '.join(conflicts)}，无法删除", 409)
        db.session.delete(obj)
        db.session.commit()
        return success_response(data={"supp_cd": supp_cd, "conflicts": []}, message="删除成功")
    except ValueError as e:
        msg = str(e)
        if "不存在" in msg:
            return error_response(msg, 404)
        return error_response(msg, 409)


# ---- 供应商商品关联 ----


@system_bp.get("/suppliers/<supp_cd>/items")
@login_required
def list_supplier_items(supp_cd: str):  # type: ignore[no-untyped-def]
    """查询供应商关联的商品列表。"""
    return success_response(data=_service.get_supplier_items(supp_cd))


@system_bp.post("/suppliers/<supp_cd>/items")
@login_required
def add_supplier_item(supp_cd: str):  # type: ignore[no-untyped-def]
    """为供应商新增商品关联。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.add_supplier_item(supp_cd, json_data), code=201)
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.put("/suppliers/<supp_cd>/items/<item_cd>")
@login_required
def update_supplier_item(supp_cd: str, item_cd: str):  # type: ignore[no-untyped-def]
    """修改供应商-商品关联。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.update_supplier_item(supp_cd, item_cd, json_data))
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.delete("/suppliers/<supp_cd>/items/<item_cd>")
@login_required
def delete_supplier_item(supp_cd: str, item_cd: str):  # type: ignore[no-untyped-def]
    """删除供应商-商品关联。"""
    try:
        _service.delete_supplier_item(supp_cd, item_cd)
        return success_response(message="删除成功")
    except ValueError as e:
        msg = str(e)
        if "不存在" in msg:
            return error_response(msg, 404)
        return error_response(msg, 409)


# ---- 供应商价格 ----

@system_bp.get("/suppliers/<supp_cd>/prices")
@login_required
def list_supplier_prices(supp_cd: str):  # type: ignore[no-untyped-def]
    """查询供应商报价，支持 ?item_cd=xxx&current_only=true。"""
    item_cd = request.args.get("item_cd", "").strip()
    current_only = request.args.get("current_only", "false").lower() == "true"
    return success_response(data=_service.get_supplier_prices(supp_cd, item_cd, current_only))


@system_bp.post("/suppliers/<supp_cd>/prices")
@login_required
def create_supplier_price(supp_cd: str):  # type: ignore[no-untyped-def]
    """新增供应商报价。"""
    json_data = request.get_json(silent=True) or {}
    force = json_data.pop("force", False)
    try:
        result = _service.create_supplier_price(supp_cd, json_data, force)
        if result.get("requires_confirmation"):
            return success_response(data=result, code=200)
        return success_response(data=result, code=201)
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.put("/suppliers/<supp_cd>/prices/<int:price_id>")
@login_required
def update_supplier_price(supp_cd: str, price_id: int):  # type: ignore[no-untyped-def]
    """修改供应商报价（按主键 id）。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.update_supplier_price(price_id, json_data))
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.get("/prices/resolve")
@login_required
def resolve_price():  # type: ignore[no-untyped-def]
    """按优先级解析价格：供应商报价 > 标准采购价 > 手动填写。"""
    item_cd = request.args.get("itemcd", "").strip()
    supp_cd = request.args.get("supp_cd", "").strip()
    qty = request.args.get("qty", 1, type=float)
    if not item_cd or not supp_cd:
        return error_response("itemcd 和 supp_cd 不能为空", 400)
    return success_response(data=_service.resolve_price(item_cd, supp_cd, qty))


@system_bp.delete("/suppliers/<supp_cd>/prices/<int:price_id>")
@login_required
def delete_supplier_price(supp_cd: str, price_id: int):  # type: ignore[no-untyped-def]
    """删除供应商报价（按主键 id）。"""
    try:
        _service.delete_supplier_price(price_id)
        return success_response(message="删除成功")
    except ValueError as e:
        msg = str(e)
        if "不存在" in msg:
            return error_response(msg, 404)
        return error_response(msg, 400)


@system_bp.get("/items/<item_cd>/related-boms")
@login_required
def get_related_boms(item_cd: str):  # type: ignore[no-untyped-def]
    """反查包含该物料的 BOM 列表（该物料作为配件的所有整机 BOM）。"""
    return success_response(data=_service.get_related_boms(item_cd))


@system_bp.get("/items/<item_cd>/prices")
@login_required
def get_item_prices(item_cd: str):  # type: ignore[no-untyped-def]
    """查询物料关联的价格记录。"""
    return success_response(data=_service.get_item_prices(item_cd))


@system_bp.post("/items/<item_cd>/prices")
@login_required
def add_item_price(item_cd: str):  # type: ignore[no-untyped-def]
    """添加物料价格记录。"""
    body = request.get_json(silent=True) or {}
    body["itemcd"] = item_cd
    return success_response(data=_service.add_item_price(body), code=201)


@system_bp.put("/items/<item_cd>/prices/<busityp>")
@login_required
def update_item_price(item_cd: str, busityp: str):  # type: ignore[no-untyped-def]
    """更新物料价格记录。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_item_price(item_cd, busityp, body)
    return success_response(data=r) if r else error_response("不存在", 404)


@system_bp.delete("/items/<item_cd>/prices/<busityp>")
@login_required
def delete_item_price(item_cd: str, busityp: str):  # type: ignore[no-untyped-def]
    """删除物料价格记录。"""
    return success_response() if _service.delete_item_price(item_cd, busityp) else error_response("不存在", 404)


@system_bp.get("/items/<item_cd>/suppliers")
@login_required
def get_item_suppliers(item_cd: str):  # type: ignore[no-untyped-def]
    """查询物料关联的供应商列表（含供应商名称+周期参数）。"""
    return success_response(data=_service.get_item_suppliers(item_cd))


@system_bp.post("/items/<item_cd>/suppliers")
@login_required
def add_item_supplier(item_cd: str):  # type: ignore[no-untyped-def]
    """添加物料供应商关联。"""
    body = request.get_json(silent=True) or {}
    body["itemcd"] = item_cd
    data = _service.add_item_supplier(body)
    return success_response(data=data, code=201)


@system_bp.put("/items/<item_cd>/suppliers/<cust_cd>")
@login_required
def update_item_supplier(item_cd: str, cust_cd: str):  # type: ignore[no-untyped-def]
    """更新物料供应商关联（dfltflg/周期参数）。"""
    body = request.get_json(silent=True) or {}
    result = _service.update_item_supplier(item_cd, cust_cd, body)
    return success_response(data=result) if result else error_response("不存在", 404)


@system_bp.delete("/items/<item_cd>/suppliers/<cust_cd>")
@login_required
def delete_item_supplier(item_cd: str, cust_cd: str):  # type: ignore[no-untyped-def]
    """删除物料供应商关联。"""
    return success_response() if _service.delete_item_supplier(item_cd, cust_cd) else error_response("不存在", 404)


# ---- 供应商分类 ----


@system_bp.get("/supplierclasses/tree")
@login_required
def get_supplier_class_tree():  # type: ignore[no-untyped-def]
    """供应商分类树形结构。"""
    return success_response(data=_service.get_supplier_class_tree())


@system_bp.get("/supplierclasses")
@login_required
def list_supplier_classes():  # type: ignore[no-untyped-def]
    """供应商分类列表。"""
    return success_response(data=_service.get_supplier_classes())


@system_bp.post("/supplierclasses")
@login_required
def create_supplier_class():  # type: ignore[no-untyped-def]
    """新增供应商分类（编码自动生成）。"""
    json_data = request.get_json(silent=True) or {}
    if not json_data.get("class_nm"):
        return error_response("分类名称不能为空", 400)
    try:
        class_cd = (json_data.get("class_cd") or "").strip()
        if not class_cd:
            max_cd = (
                db.session.query(SupplierClass.class_cd)
                .filter(SupplierClass.class_cd.op("~")("^[0-9]{1,2}$"))
                .order_by(SupplierClass.class_cd.desc())
                .first()
            )
            if max_cd and max_cd[0].isdigit():
                class_cd = str(int(max_cd[0]) + 1).zfill(2)
            else:
                class_cd = "01"
        if db.session.get(SupplierClass, class_cd):
            return error_response(f"分类编码 {class_cd} 已存在", 400)
        obj = SupplierClass(
            class_cd=class_cd,
            class_nm=json_data["class_nm"],
            parent=json_data.get("parent") or "%",
            classtyp=json_data.get("classtyp") or "1",
            childflg=json_data.get("childflg") or "0",
            useflg=json_data.get("useflg") or "1",
        )
        db.session.add(obj)
        db.session.commit()
        saved = db.session.get(SupplierClass, class_cd)
        return success_response(data=saved.to_dict() if saved else obj.to_dict(), code=201)
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.put("/supplierclasses/<class_cd>")
@login_required
def update_supplier_class(class_cd: str):  # type: ignore[no-untyped-def]
    """编辑供应商分类。"""
    json_data = request.get_json(silent=True) or {}
    try:
        obj = db.session.get(SupplierClass, class_cd)
        if obj is None:
            return error_response(f"分类 {class_cd} 不存在", 404)
        for field in ("class_nm", "parent", "classtyp", "childflg", "useflg"):
            if field in json_data:
                setattr(obj, field, json_data[field])
        db.session.commit()
        saved = db.session.get(SupplierClass, class_cd)
        return success_response(data=saved.to_dict() if saved else obj.to_dict())
    except ValueError as e:
        return error_response(str(e), 400)


@system_bp.delete("/supplierclasses/<class_cd>")
@login_required
def delete_supplier_class(class_cd: str):  # type: ignore[no-untyped-def]
    """删除供应商分类。"""
    try:
        obj = db.session.get(SupplierClass, class_cd)
        if obj is None:
            return error_response(f"分类 {class_cd} 不存在", 404)
        child_count = db.session.query(SupplierClass).filter(SupplierClass.parent == class_cd).count()
        if child_count > 0:
            return error_response(f"分类 {class_cd} 下存在 {child_count} 个子分类，无法删除", 409)
        supplier_count = db.session.query(Supplier).filter(Supplier.class_cd == class_cd).count()
        if supplier_count > 0:
            return error_response(f"分类 {class_cd} 下存在 {supplier_count} 个供应商，无法删除", 409)
        db.session.delete(obj)
        db.session.commit()
        return success_response(message="删除成功")
    except ValueError as e:
        msg = str(e)
        if "不存在" in msg:
            return error_response(msg, 404)
        return error_response(msg, 409)


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
    customer_status = request.args.get("customer_status")
    useflg = request.args.get("useflg")
    result = _service.list_customers(page=page, per_page=per_page, class_cd=class_cd, search=search, customer_status=customer_status, useflg=useflg)
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


@system_bp.get("/eid/<eid_val>")
@login_required
def get_eid_info(eid_val: str):  # type: ignore[no-untyped-def]
    """查询单个EID的基本信息（含所在仓库）。"""
    from app.models.master import Eid as EidModel
    eid = db.session.query(EidModel).filter(EidModel.eid == eid_val).first()
    if not eid:
        return error_response("EID 不存在", 404)
    return success_response(data={"eid": eid.eid, "itemcd": eid.itemcd, "whcd": eid.whcd})


@system_bp.get("/eid")
@login_required
def list_eid():  # type: ignore[no-untyped-def]
    """EID 设备列表（分页），支持分类筛选、搜索和按仓库过滤。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    class_cd = request.args.get("class_cd")
    search = request.args.get("search")
    whcd = request.args.get("whcd")
    result = _service.list_eid(page=page, per_page=per_page, class_cd=class_cd, search=search, whcd=whcd)
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


@system_bp.post("/warehouses")
@login_required
def create_warehouse():  # type: ignore[no-untyped-def]
    """新增仓库。"""
    body = request.get_json(silent=True) or {}
    return success_response(data=_service.create_warehouse(body), code=201)


@system_bp.put("/warehouses/<whcd>")
@login_required
def update_warehouse(whcd: str):  # type: ignore[no-untyped-def]
    """更新仓库。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_warehouse(whcd, body)
    return success_response(data=r) if r else error_response("仓库不存在", 404)


@system_bp.delete("/warehouses/<whcd>")
@login_required
def delete_warehouse(whcd: str):  # type: ignore[no-untyped-def]
    """删除仓库。"""
    return success_response() if _service.delete_warehouse(whcd) else error_response("仓库不存在", 404)


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
    location = request.args.get("location")
    whcd = request.args.get("whcd")
    sflg = request.args.get("sflg")
    cust_cd = request.args.get("cust_cd")
    class_cd = request.args.get("class_cd")
    item_class = request.args.get("item_class")
    result = _service.list_assets(page=page, per_page=per_page, class_cd=class_cd, search=search, asset_type=asset_type, asset_owner=asset_owner, useflg=useflg, location=location, whcd=whcd, sflg=sflg, cust_cd=cust_cd, item_class=item_class)
    return success_response(data={"items": result["items"], "total": result["total"]})


@system_bp.get("/assets/bom")
@login_required
def get_asset_bom():  # type: ignore[no-untyped-def]
    """查询设备 BOM 配件明细（通过 tmm44_pos_r_eid），含质保信息。"""
    eid = request.args.get("eid", "")
    if not eid:
        return error_response("缺少 eid 参数", 400)
    from app.extensions import db
    from app.models.master import Customer, CustPosRl, Item, PosREid
    from app.models.master import Eid as EidModel

    rows = db.session.query(PosREid).filter(PosREid.posid == eid).all()

    # 主机信息
    eid_row = db.session.query(EidModel).filter(EidModel.eid == eid).first()
    host_item = db.session.get(Item, eid_row.itemcd) if eid_row else None
    host_nm = host_item.item_nm if host_item else ""

    # 客户质保信息 + 门店分配状态
    parent_rl = db.session.query(CustPosRl).filter(
        CustPosRl.eid == eid, CustPosRl.useflg == "1"
    ).first()
    cust = db.session.query(Customer).filter(
        Customer.cust_cd == parent_rl.cust_cd
    ).first() if parent_rl else None

    result = []
    for r in rows:
        d = r.to_dict()
        d["host_nm"] = host_nm
        d["host_eid"] = eid
        # 配件有效 = 自身有效 且 整机门店分配有效（未退回）
        acc_active = (r.useflg or "1") == "1"
        d["active"] = acc_active and parent_rl is not None
        d["store_returned"] = parent_rl is None  # 门店已退回
        item = db.session.query(Item).filter(Item.item_cd == r.itemcd).first()
        d["item_nm"] = item.item_nm if item else ""
        # EID 质保信息
        eid_info = db.session.query(EidModel).filter(EidModel.eid == r.eid, EidModel.itemcd == r.itemcd).first()
        if eid_info:
            d["old_degree"] = str(eid_info.old_degree) if eid_info.old_degree else ""
            d["asset_owner"] = eid_info.asset_owner or ""
            d["warranty_start"] = str(cust.opendate) if cust and cust.opendate else ""
            d["warranty_days"] = item.newperiod if eid_info.old_degree and str(eid_info.old_degree) == '12' else (item.oldperiod or 0)
        else:
            d["old_degree"] = ""; d["asset_owner"] = ""; d["warranty_start"] = ""; d["warranty_days"] = 0
        result.append(d)
    return success_response(data=result)


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
    from app.extensions import db
    from app.models.master import Eid
    e = db.session.get(Eid, (itemcd, eid))
    if not e:
        return error_response("设备不存在", 404)
    for k, v in body.items():
        if hasattr(e, k):
            setattr(e, k, v)
    db.session.commit()
    return success_response(data=e.to_dict())


# ---- 调拨科目 (TTX01_TXKMG) ----


@system_bp.get("/transfers")
@login_required
def list_transfers():  # type: ignore[no-untyped-def]
    """调拨科目列表。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    data = TransferAccountService.list_records(page=page, per_page=per_page)
    return success_response(data=data)


@system_bp.get("/transfers/<txkno>")
@login_required
def get_transfer(txkno: str):  # type: ignore[no-untyped-def]
    """调拨科目详情。"""
    data = TransferAccountService.get(txkno)
    if data is None:
        return error_response(message="调拨科目不存在", code=404)
    return success_response(data=data)


@system_bp.post("/transfers")
@login_required
def create_transfer():  # type: ignore[no-untyped-def]
    """创建调拨科目。"""
    body = TransferAccountCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = TransferAccountService.create(body.model_dump(exclude_none=True), creator=user_cd)
    return success_response(data=data, message="创建成功", code=201)


@system_bp.put("/transfers/<txkno>")
@login_required
def update_transfer(txkno: str):  # type: ignore[no-untyped-def]
    """更新调拨科目。"""
    body = TransferAccountUpdate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = TransferAccountService.update(txkno, body.model_dump(exclude_unset=True), updator=user_cd)
    if data is None:
        return error_response(message="调拨科目不存在", code=404)
    return success_response(data=data)
