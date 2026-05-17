"""
押金管理 API。

路由前缀：/api/v1/deposit
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.deposit import (
    DepositCreate,
    DepositDetailCreate,
    DepositIOQuery,
    DepositPosModelCreate,
    DepositPosModelUpdate,
    DepositUpdate,
)
from app.services.deposit_service import (
    DepositDetailService,
    DepositIOService,
    DepositPosModelService,
    DepositService,
)
from app.utils.response import error_response, success_response

__all__ = ["deposit_bp"]

deposit_bp = Blueprint("deposit", __name__)


# ---- 押金主记录 ----


@deposit_bp.get("/deposits")
@login_required
def list_deposits():  # type: ignore[no-untyped-def]
    """押金列表。"""
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = DepositService.list_all(page, per_page)
    return success_response(data=data)


@deposit_bp.get("/deposits/<custcd>")
@login_required
def get_deposit(custcd: str):  # type: ignore[no-untyped-def]
    """押金详情。"""
    data = DepositService.get(custcd)
    if data is None:
        return error_response(message="押金记录不存在", code=404)
    return success_response(data=data)


@deposit_bp.post("/deposits")
@login_required
def create_deposit():  # type: ignore[no-untyped-def]
    """创建押金记录。"""
    body = DepositCreate(**request.get_json(force=True))
    data = DepositService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@deposit_bp.put("/deposits/<custcd>")
@login_required
def update_deposit(custcd: str):  # type: ignore[no-untyped-def]
    """更新押金记录。"""
    body = DepositUpdate(**request.get_json(force=True))
    data = DepositService.update(custcd, body.model_dump(exclude_unset=True))
    if data is None:
        return error_response(message="押金记录不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 押金变更明细 ----


@deposit_bp.get("/deposits/details")
@login_required
def list_all_deposit_details():  # type: ignore[no-untyped-def]
    """押金变更明细列表（全部）。"""
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = DepositDetailService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@deposit_bp.get("/deposits/<custcd>/details")
@login_required
def list_deposit_details(custcd: str):  # type: ignore[no-untyped-def]
    """押金变更明细列表（按客户）。"""
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = DepositDetailService.list_by_customer(custcd, page, per_page)
    return success_response(data=data)


# Backward compat: /deposit/details → /deposits/details
@deposit_bp.get("/details")
@login_required
def list_all_deposit_details_short():  # type: ignore[no-untyped-def]
    """押金变更明细列表。"""
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = DepositDetailService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@deposit_bp.post("/deposits/details")
@login_required
def create_deposit_detail():  # type: ignore[no-untyped-def]
    """创建押金变更明细。"""
    body = DepositDetailCreate(**request.get_json(force=True))
    data = DepositDetailService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


# ---- 设备型号押金标准 ----


@deposit_bp.get("/deposit-models")
@login_required
def list_deposit_models():  # type: ignore[no-untyped-def]
    """设备型号押金标准列表。"""
    data = DepositPosModelService.list_all()
    return success_response(data=data)


@deposit_bp.post("/deposit-models")
@login_required
def create_deposit_model():  # type: ignore[no-untyped-def]
    """创建设备型号押金标准。"""
    body = DepositPosModelCreate(**request.get_json(force=True))
    data = DepositPosModelService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@deposit_bp.put("/deposit-models/<model_cd>")
@login_required
def update_deposit_model(model_cd: str):  # type: ignore[no-untyped-def]
    """更新设备型号押金标准。"""
    body = DepositPosModelUpdate(**request.get_json(force=True))
    data = DepositPosModelService.update(model_cd, body.model_dump(exclude_unset=True))
    if data is None:
        return error_response(message="型号标准不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 押金出入流水 ----


@deposit_bp.get("/deposits/io")
@login_required
def list_deposit_io():  # type: ignore[no-untyped-def]
    """押金出入流水列表。"""
    params = DepositIOQuery.model_validate(request.args.to_dict())
    data = DepositIOService.list_records(
        custcd=params.custcd,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@deposit_bp.post("/deposits/<custcd>/audit")
@login_required
def audit_deposit(custcd: str):  # type: ignore[no-untyped-def]
    """审核押金记录。"""
    from datetime import UTC, datetime

    from app.extensions import db as _db
    from app.models.deposit import Deposit
    record = _db.session.get(Deposit, custcd)
    if record is None:
        return error_response(message="押金记录不存在", code=404)
    if record.auditflg == "1":
        return error_response(message="已审核", code=400)
    user_cd: str = g.current_user
    record.auditflg = "1"
    record.auditman = user_cd
    record.auditdate = datetime.now(UTC)
    _db.session.commit()
    return success_response(data=record.to_dict(), message="审核成功")


@deposit_bp.get("/stats")
@login_required
def deposit_stats():  # type: ignore[no-untyped-def]
    """押金汇总统计。"""
    from sqlalchemy import func

    from app.extensions import db as _db
    from app.models.deposit import Deposit, DepositIO
    total_customers = _db.session.query(func.count(Deposit.custcd)).scalar() or 0
    total_amount = _db.session.query(func.coalesce(func.sum(Deposit.amount_money), 0)).scalar() or 0
    io_count = _db.session.query(func.count(DepositIO.id)).scalar() or 0
    return success_response(data={
        "total_customers": total_customers,
        "total_deposit_amount": float(total_amount),
        "io_record_count": io_count,
    })


# ---- 标签管理 (TMM40_LABEL) ----


@deposit_bp.get("/labels")
@login_required
def list_labels():  # type: ignore[no-untyped-def]
    """标签列表（占位 — 待 TMM40_LABEL 表建迁移后启用）。"""
    return success_response(data={"items": [], "total": 0, "message": "TMM40_LABEL 表待迁移创建"})
