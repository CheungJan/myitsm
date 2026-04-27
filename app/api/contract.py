"""
合同与发票管理 API（Tier-1 扩展）。

路由前缀：/api/v1/contract
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    InvoiceCreate,
    InvoiceUpdate,
)
from app.services.contract_service import ContractService, InvoiceService
from app.utils.response import error_response, success_response

__all__ = ["contract_bp"]

contract_bp = Blueprint("contract", __name__)


# ---- 合同管理 ----


@contract_bp.get("/contracts")
@login_required
def list_contracts():  # type: ignore[no-untyped-def]
    """合同列表。"""
    classcd = request.args.get("classcd")
    busityp = request.args.get("busityp")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = ContractService.list_all(classcd, busityp, page, per_page)
    return success_response(data=data)


@contract_bp.get("/contracts/<htbh>")
@login_required
def get_contract(htbh: str):  # type: ignore[no-untyped-def]
    """合同详情。"""
    data = ContractService.get(htbh)
    if data is None:
        return error_response(message="合同不存在", code=404)
    return success_response(data=data)


@contract_bp.post("/contracts")
@login_required
def create_contract():  # type: ignore[no-untyped-def]
    """创建合同。"""
    body = ContractCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = ContractService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@contract_bp.put("/contracts/<htbh>")
@login_required
def update_contract(htbh: str):  # type: ignore[no-untyped-def]
    """更新合同。"""
    body = ContractUpdate(**request.get_json(force=True))
    data = ContractService.update(htbh, body.model_dump(exclude_none=True))
    if data is None:
        return error_response(message="合同不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 发票管理 ----


@contract_bp.get("/invoices")
@login_required
def list_invoices():  # type: ignore[no-untyped-def]
    """发票列表。"""
    htbh = request.args.get("htbh")
    classcd = request.args.get("classcd")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = InvoiceService.list_all(htbh, classcd, page, per_page)
    return success_response(data=data)


@contract_bp.get("/invoices/<fpbh>")
@login_required
def get_invoice(fpbh: str):  # type: ignore[no-untyped-def]
    """发票详情。"""
    data = InvoiceService.get(fpbh)
    if data is None:
        return error_response(message="发票不存在", code=404)
    return success_response(data=data)


@contract_bp.post("/invoices")
@login_required
def create_invoice():  # type: ignore[no-untyped-def]
    """创建发票。"""
    body = InvoiceCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = InvoiceService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@contract_bp.put("/invoices/<fpbh>")
@login_required
def update_invoice(fpbh: str):  # type: ignore[no-untyped-def]
    """更新发票。"""
    body = InvoiceUpdate(**request.get_json(force=True))
    data = InvoiceService.update(fpbh, body.model_dump(exclude_none=True))
    if data is None:
        return error_response(message="发票不存在", code=404)
    return success_response(data=data, message="更新成功")
