"""BOM 管理业务逻辑层。"""

from __future__ import annotations

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
        items_map: dict[str, str] = {}
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
