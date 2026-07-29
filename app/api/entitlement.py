"""Entitlement 权益判定 API（P2 扩展）。

路由前缀：/api/v1/entitlement
特殊客户协议 + 维保合同 CRUD。
"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.services.entitlement_crud_service import (
    ServiceContractService,
    SpecialAgreementService,
)
from app.utils.response import error_response, success_response

__all__ = ["entitlement_bp"]

entitlement_bp = Blueprint("entitlement", __name__)


# ---- 特殊客户协议 ----


@entitlement_bp.get("/special-agreements")
@login_required
def list_special_agreements():  # type: ignore[no-untyped-def]
    """特殊客户协议列表。"""
    filters = {}
    if request.args.get("cust_cd"):
        filters["cust_cd"] = request.args["cust_cd"]
    if request.args.get("useflg"):
        filters["useflg"] = request.args["useflg"]
    data = SpecialAgreementService.list(filters)
    return success_response(data=data)


@entitlement_bp.get("/special-agreements/<agreement_id>")
@login_required
def get_special_agreement(agreement_id: str):  # type: ignore[no-untyped-def]
    """获取特殊客户协议详情。"""
    data = SpecialAgreementService.get(agreement_id)
    if data is None:
        return error_response(message="协议不存在", code=404)
    return success_response(data=data)


@entitlement_bp.post("/special-agreements")
@login_required
def create_special_agreement():  # type: ignore[no-untyped-def]
    """创建特殊客户协议。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = SpecialAgreementService.create(body, creator=user_cd)
    return success_response(data=data, code=201)


@entitlement_bp.put("/special-agreements/<agreement_id>")
@login_required
def update_special_agreement(agreement_id: str):  # type: ignore[no-untyped-def]
    """更新特殊客户协议。"""
    body = request.get_json(force=True)
    data = SpecialAgreementService.update(agreement_id, body)
    if data is None:
        return error_response(message="协议不存在", code=404)
    return success_response(data=data)


# ---- 维保合同 ----


@entitlement_bp.get("/service-contracts")
@login_required
def list_service_contracts():  # type: ignore[no-untyped-def]
    """维保合同列表。"""
    filters = {}
    if request.args.get("cust_cd"):
        filters["cust_cd"] = request.args["cust_cd"]
    if request.args.get("eid"):
        filters["eid"] = request.args["eid"]
    if request.args.get("useflg"):
        filters["useflg"] = request.args["useflg"]
    data = ServiceContractService.list(filters)
    return success_response(data=data)


@entitlement_bp.get("/service-contracts/<contract_id>")
@login_required
def get_service_contract(contract_id: str):  # type: ignore[no-untyped-def]
    """获取维保合同详情。"""
    data = ServiceContractService.get(contract_id)
    if data is None:
        return error_response(message="合同不存在", code=404)
    return success_response(data=data)


@entitlement_bp.post("/service-contracts")
@login_required
def create_service_contract():  # type: ignore[no-untyped-def]
    """创建维保合同。"""
    body = request.get_json(force=True)
    user_cd: str = request.headers.get("X-User-Cd", "system")
    data = ServiceContractService.create(body, creator=user_cd)
    return success_response(data=data, code=201)


@entitlement_bp.put("/service-contracts/<contract_id>")
@login_required
def update_service_contract(contract_id: str):  # type: ignore[no-untyped-def]
    """更新维保合同。"""
    body = request.get_json(force=True)
    data = ServiceContractService.update(contract_id, body)
    if data is None:
        return error_response(message="合同不存在", code=404)
    return success_response(data=data)
