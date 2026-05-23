"""采购管理数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from datetime import datetime as dt
from typing import Any

import sqlalchemy as sa
from sqlalchemy import desc

from app.extensions import db
from app.models.procurement import (
    PurchaseBill,
    PurchasePlan,
    PurchasePlanDt,
    PurchasePlanStatus,
    PurchaseRegister,
    PurchaseRegisterDt,
    RequisitionOrderLink,
    ReturnPurchaseBill,
    ReturnPurchaseBillDt,
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
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PurchasePlan], int]:
        query = db.session.query(PurchasePlan)
        if auditflg:
            query = query.filter(PurchasePlan.auditflg == auditflg)
        if pctyp:
            query = query.filter(PurchasePlan.pctyp == pctyp)
        if start_date:
            query = query.filter(PurchasePlan.plandate >= start_date)
        if end_date:
            query = query.filter(PurchasePlan.plandate <= end_date)
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
    def audit(record: PurchasePlan, auditor: str, auditflg: str = "2", checkmemo: str = "") -> PurchasePlan:
        record.auditflg = auditflg
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        if checkmemo:
            record.checkmemo = checkmemo
        return record

    @staticmethod
    def update_audit_qty(pcplanid: str, lineno: int, auditqty: int) -> None:
        db.session.query(PurchasePlanDt).filter(
            PurchasePlanDt.pcplanid == pcplanid,
            PurchasePlanDt.lineno == lineno,
        ).update({"auditqty": auditqty})

    @staticmethod
    def get_available_qty(pcplanid: str, pclineno: int) -> float:
        row = db.session.execute(
            sa.text(
                "SELECT available_qty FROM v_requisition_execution "
                "WHERE pcplanid = :pid AND lineno = :lno"
            ),
            {"pid": pcplanid, "lno": pclineno},
        ).fetchone()
        return float(row.available_qty) if row else 0.0

    @staticmethod
    def dashboard_stats() -> dict[str, Any]:
        stats = db.session.execute(sa.text("""
            SELECT
                COUNT(DISTINCT pcplanid) AS total,
                COUNT(DISTINCT CASE WHEN execution_status = '已完成' THEN pcplanid END) AS completed,
                COUNT(DISTINCT CASE WHEN execution_status IN ('已下单','执行中') THEN pcplanid END) AS in_progress,
                COUNT(DISTINCT CASE WHEN execution_status = '未开始' THEN pcplanid END) AS not_started
            FROM v_requisition_execution
        """)).fetchone()

        top_items = [
            dict(row._mapping)
            for row in db.session.execute(sa.text("""
                SELECT itemcd, itemnm, SUM(plan_qty)::int AS total_plan,
                    SUM(ordered_qty)::numeric AS total_ordered,
                    SUM(received_qty)::numeric AS total_received,
                    ROUND(AVG(execution_rate), 1) AS execution_rate
                FROM v_requisition_execution
                GROUP BY itemcd, itemnm
                ORDER BY total_plan DESC LIMIT 10
            """)).fetchall()
        ]

        overdue = [
            dict(row._mapping)
            for row in db.session.execute(sa.text("""
                SELECT pcplanid, itemcd, itemnm, plandate::text,
                    plan_qty, ordered_qty::numeric, received_qty::numeric,
                    execution_status
                FROM v_requisition_execution
                WHERE execution_status != '已完成'
                    AND plandate < CURRENT_DATE - INTERVAL '7 days'
                ORDER BY plandate LIMIT 10
            """)).fetchall()
        ]

        return {
            "stats": dict(stats._mapping) if stats else {},
            "top_items": top_items,
            "overdue": overdue,
        }


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
    def audit(record: PurchaseRegister, auditor: str, auditflg: str = "2", checkmemo: str = "") -> PurchaseRegister:
        record.auditflg = auditflg
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        if checkmemo:
            record.checkmemo = checkmemo
        return record

    @staticmethod
    def update_audit_qty(rgstbillid: str, lineno: int, auditqty: int) -> None:
        db.session.query(PurchaseRegisterDt).filter(
            PurchaseRegisterDt.rgstbillid == rgstbillid,
            PurchaseRegisterDt.lineno == lineno,
        ).update({"auditqty": auditqty})


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
    def list_by_filters(
        whcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ReturnPurchaseBill], int]:
        query = db.session.query(ReturnPurchaseBill)
        if whcd:
            query = query.filter(ReturnPurchaseBill.whcd == whcd)
        query = query.order_by(desc(ReturnPurchaseBill.gendate))
        total: int = query.count()
        items: list[ReturnPurchaseBill] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

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

    @staticmethod
    def add_detail(pcbillid: str, lineno: int, data: dict[str, Any]) -> ReturnPurchaseBillDt:
        record = ReturnPurchaseBillDt(
            pcbillid=pcbillid,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record


class RequisitionOrderLinkRepository:
    """需求-订单关联表数据访问。"""

    @staticmethod
    def create_links(details: list[dict[str, Any]]) -> None:
        now = datetime.now(UTC)
        for d in details:
            link = RequisitionOrderLink(
                pcplanid=d["ref_pcplanid"],
                pclineno=d["ref_pclineno"],
                rgstbillid=d["rgstbillid"],
                rgstlineno=d["rgstlineno"],
                linkqty=d["rgsqty"],
                gendate=now,
            )
            db.session.add(link)

    @staticmethod
    def get_available_items(suppliercd: str | None = None) -> list[dict[str, Any]]:
        sql = sa.text(
            "SELECT * FROM v_item_requisition_status"
            + (
                " WHERE itemcd IN ("
                "SELECT itemcd FROM tip02_supplier_price WHERE supp_cd = :supp_cd"
                ")"
                if suppliercd
                else ""
            )
        )
        params = {"supp_cd": suppliercd} if suppliercd else {}
        result = db.session.execute(sql, params)
        return [dict(row._mapping) for row in result]


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


class PurchasePlanStatusRepository:
    """采购计划状态汇总数据访问（TPC03_PCPLANSTATUS）。"""

    @staticmethod
    def get_by_id(itemcd: str) -> PurchasePlanStatus | None:
        return db.session.get(PurchasePlanStatus, itemcd)

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> tuple[list[PurchasePlanStatus], int]:
        query = db.session.query(PurchasePlanStatus).order_by(PurchasePlanStatus.itemcd)
        total: int = query.count()
        items: list[PurchasePlanStatus] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PurchasePlanStatus:
        now = datetime.now(UTC)
        record = PurchasePlanStatus(opercd=creator, gendate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: PurchasePlanStatus, data: dict[str, Any]) -> PurchasePlanStatus:
        now = datetime.now(UTC)
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        record.upddate = now
        return record
