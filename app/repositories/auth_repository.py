"""认证数据访问层。"""

from __future__ import annotations

from datetime import datetime, timedelta

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
    def has_recent_login(user_cd: str, hours: int = 8) -> bool:
        """检查用户是否在指定小时内有无有效登录（多点登录检查）。"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return db.session.query(AccLog).filter(
            AccLog.user_cd == user_cd,
            AccLog.action == "LOGIN",
            AccLog.created_at >= cutoff,
        ).count() > 0
