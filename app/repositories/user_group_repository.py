"""
用户组与权限仓储。
作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08
注意事项：用户组、组权限、用户菜单管理，对应 app_system.pbl 权限模块。
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None

__all__ = ["UserGroupRepository"]

logger = logging.getLogger(__name__)

# 用户组列表查询
GROUPS_LIST_SQL = """
SELECT
    GroupCd AS "GroupCd",
    GroupNm AS "GroupNm",
    GroupType AS "GroupType",
    UseFlg AS "UseFlg"
FROM TMC30_GROUPS
WHERE UseFlg = '1'
ORDER BY GroupCd
""".strip()

# 用户所属组查询
USER_GROUPS_SQL = """
SELECT
    g.GroupCd AS "GroupCd",
    g.GroupNm AS "GroupNm",
    g.GroupType AS "GroupType"
FROM TMC21_USERGROUP ug
JOIN TMC30_GROUPS g ON ug.GroupCd = g.GroupCd
WHERE ug.UserCd = :user_id
  AND g.UseFlg = '1'
ORDER BY g.GroupCd
""".strip()

# 组内用户查询
GROUP_USERS_SQL = """
SELECT
    u.UserCd AS "UserCd",
    u.UserNm AS "UserNm",
    u.Status AS "Status"
FROM TMC21_USERGROUP ug
JOIN TMC20_USERS u ON ug.UserCd = u.UserCd
WHERE ug.GroupCd = :group_cd
  AND u.Status = '1'
ORDER BY u.UserCd
""".strip()

# 组权限查询
GROUP_RIGHTS_SQL = """
SELECT
    GroupCd AS "GroupCd",
    MenuCd AS "MenuCd",
    FuncCd AS "FuncCd",
    Scale AS "Scale"
FROM TMC31_GroupRight
WHERE GroupCd = :group_cd
  AND UseFlg = '1'
""".strip()

# 用户菜单查询（基于组权限聚合）
USER_MENU_RIGHTS_SQL = """
SELECT DISTINCT
    m.MenuCd AS "MenuCd",
    m.MenuNm AS "MenuNm",
    m.Parent AS "Parent",
    m.LevelCd AS "LevelCd",
    m.ChildFlg AS "ChildFlg",
    m.OrdNo AS "OrdNo",
    m.ExePath AS "ExePath",
    MAX(gr.Scale) AS "Scale"
FROM TMC01_MENUS m
JOIN TMC31_GroupRight gr ON m.MenuCd = gr.MenuCd
JOIN TMC21_USERGROUP ug ON gr.GroupCd = ug.GroupCd
WHERE ug.UserCd = :user_id
  AND m.UseFlg = '1'
  AND gr.UseFlg = '1'
GROUP BY m.MenuCd, m.MenuNm, m.Parent, m.LevelCd, m.ChildFlg, m.OrdNo, m.ExePath
ORDER BY m.OrdNo
""".strip()


class UserGroupRepository:
    """
    用户组与权限数据访问仓储。

    功能概述：
        封装用户组、组权限、用户菜单权限查询逻辑；
        对应 PB app_system.pbl 的 u_mc_groups, w_r_mc_groupright 等功能。
    """

    def __init__(self) -> None:
        """初始化仓储。"""
        pass

    def list_groups(self) -> list[dict[str, Any]]:
        """
        获取所有用户组列表。

        返回值：
            list[dict[str, Any]]: 用户组列表。
        """
        rows = self._query_all(GROUPS_LIST_SQL, {})
        if rows is None:
            return []
        return [
            {
                "group_code": row["GroupCd"],
                "group_name": row["GroupNm"],
                "group_type": row["GroupType"],
                "use_flag": row["UseFlg"],
            }
            for row in rows
        ]

    def get_user_groups(self, user_id: str) -> list[dict[str, Any]]:
        """
        获取用户所属的用户组列表。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 用户组列表。
        """
        rows = self._query_all(USER_GROUPS_SQL, {"user_id": user_id})
        if rows is None:
            return []
        return [
            {
                "group_code": row["GroupCd"],
                "group_name": row["GroupNm"],
                "group_type": row["GroupType"],
            }
            for row in rows
        ]

    def get_group_users(self, group_cd: str) -> list[dict[str, Any]]:
        """
        获取用户组内的用户列表。

        参数：
            group_cd: 用户组编码。

        返回值：
            list[dict[str, Any]]: 用户列表。
        """
        rows = self._query_all(GROUP_USERS_SQL, {"group_cd": group_cd})
        if rows is None:
            return []
        return [
            {
                "user_code": row["UserCd"],
                "user_name": row["UserNm"],
                "status": row["Status"],
            }
            for row in rows
        ]

    def get_group_rights(self, group_cd: str) -> list[dict[str, Any]]:
        """
        获取用户组的权限列表。

        参数：
            group_cd: 用户组编码。

        返回值：
            list[dict[str, Any]]: 权限列表（菜单编码+权限级别）。
        """
        rows = self._query_all(GROUP_RIGHTS_SQL, {"group_cd": group_cd})
        if rows is None:
            return []
        return [
            {
                "group_code": row["GroupCd"],
                "menu_code": row["MenuCd"],
                "func_code": row["FuncCd"],
                "scale": row["Scale"],
            }
            for row in rows
        ]

    def get_user_menu_rights(self, user_id: str) -> list[dict[str, Any]]:
        """
        获取用户有权限的菜单列表（基于所属组的权限聚合）。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 有权限的菜单列表，包含最高权限级别。
        """
        rows = self._query_all(USER_MENU_RIGHTS_SQL, {"user_id": user_id})
        if rows is None:
            return []
        return [
            {
                "menu_code": row["MenuCd"],
                "menu_name": row["MenuNm"],
                "parent": row["Parent"],
                "level_cd": row["LevelCd"],
                "child_flag": row["ChildFlg"],
                "order_no": row["OrdNo"],
                "exe_path": row["ExePath"],
                "scale": row["Scale"],  # 权限级别
            }
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
            logger.exception("用户组权限查询失败")
            return None
