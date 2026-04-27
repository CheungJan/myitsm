"""
租金/费用结算 API（Tier-2 G4）。

路由前缀：/api/v1/billing
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.billing import (
    BillCreate,
    BillingBatchCreate,
    BillingBatchUpdate,
    BillingRuleCreate,
    BillingRuleUpdate,
    BillUpdate,
)
from app.services.billing_service import (
    BillingBatchService,
    BillingRuleService,
    BillService,
)
from app.utils.response import error_response, success_response

__all__ = ["billing_bp"]

billing_bp = Blueprint("billing", __name__)


# ---- 结算规则 ----


@billing_bp.get("/rules")
@login_required
def list_rules():  # type: ignore[no-untyped-def]
    """结算规则列表。"""
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = BillingRuleService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@billing_bp.get("/rules/<rule_id>")
@login_required
def get_rule(rule_id: str):  # type: ignore[no-untyped-def]
    """结算规则详情。"""
    data = BillingRuleService.get(rule_id)
    if data is None:
        return error_response(message="规则不存在", code=404)
    return success_response(data=data)


@billing_bp.post("/rules")
@login_required
def create_rule():  # type: ignore[no-untyped-def]
    """创建结算规则。"""
    body = BillingRuleCreate(**request.get_json(force=True))
    data = BillingRuleService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@billing_bp.put("/rules/<rule_id>")
@login_required
def update_rule(rule_id: str):  # type: ignore[no-untyped-def]
    """更新结算规则。"""
    body = BillingRuleUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = BillingRuleService.update(rule_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="规则不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 账单 ----


@billing_bp.get("/bills")
@login_required
def list_bills():  # type: ignore[no-untyped-def]
    """账单列表。"""
    custcd = request.args.get("custcd")
    status = request.args.get("status")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = BillService.list_all(custcd=custcd, status=status, page=page, per_page=per_page)
    return success_response(data=data)


@billing_bp.get("/bills/<bill_id>")
@login_required
def get_bill(bill_id: str):  # type: ignore[no-untyped-def]
    """账单详情（含明细）。"""
    data = BillService.get(bill_id)
    if data is None:
        return error_response(message="账单不存在", code=404)
    return success_response(data=data)


@billing_bp.post("/bills")
@login_required
def create_bill():  # type: ignore[no-untyped-def]
    """创建账单。"""
    body = BillCreate(**request.get_json(force=True))
    bill_data = body.model_dump(exclude_none=True)
    details = bill_data.pop("details", None)
    data = BillService.create(bill_data, details)
    return success_response(data=data, message="创建成功", code=201)


@billing_bp.put("/bills/<bill_id>")
@login_required
def update_bill(bill_id: str):  # type: ignore[no-untyped-def]
    """更新账单。"""
    body = BillUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = BillService.update(bill_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="账单不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 结算批次 ----


@billing_bp.get("/batches")
@login_required
def list_batches():  # type: ignore[no-untyped-def]
    """结算批次列表。"""
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = BillingBatchService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@billing_bp.get("/batches/<batch_id>")
@login_required
def get_batch(batch_id: str):  # type: ignore[no-untyped-def]
    """结算批次详情。"""
    data = BillingBatchService.get(batch_id)
    if data is None:
        return error_response(message="批次不存在", code=404)
    return success_response(data=data)


@billing_bp.post("/batches")
@login_required
def create_batch():  # type: ignore[no-untyped-def]
    """创建结算批次。"""
    body = BillingBatchCreate(**request.get_json(force=True))
    data = BillingBatchService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@billing_bp.put("/batches/<batch_id>")
@login_required
def update_batch(batch_id: str):  # type: ignore[no-untyped-def]
    """更新结算批次。"""
    body = BillingBatchUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = BillingBatchService.update(batch_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="批次不存在", code=404)
    return success_response(data=data, message="更新成功")
