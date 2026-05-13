"""押金管理业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.deposit_repository import (
    DepositDetailRepository,
    DepositPosModelRepository,
    DepositRepository,
)


class DepositService:
    """押金主记录服务。"""

    @staticmethod
    def get(custcd: str) -> dict[str, Any] | None:
        record = DepositRepository.get_by_id(custcd)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = DepositRepository.list_all(page, per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = DepositRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(custcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = DepositRepository.get_by_id(custcd)
        if record is None:
            return None
        DepositRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class DepositDetailService:
    """押金变更明细服务。"""

    @staticmethod
    def list_by_customer(custcd: str, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = DepositDetailRepository.list_by_customer(custcd, page, per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = DepositDetailRepository.create(data)
        db.session.commit()
        return record.to_dict()


class DepositPosModelService:
    """设备型号押金标准服务。"""

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        records = DepositPosModelRepository.list_all()
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = DepositPosModelRepository.create(data)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(model_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = DepositPosModelRepository.get_by_id(model_cd)
        if record is None:
            return None
        DepositPosModelRepository.update(record, data)
        db.session.commit()
        return record.to_dict()
