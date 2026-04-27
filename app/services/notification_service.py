"""通知/消息系统业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.notification_repository import (
    NotificationRepository,
    NotificationTemplateRepository,
)


class NotificationTemplateService:
    """通知模板服务。"""

    @staticmethod
    def get(template_id: str) -> dict[str, Any] | None:
        record = NotificationTemplateRepository.get_by_id(template_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        records = NotificationTemplateRepository.list_all()
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = NotificationTemplateRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def update(
        template_id: str, data: dict[str, Any], creator: str | None = None
    ) -> dict[str, Any] | None:
        record = NotificationTemplateRepository.get_by_id(template_id)
        if record is None:
            return None
        NotificationTemplateRepository.update(record, data, creator)
        db.session.commit()
        return record.to_dict()


class NotificationService:
    """通知记录服务。"""

    @staticmethod
    def get(notification_id: int) -> dict[str, Any] | None:
        record = NotificationRepository.get_by_id(notification_id)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_all(
        channel: str | None = None,
        send_status: str | None = None,
        ref_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = NotificationRepository.list_by_filters(
            channel, send_status, ref_type, page, per_page
        )
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = NotificationRepository.create(data, creator)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def send(notification_id: int) -> dict[str, Any] | None:
        """模拟发送通知（实际发送逻辑后续对接短信/邮件网关）。"""
        record = NotificationRepository.get_by_id(notification_id)
        if record is None:
            return None
        NotificationRepository.mark_sent(record)
        db.session.commit()
        return record.to_dict()
