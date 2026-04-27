"""
认证与会话 API。
作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08
注意事项：对应 PB w_r_logon 登录窗口事件链与 nvo_appmanager 会话管理。
"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.services.auth_service import AuthService

__all__ = ["auth_bp"]

auth_bp = Blueprint("auth", __name__)
_service = AuthService()


def _bad_request(message: str):
    """生成统一 400 响应。"""
    payload = {
        "code": 400,
        "message": message,
        "data": {"request_id": getattr(g, "request_id", "")},
    }
    return jsonify(payload), 400


def _unauthorized(message: str = "未授权"):
    """生成统一 401 响应。"""
    payload = {
        "code": 401,
        "message": message,
        "data": {"request_id": getattr(g, "request_id", "")},
    }
    return jsonify(payload), 401


@auth_bp.post("/login")
def login():
    """
    用户登录。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        POST /api/v1/login
        {"user_id": "U001", "password": "secret", "server": "CCGL_MIG"}
    """
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id", "").strip()
    password = body.get("password", "").strip()
    server = body.get("server", "").strip()

    if user_id == "":
        return _bad_request("缺少参数 user_id")
    if password == "":
        return _bad_request("缺少参数 password")

    result = _service.login(user_id=user_id, password=password, server=server or None)
    if result is None:
        return _unauthorized("用户名或密码错误")

    payload = {
        "code": 0,
        "message": "登录成功",
        "data": result,
    }
    return jsonify(payload), 200


@auth_bp.post("/logout")
def logout():
    """
    用户登出。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        POST /api/v1/logout
        Header: Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()

    if token == "":
        return _bad_request("缺少认证令牌")

    success = _service.logout(token=token)
    payload = {
        "code": 0,
        "message": "登出成功" if success else "令牌无效或已过期",
        "data": {"logout": success},
    }
    return jsonify(payload), 200


@auth_bp.get("/session")
def get_session():
    """
    获取当前会话信息。

    返回值：
        Response: 统一结构 JSON 响应。

    示例：
        GET /api/v1/session
        Header: Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()

    if token == "":
        return _unauthorized("缺少认证令牌")

    session = _service.get_session(token)
    if session is None:
        return _unauthorized("令牌无效或已过期")

    payload = {
        "code": 0,
        "message": "成功",
        "data": session,
    }
    return jsonify(payload), 200
