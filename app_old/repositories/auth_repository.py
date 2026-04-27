"""
认证仓储。
作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08
注意事项：用户认证与权限查询，对接 Oracle CCGL_MIG 用户表。
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None

__all__ = ["AuthRepository"]

logger = logging.getLogger(__name__)

# 用户认证查询 - 对应原 PB 登录验证逻辑
USER_AUTH_SQL = """
SELECT
    UserCd AS "UserCd",
    UserNm AS "UserNm",
    Password AS "Password",
    Status AS "Status"
FROM TMC20_USERS
WHERE UserCd = :user_id
  AND Status = '1'
""".strip()

# 用户所属用户组查询
USER_GROUPS_SQL = """
SELECT
    g.GroupCd AS "GroupCd",
    g.GroupNm AS "GroupNm"
FROM TMC21_USERGROUP ug
JOIN TMC30_GROUPS g ON ug.GroupCd = g.GroupCd
WHERE ug.UserCd = :user_id
""".strip()


class AuthRepository:
    """
    认证数据访问仓储。

    功能概述：
        封装用户认证、权限查询逻辑。
    """

    def __init__(self) -> None:
        """初始化仓储。"""
        pass

    def verify_user(self, user_id: str, password: str) -> dict[str, Any] | None:
        """
        验证用户凭据。

        参数：
            user_id: 用户编码。
            password: 密码（明文，Repository层不做加密比对）。

        返回值：
            dict[str, Any] | None: 用户信息（成功）或空（失败）。
            返回字段：UserCd, UserNm, Status
        """
        rows = self._query_all(USER_AUTH_SQL, {"user_id": user_id})
        if rows is None or len(rows) == 0:
            return None

        user = rows[0]
        # 密码比对逻辑：原PB使用 of_Encrypt/of_Decrypt
        # 当前简化实现：直接比对（后续应接入统一加密服务）
        stored_password = user.get("Password", "")
        if stored_password != password:
            return None

        return {
            "user_code": user["UserCd"],
            "user_name": user["UserNm"],
            "status": user["Status"],
        }

    def get_user_groups(self, user_id: str) -> list[dict[str, Any]]:
        """
        获取用户所属用户组列表。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 用户组列表。
        """
        rows = self._query_all(USER_GROUPS_SQL, {"user_id": user_id})
        if rows is None:
            return []
        return [
            {"group_code": row["GroupCd"], "group_name": row["GroupNm"]}
            for row in rows
        ]

    def _get_oracle_config(self) -> dict[str, str] | None:
        """解析 Oracle 连接配置。"""
        oracle_user = os.getenv("ORACLE_USER", os.getenv("DB_USER", "")).strip()
        oracle_password = os.getenv("ORACLE_PASSWORD", os.getenv("DB_PASSWORD", "")).strip()
        oracle_dsn = os.getenv("ORACLE_DSN", os.getenv("DB_DSN", "")).strip()
        tns_admin = os.getenv("TNS_ADMIN", os.getenv("ORACLE_TNS_ADMIN", "")).strip()

        if oracle_user == "" or oracle_password == "" or oracle_dsn == "":
            return None

        config = {
            "user": oracle_user,
            "password": oracle_password,
            "dsn": oracle_dsn,
        }
        if tns_admin != "":
            config["tns_admin"] = tns_admin
        return config

    def _query_all(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]] | None:
        """执行查询并返回多行结果。"""
        if oracledb is None:
            logger.warning("未安装 oracledb")
            return None

        config = self._get_oracle_config()
        if config is None:
            logger.warning("Oracle 连接环境变量不完整")
            return None

        try:
            tns_admin = config.get("tns_admin")
            if tns_admin is not None:
                os.environ.setdefault("TNS_ADMIN", tns_admin)

            with oracledb.connect(
                user=config["user"],
                password=config["password"],
                dsn=config["dsn"],
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    columns = [item[0] for item in cursor.description]
                    return [
                        {columns[index]: value for index, value in enumerate(row)}
                        for row in cursor.fetchall()
                    ]
        except Exception:
            logger.exception("认证查询失败")
            return None
