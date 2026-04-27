"""租金/费用结算业务服务层（Tier-2 G4）。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.billing_repository import (
    BillDetailRepository,
    BillingBatchRepository,
    BillingRuleRepository,
    BillRepository,
)


class BillingRuleService:
    """结算规则服务。"""

    @staticmethod
    def get(rule_id: str) -> dict[str, Any] | None:
        record = BillingRuleRepository.get_by_id(rule_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(
        useflg: str | None = "1",
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = BillingRuleRepository.list_all(useflg=useflg, page=page, per_page=per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = BillingRuleRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        rule_id: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = BillingRuleRepository.get_by_id(rule_id)
        if record is None:
            return None
        BillingRuleRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class BillService:
    """账单服务。"""

    @staticmethod
    def get(bill_id: str) -> dict[str, Any] | None:
        record = BillRepository.get_by_id(bill_id)
        if record is None:
            return None
        result = record.to_dict()
        details = BillDetailRepository.list_by_bill(bill_id)
        result["details"] = [d.to_dict() for d in details]
        return result

    @staticmethod
    def list_all(
        custcd: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = BillRepository.list_all(
            custcd=custcd, status=status, page=page, per_page=per_page
        )
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]] | None = None,
        creator: str | None = None,
    ) -> dict[str, Any]:
        bill = BillRepository.create(data, creator)
        if details:
            for dtl in details:
                dtl["bill_id"] = bill.bill_id
                BillDetailRepository.create(dtl)
        db.session.commit()
        return bill.to_dict()

    @staticmethod
    def update(
        bill_id: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = BillRepository.get_by_id(bill_id)
        if record is None:
            return None
        BillRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class BillingBatchService:
    """结算批次服务。"""

    @staticmethod
    def get(batch_id: str) -> dict[str, Any] | None:
        record = BillingBatchRepository.get_by_id(batch_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = BillingBatchRepository.list_all(page=page, per_page=per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = BillingBatchRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        batch_id: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = BillingBatchRepository.get_by_id(batch_id)
        if record is None:
            return None
        BillingBatchRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()
