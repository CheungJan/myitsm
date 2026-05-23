"""采购管理业务服务层。"""

from __future__ import annotations

from datetime import datetime as dt
from typing import Any

from app.extensions import db
from app.repositories.procurement_repository import (
    PurchaseBillRepository,
    PurchasePlanRepository,
    PurchasePlanStatusRepository,
    PurchaseRegisterRepository,
    RequisitionOrderLinkRepository,
    ReturnPurchaseRepository,
    SupplierAppraisalRepository,
)


class PurchasePlanService:
    """采购需求服务 (原采购计划，TPC01/TPC02)。"""

    @staticmethod
    def dashboard_stats() -> dict[str, Any]:
        """执行看板统计数据。"""
        return PurchasePlanRepository.dashboard_stats()

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
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PurchasePlanRepository.list_by_filters(
            auditflg=auditflg, pctyp=pctyp, start_date=start_date, end_date=end_date, page=page, per_page=per_page
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
            return {"success": False, "error": "采购需求不存在"}
        if record.auditflg == "1":
            return {"success": False, "error": "已审核"}
        PurchasePlanRepository.audit(record, auditor)
        db.session.commit()
        return {"success": True, "pcplanid": record.pcplanid}


class PurchaseRegisterService:
    """采购订单服务 (原采购登记，TPC12/TPC13)。"""

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
        # 校验余额：每个明细的采购数量不能超过来源需求单的可用余额
        for d in details:
            ref_pcplanid = d.get("ref_pcplanid")
            ref_pclineno = d.get("ref_pclineno")
            rgsqty = float(d.get("rgsqty", 0))
            if ref_pcplanid and ref_pclineno is not None:
                available = PurchasePlanRepository.get_available_qty(
                    str(ref_pcplanid), int(ref_pclineno)
                )
                if rgsqty > available:
                    raise ValueError(
                        f"采购数量({rgsqty})超过需求 {ref_pcplanid} "
                        f"行 {ref_pclineno} 的可用余额({available})"
                    )

        record = PurchaseRegisterRepository.create(data, creator)
        rgstbillid = record.rgstbillid

        for i, d in enumerate(details, start=1):
            PurchaseRegisterRepository.add_detail(
                rgstbillid=rgstbillid, lineno=i, data=d
            )

        # 写入 TPC20 关联表
        link_details = [
            {**d, "rgstbillid": rgstbillid, "rgstlineno": i}
            for i, d in enumerate(details, start=1)
            if d.get("ref_pcplanid") and d.get("ref_pclineno") is not None
        ]
        if link_details:
            RequisitionOrderLinkRepository.create_links(link_details)

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
    """采购结算单服务 (原采购单据，TPC14)。"""

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
    """采购退货服务 (TPC16/TPC17)。"""

    @staticmethod
    def get(pcbillid: str) -> dict[str, Any] | None:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        whcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = ReturnPurchaseRepository.list_by_filters(
            whcd=whcd, page=page, per_page=per_page
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
        record = ReturnPurchaseRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            ReturnPurchaseRepository.add_detail(
                pcbillid=record.pcbillid, lineno=idx, data=detail_data
            )
        db.session.commit()
        return record.to_dict()


class SupplierAppraisalService:
    """供应商评价服务 (TPC20/TPC21)。"""

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


class PurchasePlanStatusService:
    """@deprecated 采购需求执行看板服务 (原 TPC03，已冻结)。"""

    @staticmethod
    def get(itemcd: str) -> dict[str, Any] | None:
        record = PurchasePlanStatusRepository.get_by_id(itemcd)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = PurchasePlanStatusRepository.list_all(page=page, per_page=per_page)
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = PurchasePlanStatusRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(itemcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = PurchasePlanStatusRepository.get_by_id(itemcd)
        if record is None:
            return None
        PurchasePlanStatusRepository.update(record, data)
        db.session.commit()
        return record.to_dict()
