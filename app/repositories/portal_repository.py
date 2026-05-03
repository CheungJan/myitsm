"""客户自助服务门户数据访问层（Tier-2 G9）。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.extensions import db
from app.models.portal import PortalUser, RepairRequest, ServiceRating


class PortalUserRepository:
    """门户用户数据访问。"""

    @staticmethod
    def get_by_id(portal_uid: str) -> PortalUser | None:
        return db.session.get(PortalUser, portal_uid)

    @staticmethod
    def get_by_login(login_name: str) -> PortalUser | None:
        return db.session.query(PortalUser).filter(PortalUser.login_name == login_name).first()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> tuple[list[PortalUser], int]:
        query = db.session.query(PortalUser)
        total: int = query.count()
        items: list[PortalUser] = (
            query.order_by(PortalUser.portal_uid)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> PortalUser:
        now = datetime.now(UTC)
        record = PortalUser(opercd=creator, upddate=now, **data)
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: PortalUser,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> PortalUser:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class RepairRequestRepository:
    """自助报修工单数据访问。"""

    @staticmethod
    def get_by_id(request_id: str) -> RepairRequest | None:
        return db.session.get(RepairRequest, request_id)

    @staticmethod
    def list_all(
        custcd: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[RepairRequest], int]:
        query = db.session.query(RepairRequest)
        if custcd is not None:
            query = query.filter(RepairRequest.custcd == custcd)
        if status is not None:
            query = query.filter(RepairRequest.status == status)
        total: int = query.count()
        items: list[RepairRequest] = (
            query.order_by(RepairRequest.submit_time.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> RepairRequest:
        now = datetime.now(UTC)
        record = RepairRequest(opercd=creator, upddate=now, **data)
        record.submit_time = now
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: RepairRequest,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> RepairRequest:
        now = datetime.now(UTC)
        new_status = data.get("status")
        if new_status == "ACCEPTED" and record.accept_time is None:
            record.accept_time = now
        if new_status == "COMPLETED" and record.complete_time is None:
            record.complete_time = now
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = now
        return record


class ServiceRatingRepository:
    """服务评价数据访问。"""

    @staticmethod
    def list_all(
        custcd: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[ServiceRating], int]:
        query = db.session.query(ServiceRating)
        if custcd is not None:
            query = query.filter(ServiceRating.custcd == custcd)
        total: int = query.count()
        items: list[ServiceRating] = (
            query.order_by(ServiceRating.rating_time.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> ServiceRating:
        now = datetime.now(UTC)
        record = ServiceRating(opercd=creator, upddate=now, **data)
        record.rating_time = now
        db.session.add(record)
        return record
