"""质检管理业务逻辑层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.qc_repository import QcRepository


class QcService:
    """质检结果业务逻辑。"""

    @staticmethod
    def list_results(
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
    ) -> dict[str, Any]:
        rows, total = QcRepository.list_results(
            page=page, per_page=per_page, search=search
        )
        return {"items": [r.to_dict() for r in rows], "total": total}

    @staticmethod
    def get_result(qcbillid: str) -> dict[str, Any] | None:
        qc = QcRepository.get_result(qcbillid)
        if not qc:
            return None
        data = qc.to_dict()
        data["details"] = [dt.to_dict() for dt in QcRepository.list_details(qcbillid)]
        data["eid_details"] = [
            e.to_dict() for e in QcRepository.list_eid_details(qcbillid)
        ]
        return data

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]] | None = None,
        eid_details: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        qc = QcRepository.create(data)
        if details:
            for idx, d in enumerate(details, start=1):
                QcRepository.add_detail(qc.qcbillid, idx, d)
        if eid_details:
            for idx, d in enumerate(eid_details, start=1):
                QcRepository.add_eid_detail(qc.qcbillid, idx, d)
        db.session.commit()
        return qc.to_dict()

    @staticmethod
    def audit(qcbillid: str, auditor: str) -> dict[str, object]:
        qc = QcRepository.get_result(qcbillid)
        if qc is None:
            return {"success": False, "error": "质检单不存在"}
        if qc.auditflg == "1":
            return {"success": False, "error": "已审核，不可重复审核"}
        QcRepository.audit(qc, auditor)
        return {"success": True}

    @staticmethod
    def get_stats() -> list[dict[str, Any]]:
        return [dict(r) for r in QcRepository.get_stats()]
