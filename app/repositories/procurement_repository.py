"""采购管理数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc

from app.extensions import db
from app.models.procurement import (
    PurchaseBill,
    PurchasePlan,
    PurchasePlanDt,
    PurchaseRegister,
    PurchaseRegisterDt,
    ReturnPurchaseBill,
    SupplierAppraisal,
    SupplierAppraisalDt,
)


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


class PurchasePlanRepository:
    """采购计划数据访问。"""

    @staticmethod
    def get_by_id(pcplanid: str) -> PurchasePlan | None:
        return db.session.get(PurchasePlan, pcplanid)

    @staticmethod
    def list_by_filters(
        auditflg: str | None = None,
        pctyp: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PurchasePlan], int]:
        query = db.session.query(PurchasePlan)
        if auditflg:
            query = query.filter(PurchasePlan.auditflg == auditflg)
        if pctyp:
            query = query.filter(PurchasePlan.pctyp == pctyp)
        query = query.order_by(desc(PurchasePlan.gendate))
        total: int = query.count()
        items: list[PurchasePlan] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PurchasePlan:
        now = datetime.now(UTC)
        record = PurchasePlan(
            pcplanid=_gen_id(),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail(pcplanid: str, lineno: int, data: dict[str, Any]) -> PurchasePlanDt:
        record = PurchasePlanDt(
            pcplanid=pcplanid,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def audit(record: PurchasePlan, auditor: str) -> PurchasePlan:
        record.auditflg = "1"
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        return record


class PurchaseRegisterRepository:
    """采购登记数据访问。"""

    @staticmethod
    def get_by_id(rgstbillid: str) -> PurchaseRegister | None:
        return db.session.get(PurchaseRegister, rgstbillid)

    @staticmethod
    def list_by_filters(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PurchaseRegister], int]:
        query = db.session.query(PurchaseRegister)
        if suppliercd:
            query = query.filter(PurchaseRegister.suppliercd == suppliercd)
        if auditflg:
            query = query.filter(PurchaseRegister.auditflg == auditflg)
        query = query.order_by(desc(PurchaseRegister.gendate))
        total: int = query.count()
        items: list[PurchaseRegister] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PurchaseRegister:
        now = datetime.now(UTC)
        record = PurchaseRegister(
            rgstbillid=_gen_id(),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail(rgstbillid: str, lineno: int, data: dict[str, Any]) -> PurchaseRegisterDt:
        record = PurchaseRegisterDt(
            rgstbillid=rgstbillid,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def audit(record: PurchaseRegister, auditor: str) -> PurchaseRegister:
        record.auditflg = "1"
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        return record


class PurchaseBillRepository:
    """采购单据数据访问。"""

    @staticmethod
    def get_by_id(pcbillid: str) -> PurchaseBill | None:
        return db.session.get(PurchaseBill, pcbillid)

    @staticmethod
    def list_by_filters(
        whcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PurchaseBill], int]:
        query = db.session.query(PurchaseBill)
        if whcd:
            query = query.filter(PurchaseBill.whcd == whcd)
        query = query.order_by(desc(PurchaseBill.gendate))
        total: int = query.count()
        items: list[PurchaseBill] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PurchaseBill:
        now = datetime.now(UTC)
        record = PurchaseBill(
            pcbillid=_gen_id(),
            opercd=creator,
            gendate=now,
            **data,
        )
        db.session.add(record)
        return record


class ReturnPurchaseRepository:
    """采购退货数据访问。"""

    @staticmethod
    def get_by_id(pcbillid: str) -> ReturnPurchaseBill | None:
        return db.session.get(ReturnPurchaseBill, pcbillid)

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> ReturnPurchaseBill:
        now = datetime.now(UTC)
        record = ReturnPurchaseBill(
            pcbillid=_gen_id(),
            opercd=creator,
            gendate=now,
            **data,
        )
        db.session.add(record)
        return record


class SupplierAppraisalRepository:
    """供应商评价数据访问。"""

    @staticmethod
    def get_by_id(appid: str) -> SupplierAppraisal | None:
        return db.session.get(SupplierAppraisal, appid)

    @staticmethod
    def list_by_filters(
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[SupplierAppraisal], int]:
        query = db.session.query(SupplierAppraisal)
        if auditflg:
            query = query.filter(SupplierAppraisal.auditflg == auditflg)
        query = query.order_by(desc(SupplierAppraisal.gendate))
        total: int = query.count()
        items: list[SupplierAppraisal] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> SupplierAppraisal:
        now = datetime.now(UTC)
        record = SupplierAppraisal(
            appid=_gen_id(),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail(appid: str, lineno: int, data: dict[str, Any]) -> SupplierAppraisalDt:
        record = SupplierAppraisalDt(
            appid=appid,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record
