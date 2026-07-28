"""BOM 管理业务逻辑层。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.extensions import db
from app.repositories.bom_repository import BomRepository


class BomService:
    """BOM 业务逻辑。"""

    @staticmethod
    def list_boms(page: int = 1, per_page: int = 20, search: str | None = None,
                  class_cd: str | None = None) -> dict[str, Any]:
        items, total = BomRepository.list_boms(
            page=page, per_page=per_page, search=search, class_cd=class_cd
        )
        return {"items": [i.to_dict() for i in items], "total": total}

    @staticmethod
    def get_bom(bomcd: str) -> dict[str, Any] | None:
        bom = BomRepository.get_bom(bomcd)
        if not bom:
            return None
        data = bom.to_dict()
        details = []
        dt_list = BomRepository.list_details(bomcd)
        # 批量查询物料名称，避免 N+1
        from app.models.master import Item
        itemcds = [d.itemcd for d in dt_list]
        items_map: dict = {}
        if itemcds:
            rows = db.session.query(Item.item_cd, Item.item_nm).filter(
                Item.item_cd.in_(itemcds)
            ).all()
            items_map = {r.item_cd: r.item_nm for r in rows}
        for d in dt_list:
            dd = d.to_dict()
            dd["item_nm"] = items_map.get(d.itemcd, "")
            details.append(dd)
        data["details"] = details
        return data

    @staticmethod
    def expand(bomcd: str, qty: int = 1, whcd: str | None = None) -> dict[str, Any] | None:
        """展开 BOM：返回按 qty 倍数放大后的物料明细，可附带指定仓库库存余量。

        供 OV=8 生产出库弹窗使用（PB: w_wh_scout_pop.srw）。
        """
        bom = BomRepository.get_bom(bomcd)
        if not bom:
            return None
        dt_list = BomRepository.list_details(bomcd)
        from app.models.master import Item
        from app.models.warehouse import StockDetail, StockInDetail
        itemcds = [d.itemcd for d in dt_list]
        items_map: dict = {}
        ref_map: dict[str, str] = {}
        if itemcds:
            rows = db.session.query(Item.item_cd, Item.item_nm, Item.consume).filter(
                Item.item_cd.in_(itemcds)
            ).all()
            items_map = {r.item_cd: {"item_nm": r.item_nm or "", "consume": getattr(r, 'consume', '') or ""} for r in rows}
            # 获取每个物料最新的来源入库单号
            if whcd:
                ref_rows = (
                    db.session.query(StockInDetail.itemcd, StockInDetail.inbillid)
                    .join(StockInDetail.stock_in)
                    .filter(StockInDetail.stock_in.has(whcd=whcd, auditflg="2"))
                    .filter(StockInDetail.itemcd.in_(itemcds))
                    .all()
                )
                for r in ref_rows:
                    if r.itemcd not in ref_map:
                        ref_map[r.itemcd] = r.inbillid
            if whcd:
                stock_rows = (
                    db.session.query(
                        StockDetail.itemcd, StockDetail.itemtyp, StockDetail.prddate,
                        db.func.sum(StockDetail.itemqty),
                    )
                    .filter(StockDetail.whcd == whcd, StockDetail.itemcd.in_(itemcds))
                    .group_by(StockDetail.itemcd, StockDetail.itemtyp, StockDetail.prddate)
                    .all()
                )
            else:
                stock_rows = []
        lines = []
        for d in dt_list:
            need = int((d.bomqty or 0)) * qty
            info = items_map.get(d.itemcd, {})
            batches = [r for r in stock_rows if r[0] == d.itemcd]
            if batches:
                batches.sort(key=lambda r: r[2] or datetime.min)
                remaining = need
                for b in batches:
                    batch_qty = int(b[3] or 0)
                    pick = min(batch_qty, remaining)
                    remaining -= pick
                    lines.append({
                        "itemcd": d.itemcd,
                        "item_nm": info.get("item_nm", ""),
                        "consume": info.get("consume", ""),
                        "ref_inbillid": ref_map.get(d.itemcd, ""),
                        "itemtyp": b[1] or "",
                        "prddate": b[2].isoformat() if b[2] else "",
                        "bomqty": int(d.bomqty or 0),
                        "need_qty": need,
                        "stock_qty": batch_qty if whcd else None,
                        "pick_qty": pick if whcd else 0,
                        "enough": (batch_qty >= need) if whcd else None,
                    })
            else:
                lines.append({
                    "itemcd": d.itemcd,
                    "item_nm": info.get("item_nm", ""),
                    "consume": info.get("consume", ""),
                    "ref_inbillid": ref_map.get(d.itemcd, ""),
                    "itemtyp": "",
                    "prddate": "",
                    "bomqty": int(d.bomqty or 0),
                    "need_qty": need,
                    "stock_qty": 0 if whcd else None,
                    "enough": False if whcd else None,
                })
        return {
            "bomcd": bom.bomcd,
            "bomnm": bom.bomnm or "",
            "qty": qty,
            "whcd": whcd,
            "lines": lines,
        }

    @staticmethod
    def create_bom(data: dict[str, Any]) -> dict[str, Any]:
        return BomRepository.create_bom(data).to_dict()

    @staticmethod
    def update_bom(bomcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        bom = BomRepository.get_bom(bomcd)
        if not bom:
            return None
        return BomRepository.update_bom(bom, data).to_dict()

    @staticmethod
    def delete_bom(bomcd: str) -> bool:
        bom = BomRepository.get_bom(bomcd)
        if not bom:
            return False
        BomRepository.delete_bom(bom)
        return True

    @staticmethod
    def add_detail(bomcd: str, data: dict[str, Any]) -> dict[str, Any]:
        data["bomcd"] = bomcd
        return BomRepository.add_detail(data).to_dict()

    @staticmethod
    def update_detail(bomcd: str, itemcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        dt = BomRepository.get_detail(bomcd, itemcd)
        if not dt:
            return None
        return BomRepository.update_detail(dt, data).to_dict()

    @staticmethod
    def delete_detail(bomcd: str, itemcd: str) -> bool:
        dt = BomRepository.get_detail(bomcd, itemcd)
        if not dt:
            return False
        BomRepository.delete_detail(dt)
        return True
