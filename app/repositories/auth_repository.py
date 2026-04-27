"""认证数据访问层。"""

from __future__ import annotations

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
        """写入访问日志并提交。"""
        log = AccLog(user_cd=user_cd, action=action, detail=detail)
        db.session.add(log)
        db.session.commit()
