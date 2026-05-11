"""认证数据访问层。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.system import AccLog, User, UserGroup


class AuthRepository:
    """认证 Repository。"""

    @staticmethod
    def get_user(user_cd: str) -> User | None:
        """按编码获取用户。"""
        return db.session.get(User, user_cd)

    @staticmethod
    def get_user_groups(user_cd: str) -> list[UserGroup]:
        """获取用户所属用户组。"""
        return list(db.session.query(UserGroup).filter(UserGroup.user_cd == user_cd).all())

    @staticmethod
    def add_access_log(user_cd: str, action: str, detail: str) -> None:
        """写入访问日志。"""
        log = AccLog(user_cd=user_cd, action=action, detail=detail)
        db.session.add(log)

    @staticmethod
    def register_token(user_cd: str, token: str, expires_at: datetime) -> None:
        """注册活跃 token（用于多点登录检查）。"""
        log = AccLog(
            user_cd=user_cd,
            action="ACTIVE_TOKEN",
            detail=token,
            startdate=expires_at,
        )
        db.session.add(log)

    @staticmethod
    def revoke_user_tokens(user_cd: str) -> None:
        """撤销该用户所有活跃 token（登出或被踢时调用）。"""
        db.session.query(AccLog).filter(
            AccLog.user_cd == user_cd,
            AccLog.action == "ACTIVE_TOKEN",
        ).delete(synchronize_session=False)

    @staticmethod
    def revoke_token(token: str) -> None:
        """撤销指定 token + 清理所有过期 token。"""
        db.session.query(AccLog).filter(
            AccLog.action == "ACTIVE_TOKEN",
            AccLog.detail == token,
        ).delete(synchronize_session=False)
        AuthRepository.clean_expired_tokens()

    @staticmethod
    def clean_expired_tokens() -> None:
        """清理所有已过期的 token 记录。"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.query(AccLog).filter(
            AccLog.action == "ACTIVE_TOKEN",
            AccLog.startdate <= now,
        ).delete(synchronize_session=False)

    @staticmethod
    def has_active_token(user_cd: str) -> bool:
        """检查是否有未过期的活跃 token（严格多点登录检查）。"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return (
            db.session.query(AccLog)
            .filter(
                AccLog.user_cd == user_cd,
                AccLog.action == "ACTIVE_TOKEN",
                AccLog.startdate > now,
            )
            .count() > 0
        )

    @staticmethod
    def is_token_active(token: str) -> bool:
        """检查指定 token 是否仍处于活跃状态。"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return (
            db.session.query(AccLog)
            .filter(
                AccLog.action == "ACTIVE_TOKEN",
                AccLog.detail == token,
                AccLog.startdate > now,
            )
            .count() > 0
        )
