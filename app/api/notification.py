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
    """通知模板列表，支持 ref_type、useflg 筛选（useflg 不传=全部）。"""
    ref_type = request.args.get("ref_type")
    useflg = request.args.get("useflg")
    items = NotificationTemplateService.list_all(ref_type=ref_type, useflg=useflg)
    return success_response(data={"items": items, "total": len(items)})


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


@notification_bp.post("/notification-templates/preview")
@login_required
def preview_template():  # type: ignore[no-untyped-def]
    """模板预览：用示例上下文渲染 subject/body，供编辑器实时预览。"""
    body = request.get_json(silent=True) or {}
    subject = body.get("subject", "")
    body_text = body.get("body", "")
    context = body.get("context", {}) or {}
    data = NotificationTemplateService.preview(subject, body_text, context)
    return success_response(data=data)


@notification_bp.post("/notification-templates/<template_id>/set-default")
@login_required
def set_default_template(template_id: str):  # type: ignore[no-untyped-def]
    """将指定模板设为其 ref_type 下的默认模板。"""
    data = NotificationTemplateService.set_default(template_id)
    if data is None:
        return error_response(message="模板不存在或未配置业务类型", code=404)
    return success_response(data=data, message="已设为默认")


# ---- 通知记录 ----


@notification_bp.get("/notifications")
@login_required
def list_notifications():  # type: ignore[no-untyped-def]
    """通知记录列表。

    查询参数:
        view: inbox(默认)=收件箱(recipient=当前用户), sent=我发送的(sender=当前用户), all=全量
        recipient: 指定接收方过滤
        sender: 指定发送方过滤
    """
    channel = request.args.get("channel")
    send_status = request.args.get("send_status")
    ref_type = request.args.get("ref_type")
    ref_id = request.args.get("ref_id")
    view = request.args.get("view", "inbox")
    recipient = request.args.get("recipient")
    sender = request.args.get("sender")
    user_cd: str = g.current_user
    if view == "inbox" and not recipient:
        recipient = user_cd
    elif view == "sent" and not sender:
        sender = user_cd
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    order = request.args.get("order", "desc")
    data = NotificationService.list_all(
        channel, send_status, ref_type, ref_id, recipient, sender, page, per_page, order
    )
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


@notification_bp.post("/notifications/<int:notification_id>/read")
@login_required
def mark_read_notification(notification_id: int):  # type: ignore[no-untyped-def]
    """标记站内通知为已读。"""
    data = NotificationService.mark_read(notification_id)
    if data is None:
        return error_response(message="通知不存在", code=404)
    return success_response(data=data, message="已标记为已读")


@notification_bp.get("/notifications/unread-count")
@login_required
def unread_count():  # type: ignore[no-untyped-def]
    """获取当前用户未读站内通知数（用于前端徽标）。"""
    user_cd: str = g.current_user
    count = NotificationService.unread_count(user_cd)
    return success_response(data={"count": count})


@notification_bp.get("/channels")
@login_required
def list_channels():  # type: ignore[no-untyped-def]
    """返回已实现的通知渠道列表（含启用状态、标签、所需配置）。

    供前端通知模板/通知记录页选用渠道，受 NOTIFICATION_ENABLED_CHANNELS 环境变量控制。
    """
    from app.services.gateways.factory import GatewayFactory

    return success_response(data={"channels": GatewayFactory.channels_info()})
