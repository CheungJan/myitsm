"""全模块事务查询与错账更正数据访问层。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, text

from app.extensions import db
from app.models.itsm import MaintenanceDaily
from app.models.master import Customer, CustomerHistory
from app.models.procurement import (
    PurchaseBill,
    PurchasePlan,
    PurchaseRegister,
)
from app.models.sales import PlanCust, SalesBill, SalesExtend
from app.models.warehouse import StockIn, StockOut


# ──────────────────────────────────────────────────────────────
# 全模块单据统一查询
# ──────────────────────────────────────────────────────────────

_BILL_TABLES: dict[str, Any] = {
    "itsm_maintenance": MaintenanceDaily,
    "purchase_plan": PurchasePlan,
    "purchase_register": PurchaseRegister,
    "purchase_bill": PurchaseBill,
    "sales_plan": PlanCust,
    "sales_bill": SalesBill,
    "sales_extend": SalesExtend,
    "stock_in": StockIn,
    "stock_out": StockOut,
}


class TransactionRepository:
    """全模块单据统一查询。"""

    @staticmethod
    def list_all_bills(
        bill_type: str | None = None,
        store_id: str | None = None,
        status: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """跨模块联合查询单据。

        通过 UNION ALL 将所有模块的主单据合并为统一视图。
        """
        queries: list[Any] = []
        bill_map: dict[str, tuple[Any, str, str, str, str | None]] = {
            "itsm_maintenance": (
                MaintenanceDaily,
                "maintenance_id",
                "current_status",
                "create_time",
                "store_id",
            ),
            "purchase_plan": (PurchasePlan, "pcplanid", "auditflg", "gendate", None),
            "purchase_register": (PurchaseRegister, "rgstbillid", "auditflg", "gendate", None),
            "purchase_bill": (PurchaseBill, "pcbillid", "useflg", "gendate", None),
            "sales_plan": (PlanCust, "planno", "plan_status", "gendate", None),
            "sales_bill": (SalesBill, "slbillid", "auditflg", "gendate", None),
            "sales_extend": (SalesExtend, "opbillid", "auditflg", "gendate", None),
            "stock_in": (StockIn, "inbillid", "auditflg", "gendate", None),
            "stock_out": (StockOut, "outbillid", "auditflg", "gendate", None),
        }

        types_to_query = [bill_type] if bill_type else list(bill_map.keys())

        for bt in types_to_query:
            if bt not in bill_map:
                continue
            model_cls, id_field, status_field, date_field, store_field = bill_map[bt]
            query = db.session.query(
                db.literal(bt).label("bill_type"),
                getattr(model_cls, id_field).label("bill_id"),
                getattr(model_cls, status_field).label("status"),
                getattr(model_cls, date_field).label("create_time"),
            )
            # 按门店过滤（仅支持有此字段的表）
            if store_id and store_field and hasattr(model_cls, store_field):
                query = query.filter(getattr(model_cls, store_field) == store_id)
            # 按状态过滤
            if status:
                query = query.filter(getattr(model_cls, status_field) == status)
            # 按日期范围
            if start_date:
                query = query.filter(getattr(model_cls, date_field) >= start_date)
            if end_date:
                query = query.filter(getattr(model_cls, date_field) <= end_date)
            # 按关键字（搜索单号）
            if keyword:
                query = query.filter(getattr(model_cls, id_field).ilike(f"%{keyword}%"))
            queries.append(query)

        if not queries:
            return [], 0

        # UNION ALL — 查询全部结果后 Python 排序分页
        base_q = queries[0]
        for q in queries[1:]:
            base_q = base_q.union_all(q)

        all_rows = base_q.all()
        # 按 create_time（第4列）降序
        all_rows.sort(key=lambda r: r[3] or "", reverse=True)
        total = len(all_rows)
        page_rows = all_rows[(page - 1) * per_page : page * per_page]

        items = [
            {
                "bill_type": r[0],
                "bill_id": r[1],
                "status": r[2],
                "create_time": r[3].isoformat() if r[3] else None,
                "bill_type_label": _bill_type_label(r[0]),
            }
            for r in page_rows
        ]
        return items, total

    @staticmethod
    def get_bill_types() -> list[dict[str, str]]:
        """获取所有单据类型列表。"""
        return [
            {"type": k, "label": _bill_type_label(k)}
            for k in _BILL_TABLES
        ]


# ──────────────────────────────────────────────────────────────
# 错账更正
# ──────────────────────────────────────────────────────────────


class ErrorCorrectionRepository:
    """错账更正数据访问。

    实现"红蓝单"更正模式：
    1. 原单标记为已冲销（red_flg='1'）
    2. 生成蓝字更正单（correct_flg='1'）
    3. 记录审计日志
    """

    CORRECTABLE_TABLES = {
        "stock_in": StockIn,
        "stock_out": StockOut,
    }

    @staticmethod
    def get_record(table_name: str, record_id: str) -> Any | None:
        """获取可更正的单据记录。"""
        model_cls = ErrorCorrectionRepository.CORRECTABLE_TABLES.get(table_name)
        if model_cls is None:
            return None
        pk = None
        for attr_name in ["inbillid", "outbillid"]:
            if hasattr(model_cls, attr_name):
                pk = attr_name
                break
        if pk is None:
            return None
        return db.session.get(model_cls, record_id)

    @staticmethod
    def mark_reversed(table_name: str, record_id: str, operator: str) -> dict[str, Any] | None:
        """标记原单为已冲销。"""
        model_cls = ErrorCorrectionRepository.CORRECTABLE_TABLES.get(table_name)
        if model_cls is None:
            return None

        record = ErrorCorrectionRepository.get_record(table_name, record_id)
        if record is None:
            return None

        now = datetime.now(UTC)
        # 原单标记冲销
        setattr(record, "redflg", "1")
        setattr(record, "upddate", now)

        # 记录更正日志到 AccLog (tmc41_acclog)
        log = text(
            "INSERT INTO tmc41_acclog (oper_cd, startdate, action, detail) "
            "VALUES (:oper, :dt, :action, :detail)"
        )
        db.session.execute(
            log,
            {
                "oper": operator,
                "dt": now,
                "action": "RED_CORRECTION",
                "detail": f"冲销 {table_name} {record_id}",
            },
        )

        return {
            "original_id": record_id,
            "table_name": table_name,
            "reversed_at": now.isoformat(),
            "operator": operator,
        }


# ──────────────────────────────────────────────────────────────
# 进销存汇总
# ──────────────────────────────────────────────────────────────


class StockSummaryRepository:
    """进销存汇总查询。"""

    @staticmethod
    def get_stock_summary(
        whcd: str | None = None,
        itemtyp: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """按物料汇总进销存数据。"""
        from app.models.warehouse import StockDetailDt, Warehouse as Wh

        filters: list[Any] = []
        if whcd:
            filters.append(StockDetailDt.whcd == whcd)
        if itemtyp:
            filters.append(StockDetailDt.itemtyp == itemtyp)

        query = (
            db.session.query(
                StockDetailDt.whcd,
                Wh.whnm,
                StockDetailDt.itemcd,
                StockDetailDt.itemtyp,
                func.count(StockDetailDt.seqno).label("movement_count"),
                func.sum(StockDetailDt.itemqty).label("total_change"),
                func.max(StockDetailDt.storeqty).label("current_balance"),
            )
            .outerjoin(Wh, StockDetailDt.whcd == Wh.whcd)
            .filter(*filters)
            .group_by(StockDetailDt.whcd, Wh.whnm, StockDetailDt.itemcd, StockDetailDt.itemtyp)
        )
        if start_date:
            query = query.filter(StockDetailDt.invdate >= start_date)
        if end_date:
            query = query.filter(StockDetailDt.invdate <= end_date)

        total = query.count()
        rows = (
            query.order_by(StockDetailDt.whcd, StockDetailDt.itemcd)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        items = [
            {
                "whcd": r[0],
                "warehouse_name": r[1],
                "itemcd": r[2],
                "itemtyp": r[3],
                "movement_count": int(r[4] or 0),
                "total_change": int(r[5] or 0),
                "current_balance": int(r[6] or 0),
            }
            for r in rows
        ]
        return items, total


def _bill_type_label(t: str) -> str:
    """单据类型中文标签。"""
    labels: dict[str, str] = {
        "itsm_maintenance": "日常维护单",
        "purchase_plan": "采购计划",
        "purchase_register": "采购登记",
        "purchase_bill": "采购单据",
        "sales_plan": "预计划",
        "sales_bill": "销售单据",
        "sales_extend": "销售延期",
        "stock_in": "入库单",
        "stock_out": "出库单",
    }
    return labels.get(t, t)
