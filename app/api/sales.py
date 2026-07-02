"""
销售管理 API。

路由前缀：/api/v1/sales
预计划 + 销售单据 + 延期。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.sales import (
    PlanCustCreate,
    PlanCustUpdate,
    PlanServeCreate,
    PlanServeUpdate,
    PlanTransition,
    PlanVoid,
    SalesBillCreate,
    SalesExtendCreate,
    SalesExtendDetailCreate,
    SalesQuery,
)
from app.services.sales_service import (
    PlanCustService,
    PlanServeService,
    SalesBillService,
    SalesExtendService,
)
from app.utils.response import error_response, success_response

__all__ = ["sales_bp"]

sales_bp = Blueprint("sales", __name__)


# ---- 预计划 ----


@sales_bp.get("/plans")
@login_required
def list_plans():  # type: ignore[no-untyped-def]
    """预计划列表。"""
    params = SalesQuery.model_validate(request.args.to_dict())
    data = PlanCustService.list_records(
        plantyp=params.plantyp,
        plan_status=params.plan_status,
        custcd=params.custcd,
        planno=params.planno,
        custnm=params.custnm,
        custcard=params.custcard,
        date_from=params.date_from,
        date_to=params.date_to,
        serve_status=params.serve_status,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@sales_bp.get("/plans/<planno>")
@login_required
def get_plan(planno: str):  # type: ignore[no-untyped-def]
    """预计划详情。"""
    data = PlanCustService.get(planno)
    if data is None:
        return error_response(message="预计划不存在", code=404)
    return success_response(data=data)


@sales_bp.post("/plans")
@login_required
def create_plan():  # type: ignore[no-untyped-def]
    """创建预计划。"""
    body = PlanCustCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    result = PlanCustService.create(body.model_dump(exclude_none=True), user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "创建失败")), code=400)
    return success_response(data=result, message="创建成功", code=201)


@sales_bp.get("/plans/stock-check")
@login_required
def check_plan_stock():  # type: ignore[no-untyped-def]
    """预计划机型库存校验。

    Query: model_cd=xxx
    Returns: {total_qty, wh_details, item_cd}
    """
    from app.services.plan_stock_service import PlanStockService

    model_cd = (request.args.get("model_cd") or "").strip()
    if not model_cd:
        return error_response("model_cd 不能为空", 400)
    data = PlanStockService.check_stock(model_cd)
    return success_response(data=data)


@sales_bp.get("/plans/available-eids")
@login_required
def list_available_eids():  # type: ignore[no-untyped-def]
    """预计划机型可用设备列表（TMM43_EID 设备维度）。

    Query: model_cd=xxx&whtyp=03&asset_types=01,03&itemtyp=GA&page=1&per_page=50
    Returns: {total, items: [{eid, itemcd, whcd, whnm, asset_type, asset_type_nm,
              itemtyp, itemtyp_nm, sflg, qcflg}]}
    """
    from app.services.plan_stock_service import PlanStockService

    model_cd = (request.args.get("model_cd") or "").strip()
    if not model_cd:
        return error_response("model_cd 不能为空", 400)
    whtyp = request.args.get("whtyp", "03")
    whtyp = None if whtyp == "" else whtyp
    asset_types_str = request.args.get("asset_types")
    if asset_types_str is not None:
        asset_types = [s.strip() for s in asset_types_str.split(",") if s.strip()] or None
    else:
        asset_types = None  # 默认 ['01','02','03']
    itemtyp_str = request.args.get("itemtyp")
    if itemtyp_str is not None:
        itemtyp = [s.strip() for s in itemtyp_str.split(",") if s.strip()] or None
    else:
        itemtyp = None  # 默认 ['GA','GB','GC']
    page = int(request.args.get("page", "1") or "1")
    per_page = int(request.args.get("per_page", "50") or "50")
    exclude_reserved = request.args.get("exclude_reserved", "1") != "0"
    data = PlanStockService.list_available_eids(
        model_cd=model_cd,
        whtyp=whtyp,
        asset_types=asset_types,
        itemtyp=itemtyp,
        page=page,
        per_page=per_page,
        exclude_reserved=exclude_reserved,
    )
    return success_response(data=data)


@sales_bp.get("/plans/bom-check")
@login_required
def check_plan_bom():  # type: ignore[no-untyped-def]
    """预计划机型 BOM 齐套校验。

    Query: model_cd=xxx&qty=1
    Returns: {lines: [{itemcd, item_nm, need_qty, stock_qty, enough}], all_enough}
    """
    from app.services.plan_stock_service import PlanStockService

    model_cd = (request.args.get("model_cd") or "").strip()
    if not model_cd:
        return error_response("model_cd 不能为空", 400)
    qty = int(request.args.get("qty", "1") or "1")
    if qty < 1:
        qty = 1
    data = PlanStockService.expand_bom_and_check(model_cd, qty)
    return success_response(data=data)


@sales_bp.put("/plans/<planno>")
@login_required
def update_plan(planno: str):  # type: ignore[no-untyped-def]
    """更新预计划。"""
    body = PlanCustUpdate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    result = PlanCustService.update(planno, body.model_dump(exclude_unset=True), user_cd)
    if result is None:
        return error_response(message="预计划不存在", code=404)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "更新失败")), code=400)
    return success_response(data=result)


# ---- 预计划状态管理 ----


@sales_bp.post("/plans/<planno>/transition")
@login_required
def transition_plan(planno: str):  # type: ignore[no-untyped-def]
    """预计划状态流转。"""
    body = PlanTransition.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    result = PlanCustService.transition(
        planno,
        to_status=body.to_status,
        operator=user_cd,
        remark=body.remark,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "状态流转失败")), code=400)
    return success_response(data=result)


@sales_bp.post("/plans/<planno>/void")
@login_required
def void_plan(planno: str):  # type: ignore[no-untyped-def]
    """作废预计划。"""
    body = PlanVoid.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    result = PlanCustService.void(planno, operator=user_cd, remark=body.remark)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "作废失败")), code=400)
    return success_response(data=result, message="已作废")


@sales_bp.post("/plans/<planno>/implement")
@login_required
def implement_plan(planno: str):  # type: ignore[no-untyped-def]
    """实施确认：按 plantyp 生成下游 ITSM 单据。"""
    user_cd: str = g.current_user
    result = PlanCustService.implement(planno, operator=user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "实施确认失败")), code=400)
    return success_response(data=result, message="实施确认成功")


@sales_bp.post("/plans/<planno>/complete")
@login_required
def complete_plan(planno: str):  # type: ignore[no-untyped-def]
    """完成预计划（设备出库后调用）。"""
    user_cd: str = g.current_user
    result = PlanCustService.complete(planno, operator=user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "完成失败")), code=400)
    return success_response(data=result, message="已完成")


@sales_bp.post("/plans/<planno>/outbound")
@login_required
def create_outbound(planno: str):  # type: ignore[no-untyped-def]
    """生成 OV=1 销售出库草稿（仓库实施部领机）。

    请求体可选 eids: list[str] —— 方案 B 仓库人选定的 EID 列表。
    方案 A（预计划已选 posid）无需传 eids，自动带出。
    """
    json_data = request.get_json(silent=True) or {}
    whcd = json_data.get("whcd", "04")
    eids = json_data.get("eids")
    if eids is not None and not isinstance(eids, list):
        return error_response(message="eids 必须是数组", code=400)
    user_cd: str = g.current_user
    result = PlanCustService.create_outbound(
        planno,
        whcd=whcd,
        operator=user_cd,
        eids=eids,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "出库单创建失败")), code=400)
    return success_response(data=result, message="出库单已创建", code=201)


# ---- 呼出单 ----
@sales_bp.get("/plan-serve")
@login_required
def list_plan_serve():  # type: ignore[no-untyped-def]
    """呼出单列表。"""
    params = SalesQuery.model_validate(request.args.to_dict())
    data = PlanServeService.list_records(
        planno=params.planno,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@sales_bp.get("/plans/<planno>/devices/current")
@login_required
def list_plan_devices_current(planno: str):  # type: ignore[no-untyped-def]
    """预计划当前设备 BOM（对齐 PB d_plan_bom_dtl）。

    取 tmm35_cust_pos_rl.useflg='1' 的整机，左联 tmm44_pos_r_eid 取其下所有配件。
    """
    from sqlalchemy.orm import aliased

    from app.extensions import db
    from app.models.master import CustPosRl, Item, PosREid

    plan = PlanCustService.get(planno)
    if plan is None:
        return error_response(message="预计划不存在", code=404)
    custcd = plan.get("custcd") or ""
    if not custcd:
        return success_response(data=[])

    AccItem = aliased(Item)
    rows = (
        db.session.query(
            CustPosRl.item_cd.label("pos_itemcd"),
            Item.item_nm.label("pos_itemnm"),
            PosREid.itemcd.label("acc_itemcd"),
            AccItem.item_nm.label("acc_itemnm"),
            PosREid.eid.label("acc_eid"),
            CustPosRl.eid.label("pos_eid"),
            CustPosRl.useflg.label("pos_useflg"),
            PosREid.useflg.label("acc_useflg"),
            CustPosRl.posupddate,
        )
        .outerjoin(PosREid, CustPosRl.eid == PosREid.posid)
        .outerjoin(Item, CustPosRl.item_cd == Item.item_cd)
        .outerjoin(AccItem, PosREid.itemcd == AccItem.item_cd)
        .filter(CustPosRl.cust_cd == custcd, CustPosRl.useflg == "1")
        .order_by(CustPosRl.eid.asc())
        .all()
    )
    result = [
        {
            "pos_itemcd": r.pos_itemcd,
            "pos_itemnm": r.pos_itemnm or "",
            "pos_eid": r.pos_eid,
            "pos_useflg": r.pos_useflg,
            "acc_itemcd": r.acc_itemcd,
            "acc_itemnm": r.acc_itemnm or "",
            "acc_eid": r.acc_eid,
            "acc_useflg": r.acc_useflg,
            "upddate": str(r.posupddate) if r.posupddate else "",
        }
        for r in rows
        if r.acc_eid is None or r.acc_useflg == "1"
    ]
    return success_response(data=result)


@sales_bp.get("/plans/<planno>/devices/history")
@login_required
def list_plan_devices_history(planno: str):  # type: ignore[no-untyped-def]
    """预计划历史设备（对齐 PB d_plan_bom_lst）。

    取 tmm35_cust_pos_rl 中该客户的所有记录（含 useflg=0 失效），联 tmm12_items。
    """
    from app.extensions import db
    from app.models.master import CustPosRl, Item

    plan = PlanCustService.get(planno)
    if plan is None:
        return error_response(message="预计划不存在", code=404)
    custcd = plan.get("custcd") or ""
    if not custcd:
        return success_response(data=[])

    rows = (
        db.session.query(
            CustPosRl.item_cd,
            Item.item_nm,
            CustPosRl.eid,
            CustPosRl.sysinfo,
            CustPosRl.softinfo,
            CustPosRl.posinfo,
            CustPosRl.posupddate,
            CustPosRl.useflg,
        )
        .outerjoin(Item, CustPosRl.item_cd == Item.item_cd)
        .filter(CustPosRl.cust_cd == custcd)
        .order_by(CustPosRl.posupddate.asc())
        .all()
    )
    result = [
        {
            "itemcd": r.item_cd,
            "itemnm": r.item_nm or "",
            "eid": r.eid,
            "sysinfo": r.sysinfo or "",
            "softinfo": r.softinfo or "",
            "posinfo": r.posinfo or "",
            "upddate": str(r.posupddate) if r.posupddate else "",
            "useflg": r.useflg,
        }
        for r in rows
    ]
    return success_response(data=result)


@sales_bp.get("/plans/<planno>/serve")
@login_required
def list_plan_serves(planno: str):  # type: ignore[no-untyped-def]
    """指定预计划的呼出记录。"""
    data = PlanServeService.list_by_plan(planno)
    return success_response(data=data)


@sales_bp.post("/plans/<planno>/serve")
@login_required
def create_plan_serve(planno: str):  # type: ignore[no-untyped-def]
    """创建呼出单。"""
    body = PlanServeCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = PlanServeService.create(
        {**body.model_dump(exclude_none=True), "planno": planno},
        creator=user_cd,
    )
    return success_response(data=data, message="呼出单已创建", code=201)


@sales_bp.put("/plan-serve/<int:dtlid>")
@login_required
def update_plan_serve(dtlid: int):  # type: ignore[no-untyped-def]
    """更新呼出单（反馈呼出结果）。"""
    body = PlanServeUpdate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    from app.repositories.sales_repository import PlanServeRepository

    record = PlanServeRepository.get_by_id(dtlid)
    if record is None:
        return error_response(message="呼出单不存在", code=404)

    PlanServeRepository.update(
        record,
        {**body.model_dump(exclude_unset=True), "opercd": user_cd},
    )
    from app.extensions import db

    db.session.commit()
    return success_response(data=record.to_dict())


@sales_bp.post("/plan-serve/<int:dtlid>/transition")
@login_required
def transition_plan_serve(dtlid: int):  # type: ignore[no-untyped-def]
    """呼出单状态流转（00→01 标记已呼出）。"""
    body = PlanTransition.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    result = PlanServeService.transition(dtlid, to_status=body.to_status, operator=user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "流转失败")), code=400)
    return success_response(data=result)


# ---- 销售单据 ----


@sales_bp.get("/bills")
@login_required
def list_bills():  # type: ignore[no-untyped-def]
    """销售单据列表。"""
    params = SalesQuery.model_validate(request.args.to_dict())
    data = SalesBillService.list_records(
        sltyp=params.sltyp,
        custcd=params.custcd,
        auditflg=params.auditflg,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@sales_bp.get("/bills/<slbillid>")
@login_required
def get_bill(slbillid: str):  # type: ignore[no-untyped-def]
    """销售单据详情。"""
    data = SalesBillService.get(slbillid)
    if data is None:
        return error_response(message="销售单据不存在", code=404)
    return success_response(data=data)


@sales_bp.post("/bills")
@login_required
def create_bill():  # type: ignore[no-untyped-def]
    """创建销售单据。"""
    body = SalesBillCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = SalesBillService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@sales_bp.post("/bills/<slbillid>/audit")
@login_required
def audit_bill(slbillid: str):  # type: ignore[no-untyped-def]
    """审核销售单据。"""
    user_cd: str = g.current_user
    result = SalesBillService.audit(slbillid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 延期 ----


@sales_bp.get("/extends")
@login_required
def list_extends():  # type: ignore[no-untyped-def]
    """延期列表。"""
    params = SalesQuery.model_validate(request.args.to_dict())
    data = SalesExtendService.list_records(
        custcd=params.custcd,
        auditflg=params.auditflg,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@sales_bp.get("/extends/<opbillid>")
@login_required
def get_extend(opbillid: str):  # type: ignore[no-untyped-def]
    """延期详情。"""
    data = SalesExtendService.get(opbillid)
    if data is None:
        return error_response(message="延期单不存在", code=404)
    return success_response(data=data)


@sales_bp.post("/extends")
@login_required
def create_extend():  # type: ignore[no-untyped-def]
    """创建延期。"""
    json_data = request.get_json(silent=True) or {}
    body = SalesExtendCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [SalesExtendDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = SalesExtendService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)
