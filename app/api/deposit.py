"""
押金管理 API。

路由前缀：/api/v1/deposit
"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.schemas.deposit import (
    DepositCreate,
    DepositDetailCreate,
    DepositPosModelCreate,
    DepositPosModelUpdate,
    DepositUpdate,
)
from app.services.deposit_service import (
    DepositDetailService,
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
    data = DepositService.update(custcd, body.model_dump(exclude_none=True))
    if data is None:
        return error_response(message="押金记录不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 押金变更明细 ----


@deposit_bp.get("/deposits/<custcd>/details")
@login_required
def list_deposit_details(custcd: str):  # type: ignore[no-untyped-def]
    """押金变更明细列表。"""
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = DepositDetailService.list_by_customer(custcd, page, per_page)
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
    data = DepositPosModelService.update(model_cd, body.model_dump(exclude_none=True))
    if data is None:
        return error_response(message="型号标准不存在", code=404)
    return success_response(data=data, message="更新成功")
