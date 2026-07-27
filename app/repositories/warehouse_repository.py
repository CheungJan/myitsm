"""仓储管理数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func

from app.extensions import db
from app.repositories.procurement_repository import _gen_master_id

from app.models.warehouse import (
    AssetCheckAccept,
    AssetCheckAcceptDtl,
    OverLost,
    OverLostDt,
    OverLostEid,
    PosChange,
    PosChangeDt,
    StockDetail,
    StockIn,
    StockInDetail,
    StockOut,
    StockOutDetailEid,
    StockOutDetailPrd,
    TransferAccount,
    Warehouse,
)


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


class WarehouseRepository:
    """仓库主数据访问。"""

    @staticmethod
    def get_by_id(whcd: str) -> Warehouse | None:
        return db.session.get(Warehouse, whcd)

    @staticmethod
    def list_all(useflg: str | None = None) -> list[Warehouse]:
        query = db.session.query(Warehouse)
        if useflg is not None:
            query = query.filter(Warehouse.useflg == useflg)
        return query.order_by(Warehouse.whcd).all()

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> Warehouse:
        now = datetime.now(UTC)
        record = Warehouse(
            opercd=creator,
            gendate=now,
            upddate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: Warehouse, data: dict[str, Any]) -> Warehouse:
        for key, value in data.items():
            setattr(record, key, value)
        record.upddate = datetime.now(UTC)
        return record


class StockInRepository:
    """入库单数据访问。"""

    @staticmethod
    def get_by_id(inbillid: str) -> StockIn | None:
        return db.session.get(StockIn, inbillid)

    @staticmethod
    def list_by_filters(
        whcd: str | None = None,
        invtyp: str | None = None,
        auditflg: str | None = None,
        inbillid: str | None = None,
        indate_from: str | None = None,
        indate_to: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[StockIn], int]:
        query = db.session.query(StockIn)
        if whcd:
            query = query.filter(StockIn.whcd == whcd)
        if invtyp:
            query = query.filter(StockIn.invtyp == invtyp)
        if auditflg:
            query = query.filter(StockIn.auditflg == auditflg)
        if inbillid:
            query = query.filter(StockIn.inbillid.like(f"%{inbillid}%"))
        if indate_from:
            query = query.filter(StockIn.indate >= indate_from)
        if indate_to:
            from sqlalchemy import func, Date
            query = query.filter(func.date(StockIn.indate) <= indate_to)
        query = query.order_by(desc(db.func.substring(StockIn.inbillid, 3).cast(db.Integer)))
        total: int = query.count()
        items: list[StockIn] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> StockIn:
        now = datetime.now(UTC)
        data.setdefault("indate", now)
        record = StockIn(
            inbillid=_gen_master_id("IN", "入库单号"),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail(
        inbillid: str,
        whcd: str,
        lineno: int,
        data: dict[str, Any],
    ) -> StockInDetail:
        record = StockInDetail(
            inbillid=inbillid,
            whcd=whcd,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def audit(record: StockIn, auditor: str) -> StockIn:
        record.auditflg = "2"  # 对齐 PB: 0=未审, 1=在审, 2=已审
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        return record

    @staticmethod
    def find_receivable_orders() -> list[dict[str, Any]]:
        """查询可入库的采购订单（已审核且有未入库数量）。"""
        from app.models.procurement import PurchaseRegister, PurchaseRegisterDt
        from app.models.master import Supplier

        # 仅统计已审核入库的数量（排除草稿）
        sub = (
            db.session.query(
                StockInDetail.ref_rgstbillid,
                StockInDetail.reflineno,
                func.sum(StockInDetail.inqty).label("received_qty"),
            )
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(
                StockInDetail.ref_rgstbillid.isnot(None),
                StockIn.auditflg == "2",
            )
            .group_by(StockInDetail.ref_rgstbillid, StockInDetail.reflineno)
            .subquery()
        )

        rows = (
            db.session.query(
                PurchaseRegister.rgstbillid,
                PurchaseRegister.rgstdate,
                PurchaseRegister.suppliercd,
                Supplier.supp_nm,
                func.count(func.distinct(PurchaseRegisterDt.lineno)).label("total_lines"),
                func.sum(
                    PurchaseRegisterDt.rgsqty - func.coalesce(sub.c.received_qty, 0)
                ).label("total_receivable"),
            )
            .join(PurchaseRegisterDt, PurchaseRegister.rgstbillid == PurchaseRegisterDt.rgstbillid)
            .outerjoin(Supplier, PurchaseRegister.suppliercd == Supplier.supp_cd)
            .outerjoin(
                sub,
                (sub.c.ref_rgstbillid == PurchaseRegisterDt.rgstbillid)
                & (sub.c.reflineno == PurchaseRegisterDt.lineno),
            )
            .filter(
                PurchaseRegister.auditflg == "2",
                ~PurchaseRegister.useflg.in_(["9", "V"]),  # 排除已作废，兼容旧系统 useflg='2'
                PurchaseRegisterDt.rgsqty > func.coalesce(sub.c.received_qty, 0),
            )
            .group_by(
                PurchaseRegister.rgstbillid,
                PurchaseRegister.rgstdate,
                PurchaseRegister.suppliercd,
                Supplier.supp_nm,
            )
            .order_by(PurchaseRegister.rgstdate.desc(), PurchaseRegister.rgstbillid.desc())
            .all()
        )

        return [
            {
                "rgstbillid": r.rgstbillid,
                "rgstdate": r.rgstdate.isoformat() if r.rgstdate else "",
                "suppliercd": r.suppliercd,
                "supp_nm": r.supp_nm,
                "total_lines": r.total_lines,
                "total_receivable": int(r.total_receivable or 0),
            }
            for r in rows
        ]

    @staticmethod
    def get_receivable_order_lines(rgstbillid: str) -> list[dict[str, Any]]:
        """查询某采购订单的可入库明细行（含已入库量和可入库量）。"""
        from app.models.procurement import PurchaseRegisterDt
        from app.models.master import Item

        # 仅统计已审核入库的数量（排除草稿）
        sub = (
            db.session.query(
                StockInDetail.ref_rgstbillid,
                StockInDetail.reflineno,
                func.sum(StockInDetail.inqty).label("received_qty"),
            )
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(
                StockInDetail.ref_rgstbillid == rgstbillid,
                StockIn.auditflg == "2",
            )
            .group_by(StockInDetail.ref_rgstbillid, StockInDetail.reflineno)
            .subquery()
        )

        rows = (
            db.session.query(
                PurchaseRegisterDt.lineno,
                PurchaseRegisterDt.itemcd,
                Item.item_nm,
                PurchaseRegisterDt.rgsqty,
                func.coalesce(sub.c.received_qty, 0).label("received_qty"),
                (PurchaseRegisterDt.rgsqty - func.coalesce(sub.c.received_qty, 0)).label(
                    "receivable_qty"
                ),
                PurchaseRegisterDt.units,
            )
            .outerjoin(Item, PurchaseRegisterDt.itemcd == Item.item_cd)
            .outerjoin(
                sub,
                (sub.c.ref_rgstbillid == PurchaseRegisterDt.rgstbillid)
                & (sub.c.reflineno == PurchaseRegisterDt.lineno),
            )
            .filter(
                PurchaseRegisterDt.rgstbillid == rgstbillid,
                PurchaseRegisterDt.rgsqty > func.coalesce(sub.c.received_qty, 0),
            )
            .order_by(PurchaseRegisterDt.lineno)
            .all()
        )

        return [
            {
                "lineno": r.lineno,
                "itemcd": r.itemcd,
                "item_nm": r.item_nm,
                "rgsqty": r.rgsqty,
                "received_qty": int(r.received_qty or 0),
                "receivable_qty": int(r.receivable_qty or 0),
                "units": r.units,
            }
            for r in rows
        ]

    @staticmethod
    def find_service_returnable_items() -> list[dict[str, Any]]:
        """查询 ITMS 工单中可返还的自有资产旧配件（asset_owner != '01' 且未入库）。"""
        from app.models.itsm import AccessoriesUpdate

        rows = (
            db.session.query(
                AccessoriesUpdate.maintenance_id,
                AccessoriesUpdate.device_id,
                AccessoriesUpdate.old_accessories_id,
                AccessoriesUpdate.accessories_type,
                AccessoriesUpdate.create_time,
                AccessoriesUpdate.engineer_id,
                AccessoriesUpdate.c_type,
            )
            .filter(
                AccessoriesUpdate.old_accessories_id.isnot(None),
                AccessoriesUpdate.old_accessories_id != "",
                AccessoriesUpdate.in_wh.is_distinct_from("1"),
                AccessoriesUpdate.in_wh.is_distinct_from("2"),  # 已标记不入库
            )
            .order_by(AccessoriesUpdate.create_time.desc())
            .all()
        )

        if not rows:
            return []

        # 收集所有旧配件EID，查EID表获取物料编码和资产归属
        eids = list({r.old_accessories_id for r in rows if r.old_accessories_id})
        eid_map: dict[str, dict[str, Any]] = {}
        if eids:
            from app.models.master import Eid as EidModel, Item
            # 排除客户资产 + 排除耗材
            eid_rows = (
                db.session.query(EidModel)
                .filter(
                    EidModel.eid.in_(eids),
                    EidModel.asset_owner != "01",
                )
                .all()
            )
            for e in eid_rows:
                eid_map[e.eid] = {"itemcd": e.itemcd, "asset_owner": e.asset_owner}

            # 耗材列表（consume='1'的物料不需要返还入库）
            if eid_rows:
                itemcds = {e.itemcd for e in eid_rows}
                consumable_items = {
                    r[0] for r in db.session.query(Item.item_cd)
                    .filter(Item.item_cd.in_(itemcds), Item.consume == "1")
                    .all()
                }
            else:
                consumable_items = set()

        result: dict[str, dict[str, Any]] = {}
        for r in rows:
            eid_info = eid_map.get(r.old_accessories_id)
            if not eid_info:
                continue  # 跳过客户资产或未知EID
            # 跳过耗材
            if eid_info.get("itemcd") in consumable_items:
                continue
            # 推导 changetype（PB usp_itsm_trans_in 逻辑）
            prefix = (r.maintenance_id or "")[:2]
            ct_map = {"MD": "更换", "MO": "整机", "MR": "调换", "MC": "取回"}
            changetype = ct_map.get(prefix, "")

            key = r.maintenance_id
            if key not in result:
                result[key] = {
                    "maintenance_id": r.maintenance_id,
                    "create_time": r.create_time.isoformat() if r.create_time else "",
                    "engineer_id": r.engineer_id,
                    "c_type": r.c_type or "",
                    "changetype": changetype,
                    "items": [],
                }
            result[key]["items"].append({
                "eid": r.old_accessories_id,
                "itemcd": eid_info["itemcd"],
                "device_id": r.device_id,
                "accessories_type": r.accessories_type,
            })

        return sorted(result.values(), key=lambda x: x["create_time"], reverse=True)

    @staticmethod
    def find_transferable_orders() -> list[dict[str, Any]]:
        """查询可调拨入库的调拨出库单（已审核且有未入库数量）。"""
        rows = (
            db.session.query(
                StockOut.outbillid,
                StockOut.whcd,
                StockOut.targetwhcd,
                StockOut.gendate,
            )
            .filter(
                StockOut.invtyp == "3",
                StockOut.auditflg == "2",
                StockOut.targetwhcd.isnot(None),
            )
            .order_by(StockOut.gendate.desc())
            .all()
        )

        result = []
        for r in rows:
            # 汇总出库数量（PRD + EID）
            out_qty = int(
                db.session.query(func.coalesce(func.sum(StockOutDetailPrd.outqty), 0))
                .filter(StockOutDetailPrd.outbillid == r.outbillid)
                .scalar() or 0
            ) + int(
                db.session.query(func.coalesce(func.sum(StockOutDetailEid.outqty), 0))
                .filter(StockOutDetailEid.outbillid == r.outbillid)
                .scalar() or 0
            )
            # 汇总已入库数量
            in_qty = int(
                db.session.query(func.coalesce(func.sum(StockInDetail.inqty), 0))
                .join(StockIn, StockIn.inbillid == StockInDetail.inbillid)
                .filter(
                    StockIn.refbillid == r.outbillid,
                    StockIn.invtyp == "4",
                    StockIn.auditflg == "2",
                )
                .scalar() or 0
            )
            if out_qty > in_qty:
                result.append({
                    "outbillid": r.outbillid,
                    "source_whcd": r.whcd,
                    "target_whcd": r.targetwhcd,
                    "total_out": out_qty,
                    "total_in": in_qty,
                    "pending": out_qty - in_qty,
                })

        return result


    @staticmethod
    def find_lendable_orders() -> list[dict[str, Any]]:
        """查询可归还的借出出库单（已审核且未完全归还）。"""
        prd_agg = (
            db.session.query(
                StockOutDetailPrd.outbillid,
                func.coalesce(func.sum(StockOutDetailPrd.outqty), 0).label("prd_qty"),
            )
            .group_by(StockOutDetailPrd.outbillid)
            .subquery()
        )
        eid_agg = (
            db.session.query(
                StockOutDetailEid.outbillid,
                func.coalesce(func.sum(StockOutDetailEid.outqty), 0).label("eid_qty"),
            )
            .group_by(StockOutDetailEid.outbillid)
            .subquery()
        )
        returned_sub = (
            db.session.query(
                StockIn.refbillid,
                func.sum(StockInDetail.inqty).label("returned_qty"),
            )
            .join(StockInDetail, StockIn.inbillid == StockInDetail.inbillid)
            .filter(StockIn.invtyp == "5", StockIn.auditflg == "2")
            .group_by(StockIn.refbillid)
            .subquery()
        )

        rows = (
            db.session.query(
                StockOut.outbillid, StockOut.whcd,
                (func.coalesce(prd_agg.c.prd_qty, 0) + func.coalesce(eid_agg.c.eid_qty, 0)).label("total_out"),
                func.coalesce(returned_sub.c.returned_qty, 0).label("returned"),
            )
            .outerjoin(prd_agg, StockOut.outbillid == prd_agg.c.outbillid)
            .outerjoin(eid_agg, StockOut.outbillid == eid_agg.c.outbillid)
            .outerjoin(returned_sub, StockOut.outbillid == returned_sub.c.refbillid)
            .filter(StockOut.invtyp == "4", StockOut.auditflg == "2")
            .all()
        )

        result: list[dict[str, Any]] = []
        for r in rows:
            pending = int(r.total_out) - int(r.returned)
            if pending > 0:
                result.append({
                    "outbillid": r.outbillid, "whcd": r.whcd,
                    "total_out": int(r.total_out), "returned": int(r.returned), "pending": pending,
                })
        return result

    @staticmethod
    def get_lendable_order_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某借出出库单中尚未归还的明细行。"""
        from app.models.warehouse import StockOutDetailEid, StockOutDetailPrd

        # 已归还的明细（批次）
        returned_prd_sub = (
            db.session.query(
                StockInDetail.reflineno,
                func.sum(StockInDetail.inqty).label("returned_qty"),
            )
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(
                StockIn.invtyp == "5",
                StockIn.auditflg == "2",
                StockIn.refbillid == outbillid,
            )
            .group_by(StockInDetail.reflineno)
            .subquery()
        )

        # 批次明细（未归还部分）
        prd_rows = (
            db.session.query(
                StockOutDetailPrd.lineno,
                StockOutDetailPrd.itemcd,
                StockOutDetailPrd.outqty.label("out_qty"),
                func.coalesce(returned_prd_sub.c.returned_qty, 0).label("returned_qty"),
                (StockOutDetailPrd.outqty - func.coalesce(returned_prd_sub.c.returned_qty, 0)).label("pending"),
            )
            .outerjoin(
                returned_prd_sub,
                returned_prd_sub.c.reflineno == StockOutDetailPrd.lineno,
            )
            .filter(
                StockOutDetailPrd.outbillid == outbillid,
                StockOutDetailPrd.outqty > func.coalesce(returned_prd_sub.c.returned_qty, 0),
            )
            .order_by(StockOutDetailPrd.lineno)
            .all()
        )

        # EID 明细（未归还部分，按 itemcd 汇总）
        eid_returned_sub = (
            db.session.query(
                StockInDetail.eid,
                func.sum(StockInDetail.inqty).label("returned_qty"),
            )
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(
                StockIn.invtyp == "5",
                StockIn.auditflg == "2",
                StockIn.refbillid == outbillid,
            )
            .group_by(StockInDetail.eid)
            .subquery()
        )

        eid_rows = (
            db.session.query(
                StockOutDetailEid.lineno,
                StockOutDetailEid.itemcd,
                StockOutDetailEid.eid,
                StockOutDetailEid.outqty.label("out_qty"),
                func.coalesce(eid_returned_sub.c.returned_qty, 0).label("returned_qty"),
                (StockOutDetailEid.outqty - func.coalesce(eid_returned_sub.c.returned_qty, 0)).label("pending"),
            )
            .outerjoin(
                eid_returned_sub,
                eid_returned_sub.c.eid == StockOutDetailEid.eid,
            )
            .filter(
                StockOutDetailEid.outbillid == outbillid,
                StockOutDetailEid.outqty > func.coalesce(eid_returned_sub.c.returned_qty, 0),
            )
            .order_by(StockOutDetailEid.lineno)
            .all()
        )

        result: list[dict[str, Any]] = []
        for r in prd_rows:
            result.append({
                "lineno": r.lineno, "itemcd": r.itemcd, "eid": "",
                "out_qty": r.out_qty, "pending": r.pending,
            })
        for r in eid_rows:
            result.append({
                "lineno": r.lineno, "itemcd": r.itemcd, "eid": r.eid or "",
                "out_qty": r.out_qty, "pending": r.pending,
            })
        return result

    @staticmethod
    def find_repair_returnable_orders() -> list[dict[str, Any]]:
        """查询可返修入库的返修出库单（已审核且未完全入库，排除已结案行）。"""
        # 出库总量：PRD 和 EID 分别汇总后相加，排除已结案行
        prd_agg = (
            db.session.query(
                StockOutDetailPrd.outbillid,
                func.coalesce(func.sum(StockOutDetailPrd.outqty), 0).label("prd_qty"),
            )
            .filter(StockOutDetailPrd.closed_flg != "1")
            .group_by(StockOutDetailPrd.outbillid)
            .subquery()
        )
        eid_agg = (
            db.session.query(
                StockOutDetailEid.outbillid,
                func.coalesce(func.sum(StockOutDetailEid.outqty), 0).label("eid_qty"),
            )
            .filter(StockOutDetailEid.closed_flg != "1")
            .group_by(StockOutDetailEid.outbillid)
            .subquery()
        )
        # 已入库量
        returned_sub = (
            db.session.query(
                StockIn.refbillid,
                func.sum(StockInDetail.inqty).label("returned_qty"),
            )
            .join(StockInDetail, StockIn.inbillid == StockInDetail.inbillid)
            .filter(StockIn.invtyp == "9", StockIn.auditflg == "2")
            .group_by(StockIn.refbillid)
            .subquery()
        )

        rows = (
            db.session.query(
                StockOut.outbillid, StockOut.whcd,
                (func.coalesce(prd_agg.c.prd_qty, 0) + func.coalesce(eid_agg.c.eid_qty, 0)).label("total_out"),
                func.coalesce(returned_sub.c.returned_qty, 0).label("returned"),
            )
            .outerjoin(prd_agg, StockOut.outbillid == prd_agg.c.outbillid)
            .outerjoin(eid_agg, StockOut.outbillid == eid_agg.c.outbillid)
            .outerjoin(returned_sub, StockOut.outbillid == returned_sub.c.refbillid)
            .filter(StockOut.invtyp == "9", StockOut.auditflg == "2")
            .all()
        )

        result: list[dict[str, Any]] = []
        for r in rows:
            pending = int(r.total_out) - int(r.returned)
            if pending > 0:
                result.append({
                    "outbillid": r.outbillid, "whcd": r.whcd,
                    "total_out": int(r.total_out), "returned": int(r.returned), "pending": pending,
                })
        return result

    @staticmethod
    def get_repair_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某返修出库单中尚未入库的明细行（保留原始模式：EID行逐条、批次行逐条）。"""
        from app.models.warehouse import StockOutDetailEid as OutEid, StockOutDetailPrd as OutPrd

        # 已入库明细（按 reflineno 匹配）
        returned_eid = (
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "9", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno)
        )
        ret_eid_map = dict(returned_eid.all())
        returned_prd = (
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "9", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno)
        )
        ret_prd_map = dict(returned_prd.all())

        result: list[dict[str, Any]] = []
        # EID明细：逐条返回
        eid_rows = (
            db.session.query(OutEid.lineno, OutEid.itemcd, OutEid.eid, OutEid.outqty, OutEid.itemtyp)
            .filter(OutEid.outbillid == outbillid, OutEid.closed_flg != "1")
            .order_by(OutEid.lineno)
            .all()
        )
        for r in eid_rows:
            ret_qty = ret_eid_map.get(r.lineno, 0)
            pending = (r.outqty or 0) - int(ret_qty or 0)
            if pending > 0:
                result.append({
                    "opt": "eid",
                    "lineno": r.lineno,
                    "itemcd": r.itemcd,
                    "eid": r.eid or "",
                    "out_qty": r.outqty or 1,
                    "pending": pending,
                })
        # 批次明细：逐条返回
        prd_rows = (
            db.session.query(OutPrd.lineno, OutPrd.itemcd, OutPrd.outqty, OutPrd.itemtyp, OutPrd.prddate)
            .filter(OutPrd.outbillid == outbillid, OutPrd.closed_flg != "1")
            .order_by(OutPrd.lineno)
            .all()
        )
        for r in prd_rows:
            ret_qty = ret_prd_map.get(r.lineno, 0)
            pending = (r.outqty or 0) - int(ret_qty or 0)
            if pending > 0:
                result.append({
                    "opt": "prd",
                    "lineno": r.lineno,
                    "itemcd": r.itemcd,
                    "out_qty": r.outqty or 1,
                    "pending": pending,
                    "itemtyp": r.itemtyp or "",
                    "prddate": r.prddate.isoformat() if r.prddate else "",
                })
        return result

    @staticmethod
    def find_production_returnable_orders() -> list[dict[str, Any]]:
        """查询可生产入库的生产出库单（已审核且未完全入库）。"""
        prd_agg = (
            db.session.query(StockOutDetailPrd.outbillid, func.coalesce(func.sum(StockOutDetailPrd.outqty), 0).label("prd_qty"))
            .group_by(StockOutDetailPrd.outbillid).subquery()
        )
        eid_agg = (
            db.session.query(StockOutDetailEid.outbillid, func.coalesce(func.sum(StockOutDetailEid.outqty), 0).label("eid_qty"))
            .group_by(StockOutDetailEid.outbillid).subquery()
        )
        returned_sub = (
            db.session.query(StockIn.refbillid, func.sum(StockInDetail.inqty).label("returned_qty"))
            .join(StockInDetail, StockIn.inbillid == StockInDetail.inbillid)
            .filter(StockIn.invtyp == "8", StockIn.auditflg == "2")
            .group_by(StockIn.refbillid).subquery()
        )
        rows = (
            db.session.query(
                StockOut.outbillid, StockOut.whcd,
                (func.coalesce(prd_agg.c.prd_qty, 0) + func.coalesce(eid_agg.c.eid_qty, 0)).label("total_out"),
                func.coalesce(returned_sub.c.returned_qty, 0).label("returned"),
            )
            .outerjoin(prd_agg, StockOut.outbillid == prd_agg.c.outbillid)
            .outerjoin(eid_agg, StockOut.outbillid == eid_agg.c.outbillid)
            .outerjoin(returned_sub, StockOut.outbillid == returned_sub.c.refbillid)
            .filter(StockOut.invtyp == "8", StockOut.auditflg == "2")
            .all()
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            pending = int(r.total_out) - int(r.returned)
            if pending > 0:
                result.append({
                    "outbillid": r.outbillid, "whcd": r.whcd,
                    "total_out": int(r.total_out), "returned": int(r.returned), "pending": pending,
                })
        return result

    @staticmethod
    def get_production_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某生产出库单中尚未入库的明细行（保留原始模式）。"""
        from app.models.warehouse import StockOutDetailEid as OutEid, StockOutDetailPrd as OutPrd

        returned_eid = (
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "8", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno)
        )
        ret_eid_map = dict(returned_eid.all())
        returned_prd = dict(
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "8", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno).all()
        )

        result: list[dict[str, Any]] = []
        eid_rows = (
            db.session.query(OutEid.lineno, OutEid.itemcd, OutEid.eid, OutEid.outqty, OutEid.itemtyp)
            .filter(OutEid.outbillid == outbillid, OutEid.closed_flg != "1").order_by(OutEid.lineno).all()
        )
        for r in eid_rows:
            pending = (r.outqty or 0) - int(ret_eid_map.get(r.lineno, 0) or 0)
            if pending > 0:
                result.append({"opt": "eid", "lineno": r.lineno, "itemcd": r.itemcd, "eid": r.eid or "", "out_qty": r.outqty or 1, "pending": pending})
        prd_rows = (
            db.session.query(OutPrd.lineno, OutPrd.itemcd, OutPrd.outqty, OutPrd.itemtyp, OutPrd.prddate)
            .filter(OutPrd.outbillid == outbillid, OutPrd.closed_flg != "1").order_by(OutPrd.lineno).all()
        )
        for r in prd_rows:
            pending = (r.outqty or 0) - int(returned_prd.get(r.lineno, 0) or 0)
            if pending > 0:
                result.append({"opt": "prd", "lineno": r.lineno, "itemcd": r.itemcd, "out_qty": r.outqty or 1, "pending": pending, "itemtyp": r.itemtyp or "", "prddate": r.prddate.isoformat() if r.prddate else ""})
        return result


    @staticmethod
    def find_renovation_returnable_orders() -> list[dict[str, Any]]:
        """查询可翻新入库的翻新出库单（OV=10，已审核且未完全入库，供 IV=6 选单）。"""
        prd_agg = (
            db.session.query(StockOutDetailPrd.outbillid, func.coalesce(func.sum(StockOutDetailPrd.outqty), 0).label("prd_qty"))
            .filter(StockOutDetailPrd.closed_flg != "1")
            .group_by(StockOutDetailPrd.outbillid).subquery()
        )
        eid_agg = (
            db.session.query(StockOutDetailEid.outbillid, func.coalesce(func.sum(StockOutDetailEid.outqty), 0).label("eid_qty"))
            .filter(StockOutDetailEid.closed_flg != "1")
            .group_by(StockOutDetailEid.outbillid).subquery()
        )
        returned_sub = (
            db.session.query(StockIn.refbillid, func.sum(StockInDetail.inqty).label("returned_qty"))
            .join(StockInDetail, StockIn.inbillid == StockInDetail.inbillid)
            .filter(StockIn.invtyp == "6", StockIn.auditflg == "2")
            .group_by(StockIn.refbillid).subquery()
        )
        rows = (
            db.session.query(
                StockOut.outbillid, StockOut.whcd, StockOut.outdate,
                (func.coalesce(prd_agg.c.prd_qty, 0) + func.coalesce(eid_agg.c.eid_qty, 0)).label("total_out"),
                func.coalesce(returned_sub.c.returned_qty, 0).label("returned"),
            )
            .outerjoin(prd_agg, StockOut.outbillid == prd_agg.c.outbillid)
            .outerjoin(eid_agg, StockOut.outbillid == eid_agg.c.outbillid)
            .outerjoin(returned_sub, StockOut.outbillid == returned_sub.c.refbillid)
            .filter(StockOut.invtyp == "10", StockOut.auditflg == "2")
            .all()
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            pending = int(r.total_out) - int(r.returned)
            if pending > 0:
                result.append({
                    "outbillid": r.outbillid, "whcd": r.whcd,
                    "outdate": r.outdate.isoformat() if r.outdate else "",
                    "total_out": int(r.total_out), "returned": int(r.returned), "pending": pending,
                })
        return result

    @staticmethod
    def get_renovation_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某翻新出库单中尚未入库的明细行（供 IV=6 选择）。"""
        from app.models.warehouse import StockOutDetailEid as OutEid, StockOutDetailPrd as OutPrd
        ret_eid_map = dict(
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "6", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno).all()
        )
        ret_prd_map = dict(
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "6", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno).all()
        )
        result: list[dict[str, Any]] = []
        eid_rows = (
            db.session.query(OutEid.lineno, OutEid.itemcd, OutEid.eid, OutEid.outqty, OutEid.itemtyp)
            .filter(OutEid.outbillid == outbillid, OutEid.closed_flg != "1").order_by(OutEid.lineno).all()
        )
        for r in eid_rows:
            pending = (r.outqty or 0) - int(ret_eid_map.get(r.lineno, 0) or 0)
            if pending > 0:
                result.append({"opt": "eid", "lineno": r.lineno, "itemcd": r.itemcd, "eid": r.eid or "", "out_qty": r.outqty or 1, "pending": pending, "itemtyp": r.itemtyp or ""})
        prd_rows = (
            db.session.query(OutPrd.lineno, OutPrd.itemcd, OutPrd.outqty, OutPrd.itemtyp, OutPrd.prddate)
            .filter(OutPrd.outbillid == outbillid, OutPrd.closed_flg != "1").order_by(OutPrd.lineno).all()
        )
        for r in prd_rows:
            pending = (r.outqty or 0) - int(ret_prd_map.get(r.lineno, 0) or 0)
            if pending > 0:
                result.append({"opt": "prd", "lineno": r.lineno, "itemcd": r.itemcd, "out_qty": r.outqty or 1, "pending": pending, "itemtyp": r.itemtyp or "", "prddate": r.prddate.isoformat() if r.prddate else ""})
        return result

    @staticmethod
    def find_qc_returnable_orders() -> list[dict[str, Any]]:
        """查询可质检入库的质检出库单（IV=11，已审核且未完全入库）。"""
        prd_agg = (
            db.session.query(StockOutDetailPrd.outbillid, func.coalesce(func.sum(StockOutDetailPrd.outqty), 0).label("prd_qty"))
            .filter(StockOutDetailPrd.closed_flg != "1")
            .group_by(StockOutDetailPrd.outbillid).subquery()
        )
        eid_agg = (
            db.session.query(StockOutDetailEid.outbillid, func.coalesce(func.sum(StockOutDetailEid.outqty), 0).label("eid_qty"))
            .filter(StockOutDetailEid.closed_flg != "1")
            .group_by(StockOutDetailEid.outbillid).subquery()
        )
        returned_sub = (
            db.session.query(StockIn.refbillid, func.sum(StockInDetail.inqty).label("returned_qty"))
            .join(StockInDetail, StockIn.inbillid == StockInDetail.inbillid)
            .filter(StockIn.invtyp == "11", StockIn.auditflg == "2")
            .group_by(StockIn.refbillid).subquery()
        )
        rows = (
            db.session.query(
                StockOut.outbillid, StockOut.whcd, StockOut.outdate,
                (func.coalesce(prd_agg.c.prd_qty, 0) + func.coalesce(eid_agg.c.eid_qty, 0)).label("total_out"),
                func.coalesce(returned_sub.c.returned_qty, 0).label("returned"),
            )
            .outerjoin(prd_agg, StockOut.outbillid == prd_agg.c.outbillid)
            .outerjoin(eid_agg, StockOut.outbillid == eid_agg.c.outbillid)
            .outerjoin(returned_sub, StockOut.outbillid == returned_sub.c.refbillid)
            .filter(StockOut.invtyp == "5", StockOut.auditflg == "2")
            .all()
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            pending = int(r.total_out) - int(r.returned)
            if pending > 0:
                result.append({
                    "outbillid": r.outbillid, "whcd": r.whcd,
                    "outdate": r.outdate.isoformat() if r.outdate else "",
                    "total_out": int(r.total_out), "returned": int(r.returned), "pending": pending,
                })
        return result

    @staticmethod
    def get_qc_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某质检出库单中尚未入库的明细行（供 IV=11 质检入库选择）。"""
        from app.models.warehouse import StockOutDetailEid as OutEid, StockOutDetailPrd as OutPrd
        ret_eid_map = dict(
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "11", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno).all()
        )
        ret_prd_map = dict(
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "11", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno).all()
        )
        result: list[dict[str, Any]] = []
        eid_rows = (
            db.session.query(OutEid.lineno, OutEid.itemcd, OutEid.eid, OutEid.outqty, OutEid.itemtyp)
            .filter(OutEid.outbillid == outbillid, OutEid.closed_flg != "1").order_by(OutEid.lineno).all()
        )
        for r in eid_rows:
            pending = (r.outqty or 0) - int(ret_eid_map.get(r.lineno, 0) or 0)
            if pending > 0:
                result.append({"opt": "eid", "lineno": r.lineno, "itemcd": r.itemcd, "eid": r.eid or "", "out_qty": r.outqty or 1, "pending": pending, "itemtyp": r.itemtyp or ""})
        prd_rows = (
            db.session.query(OutPrd.lineno, OutPrd.itemcd, OutPrd.outqty, OutPrd.itemtyp, OutPrd.prddate)
            .filter(OutPrd.outbillid == outbillid, OutPrd.closed_flg != "1").order_by(OutPrd.lineno).all()
        )
        for r in prd_rows:
            pending = (r.outqty or 0) - int(ret_prd_map.get(r.lineno, 0) or 0)
            if pending > 0:
                result.append({"opt": "prd", "lineno": r.lineno, "itemcd": r.itemcd, "out_qty": r.outqty or 1, "pending": pending, "itemtyp": r.itemtyp or "", "prddate": r.prddate.isoformat() if r.prddate else ""})
        return result

    @staticmethod
    def find_ov5_for_qc() -> list[dict[str, Any]]:
        """查询还有未QC物料的 OV=5 质检出库单。"""
        from sqlalchemy import text
        sql = text("""
            SELECT o.outbillid, o.whcd, o.refbillid, o.gendate,
                   COALESCE(SUM(d.outqty), 0) as total_out,
                   COALESCE(qc_done.qc_qty, 0) as qc_done_qty
            FROM twh15_out o
            JOIN twh16_outdtprd d ON o.outbillid = d.outbillid
            LEFT JOIN (
                SELECT q.refbillid, SUM(COALESCE(dt.qcqty, 0) + COALESCE(eid.qcqty, 0)) as qc_qty
                FROM tqc10_result q
                LEFT JOIN tqc11_resultdt dt ON q.qcbillid = dt.qcbillid
                LEFT JOIN tqc11_resulteid eid ON q.qcbillid = eid.qcbillid
                WHERE q.auditflg = '1'
                GROUP BY q.refbillid
            ) qc_done ON o.outbillid = qc_done.refbillid
            WHERE o.invtyp = '5' AND o.auditflg = '2'
            GROUP BY o.outbillid, o.whcd, o.refbillid, o.gendate, qc_done.qc_qty
            HAVING COALESCE(SUM(d.outqty), 0) > COALESCE(qc_done.qc_qty, 0)
            ORDER BY o.gendate DESC
            LIMIT 200
        """)
        rows = db.session.execute(sql).fetchall()
        return [{"outbillid": r.outbillid, "whcd": r.whcd, "refbillid": r.refbillid or "",
                 "gendate": r.gendate.isoformat() if r.gendate else ""} for r in rows]

    def find_qc_out_pending_orders() -> list[dict[str, Any]]:
        """查询已审核采购入库单（invtyp=1）可供质检出库选单（OV=5）。

        条件：
        1. 入库单已审核（auditflg='2'）且为采购入库（invtyp='1'）
        2. 该入库单尚未被质检出库（OV=5）完全引用
        """
        from sqlalchemy import text

        # 简化查询：找出所有已审核采购入库单，排除已被完全引用的
        sql = text("""
            WITH in_summary AS (
                -- 计算每个入库单的总入库数量（按入库单汇总）
                SELECT inbillid, COALESCE(SUM(inqty), 0) AS total_in_qty
                FROM twh14_checkindt
                GROUP BY inbillid
            ),
            out_summary AS (
                -- 按明细行 ref_inbillid 汇总（支持多入库单合并出库）
                SELECT d.ref_inbillid AS inbillid, COALESCE(SUM(d.outqty), 0) AS total_out_qty
                FROM twh16_outdteid d
                JOIN twh15_out o ON d.outbillid = o.outbillid
                WHERE o.invtyp = '5' AND o.auditflg IN ('0', '2') AND d.ref_inbillid IS NOT NULL
                GROUP BY d.ref_inbillid
                UNION ALL
                SELECT p.ref_inbillid AS inbillid, COALESCE(SUM(p.outqty), 0) AS total_out_qty
                FROM twh16_outdtprd p
                JOIN twh15_out o ON p.outbillid = o.outbillid
                WHERE o.invtyp = '5' AND o.auditflg IN ('0', '2') AND p.ref_inbillid IS NOT NULL
                GROUP BY p.ref_inbillid
            ),
            out_agg AS (
                -- 合并EID和批次出库数量
                SELECT inbillid, SUM(total_out_qty) AS total_out_qty
                FROM out_summary
                GROUP BY inbillid
            ),
            pending_orders AS (
                -- 找出还有剩余数量的入库单
                SELECT i.inbillid
                FROM in_summary i
                LEFT JOIN out_agg o ON i.inbillid = o.inbillid
                WHERE i.total_in_qty > COALESCE(o.total_out_qty, 0)
            )
            -- 主查询：获取入库单详情
            SELECT i.inbillid, i.whcd, i.indate, i.refbillid
            FROM twh13_in i
            JOIN pending_orders p ON i.inbillid = p.inbillid
            WHERE i.invtyp = '1' AND i.auditflg = '2'
            ORDER BY i.gendate DESC, i.inbillid DESC
            LIMIT 300
        """)

        rows = db.session.execute(sql).fetchall()

        return [
            {
                "inbillid": r.inbillid,
                "whcd": r.whcd,
                "indate": r.indate.isoformat() if r.indate else "",
                "refbillid": r.refbillid or "",
            }
            for r in rows
        ]

    @staticmethod
    def get_qc_pending_lines(inbillid: str) -> list[dict[str, Any]]:
        """查询某采购入库单的物料明细（供 OV=5 质检出库选择）。

        返回该入库单下的所有物料明细，qty 已扣除草稿+已审核的 OV=5 占用量。
        """
        from app.models.master import Item
        from sqlalchemy import text

        # 查询入库单信息
        stock_in = db.session.get(StockIn, inbillid)
        if not stock_in:
            return []

        whcd = stock_in.whcd

        # ---- 已占用汇总（按来源入库单行号，只计草稿+已审核） ----
        reserved_sql = text("""
            SELECT d.ref_inbillid AS inbillid, d.reflineno, COALESCE(SUM(d.outqty), 0) AS used_qty
            FROM twh16_outdtprd d
            JOIN twh15_out o ON d.outbillid = o.outbillid
            WHERE d.ref_inbillid = :inbillid AND o.invtyp = '5' AND o.auditflg IN ('0', '2')
            GROUP BY d.ref_inbillid, d.reflineno
            UNION ALL
            SELECT d.ref_inbillid AS inbillid, d.reflineno, COALESCE(SUM(d.outqty), 0) AS used_qty
            FROM twh16_outdteid d
            JOIN twh15_out o ON d.outbillid = o.outbillid
            WHERE d.ref_inbillid = :inbillid AND o.invtyp = '5' AND o.auditflg IN ('0', '2')
            GROUP BY d.ref_inbillid, d.reflineno
        """)
        reserved_rows = db.session.execute(reserved_sql, {"inbillid": inbillid}).fetchall()
        # 合并 UNION ALL 结果（EID + 批次）
        reserved_map: dict[int, int] = {}
        for rr in reserved_rows:
            reserved_map[rr.reflineno] = reserved_map.get(rr.reflineno, 0) + int(rr.used_qty)

        # 查询EID明细
        eid_rows = (
            db.session.query(
                StockInDetail.lineno,
                StockInDetail.itemcd,
                StockInDetail.inqty,
                StockInDetail.eid,
                StockInDetail.itemtyp,
                StockInDetail.prddate,
                Item.item_nm,
            )
            .outerjoin(Item, StockInDetail.itemcd == Item.item_cd)
            .filter(
                StockInDetail.inbillid == inbillid,
                StockInDetail.eid.isnot(None),
            )
            .all()
        )

        # 查询批次明细
        prd_rows = (
            db.session.query(
                StockInDetail.lineno,
                StockInDetail.itemcd,
                StockInDetail.inqty,
                StockInDetail.itemtyp,
                StockInDetail.prddate,
                Item.item_nm,
            )
            .outerjoin(Item, StockInDetail.itemcd == Item.item_cd)
            .filter(
                StockInDetail.inbillid == inbillid,
                StockInDetail.eid.is_(None),
            )
            .all()
        )

        result: list[dict[str, Any]] = []

        # EID行
        for r in eid_rows:
            used = reserved_map.get(r.lineno, 0)
            remain = max(int(r.inqty or 0) - used, 0)
            result.append({
                "opt": "eid",
                "lineno": r.lineno,
                "itemcd": r.itemcd,
                "item_nm": r.item_nm or "",
                "qty": remain,
                "eid": r.eid,
                "itemtyp": r.itemtyp or "DJ",
                "prddate": r.prddate.isoformat() if r.prddate else "",
                "whcd": whcd,
            })

        # 批次行
        for r in prd_rows:
            used = reserved_map.get(r.lineno, 0)
            remain = max(int(r.inqty or 0) - used, 0)
            result.append({
                "opt": "prd",
                "lineno": r.lineno,
                "itemcd": r.itemcd,
                "item_nm": r.item_nm or "",
                "qty": remain,
                "eid": None,
                "itemtyp": r.itemtyp or "DJ",
                "prddate": r.prddate.isoformat() if r.prddate else "",
                "whcd": whcd,
            })

        return result

    @staticmethod
    def find_sales_returnable_orders() -> list[dict[str, Any]]:
        """查询可销售退货入库的销售出库单（OV=1，已审核且未完全退货）。"""
        prd_agg = (
            db.session.query(StockOutDetailPrd.outbillid, func.coalesce(func.sum(StockOutDetailPrd.outqty), 0).label("prd_qty"))
            .filter(StockOutDetailPrd.closed_flg != "1")
            .group_by(StockOutDetailPrd.outbillid).subquery()
        )
        eid_agg = (
            db.session.query(StockOutDetailEid.outbillid, func.coalesce(func.sum(StockOutDetailEid.outqty), 0).label("eid_qty"))
            .filter(StockOutDetailEid.closed_flg != "1")
            .group_by(StockOutDetailEid.outbillid).subquery()
        )
        returned_sub = (
            db.session.query(StockIn.refbillid, func.sum(StockInDetail.inqty).label("returned_qty"))
            .join(StockInDetail, StockIn.inbillid == StockInDetail.inbillid)
            .filter(StockIn.invtyp == "2", StockIn.auditflg == "2")
            .group_by(StockIn.refbillid).subquery()
        )
        rows = (
            db.session.query(
                StockOut.outbillid, StockOut.whcd, StockOut.outdate,
                (func.coalesce(prd_agg.c.prd_qty, 0) + func.coalesce(eid_agg.c.eid_qty, 0)).label("total_out"),
                func.coalesce(returned_sub.c.returned_qty, 0).label("returned"),
            )
            .outerjoin(prd_agg, StockOut.outbillid == prd_agg.c.outbillid)
            .outerjoin(eid_agg, StockOut.outbillid == eid_agg.c.outbillid)
            .outerjoin(returned_sub, StockOut.outbillid == returned_sub.c.refbillid)
            .filter(StockOut.invtyp == "1", StockOut.auditflg == "2")
            .all()
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            pending = int(r.total_out) - int(r.returned)
            if pending > 0:
                result.append({
                    "outbillid": r.outbillid, "whcd": r.whcd,
                    "outdate": r.outdate.isoformat() if r.outdate else "",
                    "total_out": int(r.total_out), "returned": int(r.returned), "pending": pending,
                })
        return result

    @staticmethod
    def get_sales_returnable_lines(outbillid: str) -> list[dict[str, Any]]:
        """查询某销售出库单中尚未退货的明细行（供 IV=2 销售退货入库选择）。"""
        from app.models.warehouse import StockOutDetailEid as OutEid, StockOutDetailPrd as OutPrd
        ret_eid_map = dict(
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "2", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno).all()
        )
        ret_prd_map = dict(
            db.session.query(StockInDetail.reflineno, func.sum(StockInDetail.inqty))
            .join(StockIn, StockInDetail.inbillid == StockIn.inbillid)
            .filter(StockIn.invtyp == "2", StockIn.auditflg == "2", StockIn.refbillid == outbillid)
            .group_by(StockInDetail.reflineno).all()
        )
        result: list[dict[str, Any]] = []
        eid_rows = (
            db.session.query(OutEid.lineno, OutEid.itemcd, OutEid.eid, OutEid.outqty, OutEid.itemtyp)
            .filter(OutEid.outbillid == outbillid, OutEid.closed_flg != "1").order_by(OutEid.lineno).all()
        )
        for r in eid_rows:
            pending = (r.outqty or 0) - int(ret_eid_map.get(r.lineno, 0) or 0)
            if pending > 0:
                result.append({"opt": "eid", "lineno": r.lineno, "itemcd": r.itemcd, "eid": r.eid or "", "out_qty": r.outqty or 1, "pending": pending, "itemtyp": r.itemtyp or ""})
        prd_rows = (
            db.session.query(OutPrd.lineno, OutPrd.itemcd, OutPrd.outqty, OutPrd.itemtyp, OutPrd.prddate)
            .filter(OutPrd.outbillid == outbillid, OutPrd.closed_flg != "1").order_by(OutPrd.lineno).all()
        )
        for r in prd_rows:
            pending = (r.outqty or 0) - int(ret_prd_map.get(r.lineno, 0) or 0)
            if pending > 0:
                result.append({"opt": "prd", "lineno": r.lineno, "itemcd": r.itemcd, "out_qty": r.outqty or 1, "pending": pending, "itemtyp": r.itemtyp or "", "prddate": r.prddate.isoformat() if r.prddate else ""})
        return result


