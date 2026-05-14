"""质检管理 API。

POST /api/v1/qc 等写操作由采购入库流程触发，F2 阶段仅提供列表与详情查询。
"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.extensions import db
from app.models.warehouse import QcResult, QcResultDt, QcResultEid
from app.utils.response import error_response, success_response

qc_bp = Blueprint("qc", __name__)


@qc_bp.get("")
@login_required
def list_qc_results():  # type: ignore[no-untyped-def]
    """质检结果列表（分页）。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search")

    q = db.session.query(QcResult)
    if search:
        q = q.filter(
            db.or_(
                QcResult.qcbillid.ilike(f"%{search}%"),
                QcResult.refbillid.ilike(f"%{search}%"),
                QcResult.itemcd.ilike(f"%{search}%"),
                QcResult.eid.ilike(f"%{search}%"),
            )
        )
    q = q.order_by(QcResult.gendate.desc())

    total = q.count()
    rows = q.offset((page - 1) * per_page).limit(per_page).all()
    return success_response(
        data={"items": [r.to_dict() for r in rows], "total": total}
    )


@qc_bp.get("/<qcbillid>")
@login_required
def get_qc_result(qcbillid: str):  # type: ignore[no-untyped-def]
    """质检结果详情（含明细-按产品 和 明细-按设备序列号）。"""
    qc = db.session.get(QcResult, qcbillid)
    if not qc:
        return error_response("质检单不存在", 404)

    data = qc.to_dict()
    data["details"] = [
        dt.to_dict()
        for dt in db.session.query(QcResultDt)
        .filter(QcResultDt.qcbillid == qcbillid)
        .order_by(QcResultDt.lineno)
        .all()
    ]
    data["eid_details"] = [
        e.to_dict()
        for e in db.session.query(QcResultEid)
        .filter(QcResultEid.qcbillid == qcbillid)
        .order_by(QcResultEid.lineno)
        .all()
    ]
    return success_response(data=data)
