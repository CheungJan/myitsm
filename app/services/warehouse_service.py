"""仓储管理业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.master import Item
from app.models.warehouse import Warehouse
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
    """批量补充明细中的物料名称 item_nm。"""
    itemcds = list({d.get("itemcd") for d in details if d.get("itemcd")})
    if not itemcds:
        return
    item_map = dict(
        db.session.query(Item.item_cd, Item.item_nm)
        .filter(Item.item_cd.in_(itemcds))
        .all()
    )
    for d in details:
        cd = d.get("itemcd")
        if cd:
            d["item_nm"] = item_map.get(cd, "")


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
    def get(inbillid: str) -> dict[str, Any] | None:
        record = StockInRepository.get_by_id(inbillid)
        if record is None:
            return None
        result = record.to_dict()
        result["details"] = [d.to_dict() for d in record.details]  # type: ignore[attr-defined]
        _enrich_warehouse_names([result])
        _enrich_item_names(result["details"])
        return result

    @staticmethod
    def list_records(
        whcd: str | None = None,
        invtyp: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = StockInRepository.list_by_filters(
            whcd=whcd, invtyp=invtyp, auditflg=auditflg, page=page, per_page=per_page
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
        creator: str,
    ) -> dict[str, Any]:
        record = StockInRepository.create(data, creator)
        # P1-1: 采购入库时冗余来源订单信息到明细
        ref_rgstbillid = data.get("refbillid") if data.get("invtyp") == "1" else None
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
        return record.to_dict()

    @staticmethod
    def audit(inbillid: str, auditor: str, whcd: str = "", checkmemo: str = "") -> dict[str, object]:
        record = StockInRepository.get_by_id(inbillid)
        if record is None:
            return {"success": False, "error": "入库单不存在"}
        if record.auditflg == "2":
            return {"success": False, "error": "已审核，不可重复审核"}
        # 如果传入 whcd 则覆盖（用于自动生成的空 whcd 草稿）
        if whcd:
            record.whcd = whcd
        if not record.whcd:
            return {"success": False, "error": "请先选择入库仓库后再审核"}
        if checkmemo:
            record.memo = checkmemo
        StockInRepository.audit(record, auditor)
        for detail in record.details:  # type: ignore[attr-defined]
            StockDetailRepository.update_balance(
                whcd=record.whcd,
                itemcd=detail.itemcd,
                qty_delta=detail.inqty or 0,
                operator=auditor,
            )
            StockDetailRepository.add_movement(
                whcd=record.whcd, itemcd=detail.itemcd,
                itemqty=detail.inqty or 0,
                billid=record.inbillid, invtyp=record.invtyp or "",
                iotyp="1", operator=auditor,
            )
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
            dt_list = record.details.all()  # type: ignore[attr-defined]
            all_full = all(dt.inqty and dt.inqty >= dt.rgsqty for dt in dt_list)
            db.session.query(RequisitionOrderLink).filter(
                RequisitionOrderLink.rgstbillid == record.refbillid
            ).update(
                {"linkstatus": "completed" if all_full else "partial_in"},
                synchronize_session=False,
            )
        db.session.commit()
        return {"success": True, "inbillid": record.inbillid}


class StockOutService:
    """出库单服务。"""

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
        return result

    @staticmethod
    def list_records(
        whcd: str | None = None,
        invtyp: str | None = None,
        auditflg: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = StockOutRepository.list_by_filters(
            whcd=whcd, invtyp=invtyp, auditflg=auditflg, page=page, per_page=per_page
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
        record = StockOutRepository.create(data, creator)
        if details_eid:
            for idx, detail_data in enumerate(details_eid, start=1):
                StockOutRepository.add_detail_eid(
                    outbillid=record.outbillid,
                    whcd=record.whcd,
                    lineno=idx,
                    data=detail_data,
                )
        if details_prd:
            for idx, detail_data in enumerate(details_prd, start=1):
                StockOutRepository.add_detail_prd(
                    outbillid=record.outbillid,
                    whcd=record.whcd,
                    lineno=idx,
                    data=detail_data,
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
        StockOutRepository.audit(record, auditor, auditflg, checkmemo=checkmemo)
        # 仅审核通过时扣库存
        if auditflg == "2":
            for detail in record.details_eid:  # type: ignore[attr-defined]
                StockDetailRepository.update_balance(
                    whcd=record.whcd,
                    itemcd=detail.itemcd,
                    qty_delta=-(detail.outqty or 0),
                    operator=auditor,
                )
                StockDetailRepository.add_movement(
                    whcd=record.whcd, itemcd=detail.itemcd,
                    itemqty=-(detail.outqty or 0),
                    billid=record.outbillid, invtyp=record.invtyp or "",
                    iotyp="0", operator=auditor,
                )
            for detail in record.details_prd:  # type: ignore[attr-defined]
                StockDetailRepository.update_balance(
                    whcd=record.whcd,
                    itemcd=detail.itemcd,
                    qty_delta=-(detail.outqty or 0),
                    operator=auditor,
                )
                StockDetailRepository.add_movement(
                    whcd=record.whcd, itemcd=detail.itemcd,
                    itemqty=-(detail.outqty or 0),
                    billid=record.outbillid, invtyp=record.invtyp or "",
                    iotyp="0", operator=auditor,
                )
            # P1-3: 退货出库审核通过 → 更新退货单状态为已完成
            if record.invtyp == "6" and record.refbillid:
                from app.models.procurement import ReturnPurchaseBill
                db.session.query(ReturnPurchaseBill).filter(
                    ReturnPurchaseBill.pcbillid == record.refbillid
                ).update(
                    {"auditflg": "2"},
                    synchronize_session=False,
                )
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