class StockOutRepository:
    """出库单数据访问。"""

    @staticmethod
    def get_by_id(outbillid: str) -> StockOut | None:
        return db.session.get(StockOut, outbillid)

    @staticmethod
    def list_by_filters(
        whcd: str | None = None,
        invtyp: str | None = None,
        auditflg: str | None = None,
        outbillid: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[StockOut], int]:
        query = db.session.query(StockOut)
        if whcd:
            query = query.filter(StockOut.whcd == whcd)
        if invtyp:
            query = query.filter(StockOut.invtyp == invtyp)
        if auditflg:
            query = query.filter(StockOut.auditflg == auditflg)
        if outbillid:
            query = query.filter(StockOut.outbillid.like(f"%{outbillid}%"))
        query = query.order_by(desc(db.func.substring(StockOut.outbillid, 3).cast(db.Integer)))
        total: int = query.count()
        items: list[StockOut] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> StockOut:
        now = datetime.now(UTC)
        data.setdefault("outdate", now)
        record = StockOut(
            outbillid=_gen_master_id("OT", "出库单号"),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail_eid(
        outbillid: str,
        whcd: str,
        lineno: int,
        data: dict[str, Any],
    ) -> StockOutDetailEid:
        record = StockOutDetailEid(
            outbillid=outbillid,
            whcd=whcd,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail_prd(
        outbillid: str,
        whcd: str,
        lineno: int,
        data: dict[str, Any],
    ) -> StockOutDetailPrd:
        record = StockOutDetailPrd(
            outbillid=outbillid,
            whcd=whcd,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def audit(record: StockOut, auditor: str, auditflg: str = "2", checkmemo: str = "") -> StockOut:
        record.auditflg = auditflg
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        if checkmemo:
            record.memo = (record.memo or "") + " [审核: " + checkmemo + "]"
        return record

    @staticmethod
    def find_returnable_orders() -> list[dict[str, Any]]:
        """查询可退货出库的采购退货单（已审核且有未退数量）。"""
        from app.models.procurement import ReturnPurchaseBill, ReturnPurchaseBillDt, PurchaseRegister
        from app.models.master import Supplier

        # 已出库的退货数量（仅已审核出库单）
        returned_sub = (
            db.session.query(
                StockOut.refbillid,
                StockOutDetailPrd.reflineno,
                func.sum(StockOutDetailPrd.outqty).label("returned_qty"),
            )
            .join(StockOut, StockOutDetailPrd.outbillid == StockOut.outbillid)
            .filter(
                StockOut.invtyp == "6",
                StockOut.auditflg == "2",
                StockOut.refbillid.isnot(None),
            )
            .group_by(StockOut.refbillid, StockOutDetailPrd.reflineno)
            .subquery()
        )

        rows = (
            db.session.query(
                ReturnPurchaseBill.pcbillid,
                ReturnPurchaseBill.ref_rgstbillid,
                PurchaseRegister.suppliercd,
                Supplier.supp_nm,
                func.count(func.distinct(ReturnPurchaseBillDt.lineno)).label("total_lines"),
                func.sum(
                    ReturnPurchaseBillDt.rpcqty - func.coalesce(returned_sub.c.returned_qty, 0)
                ).label("total_returnable"),
            )
            .join(ReturnPurchaseBillDt,
                   ReturnPurchaseBill.pcbillid == ReturnPurchaseBillDt.pcbillid)
            .join(PurchaseRegister,
                   ReturnPurchaseBill.ref_rgstbillid == PurchaseRegister.rgstbillid)
            .outerjoin(Supplier, PurchaseRegister.suppliercd == Supplier.supp_cd)
            .outerjoin(
                returned_sub,
                (returned_sub.c.refbillid == ReturnPurchaseBillDt.pcbillid)
                & (returned_sub.c.reflineno == ReturnPurchaseBillDt.lineno),
            )
            .filter(
                ReturnPurchaseBill.auditflg == "2",
                ~ReturnPurchaseBill.useflg.in_(["9", "V"]),
                ReturnPurchaseBillDt.rpcqty > func.coalesce(returned_sub.c.returned_qty, 0),
            )
            .group_by(
                ReturnPurchaseBill.pcbillid,
                ReturnPurchaseBill.ref_rgstbillid,
                PurchaseRegister.suppliercd,
                Supplier.supp_nm,
            )
            .order_by(ReturnPurchaseBill.pcbillid.desc())
            .all()
        )

        return [
            {
                "pcbillid": r.pcbillid,
                "ref_rgstbillid": r.ref_rgstbillid,
                "suppliercd": r.suppliercd,
                "supp_nm": r.supp_nm,
                "total_lines": r.total_lines,
                "total_returnable": int(r.total_returnable or 0),
            }
            for r in rows
        ]

    @staticmethod
    def get_returnable_order_lines(pcbillid: str) -> list[dict[str, Any]]:
        """查询某退货单的可退货出库明细行。"""
        from app.models.procurement import ReturnPurchaseBillDt
        from app.models.master import Item

        returned_sub = (
            db.session.query(
                StockOut.refbillid,
                StockOutDetailPrd.reflineno,
                func.sum(StockOutDetailPrd.outqty).label("returned_qty"),
            )
            .join(StockOut, StockOutDetailPrd.outbillid == StockOut.outbillid)
            .filter(
                StockOut.invtyp == "6",
                StockOut.auditflg == "2",
                StockOut.refbillid == pcbillid,
            )
            .group_by(StockOut.refbillid, StockOutDetailPrd.reflineno)
            .subquery()
        )

        rows = (
            db.session.query(
                ReturnPurchaseBillDt.lineno,
                ReturnPurchaseBillDt.itemcd,
                Item.item_nm,
                ReturnPurchaseBillDt.rpcqty,
                ReturnPurchaseBillDt.eid,
                ReturnPurchaseBillDt.seid,
                func.coalesce(returned_sub.c.returned_qty, 0).label("returned_qty"),
                (ReturnPurchaseBillDt.rpcqty - func.coalesce(returned_sub.c.returned_qty, 0)).label(
                    "returnable_qty"
                ),
            )
            .outerjoin(Item, ReturnPurchaseBillDt.itemcd == Item.item_cd)
            .outerjoin(
                returned_sub,
                (returned_sub.c.refbillid == ReturnPurchaseBillDt.pcbillid)
                & (returned_sub.c.reflineno == ReturnPurchaseBillDt.lineno),
            )
            .filter(
                ReturnPurchaseBillDt.pcbillid == pcbillid,
                ReturnPurchaseBillDt.rpcqty > func.coalesce(returned_sub.c.returned_qty, 0),
            )
            .order_by(ReturnPurchaseBillDt.lineno)
            .all()
        )

        return [
            {
                "lineno": r.lineno,
                "itemcd": r.itemcd,
                "item_nm": r.item_nm,
                "rpcqty": r.rpcqty,
                "eid": r.eid,
                "seid": r.seid,
                "returned_qty": int(r.returned_qty or 0),
                "returnable_qty": int(r.returnable_qty or 0),
            }
            for r in rows
        ]


class StockDetailRepository:
    """库存明细数据访问。"""

    @staticmethod
    def get_balance(whcd: str | None, itemcd: str) -> int:
        """查询物料库存数量。

        Args:
            whcd: 仓库编码，传入 None 表示汇总所有仓库
            itemcd: 物料编码

        Returns:
            库存数量（按 itemcd 汇总所有批次）
        """
        query = db.session.query(db.func.coalesce(db.func.sum(StockDetail.itemqty), 0)).filter(
            StockDetail.itemcd == itemcd,
            StockDetail.useflg == "1",
        )
        if whcd:
            query = query.filter(StockDetail.whcd == whcd)
        return int(query.scalar() or 0)

    @staticmethod
    def list_by_warehouse(
        whcd: str,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[StockDetail], int]:
        query = (
            db.session.query(StockDetail)
            .filter(StockDetail.whcd == whcd)
            .order_by(StockDetail.itemcd)
        )
        total: int = query.count()
        items: list[StockDetail] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def update_balance(whcd: str, itemcd: str, qty_delta: int, operator: str, itemtyp: str = None, prddate: datetime = None) -> StockDetail:
        """更新库存余量。

        匹配维度: whcd + itemcd + itemtyp + prddate（四维）。
        同维度多行时先聚合再更新，防止 first() 只命中一行导致残留负数。
        """
        now = datetime.now(UTC)
        query = db.session.query(StockDetail).filter(
            StockDetail.whcd == whcd,
            StockDetail.itemcd == itemcd,
        )
        if itemtyp:
            query = query.filter(StockDetail.itemtyp == itemtyp)
        if prddate:
            query = query.filter(func.date(StockDetail.prddate) == func.date(prddate))

        rows = query.order_by(StockDetail.seqno).all()

        if rows:
            # 仅当指定了 itemtyp 且有多行时才聚合同维度
            if itemtyp and len(rows) > 1:
                total_qty = sum((r.itemqty or 0) for r in rows)
                for r in rows[1:]:
                    db.session.delete(r)
                record = rows[0]
                record.itemqty = total_qty + qty_delta
                record.upddate = now
                if record.itemqty == 0:
                    db.session.delete(record)
                    return record
            else:
                record = rows[0]
                new_qty = (record.itemqty or 0) + qty_delta
                if new_qty == 0:
                    db.session.delete(record)
                    return record
                else:
                    record.itemqty = new_qty
                    record.upddate = now
        elif qty_delta > 0:
            record = StockDetail(
                whcd=whcd, itemcd=itemcd, itemtyp=itemtyp, prddate=prddate,
                itemqty=qty_delta, opercd=operator, gendate=now, upddate=now,
            )
            db.session.add(record)
        else:
            raise ValueError(
                f"库存不足：{whcd}/{itemcd}/{itemtyp or '-'}/{prddate or '-'} 无库存记录，无法出库 {abs(qty_delta)}"
            )
        return record

    @staticmethod
    def add_movement(
        whcd: str,
        itemcd: str,
        itemqty: int,
        billid: str,
        invtyp: str = "",
        iotyp: str = "",
        operator: str = "",
        itemtyp: str = None,
        prddate: datetime = None,
    ) -> None:
        """写入库存变动明细 (TWH12)。storeqty 记录变动后库存余量。"""
        from app.models.warehouse import StockDetailDt

        # 获取当前库存余量（同一仓库+物料可能有多行，需汇总）
        balance = int(
            db.session.query(func.coalesce(func.sum(StockDetail.itemqty), 0))
            .filter(StockDetail.whcd == whcd, StockDetail.itemcd == itemcd)
            .scalar() or 0
        )

        now = datetime.now(UTC)
        movement = StockDetailDt(
            whcd=whcd,
            itemtyp=itemtyp,
            itemcd=itemcd,
            prddate=prddate,
            itemqty=itemqty,
            storeqty=balance,
            billid=billid,
            invtyp=invtyp,
            iotyp=iotyp,
            opercd=operator,
            gendate=now,
            invdate=now,
            useflg="1",
        )
        db.session.add(movement)


# ---------------------------------------------------------------------------
# 资产盘点
# ---------------------------------------------------------------------------


class AssetCheckRepository:
    """资产盘点主表（twh19_asset_c_a）数据访问。"""

    @staticmethod
    def get_by_id(opbillid: str) -> AssetCheckAccept | None:
        return db.session.get(AssetCheckAccept, opbillid)

    @staticmethod
    def list_all(
        page: int = 1, per_page: int = 20, useflg: str | None = "1"
    ) -> tuple[list[AssetCheckAccept], int]:
        query = db.session.query(AssetCheckAccept)
        if useflg is not None:
            query = query.filter(AssetCheckAccept.useflg == useflg)
        total: int = query.count()
        items: list[AssetCheckAccept] = (
            query.order_by(desc(AssetCheckAccept.gendate))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> AssetCheckAccept:
        now = datetime.now(UTC)
        record = AssetCheckAccept(
            gendate=now, opercd=creator, useflg="1", auditflg="0", **data
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: AssetCheckAccept, data: dict[str, Any]) -> AssetCheckAccept:
        for key, value in data.items():
            setattr(record, key, value)
        return record

    @staticmethod
    def audit(record: AssetCheckAccept, auditor: str) -> AssetCheckAccept:
        record.auditflg = "2"  # 对齐 PB: 0=未审, 1=在审, 2=已审
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        return record

    @staticmethod
    def add_detail(
        opbillid: str, data: dict[str, Any]
    ) -> AssetCheckAcceptDtl:
        detail = AssetCheckAcceptDtl(opbillid=opbillid, useflg="1", **data)
        db.session.add(detail)
        return detail


# ---------------------------------------------------------------------------
# POS设备变更
# ---------------------------------------------------------------------------


class PosChangeRepository:
    """POS设备变更（twh21_pos_change / twh22_pos_change_dt）数据访问。"""

    @staticmethod
    def get_by_id(pk: int) -> PosChange | None:
        return db.session.get(PosChange, pk)

    @staticmethod
    def list_all(
        page: int = 1, per_page: int = 20, useflg: str | None = "1"
    ) -> tuple[list[PosChange], int]:
        query = db.session.query(PosChange)
        if useflg is not None:
            query = query.filter(PosChange.useflg == useflg)
        total: int = query.count()
        items: list[PosChange] = (
            query.order_by(desc(PosChange.upddate))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PosChange:
        now = datetime.now(UTC)
        record = PosChange(upddate=now, opercd=creator, useflg="1", **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: PosChange, data: dict[str, Any]) -> PosChange:
        for key, value in data.items():
            setattr(record, key, value)
        record.upddate = datetime.now(UTC)
        return record

    @staticmethod
    def add_detail(operation_id: int, data: dict[str, Any]) -> PosChangeDt:
        now = datetime.now(UTC)
        detail = PosChangeDt(
            operation_id=operation_id, upddate=now, useflg="1", **data
        )
        db.session.add(detail)
        return detail


class TransferAccountRepository:
    """调拨科目数据访问（TTX01_TXKMG）。"""

    @staticmethod
    def get_by_id(txkno: str) -> TransferAccount | None:
        return db.session.get(TransferAccount, txkno)

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> tuple[list[TransferAccount], int]:
        query = db.session.query(TransferAccount).order_by(TransferAccount.txkno)
        total: int = query.count()
        items: list[TransferAccount] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> TransferAccount:
        now = datetime.now(UTC)
        record = TransferAccount(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: TransferAccount, data: dict[str, Any], updator: str) -> TransferAccount:
        for key, value in data.items():
            setattr(record, key, value)
        record.upddate = datetime.now(UTC)
        record.opercd = updator
        return record


class OverLostRepository:
    """盘盈盘亏数据访问（TWH17_OVERLOST + TWH18 明细）。"""

    @staticmethod
    def get_by_id(olbillid: str) -> OverLost | None:
        return db.session.get(OverLost, olbillid)

    @staticmethod
    def list_by_filters(
        whcd: str | None = None,
        oltyp: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[OverLost], int]:
        query = db.session.query(OverLost)
        if whcd:
            query = query.filter(OverLost.whcd == whcd)
        if oltyp:
            query = query.filter(OverLost.oltyp == oltyp)
        if auditflg:
            query = query.filter(OverLost.auditflg == auditflg)
        query = query.order_by(desc(OverLost.gendate))
        total: int = query.count()
        items: list[OverLost] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> OverLost:
        now = datetime.now(UTC)
        record = OverLost(
            olbillid=_gen_id(),
            opercd=creator,
            gendate=now,
            auditflg="0",
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_detail(olbillid: str, lineno: int, data: dict[str, Any]) -> OverLostDt:
        record = OverLostDt(
            olbillid=olbillid,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def add_eid_detail(olbillid: str, lineno: int, data: dict[str, Any]) -> OverLostEid:
        record = OverLostEid(
            olbillid=olbillid,
            lineno=lineno,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def audit(record: OverLost, auditor: str) -> OverLost:
        now = datetime.now(UTC)
        record.auditflg = "1"
        record.cfercd = auditor
        record.cfdate = now
        return record
