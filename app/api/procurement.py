"""
采购管理 API。

路由前缀：/api/v1/procurement
采购计划→登记→单据→退货→供应商评价全链路。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.procurement import (
    ProcurementQuery,
    PurchaseBillCreate,
    PurchasePlanCreate,
    PurchasePlanDetailCreate,
    PurchaseRegisterCreate,
    PurchaseRegisterDetailCreate,
    SupplierAppraisalCreate,
    SupplierAppraisalDetailCreate,
)
from app.services.procurement_service import (
    PurchaseBillService,
    PurchasePlanService,
    PurchaseRegisterService,
    SupplierAppraisalService,
)
from app.utils.response import error_response, success_response

__all__ = ["procurement_bp"]

procurement_bp = Blueprint("procurement", __name__)


# ---- 采购计划 ----


@procurement_bp.get("/plans")
@login_required
def list_plans():  # type: ignore[no-untyped-def]
    """采购计划列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = PurchasePlanService.list_records(
        auditflg=params.auditflg,
        pctyp=params.pctyp,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@procurement_bp.get("/plans/<pcplanid>")
@login_required
def get_plan(pcplanid: str):  # type: ignore[no-untyped-def]
    """采购计划详情。"""
    data = PurchasePlanService.get(pcplanid)
    if data is None:
        return error_response(message="采购计划不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/plans")
@login_required
def create_plan():  # type: ignore[no-untyped-def]
    """创建采购计划。"""
    json_data = request.get_json(silent=True) or {}
    body = PurchasePlanCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [PurchasePlanDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = PurchasePlanService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.post("/plans/<pcplanid>/audit")
@login_required
def audit_plan(pcplanid: str):  # type: ignore[no-untyped-def]
    """审核采购计划。"""
    user_cd: str = g.current_user
    result = PurchasePlanService.audit(pcplanid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 采购登记 ----


@procurement_bp.get("/registers")
@login_required
def list_registers():  # type: ignore[no-untyped-def]
    """采购登记列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = PurchaseRegisterService.list_records(
        suppliercd=params.suppliercd,
        auditflg=params.auditflg,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@procurement_bp.get("/registers/<rgstbillid>")
@login_required
def get_register(rgstbillid: str):  # type: ignore[no-untyped-def]
    """采购登记详情。"""
    data = PurchaseRegisterService.get(rgstbillid)
    if data is None:
        return error_response(message="采购登记不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/registers")
@login_required
def create_register():  # type: ignore[no-untyped-def]
    """创建采购登记。"""
    json_data = request.get_json(silent=True) or {}
    body = PurchaseRegisterCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [PurchaseRegisterDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = PurchaseRegisterService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.post("/registers/<rgstbillid>/audit")
@login_required
def audit_register(rgstbillid: str):  # type: ignore[no-untyped-def]
    """审核采购登记。"""
    user_cd: str = g.current_user
    result = PurchaseRegisterService.audit(rgstbillid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 采购单据 ----


@procurement_bp.get("/bills")
@login_required
def list_bills():  # type: ignore[no-untyped-def]
    """采购单据列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = PurchaseBillService.list_records(
        whcd=params.whcd, page=params.page, per_page=params.per_page
    )
    return success_response(data=data)


@procurement_bp.get("/bills/<pcbillid>")
@login_required
def get_bill(pcbillid: str):  # type: ignore[no-untyped-def]
    """采购单据详情。"""
    data = PurchaseBillService.get(pcbillid)
    if data is None:
        return error_response(message="采购单据不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/bills")
@login_required
def create_bill():  # type: ignore[no-untyped-def]
    """创建采购单据。"""
    body = PurchaseBillCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = PurchaseBillService.create(body.model_dump(exclude_none=True), user_cd)
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
