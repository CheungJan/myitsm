"""特殊表处理：SYS_USER合并 + 密码迁移。"""
from __future__ import annotations

from sqlalchemy import text

from app.migration.connector import DualConnector


def handle_sys_user_merge(conn: DualConnector) -> None:
    """sys_user → tmc13_users 合并。"""
    with conn.source.connect() as src:
        result = src.execute(
            text("SELECT user_id, user_name, pwd, del_flag FROM sys_user")
        )
        sys_users = [dict(zip(result.keys(), row)) for row in result.fetchall()]

    with conn.target.connect() as dst:
        existing = dst.execute(text("SELECT user_cd FROM tmc13_users"))
        existing_cds = {row[0] for row in existing.fetchall()}

    new_users = [
        {
            "user_cd": u["user_id"].strip() if u["user_id"] else "",
            "user_nm": u["user_name"] or "",
            "passwd": u["pwd"] or "",
            "useflg": "1" if u.get("del_flag") in (None, "0") else "0",
        }
        for u in sys_users
        if u["user_id"] and u["user_id"].strip() not in existing_cds
    ]

    if new_users:
        with conn.target.connect() as dst:
            for u in new_users:
                dst.execute(
                    text(
                        "INSERT INTO tmc13_users (user_cd, user_nm, passwd, useflg) "
                        "VALUES (:user_cd, :user_nm, :passwd, :useflg) "
                        "ON CONFLICT (user_cd) DO NOTHING"
                    ),
                    u,
                )
            dst.commit()


def handle_password_migration(conn: DualConnector) -> None:
    """密码迁移：新库 password 哈希列从 passwd 复制。"""
    with conn.target.connect() as dst:
        dst.execute(
            text(
                "UPDATE tmc13_users SET password = passwd "
                "WHERE password IS NULL OR password = ''"
            )
        )
        dst.commit()
