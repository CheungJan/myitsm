"""采购管理业务服务层。"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, datetime as dt, timedelta
from typing import Any

import sqlalchemy as sa

from app.extensions import db
from app.models.finance import Payable
from app.models.procurement import (
    PurchaseBill,
    PurchaseBillDt,
    PurchasePlanDt,
    PurchaseRegisterDt,
    RequisitionOrderLink,
)
from app.models.warehouse import StockIn

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
        pcplanid: str | None = None,
        pctyp: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        execution_status: str | None = None,
        overdue_only: bool = False,
        hide_unavailable: bool = False,
        page: int = 1,
        per_page: int = 20,
        exclude_completed: bool = False,
    ) -> dict[str, Any]:
        items, total = PurchasePlanRepository.list_by_filters(
            auditflg=auditflg, pcplanid=pcplanid, pctyp=pctyp, start_date=start_date, end_date=end_date,
            execution_status=execution_status, overdue_only=overdue_only, hide_unavailable=hide_unavailable, page=page, per_page=per_page
        )
        result_items = []
        for item in items:
            d = item.to_dict()
            d["execution_status"] = PurchasePlanRepository.get_plan_execution_status(item.pcplanid)
            if exclude_completed and d["execution_status"] in ("已完成", "已下单"):
                total -= 1
                continue
            result_items.append(d)
        return {
            "items": result_items,
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
    def update(pcplanid: str, data: dict[str, Any]) -> dict[str, object]:
        """编辑采购需求（仅限已退回的）。"""
        record = PurchasePlanRepository.get_by_id(pcplanid)
        if record is None:
            return {"success": False, "error": "采购需求不存在"}
        if record.auditflg != '9':
            return {"success": False, "error": "仅已退回的需求单可编辑"}
        # 更新主表
        for k in ('pctyp', 'slbillid', 'plandate', 'memo'):
            if k in data:
                setattr(record, k, data[k] if data[k] != "" else None)
        # 更新明细
        details = data.get('details', [])
        if details:
            from app.models.procurement import PurchasePlanDt
            # 删除旧明细，重新插入
            db.session.query(PurchasePlanDt).filter(
                PurchasePlanDt.pcplanid == pcplanid
            ).delete()
            for idx, d in enumerate(details, start=1):
                PurchasePlanRepository.add_detail(pcplanid, idx, d)
        record.auditflg = '0'
        db.session.commit()
        return {"success": True, "pcplanid": pcplanid}

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
        from app.models.master import Item
        from app.models.master import Supplier

        record = PurchaseRegisterRepository.get_by_id(rgstbillid)
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
        result["details"] = details
        # 补充供应商名称
        if record.suppliercd:
            supp = db.session.query(Supplier.supp_nm).filter(Supplier.supp_cd == record.suppliercd).first()
            result["supp_nm"] = supp.supp_nm if supp else record.suppliercd
        else:
            result["supp_nm"] = ""
        return result

    @staticmethod
    def list_records(
        suppliercd: str | None = None,
        rgstbillid: str | None = None,
        ref_pcplanid: str | None = None,
        auditflg: str | None = None,
        execution_status: str | None = None,
        page: int = 1,
        per_page: int = 20,
        show_voided: bool = False,
    ) -> dict[str, Any]:
        items, total = PurchaseRegisterRepository.list_by_filters(
            suppliercd=suppliercd, rgstbillid=rgstbillid, ref_pcplanid=ref_pcplanid, auditflg=auditflg, execution_status=execution_status,
            page=page, per_page=per_page, show_voided=show_voided
        )
        result_items = []
        for item in items:
            d = item.to_dict()
            d["execution_status"] = PurchaseRegisterRepository.get_order_execution_status(item.rgstbillid)
            d["ref_pcplanids"] = PurchaseRegisterRepository.get_order_ref_pcplanids(item.rgstbillid)
            result_items.append(d)
        return {
            "items": result_items,
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
    def update(rgstbillid: str, data: dict[str, Any]) -> dict[str, object]:
        """编辑采购订单（仅限未审核或已退回的订单）。"""
        record = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if record is None:
            return {"success": False, "error": "采购订单不存在"}
        if record.auditflg not in ('0', '9'):
            return {"success": False, "error": "仅未送审或已退回的订单可编辑"}
        # 更新主表（空字符串转为None，避免timestamp类型报错）
        for k, v in data.items():
            if k == 'details':
                continue
            if hasattr(record, k) and k not in ('rgstbillid', 'auditflg', 'opercd', 'gendate'):
                setattr(record, k, v if v != "" else None)
        # 更新明细数量并同步TPC20链接
        details = data.get('details', [])
        if details:
            for d in details:
                qty = int(d.get('rgsqty', 0))
                price = float(d.get('rgstprice') or 0)
                if qty <= 0:
                    return {"success": False, "error": f"第{d.get('lineno','?')}行数量不能为0或负数"}
                if price <= 0:
                    return {"success": False, "error": f"第{d.get('lineno','?')}行（{d.get('itemcd','')}）单价不能为0，请填写有效价格"}
            dt_map = {d.lineno: d for d in record.details}  # type: ignore[attr-defined]
            for d in details:
                lineno = int(d.get('lineno', 0))
                new_qty = int(d.get('rgsqty', 0))
                dt = dt_map.get(lineno)
                if dt and new_qty > 0:
                    old_qty = int(dt.rgsqty or 0)
                    dt.rgsqty = new_qty
                    if 'rgstprice' in d:
                        dt.rgstprice = float(d['rgstprice']) if d['rgstprice'] else None
                    # 同步TPC20 linkqty
                    db.session.query(RequisitionOrderLink).filter(
                        RequisitionOrderLink.rgstbillid == rgstbillid,
                        RequisitionOrderLink.rgstlineno == lineno,
                    ).update({'linkqty': new_qty})
                    # 调减需求审核量（释放的数量不再保留为可用余额）
                    diff = old_qty - new_qty
                    if diff > 0 and dt.ref_pcplanid and dt.ref_pclineno:
                        db.session.query(PurchasePlanDt).filter(
                            PurchasePlanDt.pcplanid == dt.ref_pcplanid,
                            PurchasePlanDt.lineno == int(dt.ref_pclineno),
                        ).update({
                            'auditqty': PurchasePlanDt.auditqty - diff
                        }, synchronize_session=False)
        # 重置为未送审状态
        record.auditflg = '0'
        db.session.commit()
        return {"success": True, "rgstbillid": rgstbillid}

    @staticmethod
    def _lock_requisition_line(pcplanid: str, pclineno: int) -> None:
        """获取需求行的 advisory lock，防止并发超量。"""
        raw = int(hashlib.md5(f"{pcplanid}:{pclineno}".encode()).hexdigest()[:16], 16)
        # PostgreSQL pg_advisory_xact_lock 只接受 bigint（有符号64位），需转换
        key = raw - (1 << 64) if raw >= (1 << 63) else raw
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
        # 校验明细：数量和单价
        for i, order in enumerate(orders_data):
            for j, d in enumerate(order.get("details", [])):
                qty = float(d.get("rgsqty", 0))
                price = float(d.get("unitprice") or 0)
                if qty <= 0:
                    raise ValueError(f"第{i+1}个订单第{j+1}行采购数量不能为0或负数")
                if price <= 0:
                    raise ValueError(f"第{i+1}个订单第{j+1}行（{d.get('itemcd','')}）单价不能为0，请填写有效价格")

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

        # 3. 校验数量（含重复合并检测）
        for (pid, lno), total_qty in req_line_qty.items():
            available = PurchasePlanRepository.get_available_qty(pid, lno)
            if available <= 0:
                raise ValueError(
                    f"需求单 {pid} 行 {lno} 已被其他订单占用（可用余额为0），请刷新页面后重新操作"
                )
            if total_qty > available:
                raise ValueError(
                    f"需求单 {pid} 行 {lno} 采购数量({total_qty})超过可用余额({available})，请刷新页面后重新操作"
                )

        # 4. 逐个创建订单
        created_orders = []
        for order_data in orders_data:
            details = order_data.get("details", [])
            record = PurchaseRegisterRepository.create_from_batch(order_data, creator)
            rgstbillid = record.rgstbillid

            total_amt = 0.0
            for i, d in enumerate(details, start=1):
                PurchaseRegisterRepository.add_detail_from_batch(rgstbillid, i, d)
                qty = float(d.get("rgsqty", 0))
                price = float(d.get("unitprice") or 0)
                total_amt += qty * price
            # 回填主表金额
            if total_amt > 0:
                record.rgstamt = total_amt

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
    def batch_validate(orders_data: list[dict[str, Any]]) -> dict[str, Any]:
        """批量订单预校验，返回每个需求行的可用数量。"""
        from collections import defaultdict

        req_line_qty: dict[tuple[str, int], float] = defaultdict(float)
        for order in orders_data:
            for d in order.get("details", []):
                ref_pid = d.get("ref_pcplanid")
                ref_lno = d.get("ref_pclineno")
                if ref_pid and ref_lno is not None:
                    req_line_qty[(str(ref_pid), int(ref_lno))] += float(d.get("rgsqty", 0))

        checks = []
        valid = True
        for (pid, lno), total_qty in req_line_qty.items():
            available = PurchasePlanRepository.get_available_qty(pid, lno)
            ok = total_qty <= available
            if not ok:
                valid = False
            checks.append({
                "pcplanid": pid, "pclineno": lno,
                "available_qty": available, "requested_qty": total_qty,
                "valid": ok,
            })

        return {"valid": valid, "checks": checks}

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
        if auditflg == "2":
            if details:
                dt_map = {d.lineno: d for d in record.details}  # type: ignore[attr-defined]
                for d in details:
                    lineno = int(d.get("lineno", 0))
                    auditqty = int(d.get("auditqty", 0))
                    dt = dt_map.get(lineno)
                    if dt and auditqty > int(dt.rgsqty or 0):
                        return {
                            "success": False,
                            "error": f"行{lineno}审核数量({auditqty})超过采购数量({dt.rgsqty})",
                        }
                    PurchaseRegisterRepository.update_audit_qty(rgstbillid, lineno, auditqty)
            else:
                # 未传明细时，审核数量自动等于采购数量
                for dt in record.details:  # type: ignore[attr-defined]
                    PurchaseRegisterRepository.update_audit_qty(
                        rgstbillid, dt.lineno, int(dt.rgsqty or 0))
        db.session.commit()
        return {"success": True, "rgstbillid": record.rgstbillid}

    @staticmethod
    def void(rgstbillid: str) -> dict[str, object]:
        """作废采购订单，释放占用的需求余额。"""
        record = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if record is None:
            return {"success": False, "error": "采购订单不存在"}
        if record.auditflg == '2':
            return {"success": False, "error": "已审核通过的订单不能作废"}
        # 删除TPC20关联（释放需求余额）
        db.session.query(RequisitionOrderLink).filter(
            RequisitionOrderLink.rgstbillid == rgstbillid
        ).delete()
        # 逻辑删除订单
        record.useflg = '9'
        db.session.commit()
        return {"success": True, "rgstbillid": rgstbillid}


class PurchaseBillService:
    """采购结算单服务 (TPC14 + TPC14_DT)。"""

    @staticmethod
    def _sync_invoice_flag(data: dict[str, Any]) -> None:
        invoice_no = str(data.get("invoice_no") or "").strip()
        invoice_date = data.get("invoice_date")
        data["invoiceflg"] = "1" if invoice_no or invoice_date else "0"

    @staticmethod
    def get(pcbillid: str) -> dict[str, Any] | None:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return None
        result = record.to_dict()
        if result.get("invoiceflg") != "1" and (result.get("invoice_no") or result.get("invoice_date")):
            result["invoiceflg"] = "1"
        details = [d.to_dict() for d in PurchaseBillRepository.list_details(pcbillid)]
        for d in details:
            d.pop("bill", None)
        result["details"] = details
        return result

    @staticmethod
    def list_records(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        pay_type: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
        show_voided: bool = False,
    ) -> dict[str, Any]:
        items, total = PurchaseBillRepository.list_by_filters(
            suppliercd=suppliercd, auditflg=auditflg, pay_type=pay_type,
            start_date=start_date, end_date=end_date, page=page, per_page=per_page,
            show_voided=show_voided,
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total, "page": page, "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str, force: bool = False) -> dict[str, Any]:
        details = data.pop("details", [])
        total_amt = 0.0
        validated_details = []
        for d in details:
            ref_bill = d["ref_rgstbillid"]
            ref_line = d["ref_rgstlineno"]
            settle_qty = float(d["settle_qty"])
            settle_price = float(d["settle_price"])

            # PurchaseRegisterDt 主键是 id，用 rgstbillid + lineno 查询
            order_dt = (
                db.session.query(PurchaseRegisterDt)
                .filter(
                    PurchaseRegisterDt.rgstbillid == ref_bill,
                    PurchaseRegisterDt.lineno == ref_line,
                )
                .first()
            )
            if order_dt is None:
                raise ValueError(f"订单行 {ref_bill}:{ref_line} 不存在")

            order_qty = float(order_dt.rgsqty or 0)
            order_price = float(order_dt.rgstprice or 0)
            received_qty = float(order_dt.inqty or 0)
            already = PurchaseBillRepository.get_settled_total(ref_bill, ref_line)

            pay_type = data.get("pay_type", "COD")
            if pay_type in ("COD", "MON"):
                max_settle = received_qty - already
            else:
                max_settle = order_qty - already

            if settle_qty > max_settle:
                raise ValueError(
                    f"订单 {ref_bill} 行 {ref_line} 结算数量({settle_qty})"
                    f"超过可结算余量({max_settle})"
                )

            settle_amt = settle_qty * settle_price
            total_amt += settle_amt
            validated_details.append({
                **d,
                "order_qty": order_qty,
                "order_price": order_price,
                "received_qty": received_qty,
                "already_settled": already,
                "settle_amt": settle_amt,
            })

        # 付款方式一致性校验（force=True 时跳过校验，直接写入留痕）
        current_pay = data.get("pay_type", "COD")
        ref_bill_ids = {d["ref_rgstbillid"] for d in validated_details}
        conflict_prev_types: set[str] = set()
        for bill_id in ref_bill_ids:
            prev_rows = (
                db.session.query(PurchaseBill.pay_type)
                .join(PurchaseBillDt, PurchaseBillDt.pcbillid == PurchaseBill.pcbillid)
                .filter(
                    PurchaseBill.useflg != "9",
                    PurchaseBillDt.ref_rgstbillid == bill_id,
                )
                .distinct()
                .all()
            )
            for (pt,) in prev_rows:
                if pt and pt != current_pay:
                    conflict_prev_types.add(pt)
        if conflict_prev_types and not force:
            return {
                "success": False,
                "conflict": True,
                "prev_types": list(conflict_prev_types),
                "error": f"订单历史结算使用 {list(conflict_prev_types)}，当前选择 {current_pay}，付款方式不一致",
            }
        if conflict_prev_types and force:
            # 强制绕过：记录留痕标记，说明追加至 memo
            data["pay_type_override"] = "Y"
            override_note = f"[付款方式冲突确认] 历史使用 {','.join(sorted(conflict_prev_types))}，本次强制选择 {current_pay}"
            existing_memo = data.get("memo") or ""
            data["memo"] = f"{existing_memo} {override_note}".strip()

        # DEP 尾款校验：使用订单原始单价，非本次结算单价
        if data.get("settle_stage") == "final":
            for d in validated_details:
                order_total = float(d["order_qty"]) * float(d["order_price"])
                total_settled = float(d["already_settled"]) + float(d["settle_amt"])
                if total_settled > order_total + 0.01:
                    raise ValueError(
                        f"尾款结算：订单 {d['ref_rgstbillid']} 行 {d['ref_rgstlineno']} "
                        f"累计结算金额({total_settled:.2f})超过订单金额({order_total:.2f})"
                    )

        # INS 分期校验：检查分期序号不重复
        if data.get("pay_type") == "INS":
            installment_no = data.get("installment_no")
            if not installment_no:
                raise ValueError("分期付款必须填写分期序号")
            for d in validated_details:
                existing = (
                    db.session.query(PurchaseBill)
                    .join(PurchaseBillDt, PurchaseBillDt.pcbillid == PurchaseBill.pcbillid)
                    .filter(
                        PurchaseBill.pay_type == "INS",
                        PurchaseBill.useflg != "9",
                        PurchaseBillDt.ref_rgstbillid == d["ref_rgstbillid"],
                        PurchaseBillDt.ref_rgstlineno == d["ref_rgstlineno"],
                        PurchaseBill.installment_no == installment_no,
                    )
                    .first()
                )
                if existing:
                    raise ValueError(
                        f"订单 {d['ref_rgstbillid']} 行 {d['ref_rgstlineno']} "
                        f"第 {installment_no} 期已存在（结算单号 {existing.pcbillid}）"
                    )

        data["total_settle_amt"] = total_amt
        data["auditflg"] = "0"
        PurchaseBillService._sync_invoice_flag(data)
        record = PurchaseBillRepository.create(data, creator)
        for i, d in enumerate(validated_details, start=1):
            d.pop("order_price", None)  # 仅用于校验，不入库
            PurchaseBillRepository.add_detail(record.pcbillid, i, d)
        db.session.commit()
        return PurchaseBillService.get(record.pcbillid)  # type: ignore[return-value]

    @staticmethod
    def update(pcbillid: str, data: dict[str, Any], force: bool = False) -> dict[str, object]:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "结算单不存在"}
        if record.auditflg not in ("0", "9"):
            return {"success": False, "error": "仅未审核或已退回单据可编辑"}

        details = data.pop("details", None)
        if details is not None:
            total_amt = 0.0
            validated_details = []
            for d in details:
                ref_bill = d["ref_rgstbillid"]
                ref_line = d["ref_rgstlineno"]
                settle_qty = float(d["settle_qty"])
                settle_price = float(d["settle_price"])

                order_dt = (
                    db.session.query(PurchaseRegisterDt)
                    .filter(
                        PurchaseRegisterDt.rgstbillid == ref_bill,
                        PurchaseRegisterDt.lineno == ref_line,
                    )
                    .first()
                )
                if order_dt is None:
                    raise ValueError(f"订单行 {ref_bill}:{ref_line} 不存在")

                order_qty = float(order_dt.rgsqty or 0)
                order_price = float(order_dt.rgstprice or 0)
                received_qty = float(order_dt.inqty or 0)
                already = PurchaseBillRepository.get_settled_total(ref_bill, ref_line, pcbillid)

                pay_type = data.get("pay_type", record.pay_type or "COD")
                max_settle = (received_qty if pay_type in ("COD", "MON") else order_qty) - already
                if settle_qty > max_settle:
                    raise ValueError(
                        f"订单 {ref_bill} 行 {ref_line} 结算数量({settle_qty})"
                        f"超过可结算余量({max_settle})"
                    )

                settle_amt = settle_qty * settle_price
                total_amt += settle_amt
                validated_details.append({
                    **d, "order_qty": order_qty, "order_price": order_price,
                    "received_qty": received_qty,
                    "already_settled": already, "settle_amt": settle_amt,
                })

            # 付款方式一致性校验（force=True 时跳过）
            current_pay_u = data.get("pay_type", record.pay_type or "COD")
            ref_bill_ids_u = {d["ref_rgstbillid"] for d in validated_details}
            conflict_prev_types_u: set[str] = set()
            for bill_id in ref_bill_ids_u:
                prev_rows_u = (
                    db.session.query(PurchaseBill.pay_type)
                    .join(PurchaseBillDt, PurchaseBillDt.pcbillid == PurchaseBill.pcbillid)
                    .filter(
                        PurchaseBill.useflg != "9",
                        PurchaseBill.pcbillid != pcbillid,
                        PurchaseBillDt.ref_rgstbillid == bill_id,
                    )
                    .distinct()
                    .all()
                )
                for (pt,) in prev_rows_u:
                    if pt and pt != current_pay_u:
                        conflict_prev_types_u.add(pt)
            if conflict_prev_types_u and not force:
                return {
                    "success": False,
                    "conflict": True,
                    "prev_types": list(conflict_prev_types_u),
                    "error": f"订单历史结算使用 {list(conflict_prev_types_u)}，当前选择 {current_pay_u}，付款方式不一致",
                }
            if conflict_prev_types_u and force:
                data["pay_type_override"] = "Y"
                override_note_u = f"[付款方式冲突确认] 历史使用 {','.join(sorted(conflict_prev_types_u))}，本次强制选择 {current_pay_u}"
                existing_memo_u = data.get("memo") or record.memo or ""
                data["memo"] = f"{existing_memo_u} {override_note_u}".strip()

            # DEP 尾款校验：使用订单原始单价，非本次结算单价
            if data.get("settle_stage", record.settle_stage) == "final":
                for d in validated_details:
                    order_total = float(d["order_qty"]) * float(d["order_price"])
                    total_settled = float(d["already_settled"]) + float(d["settle_amt"])
                    if total_settled > order_total + 0.01:
                        raise ValueError(
                            f"尾款结算：订单 {d['ref_rgstbillid']} 行 {d['ref_rgstlineno']} "
                            f"累计结算金额({total_settled:.2f})超过订单金额({order_total:.2f})"
                        )

            # INS 分期校验（编辑时同样去重）
            if data.get("pay_type", record.pay_type) == "INS":
                inst_no = data.get("installment_no", record.installment_no)
                if inst_no:
                    for d in validated_details:
                        existing = (
                            db.session.query(PurchaseBill)
                            .join(PurchaseBillDt)
                            .filter(
                                PurchaseBill.pay_type == "INS",
                                PurchaseBill.useflg != "9",
                                PurchaseBill.pcbillid != pcbillid,
                                PurchaseBillDt.ref_rgstbillid == d["ref_rgstbillid"],
                                PurchaseBillDt.ref_rgstlineno == d["ref_rgstlineno"],
                                PurchaseBill.installment_no == inst_no,
                            )
                            .first()
                        )
                        if existing:
                            raise ValueError(
                                f"订单 {d['ref_rgstbillid']} 行 {d['ref_rgstlineno']} "
                                f"第 {inst_no} 期已存在（结算单号 {existing.pcbillid}）"
                            )

            data["total_settle_amt"] = total_amt
            PurchaseBillRepository.clear_details(pcbillid)
            for i, d in enumerate(validated_details, start=1):
                d.pop("order_price", None)  # 仅用于校验，不入库
                PurchaseBillRepository.add_detail(pcbillid, i, d)

        PurchaseBillService._sync_invoice_flag(data)
        PurchaseBillRepository.update(record, data)
        record.auditflg = "0"
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def audit(pcbillid: str, auditor: str, auditflg: str) -> dict[str, object]:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "结算单不存在"}
        if record.useflg == "9":
            return {"success": False, "error": "已作废单据不可审核"}
        if record.auditflg not in ("0", "1"):
            return {"success": False, "error": "不可重复审核"}
        # 驳回时退回未审核状态，允许用户修改后重新送审
        record.auditflg = "0" if auditflg == "9" else auditflg
        record.auditman = auditor
        record.auditdate = dt.now(UTC)

        # 审核通过后自动生成应付记录
        if auditflg == "2":
            existing_payable = db.session.query(Payable).filter(Payable.po_id == record.pcbillid).first()
            # 结算日期：优先用结算单日期，否则当前日期
            settle_date = (
                record.pcdate.date()
                if record.pcdate and hasattr(record.pcdate, "date")
                else dt.now(UTC).date()
            )
            # 到期日：优先用记录中的 due_date，月结且无 due_date 时默认 30 天后
            due_date_val = record.due_date if record.due_date else settle_date
            if (record.pay_type or "").upper() == "MON" and not record.due_date:
                due_date_val = settle_date + timedelta(days=30)

            amount = float(record.total_settle_amt or 0)
            if existing_payable is None:
                payable = Payable(
                    ap_id=f"AP{uuid.uuid4().hex[:6].upper()}",
                    supp_cd=record.suppliercd or "",
                    po_id=record.pcbillid,
                    ap_date=settle_date,
                    due_date=due_date_val,
                    amount=amount,
                    paid_amount=0,
                    balance=amount,
                    status="PENDING",
                    remark=f"采购结算单 {record.pcbillid}",
                    opercd=auditor,
                )
                db.session.add(payable)
            else:
                paid_amount = float(existing_payable.paid_amount or 0)
                existing_payable.supp_cd = record.suppliercd or ""
                existing_payable.ap_date = settle_date
                existing_payable.due_date = due_date_val
                existing_payable.amount = amount
                existing_payable.balance = amount - paid_amount
                existing_payable.status = (
                    "PAID" if existing_payable.balance <= 0
                    else "PARTIAL" if paid_amount > 0
                    else "PENDING"
                )
                existing_payable.remark = f"采购结算单 {record.pcbillid}"
                existing_payable.opercd = auditor

            # PIA 款到发货：标记应付状态为"已付"（等待入库流程）
            if (record.pay_type or "").upper() == "PIA":
                target = existing_payable if existing_payable else payable
                target.status = "PAID"

        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def void(pcbillid: str) -> dict[str, object]:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "结算单不存在"}
        if record.auditflg == "2":
            return {"success": False, "error": "已审核通过的结算单不能作废"}
        record.useflg = "9"
        record.auditflg = "V"
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def get_settleable_items(rgstbillid: str) -> list[dict[str, Any]]:
        """查询订单的可结算商品行。"""
        order = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if order is None:
            raise ValueError("订单不存在")
        items = []
        # 查入库仓库及最近入库日期（用于结算单自动带出和月份显示）
        receiving_wh = (
            db.session.query(StockIn.whcd, StockIn.indate)
            .filter(
                StockIn.refbillid == rgstbillid,
                StockIn.invtyp == "1",    # 仅采购入库
                StockIn.auditflg != "9",  # 排除已作废
            )
            .order_by(StockIn.indate.desc())
            .first()
        )
        receiving_whcd = receiving_wh[0] if receiving_wh else None
        receiving_date = receiving_wh[1].strftime("%Y-%m-%d") if receiving_wh and receiving_wh[1] else None
        # 查询该订单的历史结算付款方式（用于冲突检测）
        prev_settle_types = (
            db.session.query(PurchaseBill.pay_type, PurchaseBill.installment_no, PurchaseBill.total_installments)
            .join(PurchaseBillDt, PurchaseBill.pcbillid == PurchaseBillDt.pcbillid)
            .filter(
                PurchaseBill.useflg != "9",
                PurchaseBillDt.ref_rgstbillid == rgstbillid,
            )
            .distinct()
            .all()
        )
        prev_types = list({r[0] for r in prev_settle_types if r[0]})
        ins_info = next((r for r in prev_settle_types if r[0] == "INS"), None)
        ins_next_no = (ins_info[1] or 0) + 1 if ins_info else None
        ins_total = ins_info[2] if ins_info else None
        for detail_line in order.details:  # type: ignore[attr-defined]
            d = detail_line.to_dict()
            order_qty = float(detail_line.rgsqty or 0)
            received_qty = float(detail_line.inqty or 0)
            settled = PurchaseBillRepository.get_settled_total(rgstbillid, detail_line.lineno)
            returned = ReturnPurchaseRepository.get_returned_total(rgstbillid, detail_line.lineno)
            d["order_qty"] = order_qty
            d["received_qty"] = received_qty
            d["already_settled"] = settled
            d["already_returned"] = returned
            d["settleable_qty_cod"] = max(0, received_qty - settled)
            d["settleable_qty_pia"] = max(0, order_qty - settled)
            d["receiving_whcd"] = receiving_whcd
            d["receiving_date"] = receiving_date
            d["prev_pay_types"] = prev_types
            d["ins_next_no"] = ins_next_no
            d["ins_total"] = ins_total
            items.append(d)
        return items

    @staticmethod
    def get_monthly_receiving(suppliercd: str, period: str) -> list[dict[str, Any]]:
        """查询某供应商某月已审核订单的入库记录（月结汇总用）。"""
        from app.models.procurement import PurchaseRegister

        try:
            period_date = dt.strptime(period, "%Y-%m")
        except ValueError:
            raise ValueError(f"period 格式错误: {period}，应为 YYYY-MM")

        start_date = period_date
        if period_date.month == 12:
            end_date = period_date.replace(year=period_date.year + 1, month=1)
        else:
            end_date = period_date.replace(month=period_date.month + 1)

        order_ids = (
            db.session.query(PurchaseRegister.rgstbillid)
            .filter(
                PurchaseRegister.suppliercd == suppliercd,
                PurchaseRegister.auditflg == "2",
            )
            .subquery()
        )

        rows = (
            db.session.query(StockIn.refbillid, StockIn.whcd, StockIn.indate)
            .filter(
                StockIn.refbillid.in_(order_ids),
                StockIn.invtyp == "1",
                StockIn.auditflg != "9",
                StockIn.indate >= start_date,
                StockIn.indate < end_date,
            )
            .all()
        )
        return [
            {
                "rgstbillid": r.refbillid,
                "whcd": r.whcd,
                "indate": r.indate.isoformat() if r.indate else None,
            }
            for r in rows
        ]


class ReturnPurchaseService:
    """采购退货服务 (TPC16/TPC17)。"""

    @staticmethod
    def get(pcbillid: str) -> dict[str, Any] | None:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return None
        result = record.to_dict()
        details = [d.to_dict() for d in ReturnPurchaseRepository.list_details(pcbillid)]
        for d in details:
            d.pop("bill", None)
        result["details"] = details
        return result

    @staticmethod
    def list_records(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        return_reason: str | None = None,
        ref_rgstbillid: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
        show_voided: bool = False,
    ) -> dict[str, Any]:
        items, total = ReturnPurchaseRepository.list_by_filters(
            suppliercd=suppliercd, auditflg=auditflg, return_reason=return_reason,
            ref_rgstbillid=ref_rgstbillid,
            start_date=start_date, end_date=end_date, page=page, per_page=per_page,
            show_voided=show_voided,
        )
        # 批量查关联出库单状态
        pcbillids = [item.pcbillid for item in items]
        linked_out_map: dict[str, dict[str, str]] = {}
        if pcbillids:
            rows = db.session.execute(
                sa.text(
                    "SELECT refbillid, outbillid, auditflg FROM twh15_out "
                    "WHERE invtyp='6' AND refbillid = ANY(:ids)"
                ),
                {"ids": pcbillids},
            ).fetchall()
            for r in rows:
                linked_out_map[r.refbillid] = {"outbillid": r.outbillid, "auditflg": r.auditflg}
        result_items = []
        for item in items:
            d = item.to_dict()
            linked = linked_out_map.get(item.pcbillid)
            d["linked_out_id"] = linked["outbillid"] if linked else None
            d["linked_out_auditflg"] = linked["auditflg"] if linked else None
            result_items.append(d)
        return {
            "items": result_items,
            "total": total, "page": page, "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        details = data.pop("details", [])
        ref_rgstbillid = data.get("ref_rgstbillid", "")
        total_amt = 0
        for d in details:
            rpcqty = int(d.get("rpcqty", 0))
            ref_line = int(d.get("ref_rgstlineno", 0))
            if rpcqty <= 0:
                raise ValueError(f"行 {ref_line} 退货数量必须大于0")

            # PurchaseRegisterDt 主键是 id，用 rgstbillid + lineno 查询
            order_dt = (
                db.session.query(PurchaseRegisterDt)
                .filter(
                    PurchaseRegisterDt.rgstbillid == ref_rgstbillid,
                    PurchaseRegisterDt.lineno == ref_line,
                )
                .first()
            )
            if order_dt is None:
                raise ValueError(f"订单行 {ref_rgstbillid}:{ref_line} 不存在")
            received_qty = int(order_dt.inqty or 0)
            if received_qty <= 0:
                raise ValueError(f"订单行 {ref_rgstbillid}:{ref_line} 尚未入库，无法退货")

            already_returned = ReturnPurchaseRepository.get_returned_total(ref_rgstbillid, ref_line)
            max_return = received_qty - int(already_returned)
            if rpcqty > max_return:
                raise ValueError(
                    f"行 {ref_line} 退货数量({rpcqty})超过可退余量({max_return})"
                )

            return_price = float(d.get("return_price") or 0)
            return_amt = rpcqty * return_price
            total_amt += int(return_amt)
            d["return_amt"] = return_amt

        data["pcamt"] = total_amt
        data["auditflg"] = "0"
        record = ReturnPurchaseRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            ReturnPurchaseRepository.add_detail(record.pcbillid, idx, detail_data)
        db.session.commit()
        return ReturnPurchaseService.get(record.pcbillid)  # type: ignore[return-value]

    @staticmethod
    def update(pcbillid: str, data: dict[str, Any]) -> dict[str, object]:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "退货单不存在"}
        if record.auditflg not in ("0", "9"):
            return {"success": False, "error": "仅未审核或已退回单据可编辑"}

        details = data.pop("details", None)
        if details is not None:
            ref_rgstbillid = record.ref_rgstbillid or ""
            total_amt = 0
            for d in details:
                rpcqty = int(d.get("rpcqty", 0))
                ref_line = int(d.get("ref_rgstlineno", 0))
                if rpcqty <= 0:
                    raise ValueError(f"行 {ref_line} 退货数量必须大于0")
                order_dt = (
                    db.session.query(PurchaseRegisterDt)
                    .filter(
                        PurchaseRegisterDt.rgstbillid == ref_rgstbillid,
                        PurchaseRegisterDt.lineno == ref_line,
                    )
                    .first()
                )
                received_qty = int(order_dt.inqty or 0) if order_dt else 0
                already_returned = ReturnPurchaseRepository.get_returned_total(
                    ref_rgstbillid, ref_line
                )
                max_return = received_qty - int(already_returned)
                if rpcqty > max_return:
                    raise ValueError(f"行 {ref_line} 退货数量({rpcqty})超过可退余量({max_return})")
                return_price = float(d.get("return_price") or 0)
                return_amt = rpcqty * return_price
                total_amt += int(return_amt)
                d["return_amt"] = return_amt
            data["pcamt"] = total_amt
            ReturnPurchaseRepository.clear_details(pcbillid)
            for idx, d in enumerate(details, start=1):
                ReturnPurchaseRepository.add_detail(pcbillid, idx, d)

        ReturnPurchaseRepository.update(record, data)
        record.auditflg = "0"
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def audit(pcbillid: str, auditor: str, auditflg: str) -> dict[str, object]:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "退货单不存在"}
        if record.useflg == "9":
            return {"success": False, "error": "已作废单据不可审核"}
        if record.auditflg not in ("0", "1"):
            return {"success": False, "error": "不可重复审核"}
        record.auditflg = auditflg
        record.auditman = auditor
        record.auditdate = dt.now(UTC)
        # P0-3: 审核通过后自动生成退货出库草稿
        if auditflg == "2":
            from app.services.warehouse_service import StockOutService
            if not record.whcd:
                logger.warning("退货单 %s 无仓库编码，跳过生成出库草稿", pcbillid)
            else:
                try:
                    prd_details = []
                    eid_details = []
                    for dt_line in record.details:  # type: ignore[attr-defined]
                        prd_details.append({
                            "itemcd": dt_line.itemcd,
                            "itemtyp": dt_line.itemtyp or "DJ",
                            "outqty": dt_line.rpcqty or 0,
                            "reflineno": dt_line.ref_rgstlineno,
                        })
                        # 有 EID 的退货行同时生成 EID 明细
                        if dt_line.eid:
                            eid_details.append({
                                "itemcd": dt_line.itemcd,
                                "itemtyp": dt_line.itemtyp or "DJ",
                                "eid": dt_line.eid,
                                "outqty": dt_line.rpcqty or 0,
                                "reflineno": dt_line.ref_rgstlineno,
                            })
                    StockOutService.create(
                        data={
                            "invtyp": "6",
                            "whcd": record.whcd,
                            "refbillid": record.pcbillid,
                            "suppcd": record.suppliercd or "",
                        },
                        details_eid=eid_details if eid_details else None,
                        details_prd=prd_details,
                        creator=auditor,
                    )
                except Exception:
                    logger.exception("生成退货出库草稿失败: pcbillid=%s", pcbillid)
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def void(pcbillid: str) -> dict[str, object]:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "退货单不存在"}
        if record.auditflg == "2":
            return {"success": False, "error": "已审核通过的退货单不能作废"}
        record.useflg = "9"
        record.auditflg = "V"
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def get_returnable_items(rgstbillid: str) -> list[dict[str, Any]]:
        """查询订单的可退货商品行。"""
        order = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if order is None:
            raise ValueError("订单不存在")
        # 查入库仓库（用于退货单自动带出）
        receiving_wh = (
            db.session.query(StockIn.whcd)
            .filter(
                StockIn.refbillid == rgstbillid,
                StockIn.invtyp == "1",
                StockIn.auditflg != "9",
            )
            .order_by(StockIn.indate.desc())
            .first()
        )
        receiving_whcd = receiving_wh[0] if receiving_wh else None
        items = []
        for detail_line in order.details:  # type: ignore[attr-defined]
            d = detail_line.to_dict()
            received_qty = int(detail_line.inqty or 0)
            if received_qty <= 0:
                continue
            returned = ReturnPurchaseRepository.get_returned_total(rgstbillid, detail_line.lineno)
            d["received_qty"] = received_qty
            d["already_returned"] = int(returned)
            d["returnable_qty"] = max(0, received_qty - int(returned))
            d["receiving_whcd"] = receiving_whcd
            items.append(d)
        return items

    @staticmethod
    def list_returnable_orders() -> list[dict[str, Any]]:
        """列出所有有可退货商品行的已审核订单（入库量 > 已退量）。"""
        from app.models.procurement import (
            PurchaseRegister, PurchaseRegisterDt,
            ReturnPurchaseBill, ReturnPurchaseBillDt,
        )
        from sqlalchemy import func
        # 子查询：每行(rgstbillid, lineno)已退累计
        returned_sub = (
            db.session.query(
                ReturnPurchaseBill.ref_rgstbillid,
                ReturnPurchaseBillDt.ref_rgstlineno,
                func.coalesce(func.sum(ReturnPurchaseBillDt.rpcqty), 0).label("returned"),
            )
            .join(ReturnPurchaseBill, ReturnPurchaseBill.pcbillid == ReturnPurchaseBillDt.pcbillid)
            .filter(ReturnPurchaseBill.useflg != "9", ReturnPurchaseBill.ref_rgstbillid.isnot(None))
            .group_by(ReturnPurchaseBill.ref_rgstbillid, ReturnPurchaseBillDt.ref_rgstlineno)
            .subquery()
        )
        rows = (
            db.session.query(PurchaseRegister.rgstbillid, PurchaseRegister.suppliercd)
            .join(PurchaseRegisterDt, PurchaseRegister.rgstbillid == PurchaseRegisterDt.rgstbillid)
            .outerjoin(
                returned_sub,
                (PurchaseRegisterDt.rgstbillid == returned_sub.c.ref_rgstbillid)
                & (PurchaseRegisterDt.lineno == returned_sub.c.ref_rgstlineno),
            )
            .filter(
                PurchaseRegister.auditflg == "2",
                PurchaseRegister.useflg != "9",
                PurchaseRegisterDt.inqty > 0,
                PurchaseRegisterDt.inqty - func.coalesce(returned_sub.c.returned, 0) > 0,
            )
            .distinct()
            .order_by(PurchaseRegister.rgstbillid)
            .all()
        )
        return [{"rgstbillid": r.rgstbillid, "suppliercd": r.suppliercd} for r in rows]


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


class PurchasePlanMergeService:
    """智能合并服务。"""

    @staticmethod
    def merge_preview() -> dict[str, Any]:
        """扫描可合并的需求行，按 itemcd 分组，推荐供应商。"""
        details = PurchasePlanRepository.get_mergeable_details()
        if not details:
            return {
                "mergeable": [],
                "unmergeable": [],
                "summary": {
                    "mergeable_groups": 0,
                    "unmergeable_items": 0,
                    "estimated_orders": 0,
                },
            }

        from collections import defaultdict

        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for d in details:
            groups[d["itemcd"]].append(d)

        mergeable = []
        unmergeable = []
        for itemcd, lines in groups.items():
            total_qty = sum(float(l["available_qty"]) for l in lines)
            suppliers = PurchasePlanMergeService._get_suggested_suppliers(itemcd)
            group_data = {
                "itemcd": itemcd,
                "itemnm": lines[0].get("itemnm", ""),
                "total_qty": total_qty,
                "source_count": len(lines),
                "source_lines": [
                    {
                        "pcplanid": l["pcplanid"],
                        "pclineno": l["pclineno"],
                        "qty": l["available_qty"],
                        "dept": l.get("deptnm", ""),
                    }
                    for l in lines
                ],
                "suggested_suppliers": suppliers,
            }
            if len(lines) >= 2:
                mergeable.append(group_data)
            else:
                unmergeable.append(group_data)

        return {
            "mergeable": mergeable,
            "unmergeable": unmergeable,
            "summary": {
                "mergeable_groups": len(mergeable),
                "unmergeable_items": len(unmergeable),
                "estimated_orders": len(mergeable),
            },
        }

    @staticmethod
    def _get_suggested_suppliers(itemcd: str) -> list[dict[str, Any]]:
        """推荐供应商：已关联该物料的供应商，优先有报价的（价格升序）。"""
        from app.models.inventory import SupplierPrice
        from app.models.master import CustItems, Supplier

        # 1. 查已关联该物料的供应商（CustItems）
        cust_rows = (
            db.session.query(CustItems.custcd, Supplier.supp_nm)
            .join(Supplier, CustItems.custcd == Supplier.supp_cd)
            .filter(CustItems.itemcd == itemcd, Supplier.useflg == "1")
            .all()
        )
        if not cust_rows:
            return []

        # 2. 查供应商报价，用于排序和补充价格
        price_rows = (
            db.session.query(SupplierPrice)
            .filter(SupplierPrice.itemcd == itemcd)
            .all()
        )
        price_map: dict[str, dict[str, Any]] = {}
        for sp in price_rows:
            if sp.supp_cd not in price_map or float(sp.itemprice or 0) < float(price_map[sp.supp_cd]["itemprice"] or 0):
                price_map[sp.supp_cd] = {
                    "min_qty": float(sp.min_qty) if sp.min_qty else 0,
                    "itemprice": float(sp.itemprice) if sp.itemprice else 0,
                }

        # 3. 组装结果：有报价的排前面
        result = []
        for custcd, supp_nm in cust_rows:
            price_info = price_map.get(custcd)
            result.append({
                "supp_cd": custcd,
                "supp_nm": supp_nm,
                "min_qty": price_info["min_qty"] if price_info else 0,
                "itemprice": price_info["itemprice"] if price_info else 0,
            })

        result.sort(key=lambda x: (x["itemprice"] == 0, x["itemprice"]))
        return result[:5]
