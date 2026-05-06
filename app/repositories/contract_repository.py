"""合同与发票管理数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc

from app.extensions import db
from app.models.auxiliary import Contract, Invoice


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


class ContractRepository:
    """合同管理数据访问。"""

    @staticmethod
    def get_by_id(htbh: str) -> Contract | None:
        return db.session.get(Contract, htbh)

    @staticmethod
    def list_all(
        classcd: str | None = None,
        busityp: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Contract], int]:
        query = db.session.query(Contract)
        if classcd:
            query = query.filter(Contract.classcd == classcd)
        if busityp:
            query = query.filter(Contract.busityp == busityp)
        query = query.order_by(desc(Contract.upddate))
        total: int = query.count()
        items: list[Contract] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> Contract:
        now = datetime.now(UTC)
        if "htbh" not in data:
            data["htbh"] = _gen_id("HT")
        record = Contract(
            opercd=creator,
            upddate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: Contract, data: dict[str, Any], creator: str | None = None) -> Contract:
        for key, value in data.items():
            setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class InvoiceRepository:
    """发票管理数据访问。"""

    @staticmethod
    def get_by_id(fpbh: str) -> Invoice | None:
        return db.session.get(Invoice, fpbh)

    @staticmethod
    def list_by_filters(
        htbh: str | None = None,
        classcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Invoice], int]:
        query = db.session.query(Invoice)
        if htbh:
            query = query.filter(Invoice.htbh == htbh)
        if classcd:
            query = query.filter(Invoice.classcd == classcd)
        query = query.order_by(desc(Invoice.upddate))
        total: int = query.count()
        items: list[Invoice] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> Invoice:
        now = datetime.now(UTC)
        if "fpbh" not in data:
            data["fpbh"] = _gen_id("FP")
        record = Invoice(
            opercd=creator,
            upddate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: Invoice, data: dict[str, Any], creator: str | None = None) -> Invoice:
        for key, value in data.items():
            setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record
