"""采购管理业务服务层。"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime as dt
from typing import Any

import sqlalchemy as sa

from app.extensions import db
from app.repositories.procurement_repository import (
    PurchaseBillRepository,
    PurchasePlanRepository,
    PurchasePlanStatusRepository,
    PurchaseRegisterRepository,
    RequisitionOrderLinkRepository,
    ReturnPurchaseRepository,
    SupplierAppraisalRepository,
)


logger = logging.getLogger(__name__)


class PurchasePlanService:
    """采购需求服务 (原采购计划，TPC01/TPC02)。"""

    @staticmethod
    def dashboard_stats() -> dict[str, Any]:
        """执行看板统计数据。"""
        return PurchasePlanRepository.dashboard_stats()

    @staticmethod
    def get(pcplanid: str) -> dict[str, Any] | None:
        from app.models.master import Item
        record = PurchasePlanRepository.get_by_id(pcplanid)
        if record is None:
            return None
        result = record.to_dict()
        details = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        # 补充物料名称
        item_cds = [d["itemcd"] for d in details if d.get("itemcd")]
        if item_cds:
            items = db.session.query(Item.item_cd, Item.item_nm).filter(Item.item_cd.in_(item_cds)).all()
            item_nm_map = {row.item_cd: row.item_nm for row in items}
            for d in details:
                d["item_nm"] = item_nm_map.get(d.get("itemcd", ""), "")
        # 补充执行跟踪数据
        exec_data = PurchasePlanRepository.get_execution_by_plan(pcplanid)
        exec_map: dict[int, dict[str, Any]] = {}
        for row in exec_data:
            exec_map[int(row["lineno"])] = row
        for d in details:
            lineno = int(d.get("lineno", 0))
            if lineno in exec_map:
                d["ordered_qty"] = str(exec_map[lineno].get("ordered_qty", 0))
                d["received_qty"] = str(exec_map[lineno].get("received_qty", 0))
                d["available_qty"] = str(exec_map[lineno].get("available_qty", 0))
                d["execution_status"] = exec_map[lineno].get("execution_status", "")
                d["execution_rate"] = str(exec_map[lineno].get("execution_rate", 0))
        result["details"] = details
        return result

    @staticmethod
    def list_records(
        auditflg: str | None = None,
        pctyp: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PurchasePlanRepository.list_by_filters(
            auditflg=auditflg, pctyp=pctyp, start_date=start_date, end_date=end_date, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]],
        creator: str,
    ) -> dict[str, Any]:
        record = PurchasePlanRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            PurchasePlanRepository.add_detail(
                pcplanid=record.pcplanid, lineno=idx, data=detail_data
            )
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def audit(
        pcplanid: str, auditor: str,
        auditflg: str = "2", checkmemo: str = "",
        details: list[dict[str, Any]] | None = None,
    ) -> dict[str, object]:
        record = PurchasePlanRepository.get_by_id(pcplanid)
        if record is None:
            return {"success": False, "error": "采购需求不存在"}
        if record.auditflg not in ("0", "1", "9"):
            return {"success": False, "error": "已审核，不可重复操作"}
        PurchasePlanRepository.audit(record, auditor, auditflg, checkmemo)
        if auditflg == "2" and details:
            logger.info("采购需求审核明细: pcplanid=%s details=%s", pcplanid, details)
            for d in details:
                PurchasePlanRepository.update_audit_qty(
                    pcplanid, int(d.get("lineno", 0)), int(d.get("auditqty", 0))
                )
        db.session.commit()
        return {"success": True, "pcplanid": record.pcplanid}

    @staticmethod
    def void(pcplanid: str, operator: str, reason: str = "") -> dict[str, object]:
        """作废采购需求。

        规则：
        1. 未审批(auditflg='0')或送审中(auditflg='1')可直接作废
        2. 已审批(auditflg='2')需检查是否有关联订单
        3. 已作废(auditflg='9')不可重复作废
        4. 有关联订单时禁止作废
        """
        record = PurchasePlanRepository.get_by_id(pcplanid)
        if record is None:
            return {"success": False, "error": "采购需求不存在"}

        # 检查是否已作废
        if record.auditflg == "9":
            return {"success": False, "error": "该需求单已作废"}

        # 检查关联订单
        link_count = RequisitionOrderLinkRepository.count_by_pcplanid(pcplanid)
        if link_count > 0:
            return {
                "success": False,
                "error": f"该需求单已生成{link_count}个采购订单，无法作废，请先取消关联订单",
            }

        # 执行作废
        memo_suffix = f"\n[作废]操作人:{operator},时间:{dt.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if reason:
            memo_suffix += f",原因:{reason}"

        PurchasePlanRepository.void(record, memo_suffix)
        db.session.commit()
        logger.info("采购需求作废成功: pcplanid=%s, operator=%s", pcplanid, operator)
        return {"success": True, "pcplanid": record.pcplanid}


class PurchaseRegisterService:
    """采购订单服务 (原采购登记，TPC12/TPC13)。"""

    @staticmethod
    def get(rgstbillid: str) -> dict[str, Any] | None:
        record = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PurchaseRegisterRepository.list_by_filters(
            suppliercd=suppliercd, auditflg=auditflg, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]],
        creator: str,
    ) -> dict[str, Any]:
        # 校验余额：每个明细的采购数量不能超过来源需求单的可用余额
        for d in details:
            ref_pcplanid = d.get("ref_pcplanid")
            ref_pclineno = d.get("ref_pclineno")
            rgsqty = float(d.get("rgsqty", 0))
            if ref_pcplanid and ref_pclineno is not None:
                available = PurchasePlanRepository.get_available_qty(
                    str(ref_pcplanid), int(ref_pclineno)
                )
                if rgsqty > available:
                    raise ValueError(
                        f"采购数量({rgsqty})超过需求 {ref_pcplanid} "
                        f"行 {ref_pclineno} 的可用余额({available})"
                    )

        record = PurchaseRegisterRepository.create(data, creator)
        rgstbillid = record.rgstbillid

        for i, d in enumerate(details, start=1):
            PurchaseRegisterRepository.add_detail(
                rgstbillid=rgstbillid, lineno=i, data=d
            )

        # 写入 TPC20 关联表
        link_details = [
            {**d, "rgstbillid": rgstbillid, "rgstlineno": i}
            for i, d in enumerate(details, start=1)
            if d.get("ref_pcplanid") and d.get("ref_pclineno") is not None
        ]
        if link_details:
            RequisitionOrderLinkRepository.create_links(link_details)

        db.session.commit()
        return record.to_dict()

    @staticmethod
    def _lock_requisition_line(pcplanid: str, pclineno: int) -> None:
        """获取需求行的 advisory lock，防止并发超量。"""
        key = int(hashlib.md5(f"{pcplanid}:{pclineno}".encode()).hexdigest()[:16], 16)
        db.session.execute(sa.text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})

    @staticmethod
    def batch_create(orders_data: list[dict[str, Any]], creator: str) -> dict[str, Any]:
        """批量创建采购订单（统一处理拆单和并单）。

        校验规则：
        1. 汇总所有 detail 按 (pcplanid, pclineno) 的 rgsqty
        2. 逐一获取 advisory lock（排序避免死锁）
        3. 检查已关联数量 + 新增数量 ≤ available_qty
        4. 写入 tpc12 → tpc13 → TPC20
        """
        from collections import defaultdict

        if not orders_data:
            raise ValueError("orders 不能为空")
        if len(orders_data) > 10:
            raise ValueError("单次最多创建 10 个订单")

        # 1. 收集需求行 + 汇总数量
        req_line_qty: dict[tuple[str, int], float] = defaultdict(float)
        for order in orders_data:
            for d in order.get("details", []):
                ref_pid = d.get("ref_pcplanid")
                ref_lno = d.get("ref_pclineno")
                if ref_pid and ref_lno is not None:
                    req_line_qty[(str(ref_pid), int(ref_lno))] += float(d.get("rgsqty", 0))

        # 2. 逐一获取 advisory lock（排序避免死锁）
        for (pid, lno) in sorted(req_line_qty.keys()):
            PurchaseRegisterService._lock_requisition_line(pid, lno)

        # 3. 校验数量
        for (pid, lno), total_qty in req_line_qty.items():
            available = PurchasePlanRepository.get_available_qty(pid, lno)
            if total_qty > available:
                raise ValueError(
                    f"需求 {pid} 行 {lno} 总采购数量({total_qty})超过可用余额({available})"
                )

        # 4. 逐个创建订单
        created_orders = []
        for order_data in orders_data:
            details = order_data.get("details", [])
            record = PurchaseRegisterRepository.create_from_batch(order_data, creator)
            rgstbillid = record.rgstbillid

            for i, d in enumerate(details, start=1):
                PurchaseRegisterRepository.add_detail_from_batch(rgstbillid, i, d)

            # 写入 TPC20 关联表（沿用现有 create_links 的键名约定）
            link_details = [
                {**d, "rgstbillid": rgstbillid, "rgstlineno": i}
                for i, d in enumerate(details, start=1)
                if d.get("ref_pcplanid") and d.get("ref_pclineno") is not None
            ]
            if link_details:
                RequisitionOrderLinkRepository.create_links(link_details)

            created_orders.append(rgstbillid)

        db.session.commit()
        return {"created_orders": created_orders, "count": len(created_orders)}

    @staticmethod
    def audit(
        rgstbillid: str, auditor: str,
        auditflg: str = "2", checkmemo: str = "",
        details: list[dict[str, Any]] | None = None,
    ) -> dict[str, object]:
        record = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if record is None:
            return {"success": False, "error": "采购订单不存在"}
        if record.auditflg not in ("0", "1", "9"):
            return {"success": False, "error": "已审核，不可重复操作"}
        PurchaseRegisterRepository.audit(record, auditor, auditflg, checkmemo)
        if auditflg == "2" and details:
            for d in details:
                PurchaseRegisterRepository.update_audit_qty(
                    rgstbillid, int(d.get("lineno", 0)), int(d.get("auditqty", 0))
                )
        db.session.commit()
        return {"success": True, "rgstbillid": record.rgstbillid}


class PurchaseBillService:
    """采购结算单服务 (原采购单据，TPC14)。"""

    @staticmethod
    def get(pcbillid: str) -> dict[str, Any] | None:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_records(
        whcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PurchaseBillRepository.list_by_filters(
            whcd=whcd, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = PurchaseBillRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class ReturnPurchaseService:
    """采购退货服务 (TPC16/TPC17)。"""

    @staticmethod
    def get(pcbillid: str) -> dict[str, Any] | None:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        whcd: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = ReturnPurchaseRepository.list_by_filters(
            whcd=whcd, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]],
        creator: str,
    ) -> dict[str, Any]:
        record = ReturnPurchaseRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            ReturnPurchaseRepository.add_detail(
                pcbillid=record.pcbillid, lineno=idx, data=detail_data
            )
        db.session.commit()
        return record.to_dict()


class SupplierAppraisalService:
    """供应商评价服务 (TPC20/TPC21)。"""

    @staticmethod
    def get(appid: str) -> dict[str, Any] | None:
        record = SupplierAppraisalRepository.get_by_id(appid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = SupplierAppraisalRepository.list_by_filters(
            auditflg=auditflg, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]],
        creator: str,
    ) -> dict[str, Any]:
        record = SupplierAppraisalRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            SupplierAppraisalRepository.add_detail(appid=record.appid, lineno=idx, data=detail_data)
        db.session.commit()
        return record.to_dict()


class PurchasePlanStatusService:
    """@deprecated 采购需求执行看板服务 (原 TPC03，已冻结)。"""

    @staticmethod
    def get(itemcd: str) -> dict[str, Any] | None:
        record = PurchasePlanStatusRepository.get_by_id(itemcd)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = PurchasePlanStatusRepository.list_all(page=page, per_page=per_page)
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = PurchasePlanStatusRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(itemcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = PurchasePlanStatusRepository.get_by_id(itemcd)
        if record is None:
            return None
        PurchasePlanStatusRepository.update(record, data)
        db.session.commit()
        return record.to_dict()
