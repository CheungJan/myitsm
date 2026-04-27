"""生产制造MES业务服务层（Tier-3 G7）。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.mes_repository import (
    MaterialConsumeRepository,
    ProcessDefRepository,
    WorkOrderRepository,
    WorkProcessRepository,
)


class WorkOrderService:
    """生产工单服务。"""

    @staticmethod
    def get(wo_id: str) -> dict[str, Any] | None:
        record = WorkOrderRepository.get_by_id(wo_id)
        if record is None:
            return None
        result = record.to_dict()
        processes = WorkProcessRepository.list_by_wo(wo_id)
        result["processes"] = [p.to_dict() for p in processes]
        return result

    @staticmethod
    def list_all(
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = WorkOrderRepository.list_all(status=status, page=page, per_page=per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = WorkOrderRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        wo_id: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = WorkOrderRepository.get_by_id(wo_id)
        if record is None:
            return None
        WorkOrderRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class ProcessDefService:
    """工序定义服务。"""

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        records = ProcessDefRepository.list_all()
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = ProcessDefRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        process_cd: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = ProcessDefRepository.get_by_id(process_cd)
        if record is None:
            return None
        ProcessDefRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class WorkProcessService:
    """工单工序服务。"""

    @staticmethod
    def list_by_wo(wo_id: str) -> list[dict[str, Any]]:
        records = WorkProcessRepository.list_by_wo(wo_id)
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = WorkProcessRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        wp_id: int,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = WorkProcessRepository.get_by_id(wp_id)
        if record is None:
            return None
        WorkProcessRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class MaterialConsumeService:
    """物料消耗服务。"""

    @staticmethod
    def list_by_wo(wo_id: str) -> list[dict[str, Any]]:
        records = MaterialConsumeRepository.list_by_wo(wo_id)
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = MaterialConsumeRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()
