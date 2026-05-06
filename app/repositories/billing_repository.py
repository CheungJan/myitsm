"""租金/费用结算数据访问层（Tier-2 G4）。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.extensions import db
from app.models.billing import Bill, BillDetail, BillingBatch, BillingRule


class BillingRuleRepository:
    """结算规则数据访问。"""

    @staticmethod
    def get_by_id(rule_id: str) -> BillingRule | None:
        return db.session.get(BillingRule, rule_id)

    @staticmethod
    def list_all(
        useflg: str | None = "1",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[BillingRule], int]:
        query = db.session.query(BillingRule)
        if useflg is not None:
            query = query.filter(BillingRule.useflg == useflg)
        total: int = query.count()
        items: list[BillingRule] = (
            query.order_by(BillingRule.rule_id).offset((page - 1) * per_page).limit(per_page).all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> BillingRule:
        now = datetime.now(UTC)
        record = BillingRule(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: BillingRule,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> BillingRule:
        for key, value in data.items():
            setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class BillRepository:
    """账单数据访问。"""

    @staticmethod
    def get_by_id(bill_id: str) -> Bill | None:
        return db.session.get(Bill, bill_id)

    @staticmethod
    def list_all(
        custcd: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Bill], int]:
        query = db.session.query(Bill)
        if custcd is not None:
            query = query.filter(Bill.custcd == custcd)
        if status is not None:
            query = query.filter(Bill.status == status)
        total: int = query.count()
        items: list[Bill] = (
            query.order_by(Bill.bill_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> Bill:
        now = datetime.now(UTC)
        record = Bill(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: Bill,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> Bill:
        for key, value in data.items():
            setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class BillDetailRepository:
    """账单明细数据访问。"""

    @staticmethod
    def list_by_bill(bill_id: str) -> list[BillDetail]:
        return (
            db.session.query(BillDetail)
            .filter(BillDetail.bill_id == bill_id)
            .order_by(BillDetail.id)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any]) -> BillDetail:
        record = BillDetail(**data)
        db.session.add(record)
        return record


class BillingBatchRepository:
    """结算批次数据访问。"""

    @staticmethod
    def get_by_id(batch_id: str) -> BillingBatch | None:
        return db.session.get(BillingBatch, batch_id)

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> tuple[list[BillingBatch], int]:
        query = db.session.query(BillingBatch)
        total: int = query.count()
        items: list[BillingBatch] = (
            query.order_by(BillingBatch.batch_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> BillingBatch:
        now = datetime.now(UTC)
        record = BillingBatch(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: BillingBatch,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> BillingBatch:
        for key, value in data.items():
            setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record
