"""生产制造MES业务服务层（Tier-3 G7）。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.mes import WorkOrder
from app.repositories.mes_repository import (
    MaterialConsumeRepository,
    ProcessDefRepository,
    WorkOrderRepository,
    WorkProcessRepository,
)


class WorkOrderService:
    """生产工单服务。"""

    @staticmethod
    def get(wo_id: str) -> dict[str, Any] | None:
        record = WorkOrderRepository.get_by_id(wo_id)
        if record is None:
            return None
        result = record.to_dict()
        # 补充产品名称
        if result.get("item_cd"):
            from app.models.master import Item
            item = db.session.query(Item.item_nm).filter(Item.item_cd == result["item_cd"]).scalar()
            if item:
                result["item_nm"] = item
        processes = WorkProcessRepository.list_by_wo(wo_id)
        result["processes"] = [p.to_dict() for p in processes]
        # 补充 FQC 成品信息
        from app.models.warehouse import QcResult, QcResultEid
        fqc_records = db.session.query(QcResult).filter(
            QcResult.refbillid == wo_id, QcResult.auditflg == "1",
            QcResult.qcstatus.in_(["GA", "GB", "GC"]),
        ).all()
        if fqc_records:
            result["fqc_qcstatus"] = fqc_records[0].qcstatus
            # 成品+配件对应关系
            product_eids: list[str] = []
            part_eids: list[str] = []
            for fqc in fqc_records:
                eids = db.session.query(QcResultEid.eid, QcResultEid.itemcd).filter(
                    QcResultEid.qcbillid == fqc.qcbillid
                ).all()
                for e in eids:
                    if e.itemcd == record.item_cd:
                        product_eids.append(e.eid)
                    else:
                        part_eids.append(e.eid)
            # 简单分组：所有成品EID为一组，所有配件EID为另一组
            result["fqc_products"] = []
            if product_eids:
                result["fqc_products"].append({"product": ", ".join(product_eids), "parts": part_eids})
            elif part_eids:
                result["fqc_products"].append({"product": "", "parts": part_eids})
        return result

    # ------------------------------------------------------------------
    # 工单全生命周期聚合（供详情页一次性展现：下达→领料→生产→质检→补料→入库）
    # ------------------------------------------------------------------

    # 出库类型标签（TWH15_OUT.invtyp）
    _OUT_TYPE_LABELS = {
        "1": "销售出库", "2": "服务领用", "3": "调拨出库", "4": "借出出库",
        "5": "质检出库", "6": "退货出库", "7": "报废出库", "8": "其他出库",
        "9": "返修出库", "10": "翻新领料",
    }
    # 入库类型标签（TWH13_IN.invtyp）
    _IN_TYPE_LABELS = {
        "1": "采购入库", "2": "销售退货", "3": "服务返还", "4": "调拨入库",
        "5": "借出归还", "6": "翻新入库", "7": "回收入库", "8": "成品入库",
    }
    # 审核标签（出入库 0=草稿 1/2=已审核 V=作废 8=退回）
    _AUDIT_LABELS = {
        "0": "草稿", "1": "已审核", "2": "已审核", "V": "已作废", "8": "已退回",
    }
    # 消耗类型标签（TMS04.consume_type）
    _CONSUME_TYPE_LABELS = {
        "1": "定额领料", "2": "不良补料", "3": "报废出库", "4": "返修出库", "5": "退料入库",
    }
    # 不良品判定状态
    _DEFECT_STATUS = ("BF", "BH", "TH")

    @staticmethod
    def get_lifecycle(wo_id: str) -> dict[str, Any] | None:
        """聚合工单全生命周期数据，供详情页一次性展现。

        返回结构::

            {
              "work_order": {...},          # 工单头 + 产品名 + FQC概要
              "bom": [...],                 # BOM 物料清单（含需求总量）
              "material_consumes": [...],   # 物料消耗 TMS04（含类型标签）
              "replace_records": [...],     # 配件更换历史（按时间倒序）
              "qc": {                       # 质检概要
                "fqc_status": str|None,
                "defective_items": [...],   # 不良品明细
                "products": [...]           # 合格成品/配件
              },
              "documents": [...]            # 统一出入库单据流水（按日期排序）
            }
        """
        from app.models.master import BomDt, Item
        from app.models.mes import ReplaceRecord
        from app.models.system import User as SysUser
        from app.models.warehouse import (
            QcResult,
            QcResultDt,
            QcResultEid,
            Warehouse,
        )

        wo = WorkOrderRepository.get_by_id(wo_id)
        if wo is None:
            return None

        # ---- 名称映射缓存 ----
        item_nm_map: dict[str, str] = {}

        def _fill_item_names(codes: set[str]) -> None:
            missing = {c for c in codes if c and c not in item_nm_map}
            if not missing:
                return
            rows = (
                db.session.query(Item.item_cd, Item.item_nm)
                .filter(Item.item_cd.in_(missing))
                .all()
            )
            for r in rows:
                item_nm_map[r.item_cd] = r.item_nm or ""

        wh_nm_map: dict[str, str] = {
            w.whcd: (w.whnm or "")
            for w in db.session.query(Warehouse.whcd, Warehouse.whnm).all()
        }
        user_nm_map: dict[str, str] = {
            u.user_cd: (u.user_nm or "")
            for u in db.session.query(SysUser.user_cd, SysUser.user_nm).all()
        }

        # ---- 1. 工单头（复用 get 的产品名/FQC 概要补充） ----
        work_order = WorkOrderService.get(wo_id) or wo.to_dict()

        # ---- 2. BOM 物料清单 ----
        plan_qty = int(wo.plan_qty or 1)
        bom_rows = db.session.query(BomDt).filter(BomDt.bomcd == wo.item_cd).all()
        _fill_item_names({r.itemcd for r in bom_rows})
        bom = [
            {
                "itemcd": r.itemcd,
                "item_nm": item_nm_map.get(r.itemcd, ""),
                "bomqty": float(r.bomqty) if r.bomqty is not None else 0,
                "required_qty": float(r.bomqty or 0) * plan_qty,
                "itemtyp": r.itemtyp,
            }
            for r in bom_rows
        ]

        # ---- 3. 物料消耗 TMS04 ----
        consumes = MaterialConsumeRepository.list_by_wo(wo_id)
        _fill_item_names({c.item_cd for c in consumes})
        material_consumes = []
        for c in consumes:
            cd = c.to_dict()
            cd["item_nm"] = item_nm_map.get(c.item_cd, "")
            cd["consume_type_label"] = WorkOrderService._CONSUME_TYPE_LABELS.get(
                c.consume_type or "1", c.consume_type or ""
            )
            cd["warehouse_nm"] = wh_nm_map.get(c.warehouse_cd or "", "")
            material_consumes.append(cd)

        # ---- 4. 配件更换历史 ----
        replace_rows = (
            db.session.query(ReplaceRecord)
            .filter(ReplaceRecord.wo_id == wo_id)
            .order_by(
                ReplaceRecord.replace_date.desc().nullslast(),
                ReplaceRecord.id.desc(),
            )
            .all()
        )
        _fill_item_names({r.itemcd for r in replace_rows})
        replace_records = []
        for r in replace_rows:
            rd = r.to_dict()
            rd["item_nm"] = item_nm_map.get(r.itemcd, "")
            rd["operator_name"] = user_nm_map.get(r.opercd or "", r.opercd or "")
            replace_records.append(rd)

        # ---- 5. 质检概要（FQC 不良品 + 合格成品） ----
        fqc_bills = (
            db.session.query(QcResult)
            .filter(QcResult.refbillid == wo_id, QcResult.optyp == "FQ")
            .all()
        )
        fqc_ids = [b.qcbillid for b in fqc_bills]
        defective_items: list[dict[str, Any]] = []
        if fqc_ids:
            eid_defects = (
                db.session.query(QcResultEid)
                .filter(
                    QcResultEid.qcbillid.in_(fqc_ids),
                    QcResultEid.qcstatus.in_(WorkOrderService._DEFECT_STATUS),
                )
                .all()
            )
            prd_defects = (
                db.session.query(QcResultDt)
                .filter(
                    QcResultDt.qcbillid.in_(fqc_ids),
                    QcResultDt.qcstatus.in_(WorkOrderService._DEFECT_STATUS),
                )
                .all()
            )
            _fill_item_names(
                {d.itemcd for d in eid_defects} | {d.itemcd for d in prd_defects}
            )
            for d in eid_defects:
                defective_items.append({
                    "qcbillid": d.qcbillid,
                    "itemcd": d.itemcd,
                    "item_nm": item_nm_map.get(d.itemcd, ""),
                    "eid": d.eid,
                    "batch_no": None,
                    "qcstatus": d.qcstatus,
                    "prod_seq": d.prod_seq,
                    "replenish_ov_billid": d.replenish_ov_billid or None,
                    "replenish_status": d.replenish_status or None,
                })
            for d in prd_defects:
                defective_items.append({
                    "qcbillid": d.qcbillid,
                    "itemcd": d.itemcd,
                    "item_nm": item_nm_map.get(d.itemcd, ""),
                    "eid": None,
                    "batch_no": d.prddate.isoformat()[:10] if d.prddate else None,
                    "qcstatus": d.qcstatus,
                    "prod_seq": d.prod_seq,
                    "replenish_ov_billid": d.replenish_ov_billid or None,
                    "replenish_status": d.replenish_status or None,
                })

        qc_summary = {
            "fqc_status": work_order.get("fqc_qcstatus"),
            "fqc_billids": fqc_ids,
            "defective_items": defective_items,
            "products": work_order.get("fqc_products", []),
        }

        # ---- 6. 统一出入库单据流水 ----
        documents = WorkOrderService._build_document_flow(
            wo_id=wo_id,
            fqc_ids=fqc_ids,
            item_nm_map=item_nm_map,
            wh_nm_map=wh_nm_map,
            user_nm_map=user_nm_map,
            fill_item_names=_fill_item_names,
        )

        return {
            "work_order": work_order,
            "bom": bom,
            "material_consumes": material_consumes,
            "replace_records": replace_records,
            "qc": qc_summary,
            "documents": documents,
        }

    @staticmethod
    def _build_document_flow(
        wo_id: str,
        fqc_ids: list[str],
        item_nm_map: dict[str, str],
        wh_nm_map: dict[str, str],
        user_nm_map: dict[str, str],
        fill_item_names: Any,
    ) -> list[dict[str, Any]]:
        """构建工单关联的统一出入库单据流水（按日期升序）。

        包含：
        - 领料/补料出库：StockOut.refbillid == wo_id
        - 成品入库：StockIn.refbillid IN FQC单号
        - 报废/返修出库：StockOut.refbillid IN FQC单号
        """
        from app.models.warehouse import (
            StockIn,
            StockInDetail,
            StockOut,
            StockOutDetailEid,
            StockOutDetailPrd,
        )

        documents: list[dict[str, Any]] = []
        ref_ids = [wo_id, *fqc_ids]

        # 出库单（领料/补料/报废/返修），仅已审
        out_bills = (
            db.session.query(StockOut)
            .filter(StockOut.refbillid.in_(ref_ids), StockOut.useflg == "1", StockOut.auditflg == "2")
            .all()
        )
        out_ids = [o.outbillid for o in out_bills]
        out_eid_map: dict[str, list[Any]] = {}
        out_prd_map: dict[str, list[Any]] = {}
        if out_ids:
            for d in (
                db.session.query(StockOutDetailEid)
                .filter(StockOutDetailEid.outbillid.in_(out_ids))
                .all()
            ):
                out_eid_map.setdefault(d.outbillid, []).append(d)
            for d in (
                db.session.query(StockOutDetailPrd)
                .filter(StockOutDetailPrd.outbillid.in_(out_ids))
                .all()
            ):
                out_prd_map.setdefault(d.outbillid, []).append(d)

        # 入库单（成品入库），仅已审
        in_bills = (
            db.session.query(StockIn)
            .filter(StockIn.refbillid.in_(ref_ids), StockIn.auditflg == "2")
            .all()
            if ref_ids
            else []
        )
        in_ids = [i.inbillid for i in in_bills]
        in_dt_map: dict[str, list[Any]] = {}
        if in_ids:
            for d in (
                db.session.query(StockInDetail)
                .filter(StockInDetail.inbillid.in_(in_ids))
                .all()
            ):
                in_dt_map.setdefault(d.inbillid, []).append(d)

        # 补全物料名称
        all_codes: set[str] = set()
        for dts in out_eid_map.values():
            all_codes |= {d.itemcd for d in dts}
        for dts in out_prd_map.values():
            all_codes |= {d.itemcd for d in dts}
        for dts in in_dt_map.values():
            all_codes |= {d.itemcd for d in dts}
        fill_item_names(all_codes)

        # 组装出库单
        for o in out_bills:
            invtyp = o.invtyp or ""
            details: list[dict[str, Any]] = []
            for d in out_eid_map.get(o.outbillid, []):
                details.append({
                    "itemcd": d.itemcd,
                    "item_nm": item_nm_map.get(d.itemcd, ""),
                    "qty": int(d.outqty or 0),
                    "eid": d.eid,
                    "batch_no": None,
                    "prddate": d.prddate.isoformat()[:10] if d.prddate else None,
                    "itemtyp": d.itemtyp,
                })
            for d in out_prd_map.get(o.outbillid, []):
                details.append({
                    "itemcd": d.itemcd,
                    "item_nm": item_nm_map.get(d.itemcd, ""),
                    "qty": int(d.outqty or 0),
                    "eid": None,
                    "batch_no": d.prddate.isoformat()[:10] if d.prddate else None,
                    "prddate": d.prddate.isoformat()[:10] if d.prddate else None,
                    "itemtyp": d.itemtyp,
                })
            # 业务标签：区分定额领料 / 不良补料
            memo = o.memo or ""
            if invtyp == "10":
                biz_label = "翻新领料"
            elif invtyp == "8":
                biz_label = "不良补料" if "补料" in memo else "定额领料"
            else:
                biz_label = WorkOrderService._OUT_TYPE_LABELS.get(invtyp, invtyp)
            doc_date = o.outdate or o.gendate
            documents.append({
                "billid": o.outbillid,
                "direction": "out",
                "invtyp": invtyp,
                "type_label": WorkOrderService._OUT_TYPE_LABELS.get(invtyp, invtyp),
                "biz_label": biz_label,
                "ref_billid": o.refbillid,
                "audit_flg": o.auditflg,
                "audit_label": WorkOrderService._AUDIT_LABELS.get(o.auditflg or "0", o.auditflg),
                "date": doc_date.isoformat() if doc_date else None,
                "warehouse_cd": o.whcd,
                "warehouse_nm": wh_nm_map.get(o.whcd or "", ""),
                "operator_cd": o.opercd,
                "operator_name": user_nm_map.get(o.opercd or "", o.opercd or ""),
                "memo": memo,
                "details": details,
            })

        # 组装入库单
        for i in in_bills:
            invtyp = i.invtyp or ""
            details = []
            for d in in_dt_map.get(i.inbillid, []):
                details.append({
                    "itemcd": d.itemcd,
                    "item_nm": item_nm_map.get(d.itemcd, ""),
                    "qty": int(d.inqty or 0),
                    "eid": d.eid,
                    "batch_no": d.batchid,
                    "prddate": d.prddate.isoformat()[:10] if d.prddate else None,
                    "itemtyp": d.itemtyp,
                })
            doc_date = i.indate or getattr(i, "gendate", None)
            documents.append({
                "billid": i.inbillid,
                "direction": "in",
                "invtyp": invtyp,
                "type_label": WorkOrderService._IN_TYPE_LABELS.get(invtyp, invtyp),
                "biz_label": WorkOrderService._IN_TYPE_LABELS.get(invtyp, invtyp),
                "ref_billid": i.refbillid,
                "audit_flg": i.auditflg,
                "audit_label": WorkOrderService._AUDIT_LABELS.get(i.auditflg or "0", i.auditflg),
                "date": doc_date.isoformat() if doc_date else None,
                "warehouse_cd": i.whcd,
                "warehouse_nm": wh_nm_map.get(i.whcd or "", ""),
                "operator_cd": i.opercd,
                "operator_name": user_nm_map.get(i.opercd or "", i.opercd or ""),
                "memo": i.memo or "",
                "details": details,
            })

        # 按日期升序排序（无日期排最后）
        documents.sort(key=lambda d: (d["date"] is None, d["date"] or ""))
        return documents

    @staticmethod
    def list_all(
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = WorkOrderRepository.list_all(status=status, page=page, per_page=per_page)
        data = [r.to_dict() for r in items]
        wo_ids = [d["wo_id"] for d in data]
        # 批量补充产品名称
        item_cds = list({d.get("item_cd") for d in data if d.get("item_cd")})
        if item_cds:
            from app.models.master import Item
            rows = db.session.query(Item.item_cd, Item.item_nm).filter(Item.item_cd.in_(item_cds)).all()
            nm_map = {r[0]: r[1] or "" for r in rows}
            for d in data:
                if d.get("item_cd"):
                    d["item_nm"] = nm_map.get(d["item_cd"], "")
        # 批量查询补料状态
        if wo_ids:
            from app.models.warehouse import StockOut
            replenishing = set(r[0] for r in db.session.query(StockOut.refbillid).filter(
                StockOut.refbillid.in_(wo_ids),
                StockOut.invtyp == "8",
                StockOut.auditflg == "0",
                StockOut.memo.like("%补料%"),
                StockOut.useflg == "1",
            ).all())
            for d in data:
                d["has_replenish"] = d["wo_id"] in replenishing
        return {
            "items": data,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        # 自动生成工单编号 WO+年月日+3位序号
        if not data.get("wo_id"):
            from datetime import UTC, datetime as _dt
            today = _dt.now(UTC).strftime("%Y%m%d")
            prefix = f"WO{today}-"
            latest = (
                db.session.query(WorkOrder.wo_id)
                .filter(WorkOrder.wo_id.like(f"{prefix}%"))
                .order_by(WorkOrder.wo_id.desc())
                .first()
            )
            if latest and latest.wo_id:
                try:
                    seq = int(latest.wo_id.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            data["wo_id"] = f"{prefix}{seq:03d}"
        record = WorkOrderRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        wo_id: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = WorkOrderRepository.get_by_id(wo_id)
        if record is None:
            return None
        WorkOrderRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()

    # 合法状态流转表
    _TRANSITIONS: dict[str, list[str]] = {
        "DRAFT":       ["RELEASED", "CANCELLED"],
        "RELEASED":    ["PICKING", "CANCELLED"],
        "PICKING":     ["IN_PROGRESS", "CANCELLED"],
        "IN_PROGRESS": ["QC_PENDING", "CANCELLED"],  # 完工→待FQC
        "QC_PENDING":  ["CANCELLED"],   # FQC通过由质检审核推动完工
        "COMPLETED":   [],
        "CANCELLED":   [],
    }

    @staticmethod
    def delete(wo_id: str) -> dict[str, object]:
        record = WorkOrderRepository.get_by_id(wo_id)
        if record is None:
            return {"success": False, "error": "工单不存在"}
        if record.status and record.status != "DRAFT":
            return {"success": False, "error": "仅草稿状态工单可删除"}
        WorkOrderRepository.delete(wo_id)
        db.session.commit()
        return {"success": True}

    @staticmethod
    def transition(wo_id: str, target: str, operator: str) -> dict[str, object]:
        """工单状态流转（精简状态机）。

        DRAFT → RELEASED → PICKING → IN_PROGRESS → QC_PENDING → COMPLETED。
        任意中间态可取消（→ CANCELLED）。
        """
        from datetime import UTC, datetime as _dt
        record = WorkOrderRepository.get_by_id(wo_id)
        if record is None:
            return {"success": False, "error": "工单不存在"}
        current = record.status or "DRAFT"
        allowed = WorkOrderService._TRANSITIONS.get(current, [])
        if target not in allowed:
            return {"success": False, "error": f"不允许从 {current} 流转到 {target}（允许：{', '.join(allowed) or '无'}）"}
        now = _dt.now(UTC)
        record.status = target
        record.opercd = operator
        record.upddate = now
        if target == "IN_PROGRESS" and not record.actual_start:
            record.actual_start = now.date()
        if target == "QC_PENDING" and not record.actual_end:
            record.actual_end = now.date()
        # RELEASED → 自动生成 OV=8/OV=10 草稿 + 进入领料中
        if target == "RELEASED":
            result = WorkOrderService._create_production_outbound_draft(record, operator)
            if result:
                record.status = "PICKING"

        # 取消 → 对冲已出物料：VOID 草稿 OV=8 + 生成 IV=3 退货草稿
        if target == "CANCELLED" and current in ("RELEASED", "PICKING", "IN_PROGRESS", "QC_PENDING"):
            from app.models.warehouse import StockOut, StockOutDetailPrd
            from app.repositories.mes_repository import MaterialConsumeRepository
            from app.models.inventory import Price
            from app.models.mes import ConsumeType

            ov8_list = db.session.query(StockOut).filter(
                StockOut.refbillid == wo_id,
                StockOut.invtyp == "8",
                StockOut.useflg == "1",
            ).all()

            for ov in ov8_list:
                if ov.auditflg == "0":
                    # 草稿 → 直接作废
                    ov.auditflg = "V"
                    ov.upddate = now
                elif ov.auditflg == "2":
                    # 已审核 → 查明细，生成 IV=3 退货草稿
                    prd_dts = db.session.query(StockOutDetailPrd).filter(
                        StockOutDetailPrd.outbillid == ov.outbillid,
                    ).all()
                    if not prd_dts:
                        continue
                    return_items: list[dict[str, Any]] = []
                    for dt in prd_dts:
                        if not dt.itemcd or not dt.outqty or float(dt.outqty) <= 0:
                            continue
                        return_items.append({
                            "itemcd": dt.itemcd,
                            "inqty": int(float(dt.outqty)),
                        })
                    if return_items:
                        from app.services.warehouse_service import StockInService
                        StockInService.create(
                            data={
                                "invtyp": "3",
                                "whcd": ov.whcd or "01",
                                "refbillid": wo_id,
                                "memo": f"工单取消退料 {wo_id}",
                            },
                            details=return_items,
                            creator=operator,
                        )
                        # TMS04 退料记录
                        for ri in return_items:
                            price_rec = db.session.query(Price).filter(
                                Price.itemcd == ri["itemcd"], Price.busityp == "20",
                                Price.is_current == True, Price.useflg == "1",
                            ).first()
                            unit_cost = price_rec.itemprice if price_rec else None
                            total_cost = unit_cost * ri["inqty"] if unit_cost else None
                            MaterialConsumeRepository.create(
                                data={
                                    "wo_id": wo_id,
                                    "item_cd": ri["itemcd"],
                                    "plan_qty": 0,
                                    "actual_qty": ri["inqty"],
                                    "unit": "个",
                                    "warehouse_cd": ov.whcd or "01",
                                    "consume_date": now.date(),
                                    "consume_type": ConsumeType.RETURN,
                                    "ref_bill_type": "IV",
                                    "unit_cost": unit_cost,
                                    "total_cost": total_cost,
                                },
                                creator=operator,
                            )

            # QC_PENDING → 检查 + 作废关联的 FQC 质检草稿及下游出入库草稿
            if current == "QC_PENDING":
                from app.models.warehouse import QcResult, StockIn, StockOut as _SOut

                # 有已审核的 QC 记录 → 阻止取消（需先反审核QC）
                audited_qc = db.session.query(QcResult).filter(
                    QcResult.refbillid == wo_id,
                    QcResult.useflg == "1",
                    QcResult.auditflg == "1",
                ).first()
                if audited_qc:
                    return {"success": False, "error": "存在已审核的质检记录，请先反审核QC后再取消工单"}

                # 作废所有 QC 草稿/退回记录
                qc_records = db.session.query(QcResult).filter(
                    QcResult.refbillid == wo_id,
                    QcResult.useflg == "1",
                    QcResult.auditflg.in_(["0", "8"]),
                ).all()
                for qc in qc_records:
                    # 检查下游是否有已审核的出入库单
                    audited_iv = db.session.query(StockIn).filter(
                        StockIn.refbillid == qc.qcbillid,
                        StockIn.auditflg == "2",
                    ).first()
                    audited_ov = db.session.query(_SOut).filter(
                        _SOut.refbillid == qc.qcbillid,
                        _SOut.auditflg == "2",
                    ).first()
                    if audited_iv or audited_ov:
                        return {"success": False, "error": f"质检单 {qc.qcbillid} 的下游出入库单已审核，请先反审核后再取消工单"}

                    qc.auditflg = "V"
                    qc.upddate = now
                    # 作废下游出入库草稿
                    db.session.query(StockIn).filter(
                        StockIn.refbillid == qc.qcbillid,
                        StockIn.auditflg == "0",
                    ).update({"auditflg": "V"}, synchronize_session=False)
                    db.session.query(_SOut).filter(
                        _SOut.refbillid == qc.qcbillid,
                        _SOut.auditflg == "0",
                    ).update({"auditflg": "V", "upddate": now}, synchronize_session=False)

        db.session.commit()
        return {"success": True, "wo_id": wo_id, "status": record.status}

    @staticmethod
    def _create_production_outbound_draft(wo: Any, creator: str | None) -> bool:
        """工单下达时生成生产/翻新领料出库草稿。"""
        from app.services.warehouse_service import StockOutService
        from app.repositories.mes_repository import MaterialConsumeRepository
        from app.models.warehouse import StockOut

        # 去重：工单已有 OV=8/OV=10 出库单(含草稿)，不再自动生成
        existing_out = db.session.query(StockOut).filter(
            StockOut.refbillid == wo.wo_id,
            StockOut.invtyp.in_(["8", "10"]),
            StockOut.useflg == "1",
        ).first()
        if existing_out:
            return False  # 已有出库单
        from app.models.master import BomDt
        from app.extensions import db as _db

        whcd = wo.pick_whcd or "01"  # 领料仓库，默认01新品库（成品仓库是入库目标，不能用于出库）
        details_prd: list[dict[str, Any]] = []

        # 优先用实际消耗记录
        consumes = MaterialConsumeRepository.list_by_wo(wo.wo_id)
        if consumes:
            for c in consumes:
                cd = c.to_dict()
                if cd.get("item_cd") and cd.get("actual_qty"):
                    details_prd.append({
                        "itemcd": cd["item_cd"],
                        "outqty": int(cd["actual_qty"]),
                    })
        else:
            # 回退到 BOM 展开 + 库存 FIFO 自动匹配
            qty = int(wo.plan_qty or 1)
            bom_rows = (
                _db.session.query(BomDt)
                .filter(BomDt.bomcd == wo.item_cd)
                .all()
            )
            if bom_rows and whcd:
                from app.models.warehouse import StockDetail
                for row in bom_rows:
                    need = int((row.bomqty or 0)) * qty
                    if not row.itemcd or need <= 0:
                        continue
                    # FIFO: 按批次日期升序，先入库的先出
                    batches = (
                        db.session.query(StockDetail)
                        .filter(
                            StockDetail.whcd == whcd,
                            StockDetail.itemcd == row.itemcd,
                            StockDetail.itemqty > 0,
                        )
                        .order_by(StockDetail.prddate.asc().nullsfirst())
                        .all()
                    )
                    remaining = need
                    for batch in batches:
                        if remaining <= 0:
                            break
                        take = int(min(batch.itemqty or 0, remaining))
                        if take > 0:
                            details_prd.append({
                                "itemcd": row.itemcd,
                                "outqty": take,
                                "itemtyp": batch.itemtyp or "DJ",
                                "prddate": batch.prddate.isoformat() if batch.prddate and hasattr(batch.prddate, 'isoformat') else str(batch.prddate) if batch.prddate else None,
                            })
                            remaining -= take
                    if remaining > 0:
                        # 库存不足，仍创建草稿（待仓库处理）
                        details_prd.append({
                            "itemcd": row.itemcd,
                            "outqty": remaining,
                            "itemtyp": "DJ",
                        })
            else:
                for row in bom_rows:
                    need = int((row.bomqty or 0)) * qty
                    if row.itemcd and need > 0:
                        details_prd.append({
                            "itemcd": row.itemcd,
                            "outqty": need,
                        })

        if not details_prd:
            return False  # 无物料信息

        try:
            from app.repositories.warehouse_repository import StockOutRepository
            from flask import current_app
            invtyp = "10" if getattr(wo, "wo_type", "") == "RENOVATION" else "8"
            wo_rec = StockOutRepository.create(
                data={
                    "invtyp": invtyp,
                    "whcd": whcd,
                    "refbillid": wo.wo_id,
                    "memo": f"工单 {wo.wo_id} 领料",
                },
                creator=creator or "",
            )
            for idx, dt in enumerate(details_prd, start=1):
                StockOutRepository.add_detail_prd(
                    outbillid=wo_rec.outbillid, whcd=whcd, lineno=idx, data=dt,
                )
            db.session.flush()

            # 同步写入 TMS04 物料消耗（定额领料，仅 BOM 展开场景）
            if not consumes:  # 只有 BOM 展开时才写入，已有消耗记录则不重复
                from app.models.inventory import Price
                for dt in details_prd:
                    # 查询物料标准价格（业务类型='PUR'采购价，或'STD'标准成本）
                    price_rec = Price.query.filter_by(
                        itemcd=dt["itemcd"],
                        busityp="20",
                        is_current=True,
                        useflg="1"
                    ).first()
                    unit_cost = price_rec.itemprice if price_rec else None
                    actual_qty = dt["outqty"]
                    total_cost = unit_cost * actual_qty if unit_cost else None

                    MaterialConsumeRepository.create(
                        data={
                            "wo_id": wo.wo_id,
                            "item_cd": dt["itemcd"],
                            "plan_qty": actual_qty,
                            "actual_qty": actual_qty,
                            "unit": "个",
                            "warehouse_cd": whcd,
                            "consume_date": dt_parse.now(UTC).date(),
                            "consume_type": "1",  # 定额
                            "ref_bill_type": "OV",
                            "ref_bill_id": wo_rec.outbillid,
                            "ref_qc_id": None,
                            "unit_cost": unit_cost,
                            "total_cost": total_cost,
                        },
                        creator=creator,
                    )
                db.session.flush()

            return True
        except Exception:
            current_app.logger.warning(
                "工单%s 自动生成OV=%s 领料出库草稿失败", wo.wo_id, invtyp,
            )
            return False

    @staticmethod
    def replace_asset(wo_id: str, old_eid: str, new_eid: str, itemcd: str, memo: str, creator: str, old_batch_no: str = "", new_batch_no: str = "") -> dict[str, Any]:
        """工单物料更换：记录旧→新 EID 或批次号映射，更新 EID 状态。"""
        from datetime import UTC, datetime as _dt

        from app.models.master import Eid as EidModel
        from app.models.mes import ReplaceRecord

        wo = db.session.get(WorkOrder, wo_id)
        if not wo:
            return {"success": False, "error": "工单不存在"}

        if not itemcd:
            return {"success": False, "error": "物料编码不能为空"}

        # 验证至少提供EID或批次号之一
        if not old_eid and not old_batch_no:
            return {"success": False, "error": "请提供旧物料EID或批次号"}
        if not new_eid and not new_batch_no:
            return {"success": False, "error": "请提供新物料EID或批次号"}

        # 写入更换记录
        rec = ReplaceRecord(
            wo_id=wo_id,
            old_eid=old_eid or None,
            new_eid=new_eid or None,
            itemcd=itemcd,
            old_batch_no=old_batch_no or None,
            new_batch_no=new_batch_no or None,
            opercd=creator,
            memo=memo,
            replace_date=_dt.now(UTC),
        )
        db.session.add(rec)

        # 更新旧 EID → 报废（仅EID类型物料）
        if old_eid:
            db.session.query(EidModel).filter(EidModel.eid == old_eid).update(
                {"sflg": "2", "qcflg": "BF"}, synchronize_session=False,
            )
        # 更新新 EID → 正常、入库到工单仓库（仅EID类型物料）
        if new_eid:
            db.session.query(EidModel).filter(EidModel.eid == new_eid).update(
                {"sflg": "1", "qcflg": "GA", "whcd": wo.pick_whcd or wo.warehouse_cd or "01"},
                synchronize_session=False,
            )

        db.session.commit()
        return {"success": True}


class ProcessDefService:
    """工序定义服务。"""

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        records = ProcessDefRepository.list_all()
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = ProcessDefRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        process_cd: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = ProcessDefRepository.get_by_id(process_cd)
        if record is None:
            return None
        ProcessDefRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class WorkProcessService:
    """工单工序服务。"""

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = WorkProcessRepository.list_all(page=page, per_page=per_page)
        return {"items": [item.to_dict() for item in items], "total": total, "page": page, "per_page": per_page}

    @staticmethod
    def list_by_wo(wo_id: str) -> list[dict[str, Any]]:
        records = WorkProcessRepository.list_by_wo(wo_id)
        return [r.to_dict() for r in records]

    @staticmethod
    def delete(wp_id: int) -> dict[str, object]:
        record = WorkProcessRepository.get_by_id(wp_id)
        if record is None: return {"success": False, "error": "工序不存在"}
        if record.status and record.status != "PENDING": return {"success": False, "error": "仅待执行状态可删除"}
        WorkProcessRepository.delete(wp_id); db.session.commit()
        return {"success": True}

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = WorkProcessRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        wp_id: int,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = WorkProcessRepository.get_by_id(wp_id)
        if record is None:
            return None
        WorkProcessRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class MaterialConsumeService:
    """物料消耗服务。"""

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = MaterialConsumeRepository.list_all(page=page, per_page=per_page)
        return {"items": [item.to_dict() for item in items], "total": total, "page": page, "per_page": per_page}

    @staticmethod
    def list_by_wo(wo_id: str) -> list[dict[str, Any]]:
        records = MaterialConsumeRepository.list_by_wo(wo_id)
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = MaterialConsumeRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()
