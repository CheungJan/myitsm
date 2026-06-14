"""质检管理业务逻辑层。"""

from __future__ import annotations

from datetime import UTC, datetime as dt_parse
from typing import Any

from app.extensions import db
from app.models.mes import ConsumeType
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
        """质检单审核，按行级 qcstatus 分流触发仓库联动与 EID 状态更新。

        auditflg='1' → 审核通过（触发仓库联动）
        auditflg='8' → 审核退回（仅改状态，不触发仓库联动）
        """
        from app.models.master import Eid as EidModel
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

        # 审核前检查：暂存草稿不允许审核
        if (qc.draft_type or "").strip() == "S":
            return {"success": False, "error": "暂存草稿不允许审核，请先完成质检录入后再提交"}
        all_rows = list(qc.detail_eids) + list(qc.detail_items)
        if not all_rows:
            return {"success": False, "error": "无明细数据，无法审核"}
        incomplete = [row for row in all_rows if not (getattr(row, "qcstatus", "") or "").strip()]
        if incomplete:
            return {"success": False, "error": f"存在 {len(incomplete)} 行未设置质检判定，请先完善数据"}

        # 合格/让步/待检行必须有 EID 或已申请补料（耗材豁免）
        from app.models.master import Item as _Item
        consumable_cds: set[str] = set()
        try:
            all_cds = {(getattr(r, "itemcd", "") or "").strip() for r in all_rows if (getattr(r, "itemcd", "") or "").strip()}
            if all_cds:
                consumable_cds = {r.item_cd for r in db.session.query(_Item.item_cd).filter(
                    _Item.item_cd.in_(all_cds), _Item.consume == "1"
                ).all()}
        except Exception:
            pass
        missing_eid: list[str] = []
        for row in all_rows:
            rq = (getattr(row, "qcstatus", "") or "").strip()
            if rq not in ("GA", "GB", "GC", "DJ"):
                continue
            itemcd = (getattr(row, "itemcd", "") or "").strip()
            if itemcd in consumable_cds:
                continue
            has_eid = bool((getattr(row, "eid", "") or "").strip())
            has_replenish = bool((getattr(row, "replenish_ov_billid", "") or "").strip())
            if not has_eid and not has_replenish:
                missing_eid.append(f"{itemcd}({rq})")
        if missing_eid:
            sample = missing_eid[:5]
            more = f"等共{len(missing_eid)}行" if len(missing_eid) > 5 else ""
            return {"success": False, "error": f"合格/让步行缺少EID标签：{', '.join(sample)}{more}，请先完善数据"}

        # 审核前检查：补料出库单是否已完成
        from app.models.warehouse import StockOut
        for row in all_rows:
            ov_billid = (getattr(row, "replenish_ov_billid", "") or "").strip()
            if ov_billid:
                ov = db.session.get(StockOut, ov_billid)
                if ov and ov.auditflg == "0":
                    return {"success": False, "error": f"补料出库单 {ov_billid} 未审核，请先审核补料单"}

        qcstatus = qc.qcstatus or "GA"
        # 历史数据无 draft_type，审核通过后标记为已提交
        if not (qc.draft_type or "").strip():
            qc.draft_type = "C"
        QcRepository.audit(qc, auditor, auditflg=auditflg, checkmemo=checkmemo)

        eid_rows = list(qc.detail_eids)
        prd_rows = list(qc.detail_items)

        # --- FQC/IPQC 上下文查询（区分成品与配件EID） ---
        _qc_ref = qc.refbillid or ""
        _wo = None
        is_fqc = False
        is_ipqc = False
        product_itemcd = ""
        fqc_whcd = "04"
        if _qc_ref.startswith("WO"):
            from app.models.mes import WorkOrder
            _wo = WorkOrder.query.get(qc.refbillid)
            if _wo:
                product_itemcd = _wo.item_cd or ""
                if _wo.status == "QC_PENDING":
                    is_fqc = True
                elif _wo.status == "IN_PROGRESS":
                    is_ipqc = True
                if _wo.warehouse_cd:
                    fqc_whcd = _wo.warehouse_cd

        def _rqc(row: Any) -> str:
            """获取行级 qcstatus，无则回退主记录。"""
            return row.qcstatus or qcstatus

        # ── 按行级判定分类 ──
        pass_eid, pass_prd = [], []
        scrap_eid, scrap_prd = [], []
        repair_eid, repair_prd = [], []
        return_eid, return_prd = [], []

        for row in eid_rows:
            rq = _rqc(row)
            if rq in ("GA", "GB", "GC"):
                pass_eid.append(row)
            elif rq == "BF":
                scrap_eid.append(row)
            elif rq == "BH":
                repair_eid.append(row)
            elif rq == "TH":
                return_eid.append(row)
        for row in prd_rows:
            rq = _rqc(row)
            if rq in ("GA", "GB", "GC"):
                pass_prd.append(row)
            elif rq == "BF":
                scrap_prd.append(row)
            elif rq == "BH":
                repair_prd.append(row)
            elif rq == "TH":
                return_prd.append(row)

        # ── EID 状态更新（逐行） ──
        for row in eid_rows:
            if not row.eid:
                continue
            rq = _rqc(row)
            upd: dict[str, Any] = {}
            if rq in ("GA", "GB", "GC"):
                upd["qcflg"] = rq
                if not (_wo and row.itemcd and _wo.item_cd and row.itemcd != _wo.item_cd):
                    upd["whcd"] = "04"
                if getattr(row, "manuf_seq", None):
                    upd["manuf_seq"] = row.manuf_seq
            elif rq == "BF":
                upd["sflg"] = "2"
                upd["qcflg"] = "BF"
            elif rq == "BH":
                upd["qcflg"] = "BH"
                upd["sflg"] = "3"
            elif rq == "TH":
                upd["qcflg"] = "TH"
            else:
                upd["qcflg"] = "DJ"
            if upd:
                db.session.query(EidModel).filter(EidModel.eid == row.eid).update(upd, synchronize_session=False)
            # 合格品激活标签（逐行）
            if rq in ("GA", "GB", "GC"):
                label = db.session.get(Label, (row.eid, row.itemcd)) if row.itemcd else None
                if label:
                    if label.useflg != "0":
                        label.useflg = "0"
                        label.gendate = dt_parse.now(UTC)
                        label.upddate = dt_parse.now(UTC)
                    eid_model = db.session.get(EidModel, (row.itemcd, row.eid))
                    if not eid_model:
                        wh = "04"
                        if _wo:
                            if row.itemcd and _wo.item_cd and row.itemcd == _wo.item_cd:
                                wh = _wo.warehouse_cd or "03"
                            else:
                                wh = None
                        db.session.add(EidModel(
                            itemcd=row.itemcd, eid=row.eid,
                            sflg="1", qcflg=rq, whcd=wh,
                            new_old="1", etyp="1",
                        ))
                    else:
                        eid_model.qcflg = rq

        # ── FQC EID 回写更换记录 ──
        if is_fqc:
            from app.models.mes import ReplaceRecord
            for row in pass_eid:
                if not row.eid or not row.itemcd:
                    continue
                # 查找该工单+物料下 new_eid 为空的更换记录，回写 EID
                pending_recs = db.session.query(ReplaceRecord).filter(
                    ReplaceRecord.wo_id == _wo.wo_id,
                    ReplaceRecord.itemcd == row.itemcd,
                    ReplaceRecord.new_eid.is_(None),
                ).order_by(ReplaceRecord.replace_date.asc()).all()
                for rec in pending_recs:
                    if not rec.new_eid:
                        rec.new_eid = row.eid
                        break  # 一条 QC 通过 EID 只回写到一条更换记录

        # ── FQC 工单状态 ──
        if is_fqc:
            has_product_pass = any(
                _rqc(row) in ("GA", "GB", "GC")
                for row in eid_rows + prd_rows
                if row.itemcd == product_itemcd
            )
            if has_product_pass:
                # 自动退料：检查补料 OV=8 剩余 → 生成 IV=3 退料单
                return_details: list[dict[str, Any]] = []
                from app.models.warehouse import QcResultDt, QcResultEid, StockOut as SOut, StockOutDetailPrd
                from sqlalchemy import func as sa_func
                from app.repositories.mes_repository import MaterialConsumeRepository as MCR
                from app.models.inventory import Price as PPrice

                replenish_ovs = db.session.query(SOut).filter(
                    SOut.refbillid == _wo.wo_id,
                    SOut.invtyp == "8",
                    SOut.memo.like("%补料%"),
                    SOut.auditflg.in_(["0", "2"]),
                ).all()

                for ov in replenish_ovs:
                    ov_details = db.session.query(StockOutDetailPrd).filter(
                        StockOutDetailPrd.outbillid == ov.outbillid,
                    ).all()
                    for od in ov_details:
                        # 统计已更换的数量（从 tms05_replace_record）
                        from app.models.mes import ReplaceRecord as _RR
                        replaced_cnt = db.session.query(sa_func.count(_RR.id)).filter(
                            _RR.wo_id == _wo.wo_id,
                            _RR.itemcd == od.itemcd,
                        ).scalar() or 0
                        unused = float(od.outqty or 0) - float(replaced_cnt)
                        if unused > 0.5:
                            return_details.append({
                                "itemcd": od.itemcd,
                                "inqty": int(unused),
                            })

                if return_details:
                    StockInService.create(
                        data={
                            "invtyp": "3",
                            "whcd": _wo.pick_whcd or _wo.warehouse_cd or "01",
                            "refbillid": _wo.wo_id,
                            "memo": f"补料退料 工单{_wo.wo_id}",
                        },
                        details=return_details, creator=auditor,
                    )
                    # TMS04 退料写入
                    for rd in return_details:
                        price_rec = db.session.query(PPrice).filter(
                            PPrice.itemcd == rd["itemcd"], PPrice.busityp == "PUR",
                            PPrice.is_current == True, PPrice.useflg == "1",
                        ).first()
                        unit_cost = price_rec.itemprice if price_rec else None
                        total_cost = unit_cost * rd["inqty"] if unit_cost else None
                        MCR.create(
                            data={
                                "wo_id": _wo.wo_id,
                                "item_cd": rd["itemcd"],
                                "plan_qty": 0,
                                "actual_qty": rd["inqty"],
                                "unit": "个",
                                "warehouse_cd": _wo.pick_whcd or _wo.warehouse_cd or "01",
                                "consume_date": dt_parse.now(UTC).date(),
                                "consume_type": ConsumeType.RETURN,
                                "ref_bill_type": "IV",
                                "ref_qc_id": qcbillid,
                                "unit_cost": unit_cost,
                                "total_cost": total_cost,
                            },
                            creator=auditor,
                        )

                _wo.status = "COMPLETED"
                _wo.actual_qty = _wo.plan_qty
                _wo.actual_end = dt_parse.now(UTC).date()
                _wo.upddate = dt_parse.now(UTC)
            else:
                _wo.status = "IN_PROGRESS"
                _wo.upddate = dt_parse.now(UTC)

        # ── 仓库联动 ──
        from app.services.warehouse_service import StockOutService
        ref = qc.refbillid or ""
        is_qc_out = ref.startswith("OT")

        # GA/GB/GC → IV=11（IQC）/ IV=8（FQC）
        if pass_eid or pass_prd:
            in_details: list[dict[str, Any]] = []
            for row in pass_eid:
                if is_fqc and product_itemcd and row.itemcd and row.itemcd != product_itemcd:
                    continue
                d_in: dict[str, Any] = {
                    "itemcd": row.itemcd or "", "inqty": int(row.qcqty or 1), "eid": row.eid or "",
                    **({"ref_rgstbillid": ref} if is_qc_out else {}),
                }
                if getattr(row, "prddate", None):
                    d_in["prddate"] = row.prddate.isoformat() if hasattr(row.prddate, "isoformat") else str(row.prddate)
                in_details.append(d_in)
            for row in pass_prd:
                if is_fqc and product_itemcd and row.itemcd and row.itemcd != product_itemcd:
                    continue
                d: dict[str, Any] = {"itemcd": row.itemcd or "", "inqty": int(row.qcqty or 1)}
                if row.prddate:
                    d["prddate"] = row.prddate.isoformat() if hasattr(row.prddate, "isoformat") else str(row.prddate)
                if is_qc_out:
                    d["ref_rgstbillid"] = ref
                in_details.append(d)
            if in_details and (is_qc_out or is_fqc):
                invtyp = "11" if is_qc_out else "8"
                target_whcd = fqc_whcd if is_fqc else "04"
                StockInService.create(
                    data={"invtyp": invtyp, "refbillid": qcbillid, "whcd": target_whcd},
                    details=in_details, creator=auditor,
                )

        # BF/BH/TH → 分别 IV=11 入暂存仓（后续 OV 在仓库审核 IV 时自动触发）
        def _get_defect_wh(parm_cd: str, default: str) -> str:
            """从 sysparm 读取不良品仓库编码，未配置时用默认值。"""
            from app.models.system import SysParm
            sp = db.session.get(SysParm, parm_cd)
            return (sp.parm_val or default) if sp else default

        def _gen_iv(rows_eid: list, rows_prd: list, wh: str, label: str, itemtyp: str) -> None:
            """生成 IV=11 入库单，绕过草稿复用直接创建独立单据。"""
            in_list: list[dict[str, Any]] = []
            for r in rows_eid:
                if r.eid:
                    d_in: dict[str, Any] = {"itemcd": r.itemcd or "", "inqty": int(r.qcqty or 1), "eid": r.eid or "", "itemtyp": itemtyp}
                    if getattr(r, "prddate", None):
                        d_in["prddate"] = r.prddate.isoformat() if hasattr(r.prddate, "isoformat") else str(r.prddate)
                    in_list.append(d_in)
            for r in rows_prd:
                if r.itemcd:
                    d_in: dict[str, Any] = {"itemcd": r.itemcd or "", "inqty": int(r.qcqty or 1), "itemtyp": itemtyp}
                    if r.prddate:
                        d_in["prddate"] = r.prddate.isoformat() if hasattr(r.prddate, "isoformat") else str(r.prddate)
                    in_list.append(d_in)
            if in_list:
                from app.repositories.warehouse_repository import StockInRepository
                data = {"invtyp": "11", "whcd": wh, "refbillid": qcbillid, "memo": f"QC判定{label}待入库 {qcbillid}", "indate": dt_parse.now(UTC)}
                record = StockInRepository.create(data, auditor)
                for idx, detail_data in enumerate(in_list, start=1):
                    StockInRepository.add_detail(
                        inbillid=record.inbillid,
                        whcd=record.whcd,
                        lineno=idx,
                        data=detail_data,
                    )

        if scrap_eid or scrap_prd:
            _gen_iv(scrap_eid, scrap_prd, _get_defect_wh("qc_scrap_warehouse", "L1"), "报废", "BF")
        if repair_eid or repair_prd:
            _gen_iv(repair_eid, repair_prd, _get_defect_wh("qc_repair_warehouse", "LS"), "返修", "BH")
        if return_eid or return_prd:
            _gen_iv(return_eid, return_prd, _get_defect_wh("qc_return_warehouse", "LS"), "退换", "TH")

        # IPQC/FQC 不良品补料 OV=8（跳过已在录入页申请补料的）
        non_pass_eid = [r for r in scrap_eid + repair_eid + return_eid
                        if not (getattr(r, "replenish_ov_billid", "") or "").strip()]
        non_pass_prd = [r for r in scrap_prd + repair_prd + return_prd
                        if not (getattr(r, "replenish_ov_billid", "") or "").strip()]
        if (is_ipqc or is_fqc) and (non_pass_eid or non_pass_prd):
            replenish_details: list[dict[str, Any]] = []
            for row in non_pass_eid:
                if row.itemcd:
                    replenish_details.append({"itemcd": row.itemcd, "outqty": int(row.qcqty or 1)})
            for row in non_pass_prd:
                d_rp: dict[str, Any] = {"itemcd": row.itemcd, "outqty": int(row.qcqty or 1)}
                if row.prddate:
                    d_rp["prddate"] = row.prddate.isoformat() if hasattr(row.prddate, "isoformat") else str(row.prddate)
                replenish_details.append(d_rp)
            if replenish_details:
                tag = "FQC" if is_fqc else "IPQC"
                out_rec = StockOutService.create(
                    data={
                        "invtyp": "8",
                        "whcd": fqc_whcd if _wo and _wo.pick_whcd else "01",
                        "refbillid": _wo.wo_id if _wo else qc.refbillid,
                        "memo": f"{tag}不良补料 {qcbillid}",
                    },
                    details_eid=[], details_prd=replenish_details, creator=auditor,
                )

                # 同步写入 TMS04 物料消耗（补料）
                from app.repositories.mes_repository import MaterialConsumeRepository
                from app.models.inventory import Price
                for rp in replenish_details:
                    # 查询物料标准价格
                    price_rec = Price.query.filter_by(
                        itemcd=rp["itemcd"],
                        busityp="20",
                        is_current=True,
                        useflg="1"
                    ).first()
                    unit_cost = price_rec.itemprice if price_rec else None
                    actual_qty = rp["outqty"]
                    total_cost = unit_cost * actual_qty if unit_cost else None

                    MaterialConsumeRepository.create(
                        data={
                            "wo_id": _wo.wo_id if _wo else qc.refbillid,
                            "item_cd": rp["itemcd"],
                            "plan_qty": 0,  # 补料无计划
                            "actual_qty": actual_qty,
                            "unit": "个",
                            "warehouse_cd": fqc_whcd if _wo and _wo.pick_whcd else "01",
                            "consume_date": dt_parse.now(UTC).date(),
                            "consume_type": ConsumeType.REPLENISH,
                            "ref_bill_type": "OV",
                            "ref_bill_id": out_rec.get("outbillid", ""),
                            "ref_qc_id": qcbillid,
                            "unit_cost": unit_cost,
                            "total_cost": total_cost,
                        },
                        creator=auditor,
                    )
                db.session.flush()

        # ── 更换物料处理：生成 IV=11 入库（审核后自动生成 OV 出库）──
        if is_fqc and has_product_pass:
            from app.models.mes import ReplaceRecord
            replace_recs = db.session.query(ReplaceRecord).filter(
                ReplaceRecord.wo_id == _wo.wo_id,
            ).all()
            if replace_recs:
                iv11_details: list[dict[str, Any]] = []
                for rec in replace_recs:
                    judgment = "BF"
                    if rec.old_batch_no and "(" in (rec.old_batch_no or ""):
                        judgment = rec.old_batch_no.split("(")[-1].rstrip(")")
                    wh_map = {
                        "BF": _get_defect_wh("qc_scrap_warehouse", "L1"),
                        "BH": _get_defect_wh("qc_repair_warehouse", "LS"),
                        "TH": _get_defect_wh("qc_return_warehouse", "LS"),
                    }
                    d: dict[str, Any] = {"itemcd": rec.itemcd, "inqty": 1, "itemtyp": judgment, "whcd": wh_map.get(judgment, _get_defect_wh("qc_scrap_warehouse", "L1"))}
                    if rec.old_eid: d["eid"] = rec.old_eid
                    iv11_details.append(d)
                # 按仓库分组生成 IV=11
                wh_groups: dict[str, list[dict[str, Any]]] = {}
                for d in iv11_details:
                    wh = d.pop("whcd", _get_defect_wh("qc_scrap_warehouse", "L1"))
                    if wh not in wh_groups: wh_groups[wh] = []
                    wh_groups[wh].append(d)
                _JUDGMENT_CN = {"BF": "报废", "BH": "返修", "TH": "退换"}
                for wh, items in wh_groups.items():
                    typs = list({_JUDGMENT_CN.get(it.get("itemtyp") or "", it.get("itemtyp") or "?") for it in items})
                    typ_label = "、".join(sorted(typs))
                    StockInService.create(
                        data={"invtyp": "11", "whcd": wh, "refbillid": qcbillid,
                              "memo": f"FQC更换旧物料({typ_label}) {qcbillid}"},
                        details=items, creator=auditor,
                    )

        # ── 更新更换下来的旧 EID 状态（报废/返修/退换）──
        if is_fqc and has_product_pass:
            from app.models.master import Eid as _EidModel
            from app.models.mes import ReplaceRecord as _RR2
            old_recs = db.session.query(_RR2).filter(_RR2.wo_id == _wo.wo_id).all()
            for rec in old_recs:
                if rec.old_eid:
                    db.session.query(_EidModel).filter(_EidModel.eid == rec.old_eid).update(
                        {"sflg": "2", "qcflg": "BF"}, synchronize_session=False
                    )

        db.session.commit()
        return {"success": True}

    @staticmethod
    def unaudit(qcbillid: str, auditor: str) -> dict[str, object]:
        """反审核 QC：仅允许已审核且下游单据未审核的情况。"""
        from app.models.warehouse import QcResult, StockIn, StockOut

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

        # 回退 EID 状态和标签
        from app.models.master import Eid as EidModel
        from app.models.inventory import Label
        for row in qc.detail_eids:
            if not row.eid:
                continue
            db.session.query(EidModel).filter(EidModel.eid == row.eid).update({
                "qcflg": "DJ", "sflg": "1", "whcd": None,
            }, synchronize_session=False)
            # 重新激活标签
            label = db.session.get(Label, (row.eid, row.itemcd)) if row.itemcd else None
            if label and label.useflg == "0":
                label.useflg = "1"

        # 回退 FQC 工单状态（如为工单质检且无其他已审QC记录）
        _qc_ref = qc.refbillid or ""
        if _qc_ref.startswith("WO"):
            from app.models.mes import WorkOrder
            _wo = WorkOrder.query.get(_qc_ref)
            if _wo and _wo.status == "COMPLETED":
                # 检查是否还有其他已审核的QC记录关联此工单
                other_qc = db.session.query(QcResult).filter(
                    QcResult.refbillid == _qc_ref,
                    QcResult.auditflg == "1",
                    QcResult.qcbillid != qcbillid
                ).first()
                if not other_qc:
                    _wo.status = "QC_PENDING"
                    _wo.upddate = dt_parse.now(UTC)

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
            items = db.session.query(Item.item_cd, Item.item_nm, Item.class_cd, Item.typflg, Item.consume).filter(
                Item.item_cd.in_(item_cds)
            ).all()
            item_map = {i.item_cd: {
                "item_nm": i.item_nm or "",
                "class_cd": i.class_cd or "",
                "typflg": i.typflg or "0",
                "consume": i.consume or "0",
            } for i in items}
        # 批量获取分类名称
        class_cds = {v["class_cd"] for v in item_map.values() if v["class_cd"]}
        class_map: dict[str, str] = {}
        if class_cds:
            classes = db.session.query(ItemClass.class_cd, ItemClass.class_nm).filter(
                ItemClass.class_cd.in_(class_cds)
            ).all()
            class_map = {c.class_cd: c.class_nm or "" for c in classes}

        # 批量查询审核后生成的出入库单号
        from app.models.warehouse import QcResult, StockIn, StockOut

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
                    "typflg": item_map.get(dt.itemcd or "", {}).get("typflg", "0"),
                    "consume": item_map.get(dt.itemcd or "", {}).get("consume", "0"),
                }
                for dt in QcRepository.list_details(qc.qcbillid)
            ]
            rec["eid_details"] = [
                {
                    **e.to_dict(),
                    "item_nm": item_map.get(e.itemcd or "", {}).get("item_nm", ""),
                    "class_nm": class_map.get(item_map.get(e.itemcd or "", {}).get("class_cd", ""), ""),
                    "typflg": item_map.get(e.itemcd or "", {}).get("typflg", "0"),
                    "consume": item_map.get(e.itemcd or "", {}).get("consume", "0"),
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
            if qc.auditflg == "8":
                return {"success": False, "error": "批次已退回，无法重复操作"}

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
    def replenish(batch_id: str, operator: str, replenish_qty: dict[str, int] | None = None) -> dict[str, Any]:
        """为批次中的不良品行创建 OV=8 补料出库单。

        将所有 BF/BH/TH 行按物料聚合，生成一张 OV=8 草稿单，
        并更新各明细行的 replenish_status / replenish_ov_billid。
        """
        from app.models.mes import WorkOrder
        from app.models.master import Bom
        from app.services.warehouse_service import StockOutService
        from app.repositories.mes_repository import MaterialConsumeRepository
        from app.models.inventory import Price

        prd_rows, eid_rows = QcRepository.get_non_pass_details(batch_id)
        if not prd_rows and not eid_rows:
            return {"success": False, "error": "没有需要补料的物料（所有不良品行已申请补料）"}

        qcs = QcRepository.get_batch_details(batch_id)
        refbillid = qcs[0].refbillid or "" if qcs else ""
        _wo = None
        whcd = "01"
        wo_id = refbillid
        if refbillid.startswith("WO"):
            _wo = WorkOrder.query.get(refbillid)
            if _wo:
                whcd = _wo.pick_whcd or "01"
                wo_id = _wo.wo_id

        # 按 itemcd 聚合
        agg: dict[str, dict[str, Any]] = {}
        for row in prd_rows:
            cd = row.itemcd or ""
            if cd not in agg:
                agg[cd] = {"itemcd": cd, "outqty": 0}
            agg[cd]["outqty"] += int(row.qcqty or 1)
            if row.prddate and "prddate" not in agg[cd]:
                agg[cd]["prddate"] = (
                    row.prddate.isoformat()
                    if hasattr(row.prddate, "isoformat")
                    else str(row.prddate)
                )
        for row in eid_rows:
            cd = row.itemcd or ""
            if cd not in agg:
                agg[cd] = {"itemcd": cd, "outqty": 0}
            agg[cd]["outqty"] += int(row.qcqty or 1)
            if row.prddate and "prddate" not in agg[cd]:
                agg[cd]["prddate"] = (
                    row.prddate.isoformat()
                    if hasattr(row.prddate, "isoformat")
                    else str(row.prddate)
                )

        replenish_details = list(agg.values())

        # 查询 BOM 冗余量，应用到补料数量
        ratio = 0.0
        if refbillid.startswith("WO") and _wo and _wo.item_cd:
            bom = db.session.get(Bom, _wo.item_cd)
            if bom and bom.redundancy_ratio:
                ratio = float(bom.redundancy_ratio)
        if ratio > 0:
            for item in replenish_details:
                outqty = int(item["outqty"] or 1)
                item["outqty"] = max(1, int(outqty * (1 + ratio) + 0.5))

        # 用户手动调整数量（覆盖比率计算值）
        if replenish_qty:
            for item in replenish_details:
                cd = item["itemcd"]
                if cd in replenish_qty and replenish_qty[cd] > 0:
                    item["outqty"] = replenish_qty[cd]

        out_rec = StockOutService.create(
            data={
                "invtyp": "8",
                "whcd": whcd,
                "refbillid": wo_id,
                "memo": f"QC不良补料 批次{batch_id}",
            },
            details_eid=[],
            details_prd=replenish_details,
            creator=operator,
        )
        ov_billid = out_rec.get("outbillid", "")

        # 标记明细行
        QcRepository.mark_details_replenished(batch_id, ov_billid)

        # 写入 TMS04
        for rp in replenish_details:
            price_rec = Price.query.filter_by(
                itemcd=rp["itemcd"], busityp="20", is_current=True, useflg="1",
            ).first()
            unit_cost = price_rec.itemprice if price_rec else None
            actual_qty = rp["outqty"]
            total_cost = unit_cost * actual_qty if unit_cost else None
            MaterialConsumeRepository.create(
                data={
                    "wo_id": wo_id,
                    "item_cd": rp["itemcd"],
                    "plan_qty": 0,
                    "actual_qty": actual_qty,
                    "unit": "个",
                    "warehouse_cd": whcd,
                    "consume_date": dt_parse.now(UTC).date(),
                    "consume_type": ConsumeType.REPLENISH,
                    "ref_bill_type": "OV",
                    "ref_bill_id": ov_billid,
                    "ref_qc_id": qcs[0].qcbillid if qcs else "",
                    "unit_cost": unit_cost,
                    "total_cost": total_cost,
                },
                creator=operator,
            )

        db.session.commit()
        return {
            "success": True,
            "ov_billid": ov_billid,
            "item_count": len(replenish_details),
            "items": replenish_details,
        }

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
