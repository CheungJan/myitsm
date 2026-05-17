"""质检管理 API。"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.schemas.qc import QcCreate
from app.services.qc_service import QcService
from app.utils.response import error_response, success_response

qc_bp = Blueprint("qc", __name__)


@qc_bp.get("")
@login_required
def list_qc_results():  # type: ignore[no-untyped-def]
    """质检结果列表（分页）。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search")
    return success_response(
        data=QcService.list_results(page=page, per_page=per_page, search=search)
    )


@qc_bp.get("/stats")
@login_required
def get_qc_stats():  # type: ignore[no-untyped-def]
    """质检状态统计。"""
    return success_response(data=QcService.get_stats())


@qc_bp.get("/<qcbillid>")
@login_required
def get_qc_result(qcbillid: str):  # type: ignore[no-untyped-def]
    """质检结果详情（含明细-按产品 和 明细-按设备序列号）。"""
    data = QcService.get_result(qcbillid)
    if data is None:
        return error_response("质检单不存在", 404)
    return success_response(data=data)


@qc_bp.post("")
@login_required
def create_qc_result():  # type: ignore[no-untyped-def]
    """创建质检单（含明细）。"""
    body = request.get_json(silent=True) or {}
    try:
        req = QcCreate(**body)
    except Exception as e:
        return error_response(str(e), 400)
    return success_response(
        data=QcService.create(
            data=req.model_dump(exclude={"details", "eid_details"}),
            details=req.details,
            eid_details=req.eid_details,
        ),
        code=201,
    )


@qc_bp.post("/<qcbillid>/audit")
@login_required
def audit_qc_result(qcbillid: str):  # type: ignore[no-untyped-def]
    """审核质检单。"""
    user_cd: str = request.headers.get("X-User-Cd", request.args.get("user_cd", "system"))
    result = QcService.audit(qcbillid, auditor=user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(message="审核成功")
