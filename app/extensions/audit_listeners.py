"""审计字段自动维护。

为所有继承 BaseModel 的模型自动维护 update_time / updator 字段，
覆盖 Repository.update() 和 Service.transition() 未显式赋值的情况，
确保任何 UPDATE 操作都更新审计字段。
"""

from __future__ import annotations

from datetime import UTC, datetime


def register_audit_listeners() -> None:
    """注册审计字段自动维护事件监听器。"""
    from sqlalchemy import event

    from app.extensions import db

    @event.listens_for(db.session, "before_flush")
    def _auto_audit_fields(session, flush_context, instances):  # type: ignore[no-untyped-def]
        """flush 前自动填充 update_time / updator。

        仅对已修改（is_modified）的 BaseModel 子类生效，
        若应用层已显式赋值则保留应用层的值。
        """
        now = datetime.now(UTC)
        # 尝试从请求上下文取当前用户
        current_user = _get_current_user()

        for obj in session.dirty:
            if not hasattr(obj, "update_time"):
                continue

            # 如果 update_time 未被应用层显式修改，自动赋当前时间
            if hasattr(obj, "update_time") and not _is_attr_modified(
                session, obj, "update_time"
            ):
                setattr(obj, "update_time", now)

            # updator：仅在模型有此字段且未被显式修改时自动填入
            if hasattr(obj, "updator") and not _is_attr_modified(
                session, obj, "updator"
            ):
                current = getattr(obj, "updator", None)
                if not current and current_user:
                    setattr(obj, "updator", current_user)


def _get_current_user() -> str:
    """从请求上下文获取当前用户编码。"""
    try:
        from flask import g, has_request_context

        if has_request_context():
            user = getattr(g, "current_user", None)
            if user:
                return str(user)
            # fallback: X-User-Cd header
            from flask import request

            hdr = request.headers.get("X-User-Cd", "")
            if hdr:
                return hdr
    except Exception:
        pass
    return ""


def _is_attr_modified(session: object, obj: object, attr_name: str) -> bool:
    """检查指定属性在本次会话中是否已被应用层修改。"""
    try:
        from sqlalchemy.inspection import inspect as sa_inspect

        insp = sa_inspect(obj)
        if insp.attrs[attr_name].history.has_changes():
            return True
    except Exception:
        pass
    return False
