"""仓储管理业务服务层。"""

from __future__ import annotations

from datetime import UTC, datetime as dt_parse

from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models.master import Item
from app.models.warehouse import StockDetail, StockIn, StockOut, Warehouse
from app.repositories.warehouse_repository import (
    AssetCheckRepository,
    OverLostRepository,
    PosChangeRepository,
    StockDetailRepository,
    StockInRepository,
    StockOutRepository,
    TransferAccountRepository,
    WarehouseRepository,
)


def _enrich_warehouse_names(rows: list[dict[str, Any]]) -> None:
    """批量补充仓库名称 whnm。"""
    whcds = list({r.get("whcd") for r in rows if r.get("whcd")})
    if not whcds:
        return
    wh_map = dict(
        db.session.query(Warehouse.whcd, Warehouse.whnm)
        .filter(Warehouse.whcd.in_(whcds))
        .all()
    )
    for r in rows:
        cd = r.get("whcd")
        if cd and not r.get("whnm"):
            r["whnm"] = wh_map.get(cd, "")


def _enrich_item_names(details: list[dict[str, Any]]) -> None:
    """批量补充明细中的物料名称 item_nm、易耗品标志 consume、库存上下限、中类编码 class_cd、是否成品 is_bom。"""
    itemcds = list({d.get("itemcd") for d in details if d.get("itemcd")})
    if not itemcds:
        return
    rows = (
        db.session.query(Item.item_cd, Item.item_nm, Item.consume,
                         Item.upperlimit, Item.lowerlimit, Item.class_cd)
        .filter(Item.item_cd.in_(itemcds))
        .all()
    )
    item_map = {r[0]: (r[1] or "", r[2] or "", r[3], r[4], r[5] or "") for r in rows}
    # 查询哪些物料是成品（在 BOM 主表中）
    from app.models.master import Bom
    bom_cds = {r[0] for r in db.session.query(Bom.bomcd).filter(Bom.bomcd.in_(itemcds)).all()}
    _default = ("", "", None, None, "")
    for d in details:
        cd = d.get("itemcd")
        if cd:
            v = item_map.get(cd, _default)
            d["item_nm"] = v[0]
            d["consume"] = v[1]
            d["upperlimit"] = v[2]
            d["lowerlimit"] = v[3]
            d["class_cd"] = v[4]
            d["is_bom"] = cd in bom_cds


def _enrich_prddate_from_out(details: list[dict[str, Any]], outbillid: str) -> None:
    """如果入库明细 prddate 为空，从关联出库单批次明细按 reflineno 回填。"""
    from app.models.warehouse import StockOutDetailPrd

    # 找出缺少 prddate 且有 reflineno 的明细
    need_fill = [d for d in details if not d.get("prddate") and d.get("reflineno")]
    if not need_fill:
        return
    # 查询出库单批次明细
    prd_rows = (
        db.session.query(StockOutDetailPrd.lineno, StockOutDetailPrd.prddate)
        .filter(StockOutDetailPrd.outbillid == outbillid, StockOutDetailPrd.prddate.isnot(None))
        .all()
    )
    prd_map = {r.lineno: r.prddate.isoformat() for r in prd_rows}
    for d in need_fill:
        ref = d.get("reflineno")
        if ref and ref in prd_map:
            d["prddate"] = prd_map[ref]


