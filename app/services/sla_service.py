"""SLA 服务级别管理业务服务层。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.extensions import db
from app.repositories.sla_repository import (
    SlaDefinitionRepository,
    SlaTicketRepository,
)


class SlaDefinitionService:
    """SLA 定义服务。"""

    @staticmethod
    def get(sla_id: str) -> dict[str, Any] | None:
        record = SlaDefinitionRepository.get_by_id(sla_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        records = SlaDefinitionRepository.list_all()
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = SlaDefinitionRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(sla_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = SlaDefinitionRepository.get_by_id(sla_id)
        if record is None:
            return None
        SlaDefinitionRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class SlaTicketService:
    """SLA 工单监控服务。"""

    @staticmethod
    def attach_sla(
        maintenance_id: str,
        maintenance_type: str,
        priority: str,
        creator: str,
    ) -> dict[str, Any]:
        """为工单绑定SLA，优先按优先级匹配SLA定义。"""
        sla_def = SlaDefinitionRepository.get_by_priority(priority)
        if sla_def is None:
            all_defs = SlaDefinitionRepository.list_all()
            if not all_defs:
                return {"success": False, "error": "未配置SLA定义"}
            sla_def = all_defs[0]

        now = datetime.now(UTC)
        data: dict[str, Any] = {
            "sla_id": sla_def.sla_id,
            "maintenance_id": maintenance_id,
            "maintenance_type": maintenance_type,
            "sla_status": "00",
            "created_time": now,
        }
        record = SlaTicketRepository.create(data, creator)
        db.session.commit()
        return {"success": True, "ticket_id": record.id, "sla_id": sla_def.sla_id}

    @staticmethod
    def record_response(
        maintenance_id: str,
        maintenance_type: str,
        operator: str,
    ) -> dict[str, object]:
        """记录首次响应时间。"""
        ticket = SlaTicketRepository.get_by_maintenance(maintenance_id, maintenance_type)
        if ticket is None:
            return {"success": False, "error": "未找到SLA监控记录"}
        if ticket.first_response_time is not None:
            return {"success": False, "error": "已记录首次响应"}

        now = datetime.now(UTC)
        sla_def = SlaDefinitionRepository.get_by_id(ticket.sla_id)
        ct = ticket.created_time
        if ct.tzinfo is None:
            ct = ct.replace(tzinfo=UTC)
        elapsed = int((now - ct).total_seconds() / 60)
        response_met = elapsed <= (sla_def.response_minutes if sla_def else 999999)

        update_data: dict[str, Any] = {
            "first_response_time": now,
            "response_elapsed_minutes": elapsed,
            "response_met": response_met,
        }
        if not response_met:
            update_data["sla_status"] = "02"

        SlaTicketRepository.update(ticket, update_data)
        db.session.commit()
        return {
            "success": True,
            "elapsed_minutes": elapsed,
            "response_met": response_met,
        }

    @staticmethod
    def record_resolution(
        maintenance_id: str,
        maintenance_type: str,
        operator: str,
    ) -> dict[str, object]:
        """记录解决时间并关闭SLA监控。"""
        ticket = SlaTicketRepository.get_by_maintenance(maintenance_id, maintenance_type)
        if ticket is None:
            return {"success": False, "error": "未找到SLA监控记录"}

        now = datetime.now(UTC)
        sla_def = SlaDefinitionRepository.get_by_id(ticket.sla_id)
        ct = ticket.created_time
        if ct.tzinfo is None:
            ct = ct.replace(tzinfo=UTC)
        elapsed = int((now - ct).total_seconds() / 60)
        resolve_met = elapsed <= (sla_def.resolve_minutes if sla_def else 999999)

        update_data: dict[str, Any] = {
            "resolved_time": now,
            "resolve_elapsed_minutes": elapsed,
            "resolve_met": resolve_met,
            "sla_status": "99",
        }
        SlaTicketRepository.update(ticket, update_data)
        db.session.commit()
        return {
            "success": True,
            "elapsed_minutes": elapsed,
            "resolve_met": resolve_met,
        }

    @staticmethod
    def list_records(
        sla_status: str | None = None,
        sla_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = SlaTicketRepository.list_by_filters(
            sla_status=sla_status, sla_id=sla_id, page=page, per_page=per_page
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def get_compliance_stats(sla_id: str | None = None) -> dict[str, Any]:
        """获取SLA达标率统计。"""
        return SlaTicketRepository.get_compliance_stats(sla_id)
