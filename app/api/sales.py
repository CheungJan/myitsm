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
    SalesBillCreate,
    SalesExtendCreate,
    SalesExtendDetailCreate,
    SalesQuery,
)
from app.services.sales_service import (
    PlanCustService,
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
    data = PlanCustService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@sales_bp.put("/plans/<planno>")
@login_required
def update_plan(planno: str):  # type: ignore[no-untyped-def]
    """更新预计划。"""
    body = PlanCustUpdate.model_validate(request.get_json(silent=True) or {})
    data = PlanCustService.update(planno, body.model_dump(exclude_unset=True))
    if data is None:
        return error_response(message="预计划不存在", code=404)
    return success_response(data=data)


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
