"""采购管理业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.procurement_repository import (
    PurchaseBillRepository,
    PurchasePlanRepository,
    PurchaseRegisterRepository,
    ReturnPurchaseRepository,
    SupplierAppraisalRepository,
)


class PurchasePlanService:
    """采购计划服务。"""

    @staticmethod
    def get(pcplanid: str) -> dict[str, Any] | None:
        record = PurchasePlanRepository.get_by_id(pcplanid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        auditflg: str | None = None,
        pctyp: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PurchasePlanRepository.list_by_filters(
            auditflg=auditflg, pctyp=pctyp, page=page, per_page=per_page
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
        record = PurchasePlanRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            PurchasePlanRepository.add_detail(
                pcplanid=record.pcplanid, lineno=idx, data=detail_data
            )
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def audit(pcplanid: str, auditor: str) -> dict[str, object]:
        record = PurchasePlanRepository.get_by_id(pcplanid)
        if record is None:
            return {"success": False, "error": "采购计划不存在"}
        if record.auditflg == "1":
            return {"success": False, "error": "已审核"}
        PurchasePlanRepository.audit(record, auditor)
        db.session.commit()
        return {"success": True, "pcplanid": record.pcplanid}


class PurchaseRegisterService:
    """采购登记服务。"""

    @staticmethod
    def get(rgstbillid: str) -> dict[str, Any] | None:
        record = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PurchaseRegisterRepository.list_by_filters(
            suppliercd=suppliercd, auditflg=auditflg, page=page, per_page=per_page
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
        record = PurchaseRegisterRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            PurchaseRegisterRepository.add_detail(
                rgstbillid=record.rgstbillid, lineno=idx, data=detail_data
            )
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def audit(rgstbillid: str, auditor: str) -> dict[str, object]:
        record = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if record is None:
            return {"success": False, "error": "采购登记不存在"}
        if record.auditflg == "1":
            return {"success": False, "error": "已审核"}
        PurchaseRegisterRepository.audit(record, auditor)
        db.session.commit()
        return {"success": True, "rgstbillid": record.rgstbillid}


class PurchaseBillService:
    """采购单据服务。"""

    @staticmethod
    def get(pcbillid: str) -> dict[str, Any] | None:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_records(
        whcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PurchaseBillRepository.list_by_filters(
            whcd=whcd, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = PurchaseBillRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class ReturnPurchaseService:
    """采购退货服务。"""

    @staticmethod
    def get(pcbillid: str) -> dict[str, Any] | None:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = ReturnPurchaseRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class SupplierAppraisalService:
    """供应商评价服务。"""

    @staticmethod
    def get(appid: str) -> dict[str, Any] | None:
        record = SupplierAppraisalRepository.get_by_id(appid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = SupplierAppraisalRepository.list_by_filters(
            auditflg=auditflg, page=page, per_page=per_page
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
        record = SupplierAppraisalRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            SupplierAppraisalRepository.add_detail(appid=record.appid, lineno=idx, data=detail_data)
        db.session.commit()
        return record.to_dict()
