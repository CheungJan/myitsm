"""销售管理数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc

from app.extensions import db
from app.models.sales import (
    PlanCust,
    SalesBill,
    SalesExtend,
    SalesExtendDt,
)


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


def _gen_plan_id() -> str:
    """生成10位计划编号。"""
    return uuid.uuid4().hex[:10].upper()


class PlanCustRepository:
    """预计划数据访问。"""

    @staticmethod
    def get_by_id(planno: str) -> PlanCust | None:
        return db.session.get(PlanCust, planno)

    @staticmethod
    def list_by_filters(
        plantyp: str | None = None,
        plan_status: str | None = None,
        custcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PlanCust], int]:
        query = db.session.query(PlanCust)
        if plantyp:
            query = query.filter(PlanCust.plantyp == plantyp)
        if plan_status:
            query = query.filter(PlanCust.plan_status == plan_status)
        if custcd:
            query = query.filter(PlanCust.custcd == custcd)
        query = query.order_by(desc(PlanCust.gendate))
        total: int = query.count()
        items: list[PlanCust] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PlanCust:
        now = datetime.now(UTC)
        record = PlanCust(
            planno=_gen_plan_id(),
            opercd=creator,
            gendate=now,
            plan_status="00",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: PlanCust, data: dict[str, Any]) -> PlanCust:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        return record


class SalesBillRepository:
    """销售单据数据访问。"""

    @staticmethod
    def get_by_id(slbillid: str) -> SalesBill | None:
        return db.session.get(SalesBill, slbillid)

    @staticmethod
    def list_by_filters(
        sltyp: str | None = None,
        custcd: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[SalesBill], int]:
        query = db.session.query(SalesBill)
        if sltyp:
            query = query.filter(SalesBill.sltyp == sltyp)
        if custcd:
            query = query.filter(SalesBill.custcd == custcd)
        if auditflg:
            query = query.filter(SalesBill.auditflg == auditflg)
        query = query.order_by(desc(SalesBill.gendate))
        total: int = query.count()
        items: list[SalesBill] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> SalesBill:
        now = datetime.now(UTC)
        record = SalesBill(
            slbillid=_gen_id(),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def audit(record: SalesBill, auditor: str) -> SalesBill:
        record.auditflg = "1"
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        return record


class SalesExtendRepository:
    """延期数据访问。"""

    @staticmethod
    def get_by_id(opbillid: str) -> SalesExtend | None:
        return db.session.get(SalesExtend, opbillid)

    @staticmethod
    def list_by_filters(
        custcd: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[SalesExtend], int]:
        query = db.session.query(SalesExtend)
        if custcd:
            query = query.filter(SalesExtend.custcd == custcd)
        if auditflg:
            query = query.filter(SalesExtend.auditflg == auditflg)
        query = query.order_by(desc(SalesExtend.gendate))
        total: int = query.count()
        items: list[SalesExtend] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> SalesExtend:
        now = datetime.now(UTC)
        record = SalesExtend(
            opbillid=_gen_id(),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail(opbillid: str, data: dict[str, Any]) -> SalesExtendDt:
        record = SalesExtendDt(
            opbillid=opbillid,
            **data,
        )
        db.session.add(record)
        return record
