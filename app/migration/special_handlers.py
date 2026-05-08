"""特殊表处理：复合PK→代理键、P0默认值、密码迁移、B类合并表等。"""
from __future__ import annotations

from sqlalchemy import text

from app.migration.connector import DualConnector


def handle_sys_user_merge(conn: DualConnector) -> None:
    """SYS_USER → tmc13_users 合并。

    逻辑：
    1. 读取 SYS_USER 表中不在 tmc13_users 中的用户
    2. 映射字段：USER_ID→usercd, USER_NAME→usernm, PWD→passwd
    3. 以 usercd 去重，优先保留 tmc13_users 中的数据
    """
    with conn.source.connect() as src:
        result = src.execute(
            text("SELECT USER_ID, USER_NAME, PWD, DEL_FLAG FROM SYS_USER")
        )
        sys_users = [dict(zip(result.keys(), row)) for row in result.fetchall()]

    with conn.target.connect() as dst:
        existing = dst.execute(text("SELECT usercd FROM tmc13_users"))
        existing_cds = {row[0] for row in existing.fetchall()}

    new_users = [
        {
            "usercd": u["USER_ID"].strip() if u["USER_ID"] else "",
            "usernm": u["USER_NAME"] or "",
            "passwd": u["PWD"] or "",
            "useflg": "1" if u.get("DEL_FLAG") in (None, "0") else "0",
        }
        for u in sys_users
        if u["USER_ID"] and u["USER_ID"].strip() not in existing_cds
    ]

    if new_users:
        with conn.target.connect() as dst:
            for u in new_users:
                dst.execute(
                    text(
                        "INSERT INTO tmc13_users (usercd, usernm, passwd, useflg) "
                        "VALUES (:usercd, :usernm, :passwd, :useflg) "
                        "ON CONFLICT (usercd) DO NOTHING"
                    ),
                    u,
                )
            dst.commit()


def handle_password_migration(conn: DualConnector) -> None:
    """密码迁移：旧库 passwd 已导入，新库 password 哈希列置 NULL。

    迁移完成后统一重置密码为默认值。
    """
    with conn.target.connect() as dst:
        dst.execute(
            text("UPDATE tmc13_users SET password = NULL WHERE password IS NOT NULL")
        )
        dst.commit()
