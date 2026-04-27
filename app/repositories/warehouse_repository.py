"""仓储管理数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc

from app.extensions import db
from app.models.warehouse import (
    StockDetail,
    StockIn,
    StockInDetail,
    StockOut,
    StockOutDetailEid,
    StockOutDetailPrd,
    Warehouse,
)


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


class WarehouseRepository:
    """仓库主数据访问。"""

    @staticmethod
    def get_by_id(whcd: str) -> Warehouse | None:
        return db.session.get(Warehouse, whcd)

    @staticmethod
    def list_all(useflg: str | None = "1") -> list[Warehouse]:
        query = db.session.query(Warehouse)
        if useflg is not None:
            query = query.filter(Warehouse.useflg == useflg)
        return query.order_by(Warehouse.whcd).all()

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> Warehouse:
        now = datetime.now(UTC)
        record = Warehouse(
            opercd=creator,
            gendate=now,
            upddate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: Warehouse, data: dict[str, Any]) -> Warehouse:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        record.upddate = datetime.now(UTC)
        return record


class StockInRepository:
    """入库单数据访问。"""

    @staticmethod
    def get_by_id(inbillid: str) -> StockIn | None:
        return db.session.get(StockIn, inbillid)

    @staticmethod
    def list_by_filters(
        whcd: str | None = None,
        invtyp: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[StockIn], int]:
        query = db.session.query(StockIn)
        if whcd:
            query = query.filter(StockIn.whcd == whcd)
        if invtyp:
            query = query.filter(StockIn.invtyp == invtyp)
        if auditflg:
            query = query.filter(StockIn.auditflg == auditflg)
        query = query.order_by(desc(StockIn.gendate))
        total: int = query.count()
        items: list[StockIn] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> StockIn:
        now = datetime.now(UTC)
        record = StockIn(
            inbillid=_gen_id(),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail(
        inbillid: str,
        whcd: str,
        lineno: int,
        data: dict[str, Any],
    ) -> StockInDetail:
        record = StockInDetail(
            inbillid=inbillid,
            whcd=whcd,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def audit(record: StockIn, auditor: str) -> StockIn:
        record.auditflg = "1"
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        return record


class StockOutRepository:
    """出库单数据访问。"""

    @staticmethod
    def get_by_id(outbillid: str) -> StockOut | None:
        return db.session.get(StockOut, outbillid)

    @staticmethod
    def list_by_filters(
        whcd: str | None = None,
        invtyp: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[StockOut], int]:
        query = db.session.query(StockOut)
        if whcd:
            query = query.filter(StockOut.whcd == whcd)
        if invtyp:
            query = query.filter(StockOut.invtyp == invtyp)
        if auditflg:
            query = query.filter(StockOut.auditflg == auditflg)
        query = query.order_by(desc(StockOut.gendate))
        total: int = query.count()
        items: list[StockOut] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> StockOut:
        now = datetime.now(UTC)
        record = StockOut(
            outbillid=_gen_id(),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail_eid(
        outbillid: str,
        whcd: str,
        lineno: int,
        data: dict[str, Any],
    ) -> StockOutDetailEid:
        record = StockOutDetailEid(
            outbillid=outbillid,
            whcd=whcd,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail_prd(
        outbillid: str,
        whcd: str,
        lineno: int,
        data: dict[str, Any],
    ) -> StockOutDetailPrd:
        record = StockOutDetailPrd(
            outbillid=outbillid,
            whcd=whcd,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def audit(record: StockOut, auditor: str) -> StockOut:
        record.auditflg = "1"
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        return record


class StockDetailRepository:
    """库存明细数据访问。"""

    @staticmethod
    def get_balance(whcd: str, itemcd: str) -> int:
        record = (
            db.session.query(StockDetail)
            .filter(
                StockDetail.whcd == whcd,
                StockDetail.itemcd == itemcd,
                StockDetail.useflg == "1",
            )
            .first()
        )
        if record is None:
            return 0
        qty: int = record.itemqty or 0
        return qty

    @staticmethod
    def list_by_warehouse(
        whcd: str,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[StockDetail], int]:
        query = (
            db.session.query(StockDetail)
            .filter(StockDetail.whcd == whcd, StockDetail.useflg == "1")
            .order_by(StockDetail.itemcd)
        )
        total: int = query.count()
        items: list[StockDetail] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def update_balance(whcd: str, itemcd: str, qty_delta: int, operator: str) -> StockDetail:
        """更新库存余量。"""
        now = datetime.now(UTC)
        record = (
            db.session.query(StockDetail)
            .filter(StockDetail.whcd == whcd, StockDetail.itemcd == itemcd)
            .first()
        )
        if record is None:
            record = StockDetail(
                whcd=whcd,
                itemcd=itemcd,
                itemqty=qty_delta,
                opercd=operator,
                gendate=now,
                upddate=now,
            )
            db.session.add(record)
        else:
            current_qty: int = record.itemqty or 0
            record.itemqty = current_qty + qty_delta
            record.upddate = now
        return record
