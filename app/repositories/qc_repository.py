"""质检管理数据访问层。"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import g
from sqlalchemy import func

from app.extensions import db
from app.models.warehouse import QcResult, QcResultDt, QcResultEid


def _gen_qc_id() -> str:
    """生成质检单号 (QC + YYMMDD + 3位序号)。"""
    today = datetime.now(timezone.utc).strftime("%y%m%d")
    prefix = f"QC{today}"
    row = db.session.execute(
        db.text(
            "SELECT COALESCE(MAX(qcbillid), :prefix) FROM tqc10_result "
            "WHERE qcbillid LIKE :pattern"
        ),
        {"prefix": prefix, "pattern": f"{prefix}%"},
    ).fetchone()
    last_id = row[0] if row else prefix
    seq = int(last_id[len(prefix):] or "0") + 1
    return f"{prefix}{seq:03d}"


class QcRepository:
    """质检结果数据访问。"""

    @staticmethod
    def list_results(
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
    ) -> tuple[list[QcResult], int]:
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
        return rows, total

    @staticmethod
    def get_result(qcbillid: str) -> QcResult | None:
        return db.session.get(QcResult, qcbillid)

    @staticmethod
    def list_details(qcbillid: str) -> list[QcResultDt]:
        return list(
            db.session.query(QcResultDt)
            .filter(QcResultDt.qcbillid == qcbillid)
            .order_by(QcResultDt.lineno)
            .all()
        )

    @staticmethod
    def list_eid_details(qcbillid: str) -> list[QcResultEid]:
        return list(
            db.session.query(QcResultEid)
            .filter(QcResultEid.qcbillid == qcbillid)
            .order_by(QcResultEid.lineno)
            .all()
        )

    @staticmethod
    def create(data: dict[str, object]) -> QcResult:
        qc = QcResult(**data)
        qc.qcbillid = _gen_qc_id()
        qc.opercd = g.get("current_user", "")
        qc.gendate = datetime.now(timezone.utc)
        qc.auditflg = "0"
        db.session.add(qc)
        db.session.commit()
        return qc

    @staticmethod
    def add_detail(
        qcbillid: str,
        lineno: int,
        data: dict[str, object],
    ) -> QcResultDt:
        detail = QcResultDt(qcbillid=qcbillid, lineno=lineno, **data)
        db.session.add(detail)
        return detail

    @staticmethod
    def add_eid_detail(
        qcbillid: str,
        lineno: int,
        data: dict[str, object],
    ) -> QcResultEid:
        detail = QcResultEid(qcbillid=qcbillid, lineno=lineno, **data)
        db.session.add(detail)
        return detail

    @staticmethod
    def audit(qc: QcResult, auditor: str) -> QcResult:
        qc.auditflg = "1"
        qc.auditman = auditor
        qc.auditdate = datetime.now(timezone.utc)
        db.session.commit()
        return qc

    @staticmethod
    def get_stats() -> list[dict[str, object]]:
        """按质检状态统计。"""
        rows = (
            db.session.query(
                QcResult.qcstatus,
                func.count(QcResult.qcbillid).label("cnt"),
            )
            .group_by(QcResult.qcstatus)
            .order_by(QcResult.qcstatus)
            .all()
        )
        return [{"qcstatus": r.qcstatus or "未知", "cnt": r.cnt} for r in rows]
