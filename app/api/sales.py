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


@sales_bp.put("/plans/<planno>")
@login_required
def update_plan(planno: str):  # type: ignore[no-untyped-def]
    """更新预计划。"""
    body = PlanCustUpdate.model_validate(request.get_json(silent=True) or {})
    result = PlanCustService.update(planno, body.model_dump(exclude_unset=True))
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
    """生成 OV=1 销售出库草稿（仓库实施部领机）。"""
    json_data = request.get_json(silent=True) or {}
    whcd = json_data.get("whcd", "04")
    user_cd: str = g.current_user
    result = PlanCustService.create_outbound(planno, whcd=whcd, operator=user_cd)
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
    from app.extensions import db
    from app.models.master import CustPosRl, Item, PosREid

    plan = PlanCustService.get(planno)
    if plan is None:
        return error_response(message="预计划不存在", code=404)
    custcd = plan.get("custcd") or ""
    if not custcd:
        return success_response(data=[])

    rows = (
        db.session.query(
            CustPosRl.item_cd.label("pos_itemcd"),
            Item.item_nm.label("pos_itemnm"),
            PosREid.itemcd.label("acc_itemcd"),
            PosREid.eid.label("acc_eid"),
            CustPosRl.eid.label("pos_eid"),
            CustPosRl.useflg.label("pos_useflg"),
            PosREid.useflg.label("acc_useflg"),
            CustPosRl.posupddate,
        )
        .outerjoin(PosREid, CustPosRl.eid == PosREid.posid)
        .outerjoin(Item, CustPosRl.item_cd == Item.item_cd)
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
            "acc_eid": r.acc_eid,
            "acc_useflg": r.acc_useflg,
            "upddate": str(r.posupddate) if r.posupddate else "",
        }
        for r in rows
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
