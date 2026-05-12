"""仓储管理业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.warehouse_repository import (
    AssetCheckRepository,
    PosChangeRepository,
    StockDetailRepository,
    StockInRepository,
    StockOutRepository,
    WarehouseRepository,
)


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
        record = StockInRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            StockInRepository.add_detail(
                inbillid=record.inbillid,
                whcd=record.whcd,
                lineno=idx,
                data=detail_data,
            )
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def audit(inbillid: str, auditor: str) -> dict[str, object]:
        record = StockInRepository.get_by_id(inbillid)
        if record is None:
            return {"success": False, "error": "入库单不存在"}
        if record.auditflg == "1":
            return {"success": False, "error": "已审核，不可重复审核"}
        StockInRepository.audit(record, auditor)
        for detail in record.details:  # type: ignore[attr-defined]
            StockDetailRepository.update_balance(
                whcd=record.whcd,
                itemcd=detail.itemcd,
                qty_delta=detail.inqty or 0,
                operator=auditor,
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
        return {
            "items": [item.to_dict() for item in items],
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
    def audit(outbillid: str, auditor: str) -> dict[str, object]:
        record = StockOutRepository.get_by_id(outbillid)
        if record is None:
            return {"success": False, "error": "出库单不存在"}
        if record.auditflg == "1":
            return {"success": False, "error": "已审核，不可重复审核"}
        StockOutRepository.audit(record, auditor)
        for detail in record.details_eid:  # type: ignore[attr-defined]
            StockDetailRepository.update_balance(
                whcd=record.whcd,
                itemcd=detail.itemcd,
                qty_delta=-(detail.outqty or 0),
                operator=auditor,
            )
        for detail in record.details_prd:  # type: ignore[attr-defined]
            StockDetailRepository.update_balance(
                whcd=record.whcd,
                itemcd=detail.itemcd,
                qty_delta=-(detail.outqty or 0),
                operator=auditor,
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
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }


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
