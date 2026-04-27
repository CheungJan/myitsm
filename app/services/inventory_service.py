"""库存预警与价格管理业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.inventory_repository import (
    AdjustPriceRepository,
    InventoryLimitRepository,
    PriceRepository,
)


class InventoryLimitService:
    """库存预警服务。"""

    @staticmethod
    def get(itemcd: str) -> dict[str, Any] | None:
        record = InventoryLimitRepository.get_by_id(itemcd)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        records = InventoryLimitRepository.list_all()
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = InventoryLimitRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(itemcd: str, data: dict[str, Any], creator: str) -> dict[str, Any] | None:
        record = InventoryLimitRepository.get_by_id(itemcd)
        if record is None:
            return None
        InventoryLimitRepository.save_history(record)
        InventoryLimitRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class PriceService:
    """价格规则服务。"""

    @staticmethod
    def get(itemcd: str, busityp: str) -> dict[str, Any] | None:
        record = PriceRepository.get_by_key(itemcd, busityp)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        records = PriceRepository.list_all()
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = PriceRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        itemcd: str,
        busityp: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = PriceRepository.get_by_key(itemcd, busityp)
        if record is None:
            return None
        PriceRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class AdjustPriceService:
    """调价服务。"""

    @staticmethod
    def list_by_bill(pabillid: str) -> list[dict[str, Any]]:
        records = AdjustPriceRepository.list_by_bill(pabillid)
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = AdjustPriceRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()
