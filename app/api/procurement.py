"""
采购管理 API。

路由前缀：/api/v1/procurement
采购需求→订单→结算单→退货→供应商评价全链路。
"""

from __future__ import annotations

import sqlalchemy as sa
from flask import Blueprint, g, request

from app.api.auth import login_required
from app.extensions import db
from app.repositories.procurement_repository import (
    PurchaseRegisterRepository,
    RequisitionOrderLinkRepository,
)
from app.schemas.procurement import (
    ProcurementQuery,
    PurchaseBillCreate,
    PurchaseBillUpdate,
    PurchasePlanCreate,
    PurchasePlanDetailCreate,
    PurchasePlanStatusCreate,
    PurchasePlanStatusUpdate,
    PurchaseRegisterCreate,
    PurchaseRegisterDetailCreate,
    ReturnPurchaseBillCreate,
    ReturnPurchaseBillDetailCreate,
    ReturnPurchaseBillUpdate,
    SupplierAppraisalCreate,
    SupplierAppraisalDetailCreate,
)
from app.services.procurement_service import (
    PurchaseBillService,
    PurchasePlanMergeService,
    PurchasePlanService,
    PurchasePlanStatusService,
    PurchaseRegisterService,
    ReturnPurchaseService,
    SupplierAppraisalService,
)
from app.utils.response import error_response, success_response

__all__ = ["procurement_bp"]

procurement_bp = Blueprint("procurement", __name__)


# ---- 采购需求 ----


@procurement_bp.get("/requisitions")
@login_required
def list_requisitions():  # type: ignore[no-untyped-def]
    """采购需求列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = PurchasePlanService.list_records(
        auditflg=params.auditflg,
        pctyp=params.pctyp,
        start_date=params.start_date,
        end_date=params.end_date,
        execution_status=params.execution_status,
        overdue_only=params.overdue_only,
        page=params.page,
        per_page=params.per_page,
        exclude_completed=params.exclude_completed,
        hide_unavailable=params.hide_unavailable,
    )
    return success_response(data=data)


@procurement_bp.get("/requisitions/<pcplanid>")
@login_required
def get_requisition(pcplanid: str):  # type: ignore[no-untyped-def]
    """采购需求详情。"""
    data = PurchasePlanService.get(pcplanid)
    if data is None:
        return error_response(message="采购需求不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/requisitions")
@login_required
def create_requisition():  # type: ignore[no-untyped-def]
    """创建采购需求。"""
    json_data = request.get_json(silent=True) or {}
    body = PurchasePlanCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [PurchasePlanDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = PurchasePlanService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.put("/requisitions/<pcplanid>")
@login_required
def update_requisition(pcplanid: str):  # type: ignore[no-untyped-def]
    """编辑采购需求（驳回后修改）。"""
    json_data = request.get_json(silent=True) or {}
    result = PurchasePlanService.update(pcplanid, json_data)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@procurement_bp.post("/requisitions/<pcplanid>/audit")
@login_required
def audit_requisition(pcplanid: str):  # type: ignore[no-untyped-def]
    """审核采购需求（支持通过/拒绝、逐行审核数量、备注）。"""
    user_cd: str = g.current_user
    json_data = request.get_json(silent=True) or {}
    result = PurchasePlanService.audit(
        pcplanid, user_cd,
        auditflg=json_data.get("auditflg", "2"),
        checkmemo=json_data.get("checkmemo", ""),
        details=json_data.get("details"),
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@procurement_bp.post("/requisitions/<pcplanid>/void")
@login_required
def void_requisition(pcplanid: str):  # type: ignore[no-untyped-def]
    """作废采购需求（仅未审批/送审中可作废，已审批需检查关联订单）。"""
    user_cd: str = g.current_user
    json_data = request.get_json(silent=True) or {}
    reason = json_data.get("reason", "")
    result = PurchasePlanService.void(pcplanid, user_cd, reason)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result, message="作废成功")


# ---- 采购订单 ----


@procurement_bp.get("/orders")
@login_required
def list_orders():  # type: ignore[no-untyped-def]
    """采购订单列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    show_voided: bool = request.args.get("show_voided", "false").lower() == "true"
    data = PurchaseRegisterService.list_records(
        suppliercd=params.suppliercd,
        auditflg=params.auditflg,
        execution_status=params.execution_status,
        page=params.page,
        per_page=params.per_page,
        show_voided=show_voided,
    )
    return success_response(data=data)


