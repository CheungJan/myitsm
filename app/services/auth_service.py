"""认证与会话服务。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.system import AccLog, User, UserGroup

__all__ = ["AuthService"]

logger = logging.getLogger(__name__)


class AuthService:
    """认证业务服务，对应 PB nvo_appmanager 登录事件链。"""

    @staticmethod
    def login(user_id: str, password: str) -> dict[str, Any] | None:
        """用户登录，返回 JWT token 和用户信息。"""
        user = db.session.get(User, user_id)
        if user is None or user.status != "1":
            return None

        if not check_password_hash(user.password, password):
            return None

        groups = db.session.query(UserGroup).filter(UserGroup.user_cd == user_id).all()

        token = _generate_token(user_id)

        # 记录登录日志
        log = AccLog(user_cd=user_id, action="LOGIN", detail="用户登录")
        db.session.add(log)
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
    def get_session(token: str) -> dict[str, Any] | None:
        """获取会话信息。"""
        payload = AuthService.validate_token(token)
        if payload is None:
            return None

        user = db.session.get(User, payload["user_code"])
        if user is None:
            return None

        groups = db.session.query(UserGroup).filter(UserGroup.user_cd == user.user_cd).all()

        return {
            "user_code": user.user_cd,
            "user_name": user.user_nm,
            "groups": [{"group_code": ug.group_cd} for ug in groups],
        }

    @staticmethod
    def hash_password(plain: str) -> str:
        """生成密码哈希。"""
        return generate_password_hash(plain)


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
