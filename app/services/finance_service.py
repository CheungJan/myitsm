"""财务应收应付业务服务层（Tier-2 G5）。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.finance_repository import (
    AccountRepository,
    DepreciationRepository,
    PayableRepository,
    PaymentRepository,
    ReceivableRepository,
)


class AccountService:
    """会计科目服务。"""

    @staticmethod
    def get(account_cd: str) -> dict[str, Any] | None:
        record = AccountRepository.get_by_id(account_cd)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(
        account_type: str | None = None,
    ) -> list[dict[str, Any]]:
        records = AccountRepository.list_all(account_type=account_type)
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = AccountRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        account_cd: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = AccountRepository.get_by_id(account_cd)
        if record is None:
            return None
        AccountRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class ReceivableService:
    """应收记录服务。"""

    @staticmethod
    def get(ar_id: str) -> dict[str, Any] | None:
        record = ReceivableRepository.get_by_id(ar_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(
        custcd: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = ReceivableRepository.list_all(
            custcd=custcd, status=status, page=page, per_page=per_page
        )
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = ReceivableRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        ar_id: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = ReceivableRepository.get_by_id(ar_id)
        if record is None:
            return None
        ReceivableRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class PayableService:
    """应付记录服务。"""

    @staticmethod
    def get(ap_id: str) -> dict[str, Any] | None:
        record = PayableRepository.get_by_id(ap_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(
        supp_cd: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PayableRepository.list_all(
            supp_cd=supp_cd, status=status, page=page, per_page=per_page
        )
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = PayableRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        ap_id: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = PayableRepository.get_by_id(ap_id)
        if record is None:
            return None
        PayableRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class PaymentService:
    """收付款服务。"""

    @staticmethod
    def list_all(
        pay_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PaymentRepository.list_all(pay_type=pay_type, page=page, per_page=per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = PaymentRepository.create(data)
        db.session.commit()
        return record.to_dict()


class DepreciationService:
    """设备折旧服务。"""

    @staticmethod
    def get_by_eid(eid: str) -> dict[str, Any] | None:
        record = DepreciationRepository.get_by_eid(eid)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = DepreciationRepository.list_all(page=page, per_page=per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = DepreciationRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        eid: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = DepreciationRepository.get_by_eid(eid)
        if record is None:
            return None
        DepreciationRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()
