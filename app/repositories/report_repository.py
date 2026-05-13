"""报表查询数据访问层。

提供库存报表、EID追踪、销售状态统计等聚合查询。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models.inventory import InventoryLimit
from app.models.master import Bom, BomDt, CustPosRl, Eid, EidTrack
from app.models.sales import PlanCust, SalesBill, SalesExtend
from app.models.warehouse import StockDetail, StockDetailDt, Warehouse


class InventoryReportRepository:
    """库存报表查询。"""

    @staticmethod
    def get_snapshot(
        whcd: str | None = None,
        itemtyp: str | None = None,
        itemcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """库存快照：当前各仓库各物料库存余量。"""
        query = (
            db.session.query(
                StockDetail.whcd,
                Warehouse.whnm,
                StockDetail.itemtyp,
                StockDetail.itemcd,
                StockDetail.itemqty,
                StockDetail.upddate,
            )
            .outerjoin(Warehouse, StockDetail.whcd == Warehouse.whcd)
            .filter(StockDetail.useflg == "1", StockDetail.itemqty > 0)
        )
        if whcd:
            query = query.filter(StockDetail.whcd == whcd)
        if itemtyp:
            query = query.filter(StockDetail.itemtyp == itemtyp)
        if itemcd:
            query = query.filter(StockDetail.itemcd == itemcd)

        total = query.count()
        results = (
            query.order_by(StockDetail.whcd, StockDetail.itemcd)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        items = [
            {
                "whcd": r[0],
                "warehouse_name": r[1],
                "itemtyp": r[2],
                "itemcd": r[3],
                "itemqty": int(r[4] or 0),
                "updated_at": r[5].isoformat() if r[5] else None,
            }
            for r in results
        ]
        return items, total

    @staticmethod
    def get_alert_items() -> list[dict[str, Any]]:
        """库存预警清单：当前库存低于预警下限的物料。"""
        results = (
            db.session.query(
                StockDetail.whcd,
                Warehouse.whnm,
                StockDetail.itemcd,
                InventoryLimit.invlow,
                StockDetail.itemqty,
            )
            .join(Warehouse, StockDetail.whcd == Warehouse.whcd)
            .join(InventoryLimit, StockDetail.itemcd == InventoryLimit.itemcd)
            .filter(
                StockDetail.useflg == "1",
                InventoryLimit.invlow > StockDetail.itemqty,
            )
            .all()
        )
        return [
            {
                "whcd": r[0],
                "warehouse_name": r[1],
                "itemcd": r[2],
                "lower_limit": int(r[3] or 0),
                "current_qty": int(r[4] or 0),
                "shortage": int(r[3] or 0) - int(r[4] or 0),
            }
            for r in results
        ]

    @staticmethod
    def get_movement_log(
        whcd: str | None = None,
        itemcd: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """库存变动流水查询。"""
        query = db.session.query(StockDetailDt)
        if whcd:
            query = query.filter(StockDetailDt.whcd == whcd)
        if itemcd:
            query = query.filter(StockDetailDt.itemcd == itemcd)
        if start_date:
            query = query.filter(StockDetailDt.invdate >= start_date)
        if end_date:
            query = query.filter(StockDetailDt.invdate <= end_date)

        total = query.count()
        results = (
            query.order_by(StockDetailDt.invdate.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        items = [r.to_dict() for r in results]
        return items, total


class EidReportRepository:
    """EID 设备追踪报表查询。"""

    @staticmethod
    def get_lifecycle(
        eid_val: str | None = None,
        itemcd_val: str | None = None,
        custcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """EID 全生命周期追踪。

        从 tmm43_eid 获取当前状态，tmm35_cust_pos_rl 获取客户关联，
        tmm43_eid_track 获取变更历史。
        """
        query = (
            db.session.query(
                Eid.eid,
                Eid.itemcd,
                CustPosRl.cust_cd,
                Eid.sflg,
                Eid.gendate,
            )
            .outerjoin(CustPosRl, Eid.eid == CustPosRl.eid)
            .group_by(Eid.eid, Eid.itemcd, CustPosRl.cust_cd, Eid.sflg, Eid.gendate)
        )
        if eid_val:
            query = query.filter(Eid.eid.ilike(f"%{eid_val}%"))
        if itemcd_val:
            query = query.filter(Eid.itemcd == itemcd_val)
        if custcd:
            query = query.filter(CustPosRl.cust_cd == custcd)

        total = query.count()
        results = (
            query.order_by(Eid.gendate.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        items = [
            {
                "eid": r[0],
                "itemcd": r[1],
                "cust_cd": r[2],
                "status": r[3],
                "create_time": r[4].isoformat() if r[4] else None,
            }
            for r in results
        ]
        return items, total

    @staticmethod
    def get_tracks(
        eid_val: str, page: int = 1, per_page: int = 20
    ) -> tuple[list[dict[str, Any]], int]:
        """单个 EID 的变更追溯明细。"""
        query = (
            db.session.query(EidTrack)
            .filter(EidTrack.eid == eid_val)
            .order_by(EidTrack.change_date.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        items = [r.to_dict() for r in results]
        return items, total


class SalesReportRepository:
    """销售报表查询。"""

    @staticmethod
    def get_status_summary(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """销售状态汇总：按状态统计预计划/销售单/延期单数量。"""
        # 预计划按 plan_status 分组
        plan_query = db.session.query(
            PlanCust.plan_status, func.count(PlanCust.planno)
        )
        if start_date:
            plan_query = plan_query.filter(PlanCust.gendate >= start_date)
        if end_date:
            plan_query = plan_query.filter(PlanCust.gendate <= end_date)
        plan_stats = {
            row[0] or "未知": row[1]
            for row in plan_query.group_by(PlanCust.plan_status).all()
        }

        # 销售单据按 auditflg 分组
        bill_query = db.session.query(
            SalesBill.auditflg, func.count(SalesBill.slbillid)
        )
        if start_date:
            bill_query = bill_query.filter(SalesBill.gendate >= start_date)
        if end_date:
            bill_query = bill_query.filter(SalesBill.gendate <= end_date)
        bill_stats = {
            "已审核" if row[0] == "1" else "未审核": row[1]
            for row in bill_query.group_by(SalesBill.auditflg).all()
        }

        # 延期单按 auditflg 分组
        ext_query = db.session.query(
            SalesExtend.auditflg, func.count(SalesExtend.opbillid)
        )
        if start_date:
            ext_query = ext_query.filter(SalesExtend.gendate >= start_date)
        if end_date:
            ext_query = ext_query.filter(SalesExtend.gendate <= end_date)
        ext_stats = {
            "已审核" if row[0] == "1" else "未审核": row[1]
            for row in ext_query.group_by(SalesExtend.auditflg).all()
        }

        return {
            "plan_statistics": plan_stats,
            "bill_statistics": bill_stats,
            "extend_statistics": ext_stats,
            "period": {"start": start_date, "end": end_date},
        }

    @staticmethod
    def get_open_bills(
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """未结单据清单：预计划未实施 + 销售未审核 + 延期未审核。"""
        queries = []

        # 未实施预计划
        open_plans = (
            db.session.query(
                db.literal("plan").label("source"),
                PlanCust.planno.label("bill_id"),
                PlanCust.plan_status.label("status"),
                PlanCust.gendate.label("create_time"),
            )
            .filter(PlanCust.plan_status.notin_(["03", "09"]))
        )
        queries.append(open_plans)

        # 未审核销售单
        open_bills = (
            db.session.query(
                db.literal("sales_bill").label("source"),
                SalesBill.slbillid.label("bill_id"),
                SalesBill.auditflg.label("status"),
                SalesBill.gendate.label("create_time"),
            )
            .filter(SalesBill.auditflg != "1")
        )
        queries.append(open_bills)

        # 未审核延期
        open_ext = (
            db.session.query(
                db.literal("extend").label("source"),
                SalesExtend.opbillid.label("bill_id"),
                SalesExtend.auditflg.label("status"),
                SalesExtend.gendate.label("create_time"),
            )
            .filter(SalesExtend.auditflg != "1")
        )
        queries.append(open_ext)

        base_q = queries[0].union_all(queries[1]).union_all(queries[2])

        all_rows = base_q.all()
        all_rows.sort(key=lambda r: r[3] or "", reverse=True)
        total = len(all_rows)
        page_rows = all_rows[(page - 1) * per_page : page * per_page]

        source_label = {"plan": "预计划", "sales_bill": "销售单", "extend": "延期单"}
        items = [
            {
                "source": r[0],
                "source_label": source_label.get(r[0], r[0]),
                "bill_id": r[1],
                "status": r[2],
                "create_time": r[3].isoformat() if r[3] else None,
            }
            for r in page_rows
        ]
        return items, total


class BOMReportRepository:
    """BOM 报表查询。"""

    @staticmethod
    def get_bom_tree(
        itemcd_val: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """BOM 结构树查询：主物料→子物料清单。"""
        query = (
            db.session.query(
                Bom.bomcd,
                Bom.bomnm,
                BomDt.itemcd,
                BomDt.bomqty,
            )
            .join(BomDt, Bom.bomcd == BomDt.bomcd)
        )
        if itemcd_val:
            query = query.filter(BomDt.itemcd == itemcd_val)

        total = query.count()
        results = (
            query.order_by(Bom.bomcd, BomDt.itemcd)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        items = [
            {
                "bom_cd": r[0],
                "bom_name": r[1],
                "itemcd": r[2],
                "sub_qty": int(r[3] or 0) if r[3] else 0,
            }
            for r in results
        ]
        return items, total
