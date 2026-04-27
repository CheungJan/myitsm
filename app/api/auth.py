"""
认证与会话 API。

对应 PB w_r_logon 登录窗口事件链与 nvo_appmanager 会话管理。
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Blueprint, g, request
from pydantic import ValidationError

from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService
from app.utils.response import error_response, success_response

__all__ = ["auth_bp", "login_required"]

auth_bp = Blueprint("auth", __name__)


def login_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    """JWT 认证装饰器。"""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response(message="缺少认证令牌", code=401)

        token = auth_header[7:].strip()
        if not token:
            return error_response(message="令牌为空", code=401)

        payload = AuthService.validate_token(token)
        if payload is None:
            return error_response(message="令牌无效或已过期", code=401)

        g.current_user = payload["user_code"]
        return fn(*args, **kwargs)

    return wrapper


@auth_bp.post("/login")
def login():  # type: ignore[no-untyped-def]
    """
    用户登录。

    POST /api/v1/login
    {"user_id": "U001", "password": "secret"}
    """
    body = request.get_json(silent=True) or {}

    try:
        req = LoginRequest(**body)
    except ValidationError as exc:
        errors = exc.errors()
        msg = "; ".join(f"{e['loc'][0]}: {e['msg']}" for e in errors if e.get("loc"))
        return error_response(message=msg or "参数校验失败", code=400)

    result = AuthService.login(user_id=req.user_id, password=req.password)
    if result is None:
        return error_response(message="用户名或密码错误", code=401)

    return success_response(data=result, message="登录成功")


@auth_bp.get("/session")
@login_required
def get_session():  # type: ignore[no-untyped-def]
    """
    获取当前会话信息。

    GET /api/v1/session (Header: Authorization: Bearer <token>)
    """
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:].strip()
    session = AuthService.get_session(token)
    if session is None:
        return error_response(message="会话无效", code=401)
    return success_response(data=session)
