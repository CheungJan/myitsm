"""通知/消息系统数据访问层。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc

from app.extensions import db
from app.models.notification import Notification, NotificationTemplate


def _gen_id(prefix: str = "") -> str:
    """生成8位唯一ID。"""
    return (prefix + uuid.uuid4().hex[:8].upper())[:8]


class NotificationTemplateRepository:
    """通知模板数据访问。"""

    @staticmethod
    def get_by_id(template_id: str) -> NotificationTemplate | None:
        return db.session.get(NotificationTemplate, template_id)

    @staticmethod
    def list_all(useflg: str | None = "1") -> list[NotificationTemplate]:
        query = db.session.query(NotificationTemplate)
        if useflg is not None:
            query = query.filter(NotificationTemplate.useflg == useflg)
        return query.order_by(NotificationTemplate.template_id).all()

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> NotificationTemplate:
        now = datetime.now(UTC)
        if "template_id" not in data:
            data["template_id"] = _gen_id("NT")
        record = NotificationTemplate(
            opercd=creator,
            gendate=now,
            upddate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def update(
        record: NotificationTemplate,
        data: dict[str, Any],
        creator: str | None = None,
    ) -> NotificationTemplate:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        if creator:
            record.opercd = creator
        record.upddate = datetime.now(UTC)
        return record


class NotificationRepository:
    """通知记录数据访问。"""

    @staticmethod
    def get_by_id(notification_id: int) -> Notification | None:
        return db.session.get(Notification, notification_id)

    @staticmethod
    def list_by_filters(
        channel: str | None = None,
        send_status: str | None = None,
        ref_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Notification], int]:
        query = db.session.query(Notification).filter(Notification.useflg == "1")
        if channel:
            query = query.filter(Notification.channel == channel)
        if send_status:
            query = query.filter(Notification.send_status == send_status)
        if ref_type:
            query = query.filter(Notification.ref_type == ref_type)
        query = query.order_by(desc(Notification.gendate))
        total: int = query.count()
        items: list[Notification] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> Notification:
        now = datetime.now(UTC)
        record = Notification(
            opercd=creator,
            gendate=now,
            **data,
        )
        db.session.add(record)
        return record

    @staticmethod
    def mark_sent(record: Notification) -> Notification:
        """标记为已发送。"""
        record.send_status = "sent"
        record.send_time = datetime.now(UTC)
        return record

    @staticmethod
    def mark_failed(record: Notification, error: str) -> Notification:
        """标记为发送失败。"""
        record.send_status = "failed"
        record.error_msg = error
        return record
