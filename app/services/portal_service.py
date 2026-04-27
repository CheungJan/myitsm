"""客户自助服务门户业务服务层（Tier-2 G9）。"""

from __future__ import annotations

from typing import Any

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.repositories.portal_repository import (
    PortalUserRepository,
    RepairRequestRepository,
    ServiceRatingRepository,
)


class PortalUserService:
    """门户用户服务。"""

    @staticmethod
    def get(portal_uid: str) -> dict[str, Any] | None:
        record = PortalUserRepository.get_by_id(portal_uid)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = PortalUserRepository.list_all(page=page, per_page=per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        plain_pw = data.pop("password", None)
        if plain_pw is not None:
            data["password_hash"] = generate_password_hash(str(plain_pw))
        record = PortalUserRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        portal_uid: str,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> dict[str, Any] | None:
        record = PortalUserRepository.get_by_id(portal_uid)
        if record is None:
            return None
        PortalUserRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class RepairRequestService:
    """自助报修工单服务。"""

    @staticmethod
    def get(request_id: str) -> dict[str, Any] | None:
        record = RepairRequestRepository.get_by_id(request_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(
        custcd: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = RepairRequestRepository.list_all(
            custcd=custcd, status=status, page=page, per_page=per_page
        )
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = RepairRequestRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(request_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = RepairRequestRepository.get_by_id(request_id)
        if record is None:
            return None
        RepairRequestRepository.update(record, data)
        db.session.commit()
        return record.to_dict()


class ServiceRatingService:
    """服务评价服务。"""

    @staticmethod
    def list_all(custcd: str | None = None, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        items, total = ServiceRatingRepository.list_all(custcd=custcd, page=page, per_page=per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str | None = None) -> dict[str, Any]:
        record = ServiceRatingRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()
