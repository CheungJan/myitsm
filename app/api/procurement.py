"""
采购管理 API。

路由前缀：/api/v1/procurement
采购需求→订单→结算单→退货→供应商评价全链路。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.repositories.procurement_repository import (
    RequisitionOrderLinkRepository,
)
from app.schemas.procurement import (
    ProcurementQuery,
    PurchaseBillCreate,
    PurchasePlanCreate,
    PurchasePlanDetailCreate,
    PurchasePlanStatusCreate,
    PurchasePlanStatusUpdate,
    PurchaseRegisterCreate,
    PurchaseRegisterDetailCreate,
    ReturnPurchaseBillCreate,
    ReturnPurchaseBillDetailCreate,
    SupplierAppraisalCreate,
    SupplierAppraisalDetailCreate,
)
from app.services.procurement_service import (
    PurchaseBillService,
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
        page=params.page,
        per_page=params.per_page,
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


# ---- 采购订单 ----


@procurement_bp.get("/orders")
@login_required
def list_orders():  # type: ignore[no-untyped-def]
    """采购订单列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = PurchaseRegisterService.list_records(
        suppliercd=params.suppliercd,
        auditflg=params.auditflg,
        page=params.page,
        per_page=params.per_page,
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
    data = PurchaseBillService.list_records(
        whcd=params.whcd, page=params.page, per_page=params.per_page
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


# ---- 采购退货 ----


@procurement_bp.get("/returns")
@login_required
def list_returns():  # type: ignore[no-untyped-def]
    """采购退货列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = ReturnPurchaseService.list_records(
        whcd=params.whcd, page=params.page, per_page=params.per_page
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
    data = ReturnPurchaseService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


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
