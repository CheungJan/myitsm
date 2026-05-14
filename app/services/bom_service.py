"""BOM 管理业务逻辑层。"""

from __future__ import annotations

from typing import Any

from app.repositories.bom_repository import BomRepository


class BomService:
    """BOM 业务逻辑。"""

    @staticmethod
    def list_boms(page: int = 1, per_page: int = 20, search: str | None = None) -> dict[str, Any]:
        items, total = BomRepository.list_boms(page=page, per_page=per_page, search=search)
        return {"items": [i.to_dict() for i in items], "total": total}

    @staticmethod
    def get_bom(bomcd: str) -> dict[str, Any] | None:
        bom = BomRepository.get_bom(bomcd)
        if not bom:
            return None
        data = bom.to_dict()
        data["details"] = [d.to_dict() for d in BomRepository.list_details(bomcd)]
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
