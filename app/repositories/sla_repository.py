"""SLA 服务级别管理数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func

from app.extensions import db
from app.models.sla import SlaDefinition, SlaTicket


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


class SlaDefinitionRepository:
    """SLA 定义数据访问。"""

    @staticmethod
    def get_by_id(sla_id: str) -> SlaDefinition | None:
        return db.session.get(SlaDefinition, sla_id)

    @staticmethod
    def list_all(useflg: str | None = "1") -> list[SlaDefinition]:
        query = db.session.query(SlaDefinition)
        if useflg is not None:
            query = query.filter(SlaDefinition.useflg == useflg)
        return query.order_by(SlaDefinition.priority, SlaDefinition.sla_id).all()

    @staticmethod
    def get_by_priority(priority: str) -> SlaDefinition | None:
        return (
            db.session.query(SlaDefinition)
            .filter(SlaDefinition.priority == priority, SlaDefinition.useflg == "1")
            .first()
        )

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> SlaDefinition:
        now = datetime.now(UTC)
        record = SlaDefinition(
            sla_id=_gen_id("SL"),
            opercd=creator,
            gendate=now,
            upddate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: SlaDefinition, data: dict[str, Any]) -> SlaDefinition:
        for key, value in data.items():
            setattr(record, key, value)
        record.upddate = datetime.now(UTC)
        return record


class SlaTicketRepository:
    """SLA 工单监控数据访问。"""

    @staticmethod
    def get_by_id(ticket_id: int) -> SlaTicket | None:
        return db.session.get(SlaTicket, ticket_id)

    @staticmethod
    def get_by_maintenance(maintenance_id: str, maintenance_type: str) -> SlaTicket | None:
        return (
            db.session.query(SlaTicket)
            .filter(
                SlaTicket.maintenance_id == maintenance_id,
                SlaTicket.maintenance_type == maintenance_type,
                SlaTicket.useflg == "1",
            )
            .first()
        )

    @staticmethod
    def list_by_filters(
        sla_status: str | None = None,
        sla_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[SlaTicket], int]:
        query = db.session.query(SlaTicket).filter(SlaTicket.useflg == "1")
        if sla_status:
            query = query.filter(SlaTicket.sla_status == sla_status)
        if sla_id:
            query = query.filter(SlaTicket.sla_id == sla_id)
        query = query.order_by(desc(SlaTicket.created_time))
        total: int = query.count()
        items: list[SlaTicket] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> SlaTicket:
        now = datetime.now(UTC)
        record = SlaTicket(
            opercd=creator,
            gendate=now,
            upddate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(record: SlaTicket, data: dict[str, Any]) -> SlaTicket:
        for key, value in data.items():
            setattr(record, key, value)
        record.upddate = datetime.now(UTC)
        return record

    @staticmethod
    def get_compliance_stats(sla_id: str | None = None) -> dict[str, Any]:
        """获取SLA达标率统计。"""
        query = db.session.query(SlaTicket).filter(
            SlaTicket.useflg == "1",
            SlaTicket.sla_status == "99",
        )
        if sla_id:
            query = query.filter(SlaTicket.sla_id == sla_id)

        total_closed: int = query.count()
        if total_closed == 0:
            return {
                "total_closed": 0,
                "response_met_count": 0,
                "resolve_met_count": 0,
                "response_rate": 0.0,
                "resolve_rate": 0.0,
            }

        response_met: int = query.filter(SlaTicket.response_met.is_(True)).count()
        resolve_met: int = (
            db.session.query(SlaTicket)
            .filter(
                SlaTicket.useflg == "1",
                SlaTicket.sla_status == "99",
                SlaTicket.resolve_met.is_(True),
            )
            .count()
        )
        if sla_id:
            resolve_met = (
                db.session.query(SlaTicket)
                .filter(
                    SlaTicket.useflg == "1",
                    SlaTicket.sla_status == "99",
                    SlaTicket.sla_id == sla_id,
                    SlaTicket.resolve_met.is_(True),
                )
                .count()
            )

        avg_query = db.session.query(func.avg(SlaTicket.response_elapsed_minutes)).filter(
            SlaTicket.useflg == "1",
            SlaTicket.sla_status == "99",
        )
        if sla_id:
            avg_query = avg_query.filter(SlaTicket.sla_id == sla_id)
        avg_response = avg_query.scalar()

        return {
            "total_closed": total_closed,
            "response_met_count": response_met,
            "resolve_met_count": resolve_met,
            "response_rate": round(response_met / total_closed * 100, 2),
            "resolve_rate": round(resolve_met / total_closed * 100, 2),
            "avg_response_minutes": round(float(avg_response), 1) if avg_response else 0.0,
        }
