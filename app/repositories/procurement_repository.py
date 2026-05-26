"""采购管理数据访问层。"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from datetime import datetime as dt
from typing import Any

import sqlalchemy as sa
from sqlalchemy import desc

from app.extensions import db
from app.models.master import IdMaster
from app.models.procurement import (
    PurchaseBill,
    PurchaseBillDt,
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


logger = logging.getLogger(__name__)


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


def _gen_pp_id() -> str:
    """生成采购需求单号，沿用PP前缀自增规则。"""
    return _gen_master_id("PP", "采购需求单号")


def _gen_pr_id() -> str:
    """生成采购订单号，沿用PR前缀自增规则。"""
    return _gen_master_id("PR", "采购订单号")


def _gen_master_id(id_type: str, id_type_name: str) -> str:
    """从 IdMaster 表取号并自增。"""
    id_master = db.session.get(IdMaster, id_type)
    if id_master is None:
        id_master = IdMaster(id_type=id_type, prefix=id_type, current_no=0, step=1, idtyp=id_type, idtypnm=id_type_name, curbillid="0", useflg="1")
        db.session.add(id_master)
        db.session.flush()
    step = id_master.step or 1
    current_no = id_master.current_no or 0
    next_no = current_no + step
    id_master.current_no = next_no
    id_master.curbillid = str(next_no)
    prefix = id_master.prefix or id_type
    return f"{prefix}{next_no:06d}"[:8]


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
        execution_status: str | None = None,
        overdue_only: bool = False,
        hide_unavailable: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PurchasePlan], int]:
        query = db.session.query(PurchasePlan).filter(PurchasePlan.useflg != "9")
        if auditflg:
            query = query.filter(PurchasePlan.auditflg == auditflg)
        if pctyp:
            query = query.filter(PurchasePlan.pctyp == pctyp)
        if start_date:
            query = query.filter(PurchasePlan.plandate >= start_date)
        if end_date:
            query = query.filter(PurchasePlan.plandate <= end_date)
        if execution_status:
            # 通过原生子查询过滤：汇总各需求单执行状态后与筛选值比对
            matched_ids_raw = db.session.execute(
                sa.text(
                    """
                    SELECT pcplanid FROM (
                        SELECT pcplanid,
                            CASE
                                WHEN COUNT(*) = SUM(CASE WHEN execution_status = '已完成' THEN 1 ELSE 0 END) THEN '已完成'
                                WHEN SUM(CASE WHEN execution_status != '未开始' THEN 1 ELSE 0 END) = 0 THEN '未开始'
                                WHEN SUM(CASE WHEN execution_status = '已下单' THEN 1 ELSE 0 END) > 0
                                     AND SUM(CASE WHEN execution_status NOT IN ('已下单','已完成') THEN 1 ELSE 0 END) = 0 THEN '已下单'
                                ELSE '执行中'
                            END AS agg_status
                        FROM v_requisition_execution
                        GROUP BY pcplanid
                    ) t WHERE agg_status = :status
                    """
                ),
                {"status": execution_status},
            ).fetchall()
            matched_ids = [r[0] for r in matched_ids_raw]
            if not matched_ids:
                return [], 0
            query = query.filter(PurchasePlan.pcplanid.in_(matched_ids))
        if hide_unavailable:
            query = query.filter(
                PurchasePlan.pcplanid.in_(
                    sa.text("SELECT DISTINCT pcplanid FROM v_requisition_execution WHERE available_qty > 0")
                )
            )
        if overdue_only:
            query = query.filter(
                PurchasePlan.pcplanid.in_(
                    sa.text("""
                        SELECT DISTINCT pcplanid FROM v_requisition_execution
                        WHERE execution_status != '已完成'
                          AND plandate < CURRENT_DATE - INTERVAL '7 days'
                    """)
                )
            )
        query = query.order_by(desc(PurchasePlan.gendate))
        total: int = query.count()
        items: list[PurchasePlan] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PurchasePlan:
        now = datetime.now(UTC)
        record = PurchasePlan(
            pcplanid=_gen_pp_id(),
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
    def void(record: PurchasePlan, memo_suffix: str) -> PurchasePlan:
        """作废采购需求。"""
        record.auditflg = "9"
        record.useflg = "9"
        record.memo = (record.memo or "") + memo_suffix
        return record

    @staticmethod
    def update_audit_qty(pcplanid: str, lineno: int, auditqty: int) -> None:
        logger.info("更新采购需求审核数量: pcplanid=%s lineno=%s auditqty=%s", pcplanid, lineno, auditqty)
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
    def get_mergeable_details() -> list[dict[str, Any]]:
        """查询可合并的需求明细：已审核 + 有可用余额。"""
        rows = db.session.execute(
            sa.text("""
                SELECT v.pcplanid, v.lineno AS pclineno, v.itemcd, v.itemnm,
                       v.available_qty,
                       COALESCE(dep.dept_nm, '') AS deptnm
                FROM v_requisition_execution v
                JOIN tpc02_pcplandt d ON v.pcplanid = d.pcplanid AND v.lineno = d.lineno
                JOIN tpc01_pcplan p ON v.pcplanid = p.pcplanid
                LEFT JOIN tmc13_users u ON p.opercd = u.user_cd
                LEFT JOIN tmc11_departments dep ON u.dept_cd = dep.dept_cd
                WHERE p.auditflg = '2'
                  AND v.available_qty > 0
                ORDER BY v.itemcd, v.pcplanid, v.lineno
            """)
        ).fetchall()
        return [
            {
                "pcplanid": r.pcplanid,
                "pclineno": r.pclineno,
                "itemcd": r.itemcd,
                "itemnm": r.itemnm,
                "available_qty": float(r.available_qty),
                "deptnm": r.deptnm,
            }
            for r in rows
        ]

    @staticmethod
    def get_execution_by_plan(pcplanid: str) -> list[dict[str, Any]]:
        rows = db.session.execute(sa.text(
            "SELECT lineno, ordered_qty, received_qty, available_qty, execution_status, execution_rate "
            "FROM v_requisition_execution WHERE pcplanid = :pid"
        ), {"pid": pcplanid}).fetchall()
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def get_plan_execution_status(pcplanid: str) -> str:
        """获取需求单计划级别的执行状态汇总。"""
        sql = sa.text("""
            SELECT
                CASE
                    WHEN COUNT(*) = 0 THEN '未开始'
                    WHEN COUNT(*) = SUM(CASE WHEN execution_status = '已完成' THEN 1 ELSE 0 END) THEN '已完成'
                    WHEN SUM(CASE WHEN execution_status != '未开始' THEN 1 ELSE 0 END) = 0 THEN '未开始'
                    WHEN SUM(CASE WHEN execution_status = '已下单' THEN 1 ELSE 0 END) > 0
                         AND SUM(CASE WHEN execution_status NOT IN ('已下单','已完成') THEN 1 ELSE 0 END) = 0 THEN '已下单'
                    ELSE '执行中'
                END AS plan_status
            FROM v_requisition_execution
            WHERE pcplanid = :pid
        """)
        result = db.session.execute(sql, {"pid": pcplanid}).scalar()
        return result or "未开始"

    @staticmethod
    def dashboard_stats() -> dict[str, Any]:
        stats = db.session.execute(sa.text("""
            WITH plan_status AS (
                SELECT pcplanid,
                    CASE
                        WHEN COUNT(*) = SUM(CASE WHEN execution_status = '已完成' THEN 1 ELSE 0 END) THEN '已完成'
                        WHEN SUM(CASE WHEN execution_status != '未开始' THEN 1 ELSE 0 END) = 0 THEN '未开始'
                        WHEN SUM(CASE WHEN execution_status = '已下单' THEN 1 ELSE 0 END) > 0
                             AND SUM(CASE WHEN execution_status NOT IN ('已下单','已完成') THEN 1 ELSE 0 END) = 0 THEN '已下单'
                        ELSE '执行中'
                    END AS agg_status
                FROM v_requisition_execution
                GROUP BY pcplanid
            )
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE agg_status = '已完成') AS completed,
                COUNT(*) FILTER (WHERE agg_status = '已下单') AS ordered,
                COUNT(*) FILTER (WHERE agg_status = '执行中') AS executing,
                COUNT(*) FILTER (WHERE agg_status = '未开始') AS not_started
            FROM plan_status
        """)).fetchone()

        top_items = [
            dict(row._mapping)
            for row in db.session.execute(sa.text("""
                SELECT
                    v.itemcd, v.itemnm,
                    SUM(v.plan_qty)::int AS total_plan,
                    SUM(v.ordered_qty)::numeric AS total_ordered,
                    SUM(v.received_qty)::numeric AS total_received,
                    COALESCE(ret.total_returned, 0)::numeric AS total_returned,
                    (SUM(v.received_qty) - COALESCE(ret.total_returned, 0))::numeric AS net_received,
                    CASE WHEN SUM(v.received_qty) > 0
                        THEN ROUND(COALESCE(ret.total_returned, 0) / SUM(v.received_qty) * 100, 1)
                        ELSE 0
                    END AS return_rate,
                    ROUND(AVG(v.execution_rate), 1) AS execution_rate
                FROM v_requisition_execution v
                LEFT JOIN (
                    SELECT rdt.itemcd, SUM(rdt.rpcqty)::numeric AS total_returned
                    FROM tpc17_rpcbilldt rdt
                    JOIN tpc16_rpcbill r ON rdt.pcbillid = r.pcbillid
                    WHERE r.useflg = '1'
                    GROUP BY rdt.itemcd
                ) ret ON v.itemcd = ret.itemcd
                GROUP BY v.itemcd, v.itemnm, ret.total_returned
                ORDER BY total_plan DESC LIMIT 10
            """)).fetchall()
        ]

        overdue = [
            dict(row._mapping)
            for row in db.session.execute(sa.text("""
                WITH plan_status AS (
                    SELECT pcplanid,
                        CASE
                            WHEN COUNT(*) = SUM(CASE WHEN execution_status = '已完成' THEN 1 ELSE 0 END) THEN '已完成'
                            WHEN SUM(CASE WHEN execution_status != '未开始' THEN 1 ELSE 0 END) = 0 THEN '未开始'
                            WHEN SUM(CASE WHEN execution_status = '已下单' THEN 1 ELSE 0 END) > 0
                                 AND SUM(CASE WHEN execution_status NOT IN ('已下单','已完成') THEN 1 ELSE 0 END) = 0 THEN '已下单'
                            ELSE '执行中'
                        END AS agg_status
                    FROM v_requisition_execution
                    GROUP BY pcplanid
                )
                SELECT p.pcplanid, p.plandate::date::text AS plandate,
                       CURRENT_DATE::text AS today,
                       (CURRENT_DATE - p.plandate::date) AS overdue_days,
                       ps.agg_status AS execution_status, p.memo, p.auditflg, p.pctyp
                FROM tpc01_pcplan p
                JOIN plan_status ps ON p.pcplanid = ps.pcplanid
                WHERE ps.agg_status != '已完成'
                  AND p.plandate < CURRENT_DATE - INTERVAL '7 days'
                ORDER BY p.plandate
            """)).fetchall()
        ]

        voided = db.session.execute(sa.text(
            "SELECT COUNT(*) AS cnt FROM tpc01_pcplan WHERE useflg = '9'"
        )).scalar()

        return {
            "stats": dict(stats._mapping) if stats else {},
            "voided": int(voided or 0),
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
        execution_status: str | None = None,
        page: int = 1,
        per_page: int = 20,
        show_voided: bool = False,
    ) -> tuple[list[PurchaseRegister], int]:
        query = db.session.query(PurchaseRegister)
        if suppliercd:
            query = query.filter(PurchaseRegister.suppliercd == suppliercd)
        if show_voided:
            # 只显示作废单据，忽略审批状态筛选
            query = query.filter(PurchaseRegister.useflg == "9")
        else:
            query = query.filter(PurchaseRegister.useflg != "9")
            if auditflg:
                query = query.filter(PurchaseRegister.auditflg == auditflg)
        if execution_status:
            matched_ids = db.session.execute(
                sa.text("""
                    SELECT rgstbillid FROM (
                        SELECT rgstbillid,
                            CASE
                                WHEN COALESCE(SUM(inqty), 0) = 0 THEN '未入库'
                                WHEN SUM(COALESCE(inqty,0)) >= SUM(rgsqty) THEN '已完成'
                                ELSE '部分入库'
                            END AS agg_status
                        FROM tpc13_registerdt
                        GROUP BY rgstbillid
                    ) t WHERE agg_status = :status
                """),
                {"status": execution_status},
            ).fetchall()
            matched_ids_list = [r[0] for r in matched_ids]
            if not matched_ids_list:
                return [], 0
            query = query.filter(PurchaseRegister.rgstbillid.in_(matched_ids_list))
        query = query.order_by(desc(PurchaseRegister.gendate))
        total: int = query.count()
        items: list[PurchaseRegister] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_order_execution_status(rgstbillid: str) -> str:
        """获取采购订单的执行状态。"""
        sql = sa.text("""
            SELECT
                CASE
                    WHEN COALESCE(SUM(inqty), 0) = 0 THEN '未入库'
                    WHEN SUM(COALESCE(inqty,0)) >= SUM(rgsqty) THEN '已完成'
                    ELSE '部分入库'
                END AS exec_status
            FROM tpc13_registerdt
            WHERE rgstbillid = :bid
        """)
        result = db.session.execute(sql, {"bid": rgstbillid}).scalar()
        return result or "未入库"

    @staticmethod
    def order_dashboard_stats() -> dict[str, Any]:
        """采购订单看板统计。"""
        stats = db.session.execute(sa.text("""
            WITH order_status AS (
                SELECT r.rgstbillid,
                    CASE
                        WHEN COALESCE(SUM(dt.inqty), 0) = 0 THEN '未入库'
                        WHEN SUM(COALESCE(dt.inqty,0)) >= SUM(dt.rgsqty) THEN '已完成'
                        ELSE '部分入库'
                    END AS exec_status
                FROM tpc12_register r
                JOIN tpc13_registerdt dt ON r.rgstbillid = dt.rgstbillid
                WHERE r.useflg != '9'
                GROUP BY r.rgstbillid
            )
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE exec_status = '已完成') AS completed,
                COUNT(*) FILTER (WHERE exec_status = '部分入库') AS partial,
                COUNT(*) FILTER (WHERE exec_status = '未入库') AS not_received
            FROM order_status
        """)).fetchone()

        audit_stats = db.session.execute(sa.text("""
            SELECT
                COUNT(*) FILTER (WHERE auditflg = '0') AS draft,
                COUNT(*) FILTER (WHERE auditflg = '1') AS pending,
                COUNT(*) FILTER (WHERE auditflg = '2') AS approved,
                COUNT(*) FILTER (WHERE auditflg = '9') AS rejected,
                COUNT(*) FILTER (WHERE useflg = '9') AS voided
            FROM tpc12_register
        """)).fetchone()

        return {
            "stats": dict(stats._mapping) if stats else {},
            "audit_stats": dict(audit_stats._mapping) if audit_stats else {},
        }

    @staticmethod
    def order_overdue() -> list[dict[str, Any]]:
        """采购订单逾期预警：审批滞留 + 交付逾期。"""
        rows = db.session.execute(sa.text("""
            SELECT rgstbillid, suppliercd, auditflg, gendate::date::text,
                   '审批滞留' AS type, (CURRENT_DATE - gendate::date)::int AS overdue_days
            FROM tpc12_register
            WHERE useflg != '9' AND auditflg = '1'
              AND gendate < CURRENT_DATE - INTERVAL '3 days'
            UNION ALL
            SELECT r.rgstbillid, r.suppliercd, r.auditflg, MIN(dt.deliverdate)::date::text,
                   '交付逾期' AS type,
                   (CURRENT_DATE - MIN(dt.deliverdate)::date)::int AS overdue_days
            FROM tpc12_register r
            JOIN tpc13_registerdt dt ON r.rgstbillid = dt.rgstbillid
            WHERE r.useflg != '9' AND r.auditflg = '2'
              AND dt.deliverdate IS NOT NULL AND dt.deliverdate < CURRENT_DATE
              AND COALESCE(dt.inqty, 0) < dt.rgsqty
            GROUP BY r.rgstbillid, r.suppliercd, r.auditflg
            ORDER BY overdue_days DESC
        """)).fetchall()
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PurchaseRegister:
        now = datetime.now(UTC)
        # 采购员默认取当前用户，下单日期默认当天
        if not data.get("pcrep"):
            data["pcrep"] = creator
        if not data.get("rgstdate"):
            data["rgstdate"] = now
        record = PurchaseRegister(
            rgstbillid=_gen_pr_id(),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def create_from_batch(order_data: dict[str, Any], creator: str) -> PurchaseRegister:
        """从批量数据创建订单主表记录。"""
        now = datetime.now(UTC)
        record = PurchaseRegister(
            rgstbillid=_gen_pr_id(),
            suppliercd=order_data.get("suppliercd", ""),
            pcrep=order_data.get("pcrep") or creator,
            rgstdate=order_data.get("rgstdate") or now,
            memo=order_data.get("memo", ""),
            opercd=creator,
            gendate=now,
            auditflg="0",
        )
        db.session.add(record)
        db.session.flush()
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
    def add_detail_from_batch(rgstbillid: str, lineno: int, detail: dict[str, Any]) -> PurchaseRegisterDt:
        """从批量数据创建订单明细。"""
        dt_record = PurchaseRegisterDt(
            rgstbillid=rgstbillid,
            lineno=lineno,
            itemcd=detail.get("itemcd", ""),
            rgsqty=float(detail.get("rgsqty", 0)),
            units=detail.get("units", "PCS"),
            rgstprice=float(detail.get("unitprice", 0)) if detail.get("unitprice") else None,
            ref_pcplanid=detail.get("ref_pcplanid"),
            ref_pclineno=detail.get("ref_pclineno"),
        )
        db.session.add(dt_record)
        db.session.flush()
        return dt_record

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
        suppliercd: str | None = None,
        auditflg: str | None = None,
        pay_type: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PurchaseBill], int]:
        query = db.session.query(PurchaseBill).filter(PurchaseBill.useflg != "9")
        if suppliercd:
            query = query.filter(PurchaseBill.suppliercd == suppliercd)
        if auditflg:
            query = query.filter(PurchaseBill.auditflg == auditflg)
        if pay_type:
            query = query.filter(PurchaseBill.pay_type == pay_type)
        if start_date:
            query = query.filter(PurchaseBill.gendate >= start_date)
        if end_date:
            query = query.filter(PurchaseBill.gendate <= end_date)
        query = query.order_by(desc(PurchaseBill.gendate))
        total: int = query.count()
        items: list[PurchaseBill] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PurchaseBill:
        now = datetime.now(UTC)
        record = PurchaseBill(
            pcbillid=_gen_master_id("SB", "采购结算单号"),
            opercd=creator,
            gendate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: PurchaseBill, data: dict[str, Any]) -> PurchaseBill:
        skip = {"pcbillid", "details", "opercd", "gendate", "auditflg", "auditman", "auditdate"}
        for k, v in data.items():
            if k in skip:
                continue
            setattr(record, k, v)
        return record

    @staticmethod
    def add_detail(pcbillid: str, lineno: int, data: dict[str, Any]) -> PurchaseBillDt:
        record = PurchaseBillDt(pcbillid=pcbillid, lineno=lineno, **data)
        db.session.add(record)
        return record

    @staticmethod
    def clear_details(pcbillid: str) -> None:
        db.session.query(PurchaseBillDt).filter(
            PurchaseBillDt.pcbillid == pcbillid
        ).delete()

    @staticmethod
    def list_details(pcbillid: str) -> list[PurchaseBillDt]:
        return db.session.query(PurchaseBillDt).filter(
            PurchaseBillDt.pcbillid == pcbillid
        ).order_by(PurchaseBillDt.lineno).all()

    @staticmethod
    def get_settled_total(ref_rgstbillid: str, ref_rgstlineno: int, exclude_pcbillid: str | None = None) -> float:
        """获取某订单行已结算累计（排除指定结算单）。"""
        from sqlalchemy import func
        q = db.session.query(func.coalesce(func.sum(PurchaseBillDt.settle_qty), 0)).filter(
            PurchaseBillDt.ref_rgstbillid == ref_rgstbillid,
            PurchaseBillDt.ref_rgstlineno == ref_rgstlineno,
        ).join(PurchaseBill, PurchaseBill.pcbillid == PurchaseBillDt.pcbillid).filter(
            PurchaseBill.useflg != "9"
        )
        if exclude_pcbillid:
            q = q.filter(PurchaseBillDt.pcbillid != exclude_pcbillid)
        return float(q.scalar() or 0)


class ReturnPurchaseRepository:
    """采购退货数据访问。"""

    @staticmethod
    def get_by_id(pcbillid: str) -> ReturnPurchaseBill | None:
        return db.session.get(ReturnPurchaseBill, pcbillid)

    @staticmethod
    def list_by_filters(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ReturnPurchaseBill], int]:
        query = db.session.query(ReturnPurchaseBill).filter(ReturnPurchaseBill.useflg != "9")
        if suppliercd:
            query = query.filter(ReturnPurchaseBill.suppliercd == suppliercd)
        if auditflg:
            query = query.filter(ReturnPurchaseBill.auditflg == auditflg)
        if start_date:
            query = query.filter(ReturnPurchaseBill.gendate >= start_date)
        if end_date:
            query = query.filter(ReturnPurchaseBill.gendate <= end_date)
        query = query.order_by(desc(ReturnPurchaseBill.gendate))
        total: int = query.count()
        items: list[ReturnPurchaseBill] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> ReturnPurchaseBill:
        now = datetime.now(UTC)
        record = ReturnPurchaseBill(
            pcbillid=_gen_master_id("RT", "采购退货单号"),
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

    @staticmethod
    def update(record: ReturnPurchaseBill, data: dict[str, Any]) -> ReturnPurchaseBill:
        skip = {"pcbillid", "details", "opercd", "gendate", "auditflg", "auditman", "auditdate"}
        for k, v in data.items():
            if k in skip:
                continue
            setattr(record, k, v)
        return record

    @staticmethod
    def clear_details(pcbillid: str) -> None:
        db.session.query(ReturnPurchaseBillDt).filter(
            ReturnPurchaseBillDt.pcbillid == pcbillid
        ).delete()

    @staticmethod
    def list_details(pcbillid: str) -> list[ReturnPurchaseBillDt]:
        return db.session.query(ReturnPurchaseBillDt).filter(
            ReturnPurchaseBillDt.pcbillid == pcbillid
        ).order_by(ReturnPurchaseBillDt.lineno).all()

    @staticmethod
    def get_returned_total(ref_rgstbillid: str, ref_rgstlineno: int) -> float:
        """获取某订单行已退货累计。"""
        from sqlalchemy import func
        return float(
            db.session.query(func.coalesce(func.sum(ReturnPurchaseBillDt.rpcqty), 0)).filter(
                ReturnPurchaseBillDt.ref_rgstlineno == ref_rgstlineno,
            ).join(ReturnPurchaseBill, ReturnPurchaseBill.pcbillid == ReturnPurchaseBillDt.pcbillid).filter(
                ReturnPurchaseBill.ref_rgstbillid == ref_rgstbillid,
                ReturnPurchaseBill.useflg != "9",
            ).scalar() or 0
        )


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
                " UNION "
                "SELECT itemcd FROM tmm24_custitems WHERE custcd = :supp_cd"
                ")"
                if suppliercd
                else ""
            )
        )
        params = {"supp_cd": suppliercd} if suppliercd else {}
        result = db.session.execute(sql, params)
        return [dict(row._mapping) for row in result]

    @staticmethod
    def count_by_pcplanid(pcplanid: str) -> int:
        """统计指定需求单的关联订单数量。"""
        return db.session.query(RequisitionOrderLink).filter(
            RequisitionOrderLink.pcplanid == pcplanid
        ).count()


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
