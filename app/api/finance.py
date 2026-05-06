"""
财务应收应付 API（Tier-2 G5）。

路由前缀：/api/v1/finance
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.finance import (
    AccountCreate,
    AccountUpdate,
    DepreciationCreate,
    DepreciationUpdate,
    PayableCreate,
    PayableUpdate,
    PaymentCreate,
    ReceivableCreate,
    ReceivableUpdate,
)
from app.services.finance_service import (
    AccountService,
    DepreciationService,
    PayableService,
    PaymentService,
    ReceivableService,
)
from app.utils.response import error_response, success_response

__all__ = ["finance_bp"]

finance_bp = Blueprint("finance", __name__)


# ---- 会计科目 ----


@finance_bp.get("/accounts")
@login_required
def list_accounts():  # type: ignore[no-untyped-def]
    """会计科目列表。"""
    account_type = request.args.get("account_type")
    data = AccountService.list_all(account_type=account_type)
    return success_response(data=data)


@finance_bp.get("/accounts/<account_cd>")
@login_required
def get_account(account_cd: str):  # type: ignore[no-untyped-def]
    """科目详情。"""
    data = AccountService.get(account_cd)
    if data is None:
        return error_response(message="科目不存在", code=404)
    return success_response(data=data)


@finance_bp.post("/accounts")
@login_required
def create_account():  # type: ignore[no-untyped-def]
    """创建科目。"""
    body = AccountCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = AccountService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@finance_bp.put("/accounts/<account_cd>")
@login_required
def update_account(account_cd: str):  # type: ignore[no-untyped-def]
    """更新科目。"""
    body = AccountUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = AccountService.update(account_cd, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="科目不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 应收 ----


@finance_bp.get("/receivables")
@login_required
def list_receivables():  # type: ignore[no-untyped-def]
    """应收列表。"""
    custcd = request.args.get("custcd")
    status = request.args.get("status")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = ReceivableService.list_all(custcd=custcd, status=status, page=page, per_page=per_page)
    return success_response(data=data)


@finance_bp.get("/receivables/<ar_id>")
@login_required
def get_receivable(ar_id: str):  # type: ignore[no-untyped-def]
    """应收详情。"""
    data = ReceivableService.get(ar_id)
    if data is None:
        return error_response(message="应收记录不存在", code=404)
    return success_response(data=data)


@finance_bp.post("/receivables")
@login_required
def create_receivable():  # type: ignore[no-untyped-def]
    """创建应收。"""
    body = ReceivableCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = ReceivableService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@finance_bp.put("/receivables/<ar_id>")
@login_required
def update_receivable(ar_id: str):  # type: ignore[no-untyped-def]
    """更新应收。"""
    body = ReceivableUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = ReceivableService.update(ar_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="应收记录不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 应付 ----


@finance_bp.get("/payables")
@login_required
def list_payables():  # type: ignore[no-untyped-def]
    """应付列表。"""
    supp_cd = request.args.get("supp_cd")
    status = request.args.get("status")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = PayableService.list_all(supp_cd=supp_cd, status=status, page=page, per_page=per_page)
    return success_response(data=data)


@finance_bp.get("/payables/<ap_id>")
@login_required
def get_payable(ap_id: str):  # type: ignore[no-untyped-def]
    """应付详情。"""
    data = PayableService.get(ap_id)
    if data is None:
        return error_response(message="应付记录不存在", code=404)
    return success_response(data=data)


@finance_bp.post("/payables")
@login_required
def create_payable():  # type: ignore[no-untyped-def]
    """创建应付。"""
    body = PayableCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = PayableService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@finance_bp.put("/payables/<ap_id>")
@login_required
def update_payable(ap_id: str):  # type: ignore[no-untyped-def]
    """更新应付。"""
    body = PayableUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = PayableService.update(ap_id, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="应付记录不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 收付款 ----


@finance_bp.get("/payments")
@login_required
def list_payments():  # type: ignore[no-untyped-def]
    """收付款列表。"""
    pay_type = request.args.get("pay_type")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = PaymentService.list_all(pay_type=pay_type, page=page, per_page=per_page)
    return success_response(data=data)


@finance_bp.post("/payments")
@login_required
def create_payment():  # type: ignore[no-untyped-def]
    """创建收付款。"""
    body = PaymentCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = PaymentService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


# ---- 设备折旧 ----


@finance_bp.get("/depreciations")
@login_required
def list_depreciations():  # type: ignore[no-untyped-def]
    """折旧列表。"""
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = DepreciationService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@finance_bp.get("/depreciations/<eid>")
@login_required
def get_depreciation(eid: str):  # type: ignore[no-untyped-def]
    """折旧详情。"""
    data = DepreciationService.get_by_eid(eid)
    if data is None:
        return error_response(message="折旧记录不存在", code=404)
    return success_response(data=data)


@finance_bp.post("/depreciations")
@login_required
def create_depreciation():  # type: ignore[no-untyped-def]
    """创建折旧记录。"""
    body = DepreciationCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = DepreciationService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@finance_bp.put("/depreciations/<eid>")
@login_required
def update_depreciation(eid: str):  # type: ignore[no-untyped-def]
    """更新折旧记录。"""
    body = DepreciationUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = DepreciationService.update(eid, body.model_dump(exclude_unset=True), user_cd)
    if data is None:
        return error_response(message="折旧记录不存在", code=404)
    return success_response(data=data, message="更新成功")
