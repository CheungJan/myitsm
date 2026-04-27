"""
通知/消息系统 API（Tier-1 扩展，替代飞信）。

路由前缀：/api/v1/notification
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.notification import (
    NotificationCreate,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
)
from app.services.notification_service import (
    NotificationService,
    NotificationTemplateService,
)
from app.utils.response import error_response, success_response

__all__ = ["notification_bp"]

notification_bp = Blueprint("notification", __name__)


# ---- 通知模板 ----


@notification_bp.get("/notification-templates")
@login_required
def list_templates():  # type: ignore[no-untyped-def]
    """通知模板列表。"""
    data = NotificationTemplateService.list_all()
    return success_response(data=data)


@notification_bp.get("/notification-templates/<template_id>")
@login_required
def get_template(template_id: str):  # type: ignore[no-untyped-def]
    """通知模板详情。"""
    data = NotificationTemplateService.get(template_id)
    if data is None:
        return error_response(message="模板不存在", code=404)
    return success_response(data=data)


@notification_bp.post("/notification-templates")
@login_required
def create_template():  # type: ignore[no-untyped-def]
    """创建通知模板。"""
    body = NotificationTemplateCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = NotificationTemplateService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@notification_bp.put("/notification-templates/<template_id>")
@login_required
def update_template(template_id: str):  # type: ignore[no-untyped-def]
    """更新通知模板。"""
    body = NotificationTemplateUpdate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = NotificationTemplateService.update(
        template_id, body.model_dump(exclude_unset=True), user_cd
    )
    if data is None:
        return error_response(message="模板不存在", code=404)
    return success_response(data=data, message="更新成功")


# ---- 通知记录 ----


@notification_bp.get("/notifications")
@login_required
def list_notifications():  # type: ignore[no-untyped-def]
    """通知记录列表。"""
    channel = request.args.get("channel")
    send_status = request.args.get("send_status")
    ref_type = request.args.get("ref_type")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = NotificationService.list_all(channel, send_status, ref_type, page, per_page)
    return success_response(data=data)


@notification_bp.post("/notifications")
@login_required
def create_notification():  # type: ignore[no-untyped-def]
    """创建通知记录。"""
    body = NotificationCreate(**request.get_json(force=True))
    user_cd: str = g.current_user
    data = NotificationService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@notification_bp.post("/notifications/<int:notification_id>/send")
@login_required
def send_notification(notification_id: int):  # type: ignore[no-untyped-def]
    """发送通知。"""
    data = NotificationService.send(notification_id)
    if data is None:
        return error_response(message="通知不存在", code=404)
    return success_response(data=data, message="发送成功")
