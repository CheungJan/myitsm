"""IoT数据监控业务服务层（Tier-3 G8）。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.iot_repository import (
    AlertLogRepository,
    AlertRuleRepository,
    DeviceConnRepository,
    DeviceDataRepository,
)


class DeviceConnService:
    """设备接入服务。"""

    @staticmethod
    def get(conn_id: str) -> dict[str, Any] | None:
        record = DeviceConnRepository.get_by_id(conn_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(
        online_status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = DeviceConnRepository.list_all(
            online_status=online_status, page=page, per_page=per_page
        )
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = DeviceConnRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        conn_id: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = DeviceConnRepository.get_by_id(conn_id)
        if record is None:
            return None
        DeviceConnRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class DeviceDataService:
    """设备数据服务。"""

    @staticmethod
    def list_by_eid(
        eid: str,
        data_type: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        items, total = DeviceDataRepository.list_by_eid(
            eid, data_type=data_type, page=page, per_page=per_page
        )
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = DeviceDataRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()


class AlertRuleService:
    """报警规则服务。"""

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        records = AlertRuleRepository.list_all()
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = AlertRuleRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        rule_id: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = AlertRuleRepository.get_by_id(rule_id)
        if record is None:
            return None
        AlertRuleRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class AlertLogService:
    """报警记录服务。"""

    @staticmethod
    def list_all(
        eid: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = AlertLogRepository.list_all(
            eid=eid, status=status, page=page, per_page=per_page
        )
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = AlertLogRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def acknowledge(log_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        record = AlertLogRepository.get_by_id(log_id)
        if record is None:
            return None
        AlertLogRepository.update(record, data)
        db.session.commit()
        return record.to_dict()
