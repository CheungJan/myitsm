"""质检管理业务逻辑层。"""

from __future__ import annotations

from datetime import UTC, datetime as dt_parse
from typing import Any

from app.extensions import db
from app.repositories.qc_repository import QcRepository


class QcService:
    """质检结果业务逻辑。"""

    @staticmethod
    def list_results(
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
    ) -> dict[str, Any]:
        rows, total = QcRepository.list_results(
            page=page, per_page=per_page, search=search
        )
        return {"items": [r.to_dict() for r in rows], "total": total}

    @staticmethod
    def get_result(qcbillid: str) -> dict[str, Any] | None:
        qc = QcRepository.get_result(qcbillid)
        if not qc:
            return None
        data = qc.to_dict()
        data["details"] = [dt.to_dict() for dt in QcRepository.list_details(qcbillid)]
        data["eid_details"] = [
            e.to_dict() for e in QcRepository.list_eid_details(qcbillid)
        ]
        return data

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]] | None = None,
        eid_details: list[dict[str, Any]] | None = None,
        old_batch_id: str | None = None,
    ) -> dict[str, Any]:
        """创建质检单。

        old_batch_id: 重新录入时传入，自动先作废旧批次再建新
        """
        # 重新录入：复用 batch_id，清旧子记录再建新
        if old_batch_id:
            QcRepository.batch_delete(old_batch_id)
            data["batch_id"] = old_batch_id
        elif not data.get("batch_id"):
            # 全新录入（非批次内追加）时防重复
            refbillid = data.get("refbillid")
            if refbillid:
                existing = QcRepository.find_draft_by_refbillid(refbillid)
                if existing:
                    return {
                        "success": False,
                        "error": f"已有草稿单据 {existing.qcbillid}，请先作废或审核原草稿",
                    }
        qc = QcRepository.create(data)
        if details:
            for idx, d in enumerate(details, start=1):
                QcRepository.add_detail(qc.qcbillid, idx, d)
        if eid_details:
            for idx, d in enumerate(eid_details, start=1):
                QcRepository.add_eid_detail(qc.qcbillid, idx, d)
        db.session.commit()
        return qc.to_dict()

    @staticmethod
    def audit(qcbillid: str, auditor: str, auditflg: str = "1", checkmemo: str | None = None) -> dict[str, object]:
        """质检单审核，按 qcstatus 分流触发仓库联动与 EID 状态更新。

        auditflg='1' → 审核通过（触发仓库联动）
        auditflg='8' → 审核退回（仅改状态，不触发仓库联动）
        """
        from app.models.warehouse import QcResultDt, QcResultEid, StockOut
        from app.models.master import Eid as EidModel, Item
        from app.models.inventory import Label
        from app.services.warehouse_service import StockInService

        qc = QcRepository.get_result(qcbillid)
        if qc is None:
            return {"success": False, "error": "质检单不存在"}
        if qc.auditflg == "1":
            return {"success": False, "error": "已审核，不可重复审核"}
        if qc.auditflg == "8":
            return {"success": False, "error": "已退回，请先编辑后再审核"}

        # 驳回 → 仅改状态，不做仓库联动
        if auditflg == "8":
            QcRepository.audit(qc, auditor, auditflg="8", checkmemo=checkmemo)
            return {"success": True}

        qcstatus = qc.qcstatus or "GA"
        QcRepository.audit(qc, auditor, auditflg=auditflg, checkmemo=checkmemo)

        eid_rows = list(qc.detail_eids)
        prd_rows = list(qc.detail_items)

        # 仓库动作按 qcstatus 判定:
        #   GA/GB/GC → IQC生成IV=11；FQC生成IV=8并推动工单完工
        #   BH → OV=9 返修出库（设备）
        #   BF → OV=7 报废出库
        #   TH → OV=6 退换出库（耗材退供应商）
        #   DJ → 仅标记 EID 状态，无仓库动作
        is_pass = qcstatus in ("GA", "GB", "GC")
        is_repair = qcstatus == "BH"
        is_scrap = qcstatus == "BF"
        is_return = qcstatus == "TH"

        # --- EID 状态更新 ---
        for row in eid_rows:
            if not row.eid:
                continue
            upd: dict[str, Any] = {}
            if is_pass:
                upd["qcflg"] = qcstatus
                upd["whcd"] = "04"  # 合格品入库到生产配件库
                if getattr(row, "manuf_seq", None):
                    upd["manuf_seq"] = row.manuf_seq
            elif is_scrap:
                upd["sflg"] = "2"
                upd["qcflg"] = "BF"
            elif is_repair:
                upd["qcflg"] = "BH"
            elif is_return:
                upd["qcflg"] = "TH"
            else:  # DJ
                upd["qcflg"] = "DJ"
            if upd:
                db.session.query(EidModel).filter(EidModel.eid == row.eid).update(upd, synchronize_session=False)
            # 合格品激活标签
            if is_pass:
                # Label 的 classcd 存的是物料编码（如 BS4200），不是中类编码（如 BS42）
                label = db.session.get(Label, (row.eid, row.itemcd)) if row.itemcd else None
                if label:
                    if label and label.useflg != "0":
                        label.useflg = "0"
                        label.gendate = dt_parse.now(UTC)
                        label.upddate = dt_parse.now(UTC)
                    # 同步创建/更新 TMM43_EID 记录
                    eid_model = db.session.get(EidModel, (row.itemcd, row.eid))
                    if not eid_model:
                        db.session.add(EidModel(
                            itemcd=row.itemcd, eid=row.eid,
                            sflg="1", qcflg=qcstatus,
                            whcd="04",
                            new_old="1", etyp="1",
                        ))
                    else:
                        eid_model.qcflg = qcstatus

        # --- 仓库联动 ---
        from app.services.warehouse_service import StockOutService
        ref = qc.refbillid or ""
        is_qc_out = ref.startswith("OT")

        # 获取来源仓库（仅用于参考，各判定有独立目标仓库）
        src_whcd = ""
        if is_qc_out:
            src_whcd = db.session.query(StockOut.whcd).filter(StockOut.outbillid == ref).scalar() or ""

        # 入库目标仓库: GA/GB/GC → 04(生产配件库)
        # 出库来源仓库: BF/BH/TH → 使用来源单仓库(从哪领的料就从哪出)
        in_whcd = "04"

        # GA/GB/GC → IQC生成IV=11；FQC生成IV=8
        if is_pass and (eid_rows or prd_rows):
            in_details: list[dict[str, Any]] = []
            for row in eid_rows:
                d_in: dict[str, Any] = {
                    "itemcd": row.itemcd or "", "inqty": int(row.qcqty or 1), "eid": row.eid or "",
                    **({"ref_rgstbillid": ref} if is_qc_out else {}),
                }
                if getattr(row, "prddate", None):
                    d_in["prddate"] = row.prddate.isoformat() if hasattr(row.prddate, "isoformat") else str(row.prddate)
                in_details.append(d_in)
            for row in prd_rows:
                d: dict[str, Any] = {"itemcd": row.itemcd or "", "inqty": int(row.qcqty or 1)}
                if row.prddate:
                    d["prddate"] = row.prddate.isoformat() if hasattr(row.prddate, "isoformat") else str(row.prddate)
                if is_qc_out:
                    d["ref_rgstbillid"] = ref
                in_details.append(d)
            # 区分 FQC 和 IPQC
            is_fqc = False
            fqc_whcd = in_whcd
            if not is_qc_out:
                from app.models.mes import WorkOrder
                wo = db.session.get(WorkOrder, qc.refbillid)
                if wo:
                    if wo.status == "QC_PENDING" and is_pass:
                        wo.status = "COMPLETED"
                        wo.upddate = dt_parse.now(UTC)
                        is_fqc = True
                    if wo.warehouse_cd:
                        fqc_whcd = wo.warehouse_cd
            if in_details and (is_qc_out or is_fqc):
                invtyp = "11" if is_qc_out else "8"
                target_whcd = fqc_whcd if is_fqc else in_whcd
                StockInService.create(
                    data={"invtyp": invtyp, "refbillid": qcbillid, "whcd": target_whcd},
                    details=in_details, creator=auditor,
                )

        # BF/BH/TH → 行业做法：先 IV=11 入暂存仓，再 OV 出库
        in_list: list[dict[str, Any]] = []
        for r in eid_rows:
            if r.eid:
                d_in: dict[str, Any] = {"itemcd": r.itemcd or "", "inqty": int(r.qcqty or 1), "eid": r.eid or "", "itemtyp": qcstatus}
                if getattr(r, "prddate", None):
                    d_in["prddate"] = r.prddate.isoformat() if hasattr(r.prddate, "isoformat") else str(r.prddate)
                in_list.append(d_in)
        for r in prd_rows:
            if r.itemcd:
                d_in: dict[str, Any] = {"itemcd": r.itemcd or "", "inqty": int(r.qcqty or 1), "itemtyp": qcstatus}
                if getattr(r, "prddate", None):
                    d_in["prddate"] = r.prddate.isoformat() if hasattr(r.prddate, "isoformat") else str(r.prddate)
                in_list.append(d_in)
        out_eid = [{"itemcd": r.itemcd or "", "outqty": int(r.qcqty or 1), "eid": r.eid or "", "itemtyp": qcstatus}
                   for r in eid_rows if r.eid]
        out_prd = [{"itemcd": r.itemcd or "", "outqty": int(r.qcqty or 1), "itemtyp": qcstatus}
                   for r in prd_rows if r.itemcd]

        def _gen_iv(wh: str, label: str) -> str:
            """只生成 IV=11 入库草稿，返回 refbillid。出库单在仓库审核 IV 时自动生成。"""
            if in_list:
                iv = StockInService.create(
                    data={"invtyp": "11", "whcd": wh, "refbillid": qcbillid, "memo": f"QC判定{label}待入库 {qcbillid}"},
                    details=in_list, creator=auditor,
                )
                return iv.get("inbillid", "")
            return ""

        if is_scrap:
            _gen_iv("L1", "报废")
        if is_repair:
            _gen_iv("LS", "返修")
        if is_return:
            _gen_iv("LS", "退换")

        db.session.commit()
        return {"success": True}

    @staticmethod
    def unaudit(qcbillid: str, auditor: str) -> dict[str, object]:
        """反审核 QC：仅允许已审核且下游单据未审核的情况。"""
        from app.models.warehouse import StockIn, StockOut

        qc = QcRepository.get_result(qcbillid)
        if qc is None:
            return {"success": False, "error": "质检单不存在"}
        if qc.auditflg != "1":
            return {"success": False, "error": "仅已审核单据可反审核"}

        # 检查下游单据是否已审核
        has_audited = (
            db.session.query(StockIn).filter(
                StockIn.refbillid == qcbillid, StockIn.auditflg == "2"
            ).first()
            or db.session.query(StockOut).filter(
                StockOut.refbillid == qcbillid, StockOut.auditflg == "2"
            ).first()
        )
        if has_audited:
            return {"success": False, "error": "下游出入库单据已审核，不可反审核"}

        # 作废下游草稿单据
        db.session.query(StockIn).filter(
            StockIn.refbillid == qcbillid, StockIn.auditflg == "0"
        ).update({"auditflg": "V"})
        db.session.query(StockOut).filter(
            StockOut.refbillid == qcbillid, StockOut.auditflg == "0"
        ).update({"auditflg": "V"})

        # 回退 QC 状态
        qc.auditflg = "0"
        qc.auditman = ""
        qc.auditdate = None
        db.session.commit()
        return {"success": True}

    @staticmethod
    def void(qcbillid: str, operator: str) -> dict[str, object]:
        """作废质检单（仅限草稿/已退回）。"""
        qc = QcRepository.get_result(qcbillid)
        if qc is None:
            return {"success": False, "error": "质检单不存在"}
        if qc.auditflg == "1":
            return {"success": False, "error": "已审核单据不可作废"}
        if qc.auditflg == "V":
            return {"success": False, "error": "已作废"}
        QcRepository.void(qc, operator)
        return {"success": True}

    @staticmethod
    def get_batch_details(batch_id: str) -> dict[str, Any]:
        """获取批次详情（含所有子记录 + 明细，明细含物料名称）。"""
        from app.models.master import Item, ItemClass

        qcs = QcRepository.get_batch_details(batch_id)
        if not qcs:
            return {"success": False, "error": "批次不存在"}

        # 收集所有涉及物料编码，批量获取名称和分类
        item_cds: set[str] = set()
        for qc in qcs:
            for dt in QcRepository.list_details(qc.qcbillid):
                if dt.itemcd:
                    item_cds.add(dt.itemcd)
            for eid in QcRepository.list_eid_details(qc.qcbillid):
                if eid.itemcd:
                    item_cds.add(eid.itemcd)
        item_map: dict[str, dict] = {}
        if item_cds:
            items = db.session.query(Item.item_cd, Item.item_nm, Item.class_cd).filter(
                Item.item_cd.in_(item_cds)
            ).all()
            item_map = {i.item_cd: {"item_nm": i.item_nm or "", "class_cd": i.class_cd or ""} for i in items}
        # 批量获取分类名称
        class_cds = {v["class_cd"] for v in item_map.values() if v["class_cd"]}
        class_map: dict[str, str] = {}
        if class_cds:
            classes = db.session.query(ItemClass.class_cd, ItemClass.class_nm).filter(
                ItemClass.class_cd.in_(class_cds)
            ).all()
            class_map = {c.class_cd: c.class_nm or "" for c in classes}

        # 批量查询审核后生成的出入库单号
        from app.models.warehouse import StockIn, StockOut

        qcbillids = [qc.qcbillid for qc in qcs]
        wh_map: dict[str, str] = {}  # qcbillid → 单据号
        if qcbillids:
            ins = db.session.query(StockIn.refbillid, StockIn.inbillid).filter(
                StockIn.refbillid.in_(qcbillids)
            ).all()
            for ref, bill in ins:
                wh_map[ref] = f"IV: {bill}"
            outs = db.session.query(StockOut.refbillid, StockOut.outbillid).filter(
                StockOut.refbillid.in_(qcbillids)
            ).all()
            for ref, bill in outs:
                wh_map[ref] = f"OV: {bill}"

        records = []
        for qc in qcs:
            rec = qc.to_dict()
            rec["wh_bill"] = wh_map.get(qc.qcbillid, "")
            rec["details"] = [
                {
                    **dt.to_dict(),
                    "item_nm": item_map.get(dt.itemcd or "", {}).get("item_nm", ""),
                    "class_nm": class_map.get(item_map.get(dt.itemcd or "", {}).get("class_cd", ""), ""),
                }
                for dt in QcRepository.list_details(qc.qcbillid)
            ]
            rec["eid_details"] = [
                {
                    **e.to_dict(),
                    "item_nm": item_map.get(e.itemcd or "", {}).get("item_nm", ""),
                    "class_nm": class_map.get(item_map.get(e.itemcd or "", {}).get("class_cd", ""), ""),
                }
                for e in QcRepository.list_eid_details(qc.qcbillid)
            ]
            records.append(rec)
        return {"success": True, "batch_id": batch_id, "records": records}

    @staticmethod
    def batch_audit(
        batch_id: str, auditor: str,
        auditflg: str = "1", checkmemo: str | None = None,
    ) -> dict[str, object]:
        """批次审核。auditflg='1'→逐个审核(含仓库联动)；'8'→仅标记退回。"""
        qcs = QcRepository.get_batch_details(batch_id)
        if not qcs:
            return {"success": False, "error": "批次不存在"}
        for qc in qcs:
            if qc.auditflg == "1":
                return {"success": False, "error": "批次包含已审核记录"}
            if qc.auditflg == "V":
                return {"success": False, "error": "批次包含已作废记录"}

        if auditflg == "8":
            QcRepository.batch_audit(batch_id, auditor, auditflg="8", checkmemo=checkmemo)
            return {"success": True}

        # auditflg == "1": 逐个调用单条审核逻辑（含仓库联动）
        for qc in qcs:
            result = QcService.audit(qc.qcbillid, auditor, auditflg="1", checkmemo=checkmemo)
            if not result.get("success"):
                return result
        return {"success": True}

    @staticmethod
    def batch_void(batch_id: str, operator: str) -> dict[str, object]:
        """批次作废。"""
        try:
            QcRepository.batch_void(batch_id, operator)
            return {"success": True}
        except ValueError as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_batches(
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        auditflg: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        eid: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """按批次聚合查询 QC 结果。"""
        return QcRepository.list_batches(
            page=page, per_page=per_page, search=search, auditflg=auditflg,
            start_date=start_date, end_date=end_date, eid=eid,
        )

    @staticmethod
    def get_stats() -> list[dict[str, Any]]:
        return [dict(r) for r in QcRepository.get_stats()]

    @staticmethod
    def get_ov5_completion() -> dict[str, Any]:
        """OV=5 质检出库 QC 完成情况统计。"""
        return QcRepository.get_ov5_completion()
