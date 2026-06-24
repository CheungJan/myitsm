"""销售管理数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc

from app.extensions import db
from app.models.sales import (
    PlanCust,
    PlanServe,
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
        planno: str | None = None,
        custnm: str | None = None,
        custcard: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        serve_status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PlanCust], int]:
        from datetime import datetime as _dt
        from sqlalchemy import exists, select as _select
        from app.models.sales import PlanServe

        query = db.session.query(PlanCust)
        if planno:
            query = query.filter(PlanCust.planno.ilike(f"%{planno}%"))
        if plantyp:
            query = query.filter(PlanCust.plantyp == plantyp)
        if plan_status:
            query = query.filter(PlanCust.plan_status == plan_status)
        if custcd:
            query = query.filter(PlanCust.custcd == custcd)
        if custnm:
            query = query.filter(PlanCust.custnm.ilike(f"%{custnm}%"))
        if custcard:
            query = query.filter(PlanCust.custcard.ilike(f"%{custcard}%"))
        if date_from:
            try:
                query = query.filter(PlanCust.gendate >= _dt.strptime(date_from, "%Y-%m-%d"))
            except ValueError:
                pass
        if date_to:
            try:
                query = query.filter(PlanCust.gendate < _dt.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
            except ValueError:
                pass
        if serve_status:
            subq = _select(PlanServe.planno).where(
                PlanServe.status == serve_status,
                PlanServe.planno == PlanCust.planno,
            )
            query = query.filter(exists(subq))
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
            setattr(record, key, value)
        return record

    @staticmethod
    def update_status(record: PlanCust, new_status: str) -> PlanCust:
        """更新计划状态。"""
        record.plan_status = new_status
        return record

    @staticmethod
    def find_by_custcard(custcard: str) -> PlanCust | None:
        """按磁卡号查找预计划（用于重复检查）。"""
        if not custcard:
            return None
        return (
            db.session.query(PlanCust)
            .filter(
                PlanCust.custcard == custcard,
            )
            .first()
        )


class PlanServeRepository:
    """呼出单数据访问（PLAN_SERVE）。"""

    @staticmethod
    def get_by_id(dtlid: int) -> PlanServe | None:
        return db.session.get(PlanServe, dtlid)

    @staticmethod
    def list_by_filters(
        planno: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PlanServe], int]:
        query = db.session.query(PlanServe)
        if planno:
            query = query.filter(PlanServe.planno == planno)
        if status:
            query = query.filter(PlanServe.status == status)
        query = query.order_by(desc(PlanServe.gendate))
        total: int = query.count()
        items: list[PlanServe] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def list_by_plan(planno: str) -> list[PlanServe]:
        """获取指定预计划的所有呼出记录。"""
        return (
            db.session.query(PlanServe)
            .filter(PlanServe.planno == planno)
            .order_by(desc(PlanServe.gendate))
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PlanServe:
        now = datetime.now(UTC)
        record = PlanServe(
            genercd=creator,
            gendate=now,
            opercd=creator,
            opdate=now,
            status="00",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: PlanServe, data: dict[str, Any]) -> PlanServe:
        for key, value in data.items():
            setattr(record, key, value)
        record.opercd = data.get("opercd", record.opercd)
        record.opdate = datetime.now(UTC)
        return record

    @staticmethod
    def update_status(record: PlanServe, new_status: str) -> PlanServe:
        record.status = new_status
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
