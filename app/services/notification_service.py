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
    def list_all(
        ref_type: str | None = None,
        useflg: str | None = None,
    ) -> list[dict[str, Any]]:
        records = NotificationTemplateRepository.list_all(
            useflg=useflg, ref_type=ref_type
        )
        return [r.to_dict() for r in records]

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        record = NotificationTemplateRepository.create(data, creator)
        # 若标记为默认，同 ref_type 其他模板取消默认
        if data.get("is_default") == "1" and data.get("ref_type"):
            NotificationTemplateRepository.set_default(
                record.template_id, data["ref_type"]
            )
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
        # 若标记为默认，同 ref_type 其他模板取消默认
        if data.get("is_default") == "1" and record.ref_type:
            NotificationTemplateRepository.set_default(template_id, record.ref_type)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def set_default(template_id: str) -> dict[str, Any] | None:
        """将指定模板设为其 ref_type 下的默认模板。"""
        record = NotificationTemplateRepository.get_by_id(template_id)
        if record is None or not record.ref_type:
            return None
        NotificationTemplateRepository.set_default(template_id, record.ref_type)
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def preview(
        subject: str, body: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """用 Jinja2 渲染模板预览，返回渲染后的 subject/body。

        若未提供 context，使用 DISPATCH 模板示例上下文。
        """
        from jinja2 import Template

        # DISPATCH 模板示例上下文（对齐 _create_notification 的字段）
        default_context: dict[str, Any] = {
            "maintenance_id": "MD20260715001",
            "store_id": "S001",
            "cust_card": "6222001234567890",
            "cust_nm": "示例门店",
            "address": "上海市浦东新区张江路100号",
            "phone_no": "021-12345678",
            "contactor": "李四",
            "accpectder": "552",
            "accpectder_nm": "张三",
            "accpectd_group": "A1",
            "fault_type": "1",
            "fault_type_nm": "硬件故障",
            "short_description": "POS无法开机",
            "request_time": "2026-07-15 10:00:00",
            "current_status": "1",
            "current_status_nm": "新建",
            "urgency": "一般",
            "operator": "SYSTEM",
            "operator_nm": "系统管理员",
            "dispatch_time": "2026-07-15 10:05:00",
            "area_cd": "A1",
            "area_nm": "华东区",
            "company_id": "C001",
            "company_nm": "示例有限公司",
            "d2d_time": "",
            "d2d_engineer": "",
            "d2d_engineer_nm": "",
            "expected_completion": "",
            "close_time": "",
            "close_reason": "",
        }
        ctx = {**default_context, **(context or {})}
        try:
            rendered_subject = Template(subject or "").render(**ctx)
            rendered_body = Template(body or "").render(**ctx)
        except Exception as e:
            return {"subject": subject, "body": body, "error": str(e)}
        return {"subject": rendered_subject, "body": rendered_body, "context": ctx}


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
        ref_id: str | None = None,
        recipient: str | None = None,
        sender: str | None = None,
        page: int = 1,
        per_page: int = 20,
        order: str = "desc",
    ) -> dict[str, Any]:
        items, total = NotificationRepository.list_by_filters(
            channel, send_status, ref_type, ref_id, recipient, sender, page, per_page, order
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
        """发送通知：按 channel 分发到真实网关。

        - internal: 已落库即视为发送成功（站内通知）
        - email/sms/dingtalk/feishu/wecom/ntfy: 调用对应 Gateway 真实发送
        - 支持 pending/failed 状态重试
        """
        record = NotificationRepository.get_by_id(notification_id)
        if record is None:
            return None
        # 仅允许 pending/failed 状态发送，已发送不重复
        if record.send_status == "sent":
            return record.to_dict()

        # internal 渠道：直接标记为已发送（站内通知落库即成功）
        if record.channel == "internal":
            NotificationRepository.mark_sent(record)
            record.error_msg = None
            db.session.commit()
            return record.to_dict()

        # 其他渠道：通过 GatewayFactory 分发到真实网关
        from app.services.gateways.factory import GatewayFactory

        if not GatewayFactory.is_enabled(record.channel):
            NotificationRepository.mark_failed(record, f"渠道未启用: {record.channel}（检查 NOTIFICATION_ENABLED_CHANNELS 配置）")
            db.session.commit()
            return record.to_dict()

        gateway = GatewayFactory.get(record.channel)
        if gateway is None:
            NotificationRepository.mark_failed(record, f"渠道未实现: {record.channel}")
            db.session.commit()
            return record.to_dict()

        try:
            success, error = gateway.send(
                record.recipient, record.subject or "", record.body or ""
            )
            if success:
                NotificationRepository.mark_sent(record)
                record.error_msg = None
            else:
                NotificationRepository.mark_failed(record, error or "网关返回未知错误")
        except Exception as e:
            NotificationRepository.mark_failed(record, f"网关异常: {e}")
        db.session.commit()
        return record.to_dict()

    @staticmethod
    def mark_read(notification_id: int) -> dict[str, Any] | None:
        """标记站内通知为已读。"""
        record = NotificationRepository.get_by_id(notification_id)
        if record is None:
            return None
        if record.read_status != "read":
            NotificationRepository.mark_read(record)
            db.session.commit()
        return record.to_dict()

    @staticmethod
    def unread_count(user_cd: str) -> int:
        """获取当前用户未读站内通知数（用于前端徽标）。"""
        from app.models.notification import Notification

        return (
            db.session.query(db.func.count(Notification.id))
            .filter(
                Notification.useflg == "1",
                Notification.channel == "internal",
                Notification.recipient == user_cd,
                Notification.send_status == "sent",
                Notification.read_status == "unread",
            )
            .scalar()
            or 0
        )
