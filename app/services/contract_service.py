"""合同与发票管理业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.contract_repository import ContractRepository, InvoiceRepository


class ContractService:
    """合同管理服务。"""

    @staticmethod
    def get(htbh: str) -> dict[str, Any] | None:
        record = ContractRepository.get_by_id(htbh)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(
        classcd: str | None = None,
        busityp: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = ContractRepository.list_all(classcd, busityp, page, per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = ContractRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        htbh: str, data: dict[str, Any], creator: str | None = None
    ) -> dict[str, Any] | None:
        record = ContractRepository.get_by_id(htbh)
        if record is None:
            return None
        ContractRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class InvoiceService:
    """发票管理服务。"""

    @staticmethod
    def get(fpbh: str) -> dict[str, Any] | None:
        record = InvoiceRepository.get_by_id(fpbh)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(
        htbh: str | None = None,
        classcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = InvoiceRepository.list_by_filters(htbh, classcd, page, per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = InvoiceRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        fpbh: str, data: dict[str, Any], creator: str | None = None
    ) -> dict[str, Any] | None:
        record = InvoiceRepository.get_by_id(fpbh)
        if record is None:
            return None
        InvoiceRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()
