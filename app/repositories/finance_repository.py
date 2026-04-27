"""财务应收应付数据访问层（Tier-2 G5）。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.extensions import db
from app.models.finance import Account, Depreciation, Payable, Payment, Receivable


class AccountRepository:
    """会计科目数据访问。"""

    @staticmethod
    def get_by_id(account_cd: str) -> Account | None:
        return db.session.get(Account, account_cd)

    @staticmethod
    def list_all(
        account_type: str | None = None,
        useflg: str | None = "1",
    ) -> list[Account]:
        query = db.session.query(Account)
        if account_type is not None:
            query = query.filter(Account.account_type == account_type)
        if useflg is not None:
            query = query.filter(Account.useflg == useflg)
        return query.order_by(Account.account_cd).all()

    @staticmethod
    def create(data: dict[str, Any]) -> Account:
        record = Account(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: Account,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> Account:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class ReceivableRepository:
    """应收记录数据访问。"""

    @staticmethod
    def get_by_id(ar_id: str) -> Receivable | None:
        return db.session.get(Receivable, ar_id)

    @staticmethod
    def list_all(
        custcd: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Receivable], int]:
        query = db.session.query(Receivable)
        if custcd is not None:
            query = query.filter(Receivable.custcd == custcd)
        if status is not None:
            query = query.filter(Receivable.status == status)
        total: int = query.count()
        items: list[Receivable] = (
            query.order_by(Receivable.ar_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any]) -> Receivable:
        record = Receivable(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: Receivable,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> Receivable:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class PayableRepository:
    """应付记录数据访问。"""

    @staticmethod
    def get_by_id(ap_id: str) -> Payable | None:
        return db.session.get(Payable, ap_id)

    @staticmethod
    def list_all(
        supp_cd: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Payable], int]:
        query = db.session.query(Payable)
        if supp_cd is not None:
            query = query.filter(Payable.supp_cd == supp_cd)
        if status is not None:
            query = query.filter(Payable.status == status)
        total: int = query.count()
        items: list[Payable] = (
            query.order_by(Payable.ap_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any]) -> Payable:
        record = Payable(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: Payable,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> Payable:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class PaymentRepository:
    """收付款记录数据访问。"""

    @staticmethod
    def get_by_id(pay_id: str) -> Payment | None:
        return db.session.get(Payment, pay_id)

    @staticmethod
    def list_all(
        pay_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Payment], int]:
        query = db.session.query(Payment)
        if pay_type is not None:
            query = query.filter(Payment.pay_type == pay_type)
        total: int = query.count()
        items: list[Payment] = (
            query.order_by(Payment.pay_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any]) -> Payment:
        record = Payment(**data)
        db.session.add(record)
        return record


class DepreciationRepository:
    """设备折旧数据访问。"""

    @staticmethod
    def get_by_eid(eid: str) -> Depreciation | None:
        return db.session.query(Depreciation).filter(Depreciation.eid == eid).first()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> tuple[list[Depreciation], int]:
        query = db.session.query(Depreciation)
        total: int = query.count()
        items: list[Depreciation] = (
            query.order_by(Depreciation.eid).offset((page - 1) * per_page).limit(per_page).all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any]) -> Depreciation:
        record = Depreciation(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: Depreciation,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> Depreciation:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record