@procurement_bp.get("/orders/<rgstbillid>")
@login_required
def get_order(rgstbillid: str):  # type: ignore[no-untyped-def]
    """采购订单详情。"""
    data = PurchaseRegisterService.get(rgstbillid)
    if data is None:
        return error_response(message="采购订单不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/orders")
@login_required
def create_order():  # type: ignore[no-untyped-def]
    """创建采购订单。"""
    json_data = request.get_json(silent=True) or {}
    body = PurchaseRegisterCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [PurchaseRegisterDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = PurchaseRegisterService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.post("/orders/batch")
@login_required
def create_batch_orders():  # type: ignore[no-untyped-def]
    """批量创建采购订单（拆单 + 并单统一入口）。"""
    json_data = request.get_json(silent=True) or {}

    if "orders" not in json_data or not isinstance(json_data["orders"], list):
        return error_response(message="请求格式错误：缺少 orders 数组", code=400)

    orders = json_data["orders"]
    if len(orders) == 0:
        return error_response(message="orders 不能为空", code=400)
    if len(orders) > 10:
        return error_response(message="单次最多创建 10 个订单", code=400)

    user_cd: str = g.current_user

    try:
        result = PurchaseRegisterService.batch_create(orders, user_cd)
        return success_response(data=result, message=f"成功创建{result['count']}个采购订单", code=201)
    except ValueError as e:
        return error_response(message=str(e), code=400)
    except Exception:
        db.session.rollback()
        raise


@procurement_bp.post("/orders/batch/validate")
@login_required
def validate_batch_orders():  # type: ignore[no-untyped-def]
    """批量订单预校验。"""
    json_data = request.get_json(silent=True) or {}
    orders = json_data.get("orders", [])
    if not orders:
        return error_response(message="orders 不能为空", code=400)
    try:
        result = PurchaseRegisterService.batch_validate(orders)
        return success_response(data=result)
    except Exception:
        raise


@procurement_bp.post("/requisitions/merge-preview")
@login_required
def merge_preview():  # type: ignore[no-untyped-def]
    """智能合并预览 — 自动扫描可合并需求行并推荐供应商。"""
    try:
        result = PurchasePlanMergeService.merge_preview()
        return success_response(data=result)
    except Exception:
        raise


@procurement_bp.post("/orders/<rgstbillid>/audit")
@login_required
def audit_order(rgstbillid: str):  # type: ignore[no-untyped-def]
    """审核采购订单（支持通过/拒绝、逐行审核数量、备注）。"""
    user_cd: str = g.current_user
    json_data = request.get_json(silent=True) or {}
    result = PurchaseRegisterService.audit(
        rgstbillid, user_cd,
        auditflg=json_data.get("auditflg", "2"),
        checkmemo=json_data.get("checkmemo", ""),
        details=json_data.get("details"),
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@procurement_bp.post("/orders/<rgstbillid>/void")
@login_required
def void_order(rgstbillid: str):  # type: ignore[no-untyped-def]
    """作废采购订单。"""
    result = PurchaseRegisterService.void(rgstbillid)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@procurement_bp.put("/orders/<rgstbillid>")
@login_required
def update_order(rgstbillid: str):  # type: ignore[no-untyped-def]
    """编辑采购订单（驳回后修改）。"""
    json_data = request.get_json(silent=True) or {}
    result = PurchaseRegisterService.update(rgstbillid, json_data)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


@procurement_bp.get("/available-items")
@login_required
def list_available_items():  # type: ignore[no-untyped-def]
    """查询可采购商品及来源需求单（用于订单录入时选择来源需求单）。"""
    suppliercd: str | None = request.args.get("suppliercd")
    data = RequisitionOrderLinkRepository.get_available_items(suppliercd)
    return success_response(data=data)


# ---- 采购结算单 ----


@procurement_bp.get("/settlements")
@login_required
def list_settlements():  # type: ignore[no-untyped-def]
    """采购结算单列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    pay_type = request.args.get("pay_type") or None
    data = PurchaseBillService.list_records(
        suppliercd=params.suppliercd, auditflg=params.auditflg,
        pay_type=pay_type, start_date=params.start_date, end_date=params.end_date,
        page=params.page, per_page=params.per_page
    )
    return success_response(data=data)


@procurement_bp.get("/settlements/<pcbillid>")
@login_required
def get_settlement(pcbillid: str):  # type: ignore[no-untyped-def]
    """采购结算单详情。"""
    data = PurchaseBillService.get(pcbillid)
    if data is None:
        return error_response(message="采购结算单不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/settlements")
@login_required
def create_settlement():  # type: ignore[no-untyped-def]
    """创建采购结算单。"""
    body = PurchaseBillCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = PurchaseBillService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.put("/settlements/<pcbillid>")
@login_required
def update_settlement(pcbillid: str):  # type: ignore[no-untyped-def]
    """编辑采购结算单。"""
    json_data = request.get_json(silent=True) or {}
    body = PurchaseBillUpdate.model_validate(json_data)
    try:
        result = PurchaseBillService.update(pcbillid, body.model_dump(exclude_none=True))
        if result.get("error"):
            return error_response(message=str(result["error"]), code=400)
        return success_response(data=result)
    except ValueError as e:
        return error_response(message=str(e), code=400)


@procurement_bp.post("/settlements/<pcbillid>/audit")
@login_required
def audit_settlement(pcbillid: str):  # type: ignore[no-untyped-def]
    """审核采购结算单。"""
    json_data = request.get_json(silent=True) or {}
    auditflg = json_data.get("auditflg", "2")
    user_cd: str = g.current_user
    result = PurchaseBillService.audit(pcbillid, user_cd, auditflg)
    if result.get("error"):
        return error_response(message=str(result["error"]), code=400)
    return success_response(data=result, message="审核成功")


@procurement_bp.post("/settlements/<pcbillid>/void")
@login_required
def void_settlement(pcbillid: str):  # type: ignore[no-untyped-def]
    """作废采购结算单。"""
    result = PurchaseBillService.void(pcbillid)
    if result.get("error"):
        return error_response(message=str(result["error"]), code=400)
    return success_response(data=result, message="已作废")


@procurement_bp.get("/orders/<rgstbillid>/settleable-items")
@login_required
def get_settleable_items(rgstbillid: str):  # type: ignore[no-untyped-def]
    """查询订单的可结算商品行。"""
    try:
        return success_response(data=PurchaseBillService.get_settleable_items(rgstbillid))
    except ValueError as e:
        return error_response(message=str(e), code=404)


# ---- 采购退货 ----


@procurement_bp.get("/returns")
@login_required
def list_returns():  # type: ignore[no-untyped-def]
    """采购退货列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = ReturnPurchaseService.list_records(
        suppliercd=params.suppliercd, auditflg=params.auditflg,
        start_date=params.start_date, end_date=params.end_date,
        page=params.page, per_page=params.per_page
    )
    return success_response(data=data)


@procurement_bp.get("/returns/<pcbillid>")
@login_required
def get_return(pcbillid: str):  # type: ignore[no-untyped-def]
    """采购退货详情。"""
    data = ReturnPurchaseService.get(pcbillid)
    if data is None:
        return error_response(message="采购退货单不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/returns")
@login_required
def create_return():  # type: ignore[no-untyped-def]
    """创建采购退货单。"""
    json_data = request.get_json(silent=True) or {}
    body = ReturnPurchaseBillCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [ReturnPurchaseBillDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    create_data = body.model_dump(exclude_none=True)
    create_data["details"] = details
    data = ReturnPurchaseService.create(create_data, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.put("/returns/<pcbillid>")
@login_required
def update_return(pcbillid: str):  # type: ignore[no-untyped-def]
    """编辑采购退货单。"""
    json_data = request.get_json(silent=True) or {}
    body = ReturnPurchaseBillUpdate.model_validate(json_data)
    try:
        result = ReturnPurchaseService.update(pcbillid, body.model_dump(exclude_none=True))
        if result.get("error"):
            return error_response(message=str(result["error"]), code=400)
        return success_response(data=result)
    except ValueError as e:
        return error_response(message=str(e), code=400)


@procurement_bp.post("/returns/<pcbillid>/audit")
@login_required
def audit_return(pcbillid: str):  # type: ignore[no-untyped-def]
    """审核采购退货单。"""
    json_data = request.get_json(silent=True) or {}
    auditflg = json_data.get("auditflg", "2")
    user_cd: str = g.current_user
    result = ReturnPurchaseService.audit(pcbillid, user_cd, auditflg)
    if result.get("error"):
        return error_response(message=str(result["error"]), code=400)
    return success_response(data=result, message="审核成功")


@procurement_bp.post("/returns/<pcbillid>/void")
@login_required
def void_return(pcbillid: str):  # type: ignore[no-untyped-def]
    """作废采购退货单。"""
    result = ReturnPurchaseService.void(pcbillid)
    if result.get("error"):
        return error_response(message=str(result["error"]), code=400)
    return success_response(data=result, message="已作废")


@procurement_bp.get("/orders/<rgstbillid>/returnable-items")
@login_required
def get_returnable_items(rgstbillid: str):  # type: ignore[no-untyped-def]
    """查询订单的可退货商品行。"""
    try:
        return success_response(data=ReturnPurchaseService.get_returnable_items(rgstbillid))
    except ValueError as e:
        return error_response(message=str(e), code=404)


# ---- 供应商评价 ----


@procurement_bp.get("/supplier-appraisals")
@login_required
def list_appraisals():  # type: ignore[no-untyped-def]
    """供应商评价列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = SupplierAppraisalService.list_records(
        auditflg=params.auditflg, page=params.page, per_page=params.per_page
    )
    return success_response(data=data)


@procurement_bp.get("/supplier-appraisals/<appid>")
@login_required
def get_appraisal(appid: str):  # type: ignore[no-untyped-def]
    """供应商评价详情。"""
    data = SupplierAppraisalService.get(appid)
    if data is None:
        return error_response(message="供应商评价不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/supplier-appraisals")
@login_required
def create_appraisal():  # type: ignore[no-untyped-def]
    """创建供应商评价。"""
    json_data = request.get_json(silent=True) or {}
    body = SupplierAppraisalCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [SupplierAppraisalDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = SupplierAppraisalService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


# ---- 执行看板 ----

@procurement_bp.get("/dashboard/requisition")
@login_required
def dashboard_requisition():  # type: ignore[no-untyped-def]
    """采购需求执行看板数据（查询 v_requisition_execution 视图）。"""
    data = PurchasePlanService.dashboard_stats()
    return success_response(data=data)


@procurement_bp.get("/dashboard/order")
@login_required
def dashboard_order():  # type: ignore[no-untyped-def]
    """采购订单执行看板数据。"""
    data = PurchaseRegisterRepository.order_dashboard_stats()
    return success_response(data=data)


@procurement_bp.get("/dashboard/order-overdue")
@login_required
def dashboard_order_overdue():  # type: ignore[no-untyped-def]
    """采购订单逾期预警（审批滞留 + 交付逾期）。"""
    data = PurchaseRegisterRepository.order_overdue()
    return success_response(data=data)


@procurement_bp.get("/dashboard/item-detail")
@login_required
def dashboard_item_detail():  # type: ignore[no-untyped-def]
    """看板物料执行明细（按 itemcd 查询各需求单的执行情况）。"""
    itemcd = request.args.get("itemcd", "").strip()
    if not itemcd:
        return error_response("itemcd 不能为空", 400)
    rows = db.session.execute(
        sa.text("""
            SELECT pcplanid, lineno, plan_qty, ordered_qty, received_qty,
                   execution_status, execution_rate
            FROM v_requisition_execution
            WHERE itemcd = :itemcd
            ORDER BY pcplanid, lineno
        """),
        {"itemcd": itemcd},
    ).fetchall()
    return success_response(data=[dict(r._mapping) for r in rows])


@procurement_bp.get("/dashboard/requisition-drill")
@login_required
def dashboard_requisition_drill():  # type: ignore[no-untyped-def]
    """看板需求下钻：按状态查看需求单列表。"""
    status = request.args.get("status", "").strip()
    if not status:
        return error_response("status 不能为空", 400)
    if status == "voided":
        rows = db.session.execute(
            sa.text("SELECT pcplanid, plandate::text, auditflg, memo, '已作废' AS execution_status FROM tpc01_pcplan WHERE useflg='9' ORDER BY pcplanid")
        ).fetchall()
        return success_response(data=[dict(r._mapping) for r in rows])
    rows = db.session.execute(
        sa.text("""
            WITH plan_status AS (
                SELECT pcplanid,
                    CASE
                        WHEN COUNT(*) = SUM(CASE WHEN execution_status = '已完成' THEN 1 ELSE 0 END) THEN '已完成'
                        WHEN SUM(CASE WHEN execution_status != '未开始' THEN 1 ELSE 0 END) = 0 THEN '未开始'
                        WHEN SUM(CASE WHEN execution_status = '已下单' THEN 1 ELSE 0 END) > 0
                             AND SUM(CASE WHEN execution_status NOT IN ('已下单','已完成') THEN 1 ELSE 0 END) = 0 THEN '已下单'
                        ELSE '执行中'
                    END AS agg_status
                FROM v_requisition_execution
                GROUP BY pcplanid
            )
            SELECT ps.pcplanid, p.plandate::text, p.auditflg, p.memo, ps.agg_status AS execution_status
            FROM plan_status ps
            JOIN tpc01_pcplan p ON ps.pcplanid = p.pcplanid
            WHERE ps.agg_status = :status
            ORDER BY ps.pcplanid
        """),
        {"status": status},
    ).fetchall()
    return success_response(data=[dict(r._mapping) for r in rows])


@procurement_bp.get("/dashboard/order-drill")
@login_required
def dashboard_order_drill():  # type: ignore[no-untyped-def]
    """看板订单下钻：按执行状态或审批状态查看订单列表。"""
    status = request.args.get("status", "").strip()
    auditflg = request.args.get("auditflg", "").strip()
    if not status and not auditflg:
        return error_response("status 或 auditflg 不能为空", 400)
    query = """
        SELECT r.rgstbillid, r.suppliercd, r.auditflg, r.gendate::text, r.memo, r.useflg,
               CASE WHEN COALESCE(SUM(dt.inqty),0)=0 THEN '未入库'
                    WHEN SUM(COALESCE(dt.inqty,0))>=SUM(dt.rgsqty) THEN '已完成'
                    ELSE '部分入库' END AS execution_status
        FROM tpc12_register r
        JOIN tpc13_registerdt dt ON r.rgstbillid = dt.rgstbillid
        WHERE r.useflg != '9'
        GROUP BY r.rgstbillid
    """
    if status:
        query += " HAVING CASE WHEN COALESCE(SUM(dt.inqty),0)=0 THEN '未入库' WHEN SUM(COALESCE(dt.inqty,0))>=SUM(dt.rgsqty) THEN '已完成' ELSE '部分入库' END = :status"
    if auditflg:
        query = """
            SELECT r.rgstbillid, r.suppliercd, r.auditflg, r.gendate::text, r.memo, r.useflg
            FROM tpc12_register r
            WHERE r.useflg != '9' AND r.auditflg = :auditflg
            ORDER BY r.gendate DESC
        """
    rows = db.session.execute(sa.text(query), {"status": status, "auditflg": auditflg}).fetchall()
    return success_response(data=[dict(r._mapping) for r in rows])


# ---- 采购需求执行看板 (原 TPC03，已冻结) ----


@procurement_bp.get("/plan-status")
@login_required
def list_plan_status():  # type: ignore[no-untyped-def]
    """@deprecated 采购需求执行看板（原 TPC03，后续迁移至视图）。"""
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = PurchasePlanStatusService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@procurement_bp.get("/plan-status/<itemcd>")
@login_required
def get_plan_status(itemcd: str):  # type: ignore[no-untyped-def]
    """@deprecated 采购需求执行看板详情。"""
    data = PurchasePlanStatusService.get(itemcd)
    if data is None:
        return error_response(message="不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/plan-status")
@login_required
def create_plan_status():  # type: ignore[no-untyped-def]
    """@deprecated 创建采购需求状态汇总（已冻结，不再使用）。"""
    body = PurchasePlanStatusCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = PurchasePlanStatusService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.put("/plan-status/<itemcd>")
@login_required
def update_plan_status(itemcd: str):  # type: ignore[no-untyped-def]
    """@deprecated 更新采购需求状态汇总（已冻结，不再使用）。"""
    body = PurchasePlanStatusUpdate.model_validate(request.get_json(silent=True) or {})
    data = PurchasePlanStatusService.update(itemcd, body.model_dump(exclude_none=True))
    if data is None:
        return error_response(message="不存在", code=404)
    return success_response(data=data)