class WarehouseService:
    """仓库主数据服务。"""

    @staticmethod
    def get(whcd: str) -> dict[str, Any] | None:
        record = WarehouseRepository.get_by_id(whcd)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(useflg: str | None = None) -> list[dict[str, Any]]:
        records = WarehouseRepository.list_all(useflg=useflg)
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = WarehouseRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(whcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = WarehouseRepository.get_by_id(whcd)
        if record is None:
            return None
        WarehouseRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class StockInService:
    """入库单服务。"""

    @staticmethod
    def list_receivable_orders() -> list[dict[str, Any]]:
        """查询可入库的采购订单列表（供前端选择订单下拉框）。"""
        return StockInRepository.find_receivable_orders()

    @staticmethod
    def list_transferable_orders() -> list[dict[str, Any]]:
        """查询可调拨入库的调拨出库单列表。"""
        return StockInRepository.find_transferable_orders()

    @staticmethod
    def skip_service_return(maintenance_id: str, reason: str, eids: list[str] | None = None) -> dict[str, object]:
        """按EID标记ITSM配件变更为不入库。eids为空则标记该工单全部。"""
        from app.models.itsm import AccessoriesUpdate
        query = (
            db.session.query(AccessoriesUpdate)
            .filter(
                AccessoriesUpdate.maintenance_id == maintenance_id,
                AccessoriesUpdate.old_accessories_id.isnot(None),
                AccessoriesUpdate.old_accessories_id != "",
                AccessoriesUpdate.in_wh.is_distinct_from("1"),
            )
        )
        if eids:
            query = query.filter(AccessoriesUpdate.old_accessories_id.in_(eids))
        records = query.all()
        if not records:
            return {"success": False, "error": "未找到待处理的配件变更记录"}
        for r in records:
            r.in_wh = "2"
            r.description = (r.description or "") + f" [不入库: {reason}]"
        db.session.commit()
        return {"success": True, "maintenance_id": maintenance_id, "count": len(records)}

    @staticmethod
    def confirm_service_return(maintenance_ids: list[str], operator: str) -> dict[str, object]:
        """确认ITSM配件变更并生成服务返还入库草稿。"""
        from app.models.itsm import AccessoriesUpdate

        created = []
        for mid in maintenance_ids:
            records = (
                db.session.query(AccessoriesUpdate)
                .filter(
                    AccessoriesUpdate.maintenance_id == mid,
                    AccessoriesUpdate.old_accessories_id.isnot(None),
                    AccessoriesUpdate.old_accessories_id != "",
                    AccessoriesUpdate.in_wh.is_distinct_from("1"),
                )
                .all()
            )
            if not records:
                continue

            from app.models.master import Eid as EidModel
            eids = [r.old_accessories_id for r in records if r.old_accessories_id]
            if not eids:
                continue

            details = []
            for r in records:
                details.append({
                    "itemcd": "",
                    "inqty": 1,
                    "eid": r.old_accessories_id,
                })

            if details:
                # 补物料编码
                eid_info = {
                    r[0]: r[1] for r in db.session.query(EidModel.eid, EidModel.itemcd)
                    .filter(EidModel.eid.in_([d["eid"] for d in details]))
                    .all()
                }
                for d in details:
                    d["itemcd"] = eid_info.get(d["eid"], "")

                StockInService.create(
                    data={
                        "invtyp": "3",
                        "refbillid": mid,
                        "whcd": "",
                    },
                    details=details,
                    creator=operator,
                    _commit=False,
                )
                # 标记为已入库
                for r in records:
                    r.in_wh = "1"
                created.append(mid)

        db.session.commit()
        return {"success": True, "created": len(created), "maintenance_ids": created}

    @staticmethod
    def get_lendable_order_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某借出出库单中尚未归还的明细行。"""
        return StockInRepository.get_lendable_order_lines(outbillid)

    @staticmethod
    def list_repair_returnable() -> list[dict[str, Any]]:
        """查询可返修入库的返修出库单列表（已审核且未完全入库）。"""
        return StockInRepository.find_repair_returnable_orders()

    @staticmethod
    def get_repair_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某返修出库单中尚未入库的明细行。"""
        return StockInRepository.get_repair_returnable_lines(outbillid)

    @staticmethod
    def list_production_returnable() -> list[dict[str, Any]]:
        """查询可生产入库的生产出库单列表。"""
        return StockInRepository.find_production_returnable_orders()

    @staticmethod
    def get_production_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某生产出库单中尚未入库的明细行。"""
        return StockInRepository.get_production_returnable_lines(outbillid)

    @staticmethod
    def list_renovation_returnable() -> list[dict[str, Any]]:
        """查询可翻新入库的翻新出库单列表（OV=10，供 IV=6 选单）。"""
        return StockInRepository.find_renovation_returnable_orders()

    @staticmethod
    def get_renovation_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某翻新出库单中尚未入库的明细行。"""
        return StockInRepository.get_renovation_returnable_lines(outbillid)

    @staticmethod
    def list_qc_returnable() -> list[dict[str, Any]]:
        """查询可质检入库的质检出库单列表（IV=11）。"""
        return StockInRepository.find_qc_returnable_orders()

    @staticmethod
    def list_ov5_for_qc() -> list[dict[str, Any]]:
        """查询还有未QC物料的 OV=5 质检出库单列表。"""
        return StockInRepository.find_ov5_for_qc()

    @staticmethod
    def get_qc_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某质检出库单中尚未入库的明细行。"""
        return StockInRepository.get_qc_returnable_lines(outbillid)

    @staticmethod
    def list_qc_out_pending() -> list[dict[str, Any]]:
        """查询可供质检出库选单的已审核采购入库单（OV=5 来源单）。"""
        return StockInRepository.find_qc_out_pending_orders()

    @staticmethod
    def get_qc_pending_lines(inbillid: str) -> list[dict[str, Any]]:
        """查询某采购入库单的物料明细（供 OV=5 质检出库选择）。

        返回该入库单下的所有物料明细，包括批次和EID信息。
        """
        return StockInRepository.get_qc_pending_lines(inbillid)

    @staticmethod
    def list_sales_returnable() -> list[dict[str, Any]]:
        """查询可销售退货入库的销售出库单（IV=2）。"""
        return StockInRepository.find_sales_returnable_orders()

    @staticmethod
    def get_sales_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某销售出库单中尚未退货的明细行。"""
        return StockInRepository.get_sales_returnable_lines(outbillid)

    @staticmethod
    def list_service_returnable() -> list[dict[str, Any]]:
        """查询 ITSM 工单中可返还的自有资产旧配件。"""
        result = StockInRepository.find_service_returnable_items()
        # 补充物料名称
        all_items = []
        for r in result:
            all_items.extend(r.get("items", []))
        _enrich_item_names(all_items)
        return result

    @staticmethod
    def get_receivable_order_lines(rgstbillid: str) -> list[dict[str, Any]]:
        """查询某采购订单的可入库明细行。"""
        return StockInRepository.get_receivable_order_lines(rgstbillid)

    @staticmethod
    def get(inbillid: str) -> dict[str, Any] | None:
        record = StockInRepository.get_by_id(inbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        _enrich_warehouse_names([result])
        _enrich_item_names(result["details"])
        # 如果入库明细 prddate 为空且有关联出库单，从出库单批次明细回填
        refbillid = result.get("refbillid")
        if refbillid:
            _enrich_prddate_from_out(result["details"], refbillid)
        return result

    @staticmethod
    def list_records(
        whcd: str | None = None,
        invtyp: str | None = None,
        auditflg: str | None = None,
        inbillid: str | None = None,
        indate_from: str | None = None,
        indate_to: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = StockInRepository.list_by_filters(
            whcd=whcd, invtyp=invtyp, auditflg=auditflg,
            inbillid=inbillid, indate_from=indate_from, indate_to=indate_to,
            page=page, per_page=per_page,
        )
        data = [item.to_dict() for item in items]
        _enrich_warehouse_names(data)
        return {
            "items": data,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def _validate_details(details: list[dict[str, Any]], invtyp: str = "") -> str | None:
        """校验明细：itemcd 存在性、itemtyp 合法性、EID 匹配与位置。返回错误信息或 None。"""
        from app.models.master import Item, SysCode, Eid
        valid_qc = {c.code_cd for c in db.session.query(SysCode.code_cd).filter(SysCode.code_typ == "QC").all()}
        valid_qc.add("0")  # 生产领料/通用类型，不做QC校验
        # 销售退货入库、翻新入库：EID 必须在库外且未在门店活跃部署
        check_store_off = invtyp in ("2", "6")
        # 回收入库：EID 必须在库外
        check_outside = invtyp == "7"
        for i, d in enumerate(details, 1):
            itemcd = d.get("itemcd", "")
            if not itemcd: continue
            if not db.session.query(Item.item_cd).filter(Item.item_cd == itemcd).scalar():
                return f"第{i}行物料 {itemcd} 不存在"
            ityp = d.get("itemtyp", "")
            if ityp and ityp not in valid_qc:
                return f"第{i}行物料类型 {ityp} 无效（有效值: {', '.join(sorted(valid_qc))}）"
            eid = d.get("eid", "")
            if eid:
                eid_rec = db.session.query(Eid.itemcd, Eid.eid, Eid.whcd).filter(Eid.eid == eid).first()
                if eid_rec is None:
                    return f"第{i}行 EID {eid} 不存在"
                elif eid_rec.itemcd != itemcd:
                    return f"第{i}行 EID {eid} 属于物料 {eid_rec.itemcd}，与填写的 {itemcd} 不匹配"
                if check_store_off or check_outside:
                    if eid_rec.whcd:
                        return f"第{i}行 EID {eid} 当前在 {eid_rec.whcd} 仓"
                if check_store_off:
                    from app.models.master import CustPosRl, Customer
                    active_pos = db.session.query(
                        CustPosRl.pos_cd, CustPosRl.cust_cd,
                    ).filter(
                        CustPosRl.eid == eid,
                        CustPosRl.useflg == "1",
                    ).first()
                    if active_pos:
                        location = active_pos.pos_cd or ""
                        if active_pos.cust_cd:
                            cust = db.session.query(Customer.cust_nm).filter(
                                Customer.cust_cd == active_pos.cust_cd,
                            ).scalar()
                            if cust:
                                location = f"{cust}({active_pos.cust_cd})" if location else f"客户 {cust}"
                        if not location:
                            location = "客户现场"
                        return f"第{i}行 EID {eid} 仍在 {location} 服役，请先走取机流程"
        return None


    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]],
        creator: str,
        _commit: bool = True,
    ) -> dict[str, Any]:
        # 明细校验
        err = StockInService._validate_details(details, data.get("invtyp", ""))
        if err:
            return {"success": False, "error": err}
        ref_rgstbillid = data.get("refbillid") if data.get("invtyp") in ("1", "4", "5", "8", "9") else None

        # 如果同一来源单据已有未审核草稿，则更新草稿而非新建
        existing_draft = None
        if ref_rgstbillid:
            from app.models.warehouse import StockIn as StockInModel
            existing_draft = (
                db.session.query(StockInModel)
                .filter(
                    StockInModel.refbillid == data["refbillid"],
                    StockInModel.invtyp == data.get("invtyp"),
                    StockInModel.auditflg == "0",
                    StockInModel.whcd == data.get("whcd"),
                )
                .first()
            )

        if existing_draft:
            # 更新已有草稿：仓库、供应商、日期、备注
            existing_draft.whcd = data.get("whcd", existing_draft.whcd)
            existing_draft.suppcd = data.get("suppcd", existing_draft.suppcd)
            if data.get("indate"):
                existing_draft.indate = data["indate"]
            elif not existing_draft.indate:
                existing_draft.indate = dt_parse.now(UTC)
            existing_draft.memo = (data.get("memo") or "") + " [手动更新]"
            existing_draft.opercd = creator
            # 删除旧明细，写入新明细
            existing_draft.details.delete()
            for idx, detail_data in enumerate(details, start=1):
                detail_data["ref_rgstbillid"] = ref_rgstbillid
                detail_data["ref_rgstlineno"] = detail_data.get("reflineno")
                StockInRepository.add_detail(
                    inbillid=existing_draft.inbillid,
                    whcd=existing_draft.whcd,
                    lineno=idx,
                    data=detail_data,
                )
            if _commit:
                db.session.commit()
            return existing_draft.to_dict()

        # 无草稿则新建
        record = StockInRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            if ref_rgstbillid:
                detail_data["ref_rgstbillid"] = ref_rgstbillid
                detail_data["ref_rgstlineno"] = detail_data.get("reflineno")
            StockInRepository.add_detail(
                inbillid=record.inbillid,
                whcd=record.whcd,
                lineno=idx,
                data=detail_data,
            )
        if _commit:
            db.session.commit()
        return record.to_dict()

    @staticmethod
    def audit(
        inbillid: str, auditor: str,
        whcd: str = "", checkmemo: str = "",
        auditflg: str = "2",
    ) -> dict[str, object]:
        record = StockInRepository.get_by_id(inbillid)
        if record is None:
            return {"success": False, "error": "入库单不存在"}
        if record.auditflg == "2":
            return {"success": False, "error": "已审核，不可重复审核"}
        if record.auditflg == "8" and auditflg == "8":
            return {"success": False, "error": "已退回，请先编辑后再审核"}
        # 如果传入 whcd 则覆盖（用于自动生成的空 whcd 草稿）
        if whcd:
            record.whcd = whcd
        if not record.whcd:
            return {"success": False, "error": "请先选择入库仓库后再审核"}

        # 审核退回（auditflg='8'）：仅改状态+备注，不更新库存
        if auditflg == "8":
            record.auditflg = "8"
            record.auditman = auditor
            record.auditdate = dt_parse.now(UTC)
            if checkmemo:
                record.memo = (record.memo or "") + " [退回: " + checkmemo + "]"
            db.session.commit()
            return {"success": True, "inbillid": record.inbillid}

        if checkmemo:
            record.memo = (record.memo or "") + " [审核: " + checkmemo + "]"

        if auditflg != "2":
            return {"success": False, "error": f"不支持的审核动作: {auditflg}"}

        # 服务返还入库且无明细（全部不入库）：审核后标 S
        if record.invtyp == "3" and record.details.count() == 0:  # type: ignore[attr-defined]
            record.auditflg = "S"
            record.auditman = auditor
            record.auditdate = dt_parse.now(UTC)
            # 不更新库存（无明细），直接提交
            db.session.commit()
            return {"success": True, "inbillid": record.inbillid}

        StockInRepository.audit(record, auditor)
        for detail in record.details:  # type: ignore[attr-defined]
            StockDetailRepository.update_balance(
                whcd=record.whcd,
                itemcd=detail.itemcd,
                qty_delta=detail.inqty or 0,
                operator=auditor,
                itemtyp=getattr(detail, 'itemtyp', None),
                prddate=getattr(detail, 'prddate', None),
            )
            StockDetailRepository.add_movement(
                whcd=record.whcd, itemcd=detail.itemcd,
                itemqty=detail.inqty or 0,
                billid=record.inbillid, invtyp=record.invtyp or "",
                iotyp="1", operator=auditor,
                itemtyp=getattr(detail, 'itemtyp', None),
                prddate=getattr(detail, 'prddate', None),
            )
            # EID 设备入库 → 同步更新或创建 TMM43_EID
            if detail.eid:
                from app.models.master import Eid
                eid_val = detail.eid
                itemcd_val = detail.itemcd
                whcd_val = record.whcd
                vals: dict[str, Any] = {"whcd": whcd_val}
                if record.invtyp in ("3", "7"):
                    vals["qcflg"] = "DJ"
                    vals["sflg"] = "2"
                elif record.invtyp == "5":
                    vals["sflg"] = "2"
                elif record.invtyp in ("6", "8"):
                    # 翻新/生产入库：新机/成品 EID 回库，标记在库
                    vals["sflg"] = "8"
                    vals["qcflg"] = "GA"  # 合格
                db.session.query(Eid).filter(
                    Eid.itemcd == itemcd_val, Eid.eid == eid_val,
                ).update(vals, synchronize_session=False)
        # QC 不合格品入库审核 → 按明细 itemtyp 自动生成对应出库单
        if record.invtyp == "11" and record.refbillid and record.refbillid.startswith("QC"):
            try:
                ov_map = {"BF": "7", "BH": "9", "TH": "6"}
                label_map = {"BF": "报废", "BH": "返修", "TH": "退换"}
                # 按 itemtyp 分组 IV 明细（BF/BH/TH 分别生成 OV）
                groups: dict[str, list[dict[str, Any]]] = {}
                groups_eid: dict[str, list[dict[str, Any]]] = {}
                for dt in record.details:
                    it = getattr(dt, 'itemtyp', '') or ''
                    if it not in ("BF", "BH", "TH"):
                        continue
                    if it not in groups:
                        groups[it] = []
                        groups_eid[it] = []
                    d: dict[str, Any] = {"itemcd": dt.itemcd, "outqty": dt.inqty or 1, "itemtyp": it}
                    if getattr(dt, 'prddate', None):
                        d["prddate"] = dt.prddate.isoformat() if hasattr(dt.prddate, 'isoformat') else str(dt.prddate)
                    if getattr(dt, 'eid', None):
                        d["eid"] = dt.eid
                        groups_eid[it].append(d)
                    else:
                        groups[it].append(d)
                for typ, out_prd in groups.items():
                    out_eid = groups_eid.get(typ, [])
                    if not out_eid and not out_prd:
                        continue
                    ov_type = ov_map[typ]
                    label = label_map[typ]
                    out_rec = StockOutService.create(
                        data={"invtyp": ov_type, "whcd": record.whcd, "refbillid": record.refbillid,
                              "memo": f"QC判定{label}自动出库 {record.inbillid}"},
                        details_eid=out_eid, details_prd=out_prd, creator=auditor,
                    )
                    # TMS04 在 OV 审核时写入（_write_material_consume），此处不提前写入
            except Exception:
                pass  # 自动生成失败不影响入库审核

        # 翻新入库审核通过 → 关联翻新出库单的旧机 EID 标记翻新完成（已报废/已翻新）
        if record.invtyp == "6" and record.refbillid:
            from app.models.master import Eid as EidModel
            from app.models.warehouse import StockOutDetailEid as OutEid
            old_eids = (
                db.session.query(OutEid.eid, OutEid.itemcd)
                .filter(OutEid.outbillid == record.refbillid)
                .all()
            )
            for old_eid, old_itemcd in old_eids:
                if old_eid:
                    db.session.query(EidModel).filter(
                        EidModel.eid == old_eid,
                    ).update({
                        "sflg": "8",    # 翻新完成（旧机已废弃）
                        "qcflg": "BF",
                    }, synchronize_session=False)
            # 新EID溯源：ref_eid指向旧机EID（取第一个旧EID）
            first_old = old_eids[0].eid if old_eids else None
            if first_old:
                in_eids = [d.eid for d in record.details if d.eid]  # type: ignore[attr-defined]
                for new_eid in in_eids:
                    db.session.query(EidModel).filter(
                        EidModel.eid == new_eid,
                    ).update({"ref_eid": first_old}, synchronize_session=False)
        # 返修入库审核通过 → 重新激活入库明细中的EID（待检状态）
        if record.invtyp == "9" and record.refbillid:
            from app.models.master import Eid as EidModel
            in_eids = [(d.eid, d.itemcd) for d in record.details if d.eid]  # type: ignore[attr-defined]
            for eid_val, itemcd_val in in_eids:
                db.session.query(EidModel).filter(
                    EidModel.itemcd == itemcd_val, EidModel.eid == eid_val,
                ).update({
                    "whcd": record.whcd,
                    "sflg": "3",    # 待检
                    "qcflg": "DJ",  # 待检
                }, synchronize_session=False)
        # P0-1: 采购入库审核后更新 TPC13.inqty
        if record.invtyp == "1" and record.refbillid:
            from app.models.procurement import PurchaseRegisterDt, RequisitionOrderLink
            for detail in record.details:  # type: ignore[attr-defined]
                if detail.reflineno:
                    db.session.query(PurchaseRegisterDt).filter(
                        PurchaseRegisterDt.rgstbillid == record.refbillid,
                        PurchaseRegisterDt.lineno == detail.reflineno,
                    ).update(
                        {PurchaseRegisterDt.inqty: PurchaseRegisterDt.inqty + (detail.inqty or 0)},
                        synchronize_session=False,
                    )
            # P1: 更新 TPC20 linkstatus (ordered → partial_in/completed)
            # 检查订单行是否全部入库完毕（TWH14.inqty vs TPC13.rgsqty）
            order_lines = db.session.query(
                PurchaseRegisterDt.lineno, PurchaseRegisterDt.rgsqty
            ).filter(
                PurchaseRegisterDt.rgstbillid == record.refbillid
            ).all()
            inqty_map = {d.reflineno: d.inqty or 0 for d in record.details}  # type: ignore[attr-defined]
            all_full = all(
                inqty_map.get(ol.lineno, 0) >= (ol.rgsqty or 0)
                for ol in order_lines
            )
            db.session.query(RequisitionOrderLink).filter(
                RequisitionOrderLink.rgstbillid == record.refbillid
            ).update(
                {"linkstatus": "completed" if all_full else "partial_in"},
                synchronize_session=False,
            )
        # 质检出库(OV=5)不在此自动生成——操作员通过质检出库选择器手动触发
        # 选择器接口: GET /stock-out/qc-pending（返回已审核的采购入库单列表）

        # 服务返还入库审核：按EID标记 TIT25.in_wh='1'（仅入库的EID）
        if record.invtyp == "3" and record.refbillid:
            from app.models.itsm import AccessoriesUpdate
            in_eids = [d.eid for d in record.details if d.eid]  # type: ignore[attr-defined]
            if in_eids:
                db.session.query(AccessoriesUpdate).filter(
                    AccessoriesUpdate.maintenance_id == record.refbillid,
                    AccessoriesUpdate.old_accessories_id.in_(in_eids),
                ).update({"in_wh": "1"}, synchronize_session=False)

        db.session.commit()
        return {"success": True, "inbillid": record.inbillid}

    @staticmethod
    def unaudit(inbillid: str, auditor: str) -> dict[str, object]:
        """反审核入库单：回退库存、作废下游 OV 草稿、重置 EID 状态。"""
        record = StockInRepository.get_by_id(inbillid)
        if record is None:
            return {"success": False, "error": "入库单不存在"}
        if record.auditflg != "2":
            return {"success": False, "error": "仅已审核单据可反审核"}

        from app.models.warehouse import StockOut
        # IV=11 自动生成的 OV 其 refbillid 指向 QC 单号，memo 含 IV 单号
        ov_filter = (
            (StockOut.refbillid == record.refbillid)
            if record.invtyp == "11"
            else (StockOut.refbillid == record.inbillid)
        )
        audited_ov = db.session.query(StockOut).filter(
            ov_filter,
            StockOut.auditflg == "2",
        ).first()
        if audited_ov:
            return {"success": False, "error": "下游出库单已审核，不可反审核"}

        for detail in record.details:
            StockDetailRepository.update_balance(
                whcd=record.whcd,
                itemcd=detail.itemcd,
                qty_delta=-(detail.inqty or 0),
                operator=auditor,
                itemtyp=getattr(detail, 'itemtyp', None),
                prddate=getattr(detail, 'prddate', None),
            )
            if detail.eid:
                from app.models.master import Eid
                eid_val = detail.eid
                itemcd_val = detail.itemcd
                vals: dict[str, Any] = {"whcd": None}
                if record.invtyp in ("3", "7"):
                    vals["qcflg"] = None
                    vals["sflg"] = None
                elif record.invtyp in ("5", "6", "8"):
                    vals["sflg"] = None
                    vals["qcflg"] = None
                db.session.query(Eid).filter(
                    Eid.itemcd == itemcd_val, Eid.eid == eid_val,
                ).update(vals, synchronize_session=False)

        # IV=11 的 OV refbillid 指向 QC 单号，反审核时一并作废下游草稿 OV + 清理 TMS04
        if record.invtyp == "11":
            voided_ovs = db.session.query(StockOut.outbillid).filter(
                StockOut.refbillid == record.refbillid,
                StockOut.auditflg == "0",
            ).all()
            ov_ids = [r.outbillid for r in voided_ovs]
            if ov_ids:
                db.session.query(StockOut).filter(
                    StockOut.outbillid.in_(ov_ids),
                ).update({"auditflg": "V"}, synchronize_session=False)
                from app.models.mes import MaterialConsume
                db.session.query(MaterialConsume).filter(
                    MaterialConsume.ref_bill_id.in_(ov_ids),
                ).delete(synchronize_session=False)
        else:
            db.session.query(StockOut).filter(
                StockOut.refbillid == record.inbillid,
                StockOut.auditflg == "0",
            ).update({"auditflg": "V"})

        record.auditflg = "0"
        record.auditman = None
        record.auditdate = None
        record.opercd = auditor
        record.upddate = dt_parse.now(UTC)
        db.session.commit()
        return {"success": True, "inbillid": record.inbillid}

    @staticmethod
    def void(inbillid: str, operator: str) -> dict[str, object]:
        """作废入库单（仅未审核/已退回可作废）。

        设计原则（见设计文档 §6.5.3）：
        - 草稿入库单可独立作废，不影响已审核的来源出库单
        - 入库单尚未生效（库存未增加），作废不产生库存影响
        - 作废后可手动重新创建
        """
        record = StockInRepository.get_by_id(inbillid)
        if record is None:
            return {"success": False, "error": "入库单不存在"}
        if record.auditflg == "2":
            return {"success": False, "error": "已审核单据不可作废，请先反审核"}
        if record.auditflg == "V":
            return {"success": False, "error": "已作废"}
        # 检查上游 QC：仅已审核入库单作废时拦截（草稿可自由作废）
        if record.auditflg == "2" and record.refbillid and record.refbillid.startswith("QC"):
            from app.models.warehouse import QcResult as Qc
            qc = db.session.get(Qc, record.refbillid)
            if qc and qc.auditflg == "1":
                return {"success": False, "error": "上游 QC 已审核，请先反审核 QC 后再作废"}
        # 服务返还入库：作废时按EID回退 TIT25.in_wh
        if record.invtyp == "3" and record.refbillid:
            from app.models.itsm import AccessoriesUpdate
            in_eids = [d.eid for d in record.details if d.eid]  # type: ignore[attr-defined]
            if in_eids:
                db.session.query(AccessoriesUpdate).filter(
                    AccessoriesUpdate.maintenance_id == record.refbillid,
                    AccessoriesUpdate.old_accessories_id.in_(in_eids),
                ).update({"in_wh": "0"}, synchronize_session=False)
        record.auditflg = "V"
        record.opercd = operator
        db.session.commit()
        return {"success": True, "inbillid": record.inbillid}

    @staticmethod
    def update(
        inbillid: str, operator: str,
        whcd: str = "", memo: str = "", indate: str = "",
        details: list[dict[str, Any]] | None = None,
    ) -> dict[str, object]:
        """编辑入库单（仅未审核/已退回状态可编辑）。"""
        record = StockInRepository.get_by_id(inbillid)
        if record is None:
            return {"success": False, "error": "入库单不存在"}
        if record.auditflg not in ("0", "8"):
            return {"success": False, "error": "仅未审核或已退回的单据可编辑"}
        if details is not None:
            err = StockInService._validate_details(details, record.invtyp or "")
            if err:
                return {"success": False, "error": err}
        # 编辑后重置为未审核
        record.auditflg = "0"
        record.opercd = operator
        if whcd:
            record.whcd = whcd
        if memo:
            record.memo = memo
        if indate:
            record.indate = dt_parse.fromisoformat(indate) if isinstance(indate, str) else indate
        elif not record.indate:
            record.indate = dt_parse.now(UTC)
        # 更新明细
        if details is not None:
            record.details.delete()
            ref_rgstbillid = record.refbillid if record.invtyp in ("1", "4", "5", "8", "9") else None
            for idx, detail_data in enumerate(details, start=1):
                if ref_rgstbillid:
                    detail_data["ref_rgstbillid"] = ref_rgstbillid
                    detail_data["ref_rgstlineno"] = detail_data.get("reflineno")
                StockInRepository.add_detail(
                    inbillid=record.inbillid,
                    whcd=record.whcd,
                    lineno=idx,
                    data=detail_data,
                )
        db.session.commit()
        return {"success": True, "inbillid": record.inbillid}


class StockOutService:
    """出库单服务。"""

    @staticmethod
    def _write_material_consume(record: Any, auditor: str) -> None:
        """OV=8/OV=10 审核后写入 TMS04，同物料多次出库累加 actual_qty。"""
        from app.models.mes import MaterialConsume
        wo_id = getattr(record, "refbillid", None) or record.outbillid
        now_ts = dt_parse.now(UTC)
        for detail_list in [getattr(record, "details_eid", []), getattr(record, "details_prd", [])]:
            for d in detail_list:  # type: ignore[var-annotated]
                dd = d.to_dict() if hasattr(d, "to_dict") else d
                item_cd = dd.get("itemcd", "") if isinstance(dd, dict) else ""
                qty = int(dd.get("outqty", 0) or 0) if isinstance(dd, dict) else 0
                if not item_cd or qty <= 0:
                    continue
                # BOM计划用量：首次领料生产出库时计算，补料或同单EID行沿用计划值
                plan_qty = None
                try:
                    from app.models.mes import WorkOrder
                    wo = db.session.get(WorkOrder, wo_id)
                    if wo:
                        from app.models.master import BomDt
                        bom_row = db.session.query(BomDt).filter(
                            BomDt.bomcd == wo.item_cd, BomDt.itemcd == item_cd,
                        ).first()
                        if bom_row:
                            plan_qty = int((bom_row.bomqty or 0)) * int(wo.plan_qty or 1)
                    # 已有消耗记录但非同一出库单 → 补料，计划用量为0
                    cur_bill = getattr(record, "outbillid", "")
                    if plan_qty and db.session.query(MaterialConsume).filter(
                        MaterialConsume.wo_id == wo_id, MaterialConsume.item_cd == item_cd,
                        MaterialConsume.ref_bill_id != cur_bill,
                    ).first():
                        plan_qty = 0
                except Exception:
                    pass
                # 从物料表获取单位
                unit = None
                try:
                    from app.models.master import Item
                    item = db.session.query(Item.unit).filter(Item.item_cd == item_cd).scalar()
                    unit = item
                except Exception:
                    pass
                cur_bill = getattr(record, "outbillid", "")
                # 消耗类型：按 OV 类型映射
                invtyp = getattr(record, "invtyp", "") or ""
                memo = getattr(record, "memo", "") or ""
                _ct_map = {"7": "3", "9": "4", "6": "6"}  # OV→consume_type
                consume_type = _ct_map.get(invtyp, "2" if "补料" in memo else "1")
                # 查价格：优先采购价(20)，兜底任意有效价格
                unit_cost = None
                try:
                    from app.models.inventory import Price
                    price_rec = db.session.query(Price).filter(
                        Price.itemcd == item_cd, Price.busityp == "20",
                        Price.is_current == True, Price.useflg == "1",
                    ).first()
                    if not price_rec:
                        price_rec = db.session.query(Price).filter(
                            Price.itemcd == item_cd,
                            Price.is_current == True, Price.useflg == "1",
                        ).first()
                    unit_cost = price_rec.itemprice if price_rec else None
                except Exception:
                    pass
                total_cost = unit_cost * qty if unit_cost else None
                # 已有记录则补全价格和消耗类型（补料API先写入时缺价格），否则新建
                existing = db.session.query(MaterialConsume).filter(
                    MaterialConsume.ref_bill_id == cur_bill,
                    MaterialConsume.item_cd == item_cd,
                ).first()
                if existing:
                    existing.actual_qty = (existing.actual_qty or 0) + qty
                    existing.consume_type = consume_type
                    existing.unit_cost = unit_cost
                    existing.total_cost = (existing.total_cost or 0) + (total_cost or 0)
                    existing.plan_qty = plan_qty
                    existing.upddate = now_ts
                else:
                    db.session.add(MaterialConsume(
                        wo_id=wo_id, item_cd=item_cd, plan_qty=plan_qty, actual_qty=qty,
                        unit=unit, warehouse_cd=record.whcd, consume_date=now_ts.date(),
                        consume_type=consume_type, unit_cost=unit_cost, total_cost=total_cost,
                        opercd=auditor, upddate=now_ts,
                        ref_bill_type="OV", ref_bill_id=cur_bill,
                    ))

    @staticmethod
    def list_returnable_orders() -> list[dict[str, Any]]:
        """查询可退货出库的退货单列表。"""
        return StockOutRepository.find_returnable_orders()

    @staticmethod
    def get_returnable_order_lines(pcbillid: str) -> list[dict[str, Any]]:
        """查询某退货单的可退货出库明细行。"""
        return StockOutRepository.get_returnable_order_lines(pcbillid)

    @staticmethod
    def get(outbillid: str) -> dict[str, Any] | None:
        record = StockOutRepository.get_by_id(outbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details_eid"] = [d.to_dict() for d in record.details_eid]  # type: ignore[attr-defined]
        result["details_prd"] = [d.to_dict() for d in record.details_prd]  # type: ignore[attr-defined]
        _enrich_warehouse_names([result])
        _enrich_item_names(result["details_eid"])
        _enrich_item_names(result["details_prd"])

        # 返修出库已审核：补充每行已入库数量，前端据此判断是否显示结案按钮
        if record.invtyp == "9" and record.auditflg == "2":
            from app.models.warehouse import StockIn, StockInDetail
            returned_rows = (
                db.session.query(
                    StockInDetail.reflineno,
                    func.sum(StockInDetail.inqty).label("returned_qty"),
                )
                .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
                .filter(
                    StockIn.invtyp == "9",
                    StockIn.auditflg == "2",
                    StockIn.refbillid == outbillid,
                )
                .group_by(StockInDetail.reflineno)
                .all()
            )
            # 是否已有返修入库记录（至少收过一次货才允许结案）
            result["has_returned"] = len(returned_rows) > 0
            ret_map = {r.reflineno: int(r.returned_qty or 0) for r in returned_rows}
            for d in result["details_eid"]:
                ret = ret_map.get(d.get("lineno"), 0)
                d["returned_qty"] = ret
                d["pending_qty"] = max((d.get("outqty") or 0) - ret, 0)
            for d in result["details_prd"]:
                ret = ret_map.get(d.get("lineno"), 0)
                d["returned_qty"] = ret
                d["pending_qty"] = max((d.get("outqty") or 0) - ret, 0)

        return result

    @staticmethod
    def list_records(
        whcd: str | None = None,
        invtyp: str | None = None,
        auditflg: str | None = None,
        outbillid: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = StockOutRepository.list_by_filters(
            whcd=whcd, invtyp=invtyp, auditflg=auditflg,
            outbillid=outbillid, page=page, per_page=per_page,
        )
        data = [item.to_dict() for item in items]
        _enrich_warehouse_names(data)
        return {
            "items": data,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(
        data: dict[str, Any],
        details_eid: list[dict[str, Any]] | None = None,
        details_prd: list[dict[str, Any]] | None = None,
        creator: str = "",
    ) -> dict[str, Any]:
        # 明细校验（出库不传 invtyp，避免触发入库特有的位置校验）
        all_details = (details_eid or []) + (details_prd or [])
        err = StockInService._validate_details(all_details, "")
        if err:
            return {"success": False, "error": err}
        # 退货出库：如果同一退货单已有未审核草稿，则更新草稿而非新建
        existing_draft = None
        if data.get("invtyp") == "6" and data.get("refbillid"):
            existing_draft = (
                db.session.query(StockOut)
                .filter(
                    StockOut.refbillid == data["refbillid"],
                    StockOut.invtyp == "6",
                    StockOut.auditflg == "0",
                )
                .first()
            )

        if existing_draft:
            existing_draft.whcd = data.get("whcd", existing_draft.whcd)
            existing_draft.suppcd = data.get("suppcd", existing_draft.suppcd)
            if data.get("outdate"):
                existing_draft.outdate = data["outdate"]
            existing_draft.memo = (data.get("memo") or "") + " [手动更新]"
            existing_draft.opercd = creator
            # 替换明细
            existing_draft.details_prd.delete()
            existing_draft.details_eid.delete()
            if details_eid:
                for idx, detail_data in enumerate(details_eid, start=1):
                    StockOutRepository.add_detail_eid(
                        outbillid=existing_draft.outbillid,
                        whcd=existing_draft.whcd, lineno=idx, data=detail_data,
                    )
            if details_prd:
                for idx, detail_data in enumerate(details_prd, start=1):
                    StockOutRepository.add_detail_prd(
                        outbillid=existing_draft.outbillid,
                        whcd=existing_draft.whcd, lineno=idx, data=detail_data,
                    )
            db.session.commit()
            return existing_draft.to_dict()

        # 无草稿则新建
        record = StockOutRepository.create(data, creator)
        if details_eid:
            for idx, detail_data in enumerate(details_eid, start=1):
                StockOutRepository.add_detail_eid(
                    outbillid=record.outbillid, whcd=record.whcd, lineno=idx, data=detail_data,
                )
        if details_prd:
            for idx, detail_data in enumerate(details_prd, start=1):
                StockOutRepository.add_detail_prd(
                    outbillid=record.outbillid, whcd=record.whcd, lineno=idx, data=detail_data,
                )
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def audit(outbillid: str, auditor: str, auditflg: str = "2", checkmemo: str = "") -> dict[str, object]:
        record = StockOutRepository.get_by_id(outbillid)
        if record is None:
            return {"success": False, "error": "出库单不存在"}
        if record.auditflg == "2":
            return {"success": False, "error": "已审核，不可重复审核"}
        # 审核退回（'8'）：仅改状态+备注，不扣库存。清空补料标记允许重新申请
        if auditflg == "8":
            record.auditflg = "8"
            record.auditman = auditor
            record.auditdate = dt_parse.now(UTC)
            if checkmemo:
                record.memo = (record.memo or "") + " [退回: " + checkmemo + "]"
            if record.invtyp == "8":
                from app.models.warehouse import QcResultDt, QcResultEid
                db.session.query(QcResultDt).filter(
                    QcResultDt.replenish_ov_billid == outbillid,
                ).update({"replenish_status": "", "replenish_ov_billid": ""}, synchronize_session=False)
                db.session.query(QcResultEid).filter(
                    QcResultEid.replenish_ov_billid == outbillid,
                ).update({"replenish_status": "", "replenish_ov_billid": ""}, synchronize_session=False)
            db.session.commit()
            return {"success": True, "outbillid": record.outbillid}
        if auditflg != "2":
            return {"success": False, "error": f"不支持的审核动作: {auditflg}"}

        # 库存校验（在标记审核之前，校验失败不污染状态）
        for detail in record.details_prd:  # type: ignore[attr-defined]
            stock = int(
                db.session.query(func.coalesce(func.sum(StockDetail.itemqty), 0))
                .filter(StockDetail.whcd == record.whcd, StockDetail.itemcd == detail.itemcd)
                .scalar() or 0
            )
            if stock < (detail.outqty or 0):
                return {"success": False, "error": f"仓库 {record.whcd} 物料 {detail.itemcd} 库存不足（当前{stock}，需要{detail.outqty}）"}
        for detail in record.details_eid:  # type: ignore[attr-defined]
            if detail.eid:
                from app.models.master import Eid
                eid_wh = (
                    db.session.query(Eid.whcd)
                    .filter(Eid.eid == detail.eid)
                    .scalar()
                )
                if eid_wh and eid_wh != record.whcd:
                    return {"success": False, "error": f"EID {detail.eid} 在 {eid_wh} 仓，不在出库仓库 {record.whcd}，请修改仓库"}
            stock = int(
                db.session.query(func.coalesce(func.sum(StockDetail.itemqty), 0))
                .filter(StockDetail.whcd == record.whcd, StockDetail.itemcd == detail.itemcd)
                .scalar() or 0
            )
            if stock < (detail.outqty or 0):
                return {"success": False, "error": f"仓库 {record.whcd} 物料 {detail.itemcd} 库存不足（当前{stock}，需要{detail.outqty}）"}

        StockOutRepository.audit(record, auditor, auditflg, checkmemo=checkmemo)
        # 审核通过后扣库存
        if auditflg == "2":
            for detail in record.details_eid:  # type: ignore[attr-defined]
                # EID模式：校验该设备是否在出库仓库
                if detail.eid:
                    from app.models.master import Eid
                    eid_wh = (
                        db.session.query(Eid.whcd)
                        .filter(Eid.eid == detail.eid)
                        .scalar()
                    )
                    if eid_wh and eid_wh != record.whcd:
                        return {
                            "success": False,
                            "error": f"EID {detail.eid} 在 {eid_wh} 仓，不在出库仓库 {record.whcd}，请修改仓库",
                        }
                stock = int(
                    db.session.query(func.coalesce(func.sum(StockDetail.itemqty), 0))
                    .filter(
                        StockDetail.whcd == record.whcd,
                        StockDetail.itemcd == detail.itemcd,
                    )
                    .scalar() or 0
                )
                if stock < (detail.outqty or 0):
                    return {
                        "success": False,
                        "error": f"仓库 {record.whcd} 物料 {detail.itemcd} 库存不足（当前{stock}，需要{detail.outqty}）",
                    }

            for detail in record.details_eid:  # type: ignore[attr-defined]
                StockDetailRepository.update_balance(
                    whcd=record.whcd,
                    itemcd=detail.itemcd,
                    qty_delta=-(detail.outqty or 0),
                    operator=auditor,
                    itemtyp=getattr(detail, 'itemtyp', None),
                    prddate=getattr(detail, 'prddate', None),
                )
                StockDetailRepository.add_movement(
                    whcd=record.whcd, itemcd=detail.itemcd,
                    itemqty=-(detail.outqty or 0),
                    billid=record.outbillid, invtyp=record.invtyp or "",
                    iotyp="0", operator=auditor,
                    itemtyp=getattr(detail, 'itemtyp', None),
                    prddate=getattr(detail, 'prddate', None),
                )
                # EID 设备出库
                if detail.eid:
                    from app.models.master import Eid
                    eid_updates: dict[str, Any] = {}
                    if record.invtyp == "2" and getattr(record, "targetwhcd", None):
                        # 服务领用：EID 移到工程师仓，标记持有
                        eid_updates["whcd"] = record.targetwhcd
                        eid_updates["sflg"] = "1"
                    elif record.invtyp == "4":
                        # 借出出库：EID 离库，标记借出中
                        eid_updates["whcd"] = None
                        eid_updates["sflg"] = "6"
                    elif record.invtyp == "7":
                        # 报废出库：EID 标记已报废
                        eid_updates["whcd"] = None
                        eid_updates["sflg"] = "2"
                        eid_updates["qcflg"] = "BF"
                    elif record.invtyp == "9":
                        # 返修出库：EID 离库，标记返修中
                        eid_updates["whcd"] = None
                        eid_updates["sflg"] = "5"
                    elif record.invtyp == "8":
                        # 生产出库：EID 离库，标记生产中
                        eid_updates["whcd"] = None
                        eid_updates["sflg"] = "7"
                    elif record.invtyp == "10":
                        # 翻新出库：旧机 EID 离库，标记翻新中（与生产中共用 sflg='7'）
                        eid_updates["whcd"] = None
                        eid_updates["sflg"] = "7"
                    else:
                        # 其他出库：EID 清空 whcd（离库）
                        eid_updates["whcd"] = None
                    db.session.query(Eid).filter(
                        Eid.itemcd == detail.itemcd, Eid.eid == detail.eid,
                    ).update(eid_updates, synchronize_session=False)
                # 服务领用/调拨：目的仓增加库存
                target_wh = getattr(record, "targetwhcd", None)
                if record.invtyp == "2" and target_wh:
                    StockDetailRepository.update_balance(
                        whcd=target_wh,
                        itemcd=detail.itemcd,
                        qty_delta=(detail.outqty or 0),
                        operator=auditor,
                        itemtyp=getattr(detail, 'itemtyp', None),
                        prddate=getattr(detail, 'prddate', None),
                    )
                    StockDetailRepository.add_movement(
                        whcd=target_wh, itemcd=detail.itemcd,
                        itemqty=(detail.outqty or 0),
                        billid=record.outbillid, invtyp=record.invtyp or "",
                        iotyp="1", operator=auditor,
                        itemtyp=getattr(detail, 'itemtyp', None),
                        prddate=getattr(detail, 'prddate', None),
                    )
            for detail in record.details_prd:  # type: ignore[attr-defined]
                StockDetailRepository.update_balance(
                    whcd=record.whcd,
                    itemcd=detail.itemcd,
                    qty_delta=-(detail.outqty or 0),
                    operator=auditor,
                    itemtyp=getattr(detail, 'itemtyp', None),
                    prddate=getattr(detail, 'prddate', None),
                )
                StockDetailRepository.add_movement(
                    whcd=record.whcd, itemcd=detail.itemcd,
                    itemqty=-(detail.outqty or 0),
                    billid=record.outbillid, invtyp=record.invtyp or "",
                    iotyp="0", operator=auditor,
                    itemtyp=getattr(detail, 'itemtyp', None),
                    prddate=getattr(detail, 'prddate', None),
                )
                # 服务领用/调拨：目的仓增加库存
                target_wh = getattr(record, "targetwhcd", None)
                if record.invtyp == "2" and target_wh:
                    StockDetailRepository.update_balance(
                        whcd=target_wh,
                        itemcd=detail.itemcd,
                        qty_delta=(detail.outqty or 0),
                        operator=auditor,
                        itemtyp=getattr(detail, 'itemtyp', None),
                        prddate=getattr(detail, 'prddate', None),
                    )
                    StockDetailRepository.add_movement(
                        whcd=target_wh, itemcd=detail.itemcd,
                        itemqty=(detail.outqty or 0),
                        billid=record.outbillid, invtyp=record.invtyp or "",
                        iotyp="1", operator=auditor,
                        itemtyp=getattr(detail, 'itemtyp', None),
                        prddate=getattr(detail, 'prddate', None),
                    )
                # EID 设备出库
                eid_val = getattr(detail, 'eid', None)
                if eid_val:
                    from app.models.master import Eid
                    eid_updates: dict[str, Any] = {}
                    if record.invtyp == "2" and getattr(record, "targetwhcd", None):
                        eid_updates["whcd"] = record.targetwhcd
                        eid_updates["sflg"] = "1"
                    elif record.invtyp == "4":
                        eid_updates["whcd"] = None
                        eid_updates["sflg"] = "6"
                    elif record.invtyp == "7":
                        eid_updates["whcd"] = None
                        eid_updates["sflg"] = "2"
                        eid_updates["qcflg"] = "BF"
                    elif record.invtyp == "9":
                        eid_updates["whcd"] = None
                        eid_updates["sflg"] = "5"  # 返修中
                    elif record.invtyp == "8":
                        eid_updates["whcd"] = None
                        eid_updates["sflg"] = "7"  # 生产中
                    else:
                        eid_updates["whcd"] = None
                    db.session.query(Eid).filter(
                        Eid.itemcd == detail.itemcd, Eid.eid == eid_val,
                    ).update(eid_updates, synchronize_session=False)
            # P1-3: 退货出库审核通过 → 更新退货单状态
            if record.invtyp == "6" and record.refbillid:
                from app.models.procurement import ReturnPurchaseBill
                db.session.query(ReturnPurchaseBill).filter(
                    ReturnPurchaseBill.pcbillid == record.refbillid,
                    ReturnPurchaseBill.auditflg != "2",
                ).update(
                    {"auditflg": "2"},
                    synchronize_session=False,
                )
        # P0: 调拨出库审核通过 → 自动生成调拨入库草稿
        if record.invtyp == "3" and getattr(record, "targetwhcd", None):
            from app.models.warehouse import StockOutDetailPrd as OutPrd, StockOutDetailEid as OutEid
            in_details = []
            for d in record.details_prd:
                dd = d.to_dict()
                in_details.append({
                    "itemcd": dd.get("itemcd"), "inqty": dd.get("outqty", 0),
                    "reflineno": dd.get("lineno"),
                })
            for d in record.details_eid:
                dd = d.to_dict()
                in_details.append({
                    "itemcd": dd.get("itemcd"), "inqty": dd.get("outqty", 0),
                    "eid": dd.get("eid"), "reflineno": dd.get("lineno"),
                })
            if in_details:
                StockInService.create(
                    data={
                        "invtyp": "4",
                        "refbillid": record.outbillid,
                        "whcd": record.targetwhcd,
                    },
                    details=in_details,
                    creator=auditor,
                    _commit=False,  # 由外层 audit 统一提交，保证原子性
                )
        # 返修出库审核通过 → 自动生成返修入库草稿（保留EID和批次信息）
        if record.invtyp == "9":
            in_details = []
            for d in record.details_eid:  # type: ignore[attr-defined]
                dd = d.to_dict()
                in_details.append({
                    "itemcd": dd.get("itemcd"), "inqty": dd.get("outqty", 0),
                    "eid": dd.get("eid"), "reflineno": dd.get("lineno"),
                })
            for d in record.details_prd:  # type: ignore[attr-defined]
                dd = d.to_dict()
                in_details.append({
                    "itemcd": dd.get("itemcd"), "inqty": dd.get("outqty", 0),
                    "reflineno": dd.get("lineno"),
                    **({"prddate": dd["prddate"]} if dd.get("prddate") else {}),
                })
            if in_details:
                StockInService.create(
                    data={
                        "invtyp": "9",
                        "refbillid": record.outbillid,
                        "whcd": record.whcd,
                    },
                    details=in_details,
                    creator=auditor,
                    _commit=False,
                )
        # 生产出库审核 → 写入 TMS04，并推进工单到生产中。
        # IV=8 成品入库由 FQC 审核 GA/GB/GC 后生成，避免未质检即入库。
        if record.invtyp == "8":
            # OV=8 → TMS04 + 推进工单到生产中 + 标记补料完成
            StockOutService._write_material_consume(record, auditor)
            # 补料 OV=8 审核通过 → 标记 QC 明细行补料完成
            from app.models.warehouse import QcResultDt, QcResultEid
            db.session.query(QcResultDt).filter(
                QcResultDt.replenish_ov_billid == record.outbillid,
            ).update({"replenish_status": "completed"}, synchronize_session=False)
            db.session.query(QcResultEid).filter(
                QcResultEid.replenish_ov_billid == record.outbillid,
            ).update({"replenish_status": "completed"}, synchronize_session=False)
            if record.refbillid:
                from app.models.mes import WorkOrder
                wo = db.session.get(WorkOrder, record.refbillid)
                if wo and wo.status in ("PICKING", "RELEASED"):
                    wo.status = "IN_PROGRESS"
                    wo.actual_start = dt_parse.now(UTC).date()
        # OV=10 → TMS04
        if record.invtyp == "10":
            StockOutService._write_material_consume(record, auditor)
        # OV=6/7/9 不良品出库审核 → TMS04（IV审核时不再写入，改在此处写入）
        if record.invtyp in ("6", "7", "9"):
            StockOutService._write_material_consume(record, auditor)
        # OV=5 质检出库审核：不在此生成 IV=11。
        # IV=11 在 QC 结果审核时按判定生成（仅 C1 合格物料入库）。
        # 销售出库审核通过 → 自动生成销售退货入库草稿
        if record.invtyp == "1":
            in_details = []
            for d in record.details_eid:  # type: ignore[attr-defined]
                dd = d.to_dict()
                in_details.append({
                    "itemcd": dd.get("itemcd"), "inqty": dd.get("outqty", 0),
                    "eid": dd.get("eid"), "reflineno": dd.get("lineno"),
                })
            for d in record.details_prd:  # type: ignore[attr-defined]
                dd = d.to_dict()
                in_details.append({
                    "itemcd": dd.get("itemcd"), "inqty": dd.get("outqty", 0),
                    "reflineno": dd.get("lineno"),
                    **({
                        "prddate": dd["prddate"]
                    } if dd.get("prddate") else {}),
                })
            if in_details:
                StockInService.create(
                    data={
                        "invtyp": "2",
                        "refbillid": record.outbillid,
                        "whcd": record.whcd,  # 退货入库仓库与出库仓库相同
                    },
                    details=in_details,
                    creator=auditor,
                    _commit=False,
                )
        db.session.commit()
        return {"success": True, "outbillid": record.outbillid}


    @staticmethod
    def unaudit(outbillid: str, auditor: str) -> dict[str, object]:
        """反审核出库单：回退库存、清理TMS04、重置EID状态。"""
        record = StockOutRepository.get_by_id(outbillid)
        if record is None:
            return {"success": False, "error": "出库单不存在"}
        if record.auditflg != "2":
            return {"success": False, "error": "仅已审核单据可反审核"}

        # 回退库存 eid
        for detail in record.details_eid:
            StockDetailRepository.update_balance(
                whcd=record.whcd, itemcd=detail.itemcd,
                qty_delta=(detail.outqty or 0), operator=auditor,
                itemtyp=getattr(detail, 'itemtyp', None),
                prddate=getattr(detail, 'prddate', None),
            )
            if detail.eid:
                from app.models.master import Eid
                db.session.query(Eid).filter(
                    Eid.itemcd == detail.itemcd, Eid.eid == detail.eid,
                ).update({"whcd": record.whcd, "sflg": "1", "qcflg": None}, synchronize_session=False)
        # 回退库存 prd
        for detail in record.details_prd:
            StockDetailRepository.update_balance(
                whcd=record.whcd, itemcd=detail.itemcd,
                qty_delta=(detail.outqty or 0), operator=auditor,
                itemtyp=getattr(detail, 'itemtyp', None),
                prddate=getattr(detail, 'prddate', None),
            )
            eid_val = getattr(detail, 'eid', None)
            if eid_val:
                from app.models.master import Eid
                db.session.query(Eid).filter(
                    Eid.itemcd == detail.itemcd, Eid.eid == eid_val,
                ).update({"whcd": record.whcd, "sflg": "1", "qcflg": None}, synchronize_session=False)

        # 清除 TMS04
        from app.models.mes import MaterialConsume
        db.session.query(MaterialConsume).filter(
            MaterialConsume.ref_bill_id == outbillid,
        ).delete(synchronize_session=False)

        # OV=8 清除补料标记
        if record.invtyp == "8":
            from app.models.warehouse import QcResultDt, QcResultEid
            db.session.query(QcResultDt).filter(
                QcResultDt.replenish_ov_billid == outbillid,
            ).update({"replenish_status": "", "replenish_ov_billid": ""}, synchronize_session=False)
            db.session.query(QcResultEid).filter(
                QcResultEid.replenish_ov_billid == outbillid,
            ).update({"replenish_status": "", "replenish_ov_billid": ""}, synchronize_session=False)

        record.auditflg = "0"
        record.auditman = None
        record.auditdate = None
        record.opercd = auditor
        record.upddate = dt_parse.now(UTC)
        db.session.commit()
        return {"success": True, "outbillid": record.outbillid}

    @staticmethod
    def void(outbillid: str, operator: str) -> dict[str, object]:
        """作废出库单（仅未审核/已退回可作废）。

        设计原则（见设计文档 §6.5.3）：
        - 出库单草稿作废时，关联入库单尚未自动生成（审核才生成），无需联动
        - 出库单已审核不可作废，需走反审核流程
        - 关联入库单草稿应独立作废，不影响已审核的出库单
        """
        record = StockOutRepository.get_by_id(outbillid)
        if record is None:
            return {"success": False, "error": "出库单不存在"}
        if record.auditflg == "2":
            return {"success": False, "error": "已审核单据不可作废，请先反审核"}
        if record.auditflg == "V":
            return {"success": False, "error": "已作废"}
        # 检查上游 QC：仅已审核出库单作废时拦截（草稿可自由作废）
        if record.auditflg == "2" and record.refbillid and record.refbillid.startswith("QC"):
            from app.models.warehouse import QcResult as Qc
            qc = db.session.get(Qc, record.refbillid)
            if qc and qc.auditflg == "1":
                return {"success": False, "error": "上游 QC 已审核，请先反审核 QC 后再作废"}
        # 边界保护：如有关联入库单且已审核，不可作废（库存已入，防止孤立已审核入库单）
        from app.models.warehouse import StockIn as StockInModel
        linked_audited = db.session.query(StockInModel).filter(
            StockInModel.refbillid == record.outbillid,
            StockInModel.invtyp.in_(["2", "4", "8", "9", "11"]),
            StockInModel.auditflg == "2",
        ).first()
        if linked_audited:
            return {"success": False, "error": f"关联入库单 {linked_audited.inbillid} 已审核且库存已入，不可作废"}
        record.auditflg = "V"
        record.opercd = operator
        # 补料出库单作废 → 清空 QC 明细行的补料标记 + 清除 TMS04
        if record.invtyp == "8":
            from app.models.warehouse import QcResultDt, QcResultEid
            from app.models.mes import MaterialConsume
            db.session.query(QcResultDt).filter(
                QcResultDt.replenish_ov_billid == outbillid,
            ).update({"replenish_status": "", "replenish_ov_billid": ""}, synchronize_session=False)
            db.session.query(QcResultEid).filter(
                QcResultEid.replenish_ov_billid == outbillid,
            ).update({"replenish_status": "", "replenish_ov_billid": ""}, synchronize_session=False)
            db.session.query(MaterialConsume).filter(
                MaterialConsume.ref_bill_id == outbillid,
            ).delete(synchronize_session=False)
        db.session.commit()
        return {"success": True, "outbillid": record.outbillid}

    @staticmethod
    def close_lines(
        outbillid: str,
        lines: list[dict[str, Any]],
        reason: str,
        operator: str,
    ) -> dict[str, object]:
        """出库单行级结案（标记指定明细行不再等待入库）。

        lines 格式: [{"lineno": 1, "type": "eid"}, {"lineno": 5, "type": "prd"}]
        仅已审核的出库单才允许行级结案。
        """
        from app.models.warehouse import StockOutDetailEid, StockOutDetailPrd

        record = StockOutRepository.get_by_id(outbillid)
        if record is None:
            return {"success": False, "error": "出库单不存在"}
        if record.auditflg != "2":
            return {"success": False, "error": "仅已审核的出库单可进行行级结案"}

        now = dt_parse.now(UTC)
        closed_count = 0
        for line in lines:
            lineno = line.get("lineno")
            line_type = line.get("type", "")
            if lineno is None:
                continue
            if line_type == "eid":
                detail = db.session.query(StockOutDetailEid).filter(
                    StockOutDetailEid.outbillid == outbillid,
                    StockOutDetailEid.lineno == lineno,
                ).first()
            elif line_type == "prd":
                detail = db.session.query(StockOutDetailPrd).filter(
                    StockOutDetailPrd.outbillid == outbillid,
                    StockOutDetailPrd.lineno == lineno,
                ).first()
            else:
                continue
            if detail and getattr(detail, "closed_flg", "0") != "1":
                detail.closed_flg = "1"
                detail.closed_reason = reason
                detail.closed_by = operator
                detail.closed_at = now
                closed_count += 1

        # TODO: 当前草稿复用机制下（同 refbillid+invtyp 只有一张草稿），
        # 操作员手动新建 IV=9 会更新而非新建，草稿审核后不存在待清理的草稿，
        # 因此以下 draft cleanup 逻辑在当前流程中极少触发。
        # 保留作为极端情况兜底（如并发创建绕过草稿复用），后续评估是否简化。
        if closed_count > 0:
            from app.models.warehouse import StockIn, StockInDetail
            closed_linenos = {
                line.get("lineno") for line in lines
                if line.get("lineno") is not None
            }
            # 查找关联的 IV=9 未审核草稿
            drafts = db.session.query(StockIn).filter(
                StockIn.refbillid == outbillid,
                StockIn.invtyp == "9",
                StockIn.auditflg.in_(["0", "8"]),  # 草稿或退回
            ).all()
            voided_drafts: list[str] = []
            cleaned_lines = 0
            for draft in drafts:
                # 删除草稿中 reflineno 匹配已结案行的明细
                to_delete = db.session.query(StockInDetail).filter(
                    StockInDetail.inbillid == draft.inbillid,
                    StockInDetail.reflineno.in_(closed_linenos),
                ).all()
                for td in to_delete:
                    db.session.delete(td)
                    cleaned_lines += 1
                # 如果草稿明细被删光，自动作废
                remaining = db.session.query(StockInDetail).filter(
                    StockInDetail.inbillid == draft.inbillid,
                    ~StockInDetail.reflineno.in_(closed_linenos),
                ).count()
                if remaining == 0:
                    draft.auditflg = "V"
                    voided_drafts.append(draft.inbillid)

        # 结案EID行时同步更新设备状态为已报废（确认不返修 = 报废处理）
        if closed_count > 0:
            from app.models.warehouse import StockOutDetailEid as OutEid
            from app.models.master import Eid as EidModel
            for line in lines:
                if line.get("type") != "eid":
                    continue
                eid_row = db.session.query(OutEid).filter(
                    OutEid.outbillid == outbillid,
                    OutEid.lineno == line.get("lineno"),
                ).first()
                if eid_row and eid_row.eid:
                    db.session.query(EidModel).filter(
                        EidModel.itemcd == eid_row.itemcd,
                        EidModel.eid == eid_row.eid,
                    ).update({
                        "sflg": "2",     # 已报废
                        "qcflg": "BF",   # 报废
                        "whcd": None,
                    }, synchronize_session=False)

        db.session.commit()
        result: dict[str, object] = {
            "success": True, "outbillid": outbillid, "closed_count": closed_count,
        }
        if closed_count > 0 and voided_drafts:
            result["voided_drafts"] = voided_drafts
        if closed_count > 0 and cleaned_lines:
            result["cleaned_lines"] = cleaned_lines
        return result

    @staticmethod
    def update(
        outbillid: str, operator: str,
        whcd: str = "", memo: str = "", outdate: str = "",
        details_eid: list[dict[str, Any]] | None = None,
        details_prd: list[dict[str, Any]] | None = None,
    ) -> dict[str, object]:
        """编辑出库单（仅未审核/已退回可编辑）。"""
        record = StockOutRepository.get_by_id(outbillid)
        if record is None:
            return {"success": False, "error": "出库单不存在"}
        if record.auditflg not in ("0", "8"):
            return {"success": False, "error": "仅未审核或已退回的单据可编辑"}
        if details_eid is not None or details_prd is not None:
            all_details = (details_eid or []) + (details_prd or [])
            err = StockInService._validate_details(all_details, "")
            if err:
                return {"success": False, "error": err}
        record.auditflg = "0"
        record.opercd = operator
        if whcd: record.whcd = whcd
        if memo: record.memo = memo
        if outdate: record.outdate = dt_parse.fromisoformat(outdate) if isinstance(outdate, str) else outdate
        if details_eid is not None or details_prd is not None:
            record.details_eid.delete()
            record.details_prd.delete()
            if details_eid:
                for idx, d in enumerate(details_eid, start=1):
                    StockOutRepository.add_detail_eid(outbillid=record.outbillid, whcd=record.whcd, lineno=idx, data=d)
            if details_prd:
                for idx, d in enumerate(details_prd, start=1):
                    StockOutRepository.add_detail_prd(outbillid=record.outbillid, whcd=record.whcd, lineno=idx, data=d)
        db.session.commit()
        return {"success": True, "outbillid": record.outbillid}


class StockBalanceService:
    """库存查询服务。"""

    @staticmethod
    def get_balance(whcd: str, itemcd: str) -> dict[str, Any]:
        qty = StockDetailRepository.get_balance(whcd, itemcd)
        return {"whcd": whcd, "itemcd": itemcd, "quantity": qty}

    @staticmethod
    def list_stock(
        whcd: str,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = StockDetailRepository.list_by_warehouse(
            whcd=whcd, page=page, per_page=per_page
        )
        data = [item.to_dict() for item in items]
        _enrich_warehouse_names(data)
        _enrich_item_names(data)
        return {
            "items": data,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def list_movements(
        whcd: str | None = None,
        itemcd: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        billid: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """查询 TWH12 库存流水。"""
        from app.models.warehouse import StockDetailDt

        query = db.session.query(StockDetailDt).filter(StockDetailDt.useflg == "1")
        if whcd:
            query = query.filter(StockDetailDt.whcd == whcd)
        if itemcd:
            query = query.filter(StockDetailDt.itemcd == itemcd)
        if start_date:
            query = query.filter(StockDetailDt.gendate >= start_date)
        if end_date:
            query = query.filter(StockDetailDt.gendate <= end_date + " 23:59:59")
        if billid:
            query = query.filter(StockDetailDt.billid.ilike(f"%{billid}%"))
        total = query.count()
        items = query.order_by(StockDetailDt.gendate.desc()).offset((page - 1) * per_page).limit(per_page).all()
        data = [item.to_dict() for item in items]
        _enrich_warehouse_names(data)
        _enrich_item_names(data)
        return {"items": data, "total": total, "page": page, "per_page": per_page}

    @staticmethod
    def inventory_summary(whcd: str | None = None, period: str = "", page: int = 1, per_page: int = 20) -> dict[str, Any]:
        """收发存汇总。按仓库×物料×月份聚合 TWH12 变动数据。"""
        from app.models.warehouse import StockDetailDt
        from sqlalchemy import case

        if period:
            try:
                pd = dt_parse.strptime(period, "%Y-%m")
            except ValueError:
                pd = dt_parse.now()
        else:
            pd = dt_parse.now()

        start_date = pd.replace(day=1)
        if pd.month == 12:
            end_date = pd.replace(year=pd.year + 1, month=1, day=1)
        else:
            end_date = pd.replace(month=pd.month + 1, day=1)

        # 本期变动
        month_q = db.session.query(
            StockDetailDt.whcd, StockDetailDt.itemcd,
            func.sum(case((StockDetailDt.iotyp == "1", StockDetailDt.itemqty), else_=0)).label("in_qty"),
            func.sum(case((StockDetailDt.iotyp == "0", func.abs(StockDetailDt.itemqty)), else_=0)).label("out_qty"),
        ).filter(
            StockDetailDt.useflg == "1",
            StockDetailDt.gendate >= start_date,
            StockDetailDt.gendate < end_date,
        ).group_by(StockDetailDt.whcd, StockDetailDt.itemcd).subquery()

        # 期初库存（月初之前的累计净变动）
        begin_q = db.session.query(
            StockDetailDt.whcd, StockDetailDt.itemcd,
            func.coalesce(func.sum(StockDetailDt.itemqty), 0).label("begin_qty"),
        ).filter(
            StockDetailDt.useflg == "1",
            StockDetailDt.gendate < start_date,
        ).group_by(StockDetailDt.whcd, StockDetailDt.itemcd).subquery()

        q = db.session.query(
            month_q.c.whcd, month_q.c.itemcd,
            func.coalesce(begin_q.c.begin_qty, 0).label("begin_qty"),
            month_q.c.in_qty, month_q.c.out_qty,
            (func.coalesce(begin_q.c.begin_qty, 0) + month_q.c.in_qty - month_q.c.out_qty).label("end_qty"),
        ).outerjoin(
            begin_q,
            (month_q.c.whcd == begin_q.c.whcd) & (month_q.c.itemcd == begin_q.c.itemcd),
        )
        if whcd:
            q = q.filter(month_q.c.whcd == whcd)
        total = q.count()
        rows = q.order_by(month_q.c.whcd, month_q.c.itemcd).offset((page - 1) * per_page).limit(per_page).all()

        data = [
            {
                "whcd": r.whcd, "itemcd": r.itemcd,
                "begin_qty": float(r.begin_qty or 0),
                "in_qty": float(r.in_qty or 0), "out_qty": float(r.out_qty or 0),
                "end_qty": float(r.end_qty or 0),
            }
            for r in rows
        ]
        _enrich_warehouse_names(data)
        _enrich_item_names(data)
        return {"items": data, "total": total, "page": page, "per_page": per_page, "period": period or pd.strftime("%Y-%m")}

    @staticmethod
    def daily_snapshot(whcd: str | None = None, date_str: str = "", page: int = 1, per_page: int = 20) -> dict[str, Any]:
        """库存日报。从 TWH12 取当日变动聚合。"""
        from app.models.warehouse import StockDetailDt
        from sqlalchemy import case
        from datetime import timedelta

        if date_str:
            try:
                target_date = dt_parse.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                target_date = dt_parse.now()
        else:
            target_date = dt_parse.now()

        next_date = target_date + timedelta(days=1)

        q = db.session.query(
            StockDetailDt.whcd, StockDetailDt.itemcd,
            func.sum(case((StockDetailDt.iotyp == "1", StockDetailDt.itemqty), else_=0)).label("in_qty"),
            func.sum(case((StockDetailDt.iotyp == "0", func.abs(StockDetailDt.itemqty)), else_=0)).label("out_qty"),
        ).filter(
            StockDetailDt.useflg == "1",
            StockDetailDt.gendate >= target_date,
            StockDetailDt.gendate < next_date,
        )
        if whcd:
            q = q.filter(StockDetailDt.whcd == whcd)
        q = q.group_by(StockDetailDt.whcd, StockDetailDt.itemcd)

        total = q.count()
        rows = q.order_by(StockDetailDt.whcd, StockDetailDt.itemcd).offset((page - 1) * per_page).limit(per_page).all()

        # 当日末库存快照（从 TWH11）
        from app.models.warehouse import StockDetail as SD
        item_keys = {(r.whcd, r.itemcd) for r in rows}
        snap_map = {}
        if item_keys:
            for sd_row in db.session.query(SD).filter(
                SD.whcd.in_([k[0] for k in item_keys])
            ).all():
                snap_map[(sd_row.whcd, sd_row.itemcd)] = sd_row.itemqty or 0

        data = [
            {
                "whcd": r.whcd, "itemcd": r.itemcd,
                "in_qty": float(r.in_qty or 0), "out_qty": float(r.out_qty or 0),
                "snapshot_qty": int(snap_map.get((r.whcd, r.itemcd), 0)),
            }
            for r in rows
        ]
        _enrich_warehouse_names(data)
        _enrich_item_names(data)
        return {"items": data, "total": total, "page": page, "per_page": per_page, "date": target_date.strftime("%Y-%m-%d")}

    @staticmethod
    def inventory_aging(whcd: str | None = None, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        """库龄分析：首次入库天数（简化方案，非 FIFO 批次库龄）。"""
        from app.models.warehouse import StockDetail, StockDetailDt

        now = dt_parse.now()
        first_in = db.session.query(
            StockDetailDt.whcd, StockDetailDt.itemcd,
            func.min(StockDetailDt.gendate).label("first_in_date"),
        ).filter(
            StockDetailDt.useflg == "1", StockDetailDt.iotyp == "1"
        ).group_by(StockDetailDt.whcd, StockDetailDt.itemcd).subquery()

        q = db.session.query(
            StockDetail.whcd, StockDetail.itemcd, StockDetail.itemqty,
            first_in.c.first_in_date,
        ).outerjoin(
            first_in,
            (StockDetail.whcd == first_in.c.whcd) & (StockDetail.itemcd == first_in.c.itemcd),
        ).filter(StockDetail.itemqty > 0)
        if whcd:
            q = q.filter(StockDetail.whcd == whcd)

        total = q.count()
        rows = q.order_by(StockDetail.whcd, StockDetail.itemcd).offset((page - 1) * per_page).limit(per_page).all()

        data: list[dict[str, Any]] = []
        for r in rows:
            days = (now - r.first_in_date).days if r.first_in_date else None
            data.append({
                "whcd": r.whcd, "itemcd": r.itemcd, "itemqty": r.itemqty,
                "first_in": r.first_in_date.strftime("%Y-%m-%d") if r.first_in_date else None,
                "age_days": days,
                "note": "首次入库天数（非FIFO批次库龄）",
            })
        _enrich_warehouse_names(data)
        _enrich_item_names(data)
        return {"items": data, "total": total, "page": page, "per_page": per_page}


# ---------------------------------------------------------------------------
# 资产盘点
# ---------------------------------------------------------------------------


class AssetCheckService:
    """资产盘点（twh19_asset_c_a / twh20_asset_c_a_dtl）业务编排。"""

    @staticmethod
    def get(opbillid: str) -> dict[str, Any] | None:
        record = AssetCheckRepository.get_by_id(opbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [
            d.to_dict() for d in record.details.filter_by(useflg="1").all()
        ]
        return result

    @staticmethod
    def list_records(
        page: int = 1, per_page: int = 20, useflg: str | None = "1"
    ) -> dict[str, Any]:
        items, total = AssetCheckRepository.list_all(
            page=page, per_page=per_page, useflg=useflg
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        details_data = data.pop("details", [])
        record = AssetCheckRepository.create(data, creator)
        for detail in details_data:
            AssetCheckRepository.add_detail(record.opbillid, detail)
        return record.to_dict()

    @staticmethod
    def update(opbillid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = AssetCheckRepository.get_by_id(opbillid)
        if record is None:
            return None
        record = AssetCheckRepository.update(record, data)
        return record.to_dict()

    @staticmethod
    def audit(opbillid: str, auditor: str) -> dict[str, object] | None:
        record = AssetCheckRepository.get_by_id(opbillid)
        if record is None:
            return None
        record = AssetCheckRepository.audit(record, auditor)
        return record.to_dict()


# ---------------------------------------------------------------------------
# POS设备变更
# ---------------------------------------------------------------------------


class PosChangeService:
    """POS设备变更（twh21_pos_change / twh22_pos_change_dt）业务编排。"""

    @staticmethod
    def get(pk: int) -> dict[str, Any] | None:
        record = PosChangeRepository.get_by_id(pk)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [
            d.to_dict() for d in record.details.filter_by(useflg="1").all()
        ]
        return result

    @staticmethod
    def list_records(
        page: int = 1, per_page: int = 20, useflg: str | None = "1"
    ) -> dict[str, Any]:
        items, total = PosChangeRepository.list_all(
            page=page, per_page=per_page, useflg=useflg
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        details_data = data.pop("details", [])
        record = PosChangeRepository.create(data, creator)
        for detail in details_data:
            PosChangeRepository.add_detail(record.id, detail)
        return record.to_dict()

    @staticmethod
    def update(pk: int, data: dict[str, Any]) -> dict[str, Any] | None:
        record = PosChangeRepository.get_by_id(pk)
        if record is None:
            return None
        record = PosChangeRepository.update(record, data)
        return record.to_dict()


class TransferAccountService:
    """调拨科目服务（TTX01_TXKMG）。"""

    @staticmethod
    def get(txkno: str) -> dict[str, Any] | None:
        record = TransferAccountRepository.get_by_id(txkno)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_records(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = TransferAccountRepository.list_all(page=page, per_page=per_page)
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = TransferAccountRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(txkno: str, data: dict[str, Any], updator: str) -> dict[str, Any] | None:
        record = TransferAccountRepository.get_by_id(txkno)
        if record is None:
            return None
        TransferAccountRepository.update(record, data, updator)
        db.session.commit()
        return record.to_dict()


class OverLostService:
    """盘盈盘亏业务服务（TWH17_OVERLOST + TWH18 明细）。"""

    @staticmethod
    def get(olbillid: str) -> dict[str, Any] | None:
        record = OverLostRepository.get_by_id(olbillid)
        if record is None:
            return None
        result = record.to_dict()
        _enrich_warehouse_names([result])
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        result["details_eid"] = [d.to_dict() for d in record.details_eid]  # type: ignore[attr-defined]
        return result

    @staticmethod
    def list_records(
        whcd: str | None = None,
        oltyp: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = OverLostRepository.list_by_filters(
            whcd=whcd, oltyp=oltyp, auditflg=auditflg, page=page, per_page=per_page
        )
        data = [item.to_dict() for item in items]
        _enrich_warehouse_names(data)
        return {
            "items": data,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(
        data: dict[str, Any],
        details: list[dict[str, Any]],
        eid_details: list[dict[str, Any]],
        creator: str,
    ) -> dict[str, Any]:
        record = OverLostRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            OverLostRepository.add_detail(
                olbillid=record.olbillid, lineno=idx, data=detail_data
            )
        for idx, eid_data in enumerate(eid_details, start=1):
            OverLostRepository.add_eid_detail(
                olbillid=record.olbillid, lineno=idx, data=eid_data
            )
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def audit(olbillid: str, auditor: str) -> dict[str, object]:
        record = OverLostRepository.get_by_id(olbillid)
        if record is None:
            return {"success": False, "error": "盘点单不存在"}
        if record.auditflg == "1":
            return {"success": False, "error": "已审核"}
        OverLostRepository.audit(record, auditor)
        db.session.commit()
        return {"success": True, "olbillid": record.olbillid}
