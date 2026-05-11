"""认证与会话服务。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.system import SysParm
from app.repositories.auth_repository import AuthRepository

__all__ = ["AuthService"]

logger = logging.getLogger(__name__)


class AuthService:
    """认证业务服务，对应 PB nvo_appmanager 登录事件链。"""

    def __init__(self, repo: AuthRepository | None = None) -> None:
        self._repo = repo or AuthRepository()

    @staticmethod
    def logout(user_cd: str, repo: AuthRepository | None = None) -> None:
        """登出，清除多点登录标记。"""
        _repo = repo or AuthRepository()
        _repo.add_access_log(user_cd=user_cd, action="LOGOUT", detail="用户登出")
        db.session.commit()

    @staticmethod
    def check_user_active(user_id: str, repo: AuthRepository | None = None) -> str | None:
        """
        检查用户是否可登录。返回 None 表示正常，返回字符串为错误原因。
        """
        _repo = repo or AuthRepository()
        user = _repo.get_user(user_id)
        if user is None:
            return "用户不存在"
        if user.status != "1":
            return "用户已被禁用，无法登录"
        return None

    @staticmethod
    def login(
        user_id: str,
        password: str,
        repo: AuthRepository | None = None,
    ) -> dict[str, Any] | None:
        """用户登录，返回 JWT token 和用户信息。"""
        _repo = repo or AuthRepository()

        user = _repo.get_user(user_id)
        if user is None or user.status != "1":
            return None

        # 1. 哈希比对（已升级的密码）
        if check_password_hash(user.password or "", password):
            pass
        # 2. 明文比对（从旧系统迁移未升级）+ 自动升级为哈希
        elif user.password and user.password == password:
            user.password = generate_password_hash(password, method="pbkdf2:sha256")
            user.passwd = None  # 清除明文备份
            db.session.flush()
            logger.info("用户 %s 密码已从明文升级为哈希", user_id)
        else:
            return None

        # 多点登录检查
        sp = db.session.get(SysParm, "SYSPARM")
        if sp and sp.allowmultilogon == "0":
            existed = _repo.has_recent_login(user_id, hours=8)
            if existed:
                return {"error": "该账号已在其他设备登录，管理员禁止多点登录"}

        groups = _repo.get_user_groups(user_id)
        token = _generate_token(user_id)

        _repo.add_access_log(user_cd=user_id, action="LOGIN", detail="用户登录")
        db.session.commit()

        return {
            "token": token,
            "user_code": user.user_cd,
            "user_name": user.user_nm,
            "groups": [{"group_code": ug.group_cd} for ug in groups],
        }

    @staticmethod
    def validate_token(token: str) -> dict[str, Any] | None:
        """验证 JWT token，返回用户信息。"""
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=[current_app.config.get("JWT_ALGORITHM", "HS256")],
            )
            user_cd = payload.get("sub")
            if user_cd is None:
                return None
            return {"user_code": user_cd, "exp": payload.get("exp")}
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def get_session(
        token: str,
        repo: AuthRepository | None = None,
    ) -> dict[str, Any] | None:
        """获取会话信息。"""
        _repo = repo or AuthRepository()

        payload = AuthService.validate_token(token)
        if payload is None:
            return None

        user = _repo.get_user(payload["user_code"])
        if user is None:
            return None

        groups = _repo.get_user_groups(user.user_cd)

        return {
            "user_code": user.user_cd,
            "user_name": user.user_nm,
            "groups": [{"group_code": ug.group_cd} for ug in groups],
        }

    @staticmethod
    def hash_password(plain: str) -> str:
        """生成密码哈希（pbkdf2:sha256，适配 VARCHAR(128) 列）。"""
        return generate_password_hash(plain, method="pbkdf2:sha256")


def _generate_token(user_id: str) -> str:
    """生成 JWT token。"""
    exp_seconds = current_app.config.get("JWT_EXPIRATION_SECONDS", 28800)
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=int(exp_seconds)),
    }
    return jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm=current_app.config.get("JWT_ALGORITHM", "HS256"),
    )
