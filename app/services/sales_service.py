"""销售管理业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.sales_repository import (
    PlanCustRepository,
    SalesBillRepository,
    SalesExtendRepository,
)


class PlanCustService:
    """预计划服务。"""

    @staticmethod
    def get(planno: str) -> dict[str, Any] | None:
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_records(
        plantyp: str | None = None,
        plan_status: str | None = None,
        custcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PlanCustRepository.list_by_filters(
            plantyp=plantyp,
            plan_status=plan_status,
            custcd=custcd,
            page=page,
            per_page=per_page,
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = PlanCustRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(planno: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = PlanCustRepository.get_by_id(planno)
        if record is None:
            return None
        PlanCustRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class SalesBillService:
    """销售单据服务。"""

    @staticmethod
    def get(slbillid: str) -> dict[str, Any] | None:
        record = SalesBillRepository.get_by_id(slbillid)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_records(
        sltyp: str | None = None,
        custcd: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = SalesBillRepository.list_by_filters(
            sltyp=sltyp, custcd=custcd, auditflg=auditflg, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = SalesBillRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def audit(slbillid: str, auditor: str) -> dict[str, object]:
        record = SalesBillRepository.get_by_id(slbillid)
        if record is None:
            return {"success": False, "error": "销售单不存在"}
        if record.auditflg == "1":
            return {"success": False, "error": "已审核"}
        SalesBillRepository.audit(record, auditor)
        db.session.commit()
        return {"success": True, "slbillid": record.slbillid}


class SalesExtendService:
    """延期服务。"""

    @staticmethod
    def get(opbillid: str) -> dict[str, Any] | None:
        record = SalesExtendRepository.get_by_id(opbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        custcd: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = SalesExtendRepository.list_by_filters(
            custcd=custcd, auditflg=auditflg, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]],
        creator: str,
    ) -> dict[str, Any]:
        record = SalesExtendRepository.create(data, creator)
        for detail_data in details:
            SalesExtendRepository.add_detail(opbillid=record.opbillid, data=detail_data)
        db.session.commit()
        return record.to_dict()
