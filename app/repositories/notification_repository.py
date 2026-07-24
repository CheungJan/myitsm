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
    def list_all(
        useflg: str | None = "1",
        ref_type: str | None = None,
    ) -> list[NotificationTemplate]:
        """列出模板，按 sort_no 升序、template_id 升序排序。

        Args:
            useflg: 有效标志筛选（None=全部）
            ref_type: 业务类型筛选（None=全部）
        """
        query = db.session.query(NotificationTemplate)
        if useflg is not None:
            query = query.filter(NotificationTemplate.useflg == useflg)
        if ref_type:
            query = query.filter(NotificationTemplate.ref_type == ref_type)
        return query.order_by(
            NotificationTemplate.sort_no.asc(),
            NotificationTemplate.template_id.asc(),
        ).all()

    @staticmethod
    def find_default(ref_type: str) -> NotificationTemplate | None:
        """按业务类型取默认模板（is_default='1'），无默认则取该 ref_type 下 sort_no 最小者。"""
        query = db.session.query(NotificationTemplate).filter(
            NotificationTemplate.useflg == "1",
            NotificationTemplate.ref_type == ref_type,
        )
        record = query.filter(NotificationTemplate.is_default == "1").first()
        if record is not None:
            return record
        return query.order_by(
            NotificationTemplate.sort_no.asc(),
            NotificationTemplate.template_id.asc(),
        ).first()

    @staticmethod
    def set_default(template_id: str, ref_type: str) -> None:
        """将指定模板设为该 ref_type 下默认（同 ref_type 其他模板取消默认）。"""
        db.session.query(NotificationTemplate).filter(
            NotificationTemplate.ref_type == ref_type,
            NotificationTemplate.is_default == "1",
        ).update({NotificationTemplate.is_default: "0"}, synchronize_session=False)
        db.session.query(NotificationTemplate).filter(
            NotificationTemplate.template_id == template_id,
        ).update({NotificationTemplate.is_default: "1"}, synchronize_session=False)

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
        ref_id: str | None = None,
        recipient: str | None = None,
        sender: str | None = None,
        page: int = 1,
        per_page: int = 20,
        order: str = "desc",
    ) -> tuple[list[Notification], int]:
        query = db.session.query(Notification).filter(Notification.useflg == "1")
        if channel:
            query = query.filter(Notification.channel == channel)
        if send_status:
            query = query.filter(Notification.send_status == send_status)
        if ref_type:
            query = query.filter(Notification.ref_type == ref_type)
        if ref_id:
            query = query.filter(Notification.ref_id == ref_id)
        if recipient:
            query = query.filter(Notification.recipient == recipient)
        if sender:
            query = query.filter(Notification.opercd == sender)
        query = query.order_by(
            Notification.gendate.asc() if order == "asc" else desc(Notification.gendate)
        )
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
    def find_latest_by_dispatch(dispatch_id: int | None) -> Notification | None:
        """按派工记录ID查最新一条通知（自动派工自动发送用）。"""
        if dispatch_id is None:
            return None
        return (
            db.session.query(Notification)
            .filter(Notification.useflg == "1", Notification.dispatch_id == dispatch_id)
            .order_by(desc(Notification.gendate))
            .first()
        )

    @staticmethod
    def mark_sent(record: Notification) -> Notification:
        """标记为已发送。"""
        record.send_status = "sent"
        record.send_time = datetime.now(UTC)
        return record

    @staticmethod
    def mark_failed(record: Notification, error: str) -> Notification:
        """标记为发送失败，累加重试次数。"""
        record.send_status = "failed"
        record.error_msg = error
        record.retry_count = (record.retry_count or 0) + 1
        return record

    @staticmethod
    def mark_read(record: Notification) -> Notification:
        """标记为已读（站内通知专用）。"""
        record.read_status = "read"
        record.read_time = datetime.now(UTC)
        return record
