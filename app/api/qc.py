"""质检管理 API。"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import auditor_required, login_required
from app.schemas.qc import QcAudit, QcCreate
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

@qc_bp.get("/ov5-completion")
@login_required
def get_ov5_completion():  # type: ignore[no-untyped-def]
    """OV=5质检出库完成情况统计。"""
    return success_response(data=QcService.get_ov5_completion())


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
    """创建质检单（含明细）。old_batch_id 存在时先作废旧批次再建新。"""
    body = request.get_json(silent=True) or {}
    try:
        req = QcCreate(**{k: v for k, v in body.items() if k not in ("old_batch_id", "batch_id", "draft_type")})
    except Exception as e:
        return error_response(str(e), 400)
    data = req.model_dump(exclude={"details", "eid_details"})
    if "batch_id" in body:
        data["batch_id"] = body["batch_id"]
    if "draft_type" in body:
        data["draft_type"] = body["draft_type"]
    result = QcService.create(
        data=data,
        details=req.details,
        eid_details=req.eid_details,
        old_batch_id=body.get("old_batch_id"),
    )
    if not result.get("success", True):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result, code=201)


@qc_bp.post("/<qcbillid>/audit")
@auditor_required
def audit_qc_result(qcbillid: str):  # type: ignore[no-untyped-def]
    """审核质检单（通过/退回）。"""
    user_cd: str = request.headers.get("X-User-Cd", request.args.get("user_cd", "system"))
    try:
        req = QcAudit(**(request.get_json(silent=True) or {}))
    except Exception as e:
        return error_response(str(e), 400)
    result = QcService.audit(
        qcbillid, auditor=user_cd,
        auditflg=req.auditflg,
        checkmemo=req.checkmemo,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    msg = "审核通过" if req.auditflg == "1" else "已退回"
    return success_response(message=msg)


@qc_bp.post("/<qcbillid>/unaudit")
@auditor_required
def unaudit_qc_result(qcbillid: str):  # type: ignore[no-untyped-def]
    """QC 反审核。"""
    user_cd: str = request.headers.get("X-User-Cd", request.args.get("user_cd", "system"))
    result = QcService.unaudit(qcbillid, auditor=user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(message="已反审核")


@qc_bp.post("/<qcbillid>/void")
@login_required
def void_qc_result(qcbillid: str):  # type: ignore[no-untyped-def]
    """作废质检单（仅草稿/已退回）。"""
    user_cd: str = request.headers.get("X-User-Cd", request.args.get("user_cd", "system"))
    result = QcService.void(qcbillid, operator=user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(message="已作废")


@qc_bp.get("/eids-by-refbillid/<refbillid>")
@login_required
def get_qc_eids_by_refbillid(refbillid: str):  # type: ignore[no-untyped-def]
    """获取指定来源单据的所有质检EID记录（用于FQC回显IPQC的配件EID）。"""
    from app.repositories.qc_repository import QcRepository
    eids = QcRepository.get_eids_by_refbillid(refbillid)
    return success_response(data=[e.to_dict() for e in eids])


# ── 批次层端点 ──

@qc_bp.get("/batches")
@login_required
def list_qc_batches():  # type: ignore[no-untyped-def]
    """按批次聚合查询质检结果。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search")
    auditflg = request.args.get("auditflg")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    eid = request.args.get("eid")
    batches, total = QcService.list_batches(
        page=page, per_page=per_page, search=search, auditflg=auditflg,
        start_date=start_date, end_date=end_date, eid=eid,
    )
    return success_response(data={"items": batches, "total": total})


@qc_bp.get("/batches/<batch_id>")
@login_required
def get_qc_batch(batch_id: str):  # type: ignore[no-untyped-def]
    """获取批次详情（含所有子记录及明细）。"""
    result = QcService.get_batch_details(batch_id)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=404)
    return success_response(data=result)


@qc_bp.post("/batches/<batch_id>/audit")
@auditor_required
def audit_qc_batch(batch_id: str):  # type: ignore[no-untyped-def]
    """批次审核（通过/退回）。"""
    body = request.get_json(silent=True) or {}
    try:
        req = QcAudit(**body)
    except Exception as e:
        return error_response(str(e), 400)
    user_cd: str = request.headers.get("X-User-Cd", request.args.get("user_cd", "system"))
    result = QcService.batch_audit(
        batch_id, auditor=user_cd,
        auditflg=req.auditflg,
        checkmemo=req.checkmemo,
    )
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    msg = "批次审核通过" if req.auditflg == "1" else "批次已退回"
    return success_response(message=msg)


@qc_bp.post("/batches/<batch_id>/void")
@auditor_required
def void_qc_batch(batch_id: str):  # type: ignore[no-untyped-def]
    """批次作废。"""
    user_cd: str = request.headers.get("X-User-Cd", request.args.get("user_cd", "system"))
    result = QcService.batch_void(batch_id, operator=user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(message="批次已作废")


@qc_bp.post("/batches/<batch_id>/replenish")
@login_required
def replenish_qc_batch(batch_id: str):  # type: ignore[no-untyped-def]
    """申请补料：为批次中的不良品（BF/BH/TH）创建 OV=8 出库单。"""
    body = request.get_json(silent=True) or {}
    user_cd: str = request.headers.get("X-User-Cd", request.args.get("user_cd", "system"))
    replenish_qty: dict[str, int] | None = body.get("replenish_qty")
    result = QcService.replenish(batch_id, operator=user_cd, replenish_qty=replenish_qty)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(
        data=result,
        message=f"补料出库单 {result.get('ov_billid', '')} 已生成",
    )
