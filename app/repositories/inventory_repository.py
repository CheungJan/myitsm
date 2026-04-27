"""库存预警与价格管理数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.extensions import db
from app.models.inventory import AdjustPrice, InventoryLimit, InventoryLimitHistory, Price


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


class InventoryLimitRepository:
    """库存预警数据访问。"""

    @staticmethod
    def get_by_id(itemcd: str) -> InventoryLimit | None:
        return db.session.get(InventoryLimit, itemcd)

    @staticmethod
    def list_all(useflg: str | None = "1") -> list[InventoryLimit]:
        query = db.session.query(InventoryLimit)
        if useflg is not None:
            query = query.filter(InventoryLimit.useflg == useflg)
        return query.order_by(InventoryLimit.itemcd).all()

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> InventoryLimit:
        now = datetime.now(UTC)
        record = InventoryLimit(
            opercd=creator,
            gendate=now,
            upddate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: InventoryLimit, data: dict[str, Any], creator: str | None = None
    ) -> InventoryLimit:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record

    @staticmethod
    def save_history(record: InventoryLimit) -> InventoryLimitHistory:
        """保存预警修改前的历史快照。"""
        now = datetime.now(UTC)
        hist = InventoryLimitHistory(
            itemcd=record.itemcd,
            invlow=record.invlow,
            invhigh=record.invhigh,
            daylow=record.daylow,
            dayhigh=record.dayhigh,
            opercd=record.opercd,
            gendate=now,
            upddate=now,
        )
        db.session.add(hist)
        return hist


class PriceRepository:
    """价格规则数据访问。"""

    @staticmethod
    def get_by_key(itemcd: str, busityp: str) -> Price | None:
        return db.session.get(Price, (itemcd, busityp))

    @staticmethod
    def list_all(useflg: str | None = "1") -> list[Price]:
        query = db.session.query(Price)
        if useflg is not None:
            query = query.filter(Price.useflg == useflg)
        return query.order_by(Price.itemcd, Price.busityp).all()

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> Price:
        now = datetime.now(UTC)
        record = Price(
            opercd=creator,
            gendate=now,
            upddate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: Price, data: dict[str, Any]) -> Price:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        record.upddate = datetime.now(UTC)
        return record


class AdjustPriceRepository:
    """调价记录数据访问。"""

    @staticmethod
    def get_by_key(pabillid: str, lineno: int) -> AdjustPrice | None:
        return db.session.get(AdjustPrice, (pabillid, lineno))

    @staticmethod
    def list_by_bill(pabillid: str) -> list[AdjustPrice]:
        return (
            db.session.query(AdjustPrice)
            .filter(AdjustPrice.pabillid == pabillid, AdjustPrice.useflg == "1")
            .order_by(AdjustPrice.lineno)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> AdjustPrice:
        now = datetime.now(UTC)
        if "pabillid" not in data:
            data["pabillid"] = _gen_id("PA")
        record = AdjustPrice(
            opercd=creator,
            gendate=now,
            **data,
        )
        db.session.add(record)
        return record
