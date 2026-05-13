"""
认证与会话服务。
作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08
注意事项：登录会话管理，对应 PB nvo_appmanager 登录事件。
"""

from __future__ import annotations

import secrets
import time
from typing import Any

from app.repositories.auth_repository import AuthRepository

__all__ = ["AuthService"]


class AuthService:
    """
    认证与会话业务服务。

    功能概述：
        处理用户登录、登出、会话管理；
        对应原 PB nvo_appmanager 的 oe_logon / oe_prelogon / oe_postlogon 事件链。
    """

    def __init__(
        self,
        auth_repository: AuthRepository | None = None,
    ) -> None:
        """
        初始化认证服务。

        参数：
            auth_repository: 认证仓储实例，默认自动创建。
        """
        self._auth_repository = auth_repository or AuthRepository()
        # 内存会话存储：token -> session_info
        # 后续应替换为 Redis / DB
        self._sessions: dict[str, dict[str, Any]] = {}

    def login(
        self,
        user_id: str,
        password: str,
        server: str | None = None,
    ) -> dict[str, Any] | None:
        """
        用户登录。

        参数：
            user_id: 用户编码（对应 PB Logon.UserID）。
            password: 密码（对应 PB Logon.Password）。
            server: 服务器名（可选，对应 PB Logon.Server）。

        返回值：
            dict[str, Any] | None: 登录成功返回会话信息，失败返回空。
            成功字段：token, user_code, user_name, groups, server, login_time
        """
        # 验证用户凭据（对应 PB oe_logon 事件）
        user = self._auth_repository.verify_user(user_id, password)
        if user is None:
            return None

        # 获取用户组
        groups = self._auth_repository.get_user_groups(user_id)

        # 生成会话令牌
        token = secrets.token_urlsafe(32)
        session = {
            "token": token,
            "user_code": user["user_code"],
            "user_name": user["user_name"],
            "groups": groups,
            "server": server or "",
            "login_time": time.time(),
            "last_active": time.time(),
        }

        # 存储会话
        self._sessions[token] = session

        return {
            "token": token,
            "user_code": session["user_code"],
            "user_name": session["user_name"],
            "groups": session["groups"],
            "server": session["server"],
            "login_time": session["login_time"],
        }

    def logout(self, token: str) -> bool:
        """
        用户登出。

        参数：
            token: 会话令牌。

        返回值：
            bool: 是否成功登出。
        """
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False

    def get_session(self, token: str) -> dict[str, Any] | None:
        """
        获取会话信息。

        参数：
            token: 会话令牌。

        返回值：
            dict[str, Any] | None: 会话信息或空（无效/过期）。
        """
        session = self._sessions.get(token)
        if session is None:
            return None

        # 更新最后活跃时间
        session["last_active"] = time.time()

        return {
            "token": session["token"],
            "user_code": session["user_code"],
            "user_name": session["user_name"],
            "groups": session["groups"],
            "server": session["server"],
            "login_time": session["login_time"],
        }

    def get_user_id(self, token: str) -> str | None:
        """
        从会话令牌获取用户编码。

        参数：
            token: 会话令牌。

        返回值：
            str | None: 用户编码或空（对应 PB of_GetUserID）。
        """
        session = self._sessions.get(token)
        if session is None:
            return None
        return session["user_code"]

    def validate_token(self, token: str) -> bool:
        """
        验证令牌是否有效。

        参数：
            token: 会话令牌。

        返回值：
            bool: 是否有效。
        """
        return token in self._sessions
