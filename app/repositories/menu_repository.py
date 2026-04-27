"""
主框架菜单仓储。
作者：Cascade
创建时间：2026-03-24
变更时间：2026-04-08
注意事项：优先走 Oracle 真实查询；连接不可用时回退占位数据。
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None

__all__ = ["MenuRepository"]


MENU_LIST_SQL = """
SELECT
    MenuCd AS "MenuCd",
    MenuNm AS "MenuNm",
    Parent AS "Parent",
    LevelCd AS "LevelCd",
    ChildFlg AS "ChildFlg",
    OrdNo AS "OrdNo",
    PicName AS "PicName",
    ExePath AS "ExePath",
    OpenFlg AS "OpenFlg"
FROM TMC01_MENUS
ORDER BY OrdNo
""".strip()

USER_MENU_SQL = """
SELECT
    MenuCd AS "MenuCd"
FROM TMC03_USERMENUS
WHERE UserCd = :user_id
""".strip()

OPEN_OBJECT_SQL = """
SELECT
    MenuCd AS "MenuCd",
    MenuNm AS "MenuNm",
    Parent AS "Parent",
    LevelCd AS "LevelCd",
    ChildFlg AS "ChildFlg",
    OrdNo AS "OrdNo",
    PicName AS "PicName",
    ExePath AS "ExePath",
    OpenFlg AS "OpenFlg"
FROM TMC01_MENUS
WHERE MenuCd = :menu_code
""".strip()

logger = logging.getLogger(__name__)


class MenuRepository:
    """
    菜单数据访问仓储。

    功能概述：
        封装菜单读取逻辑，向服务层提供统一数据结构。
    """

    def fetch_menus(self, user_id: str) -> list[dict[str, Any]]:
        """
        读取菜单数据。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 菜单项列表。

        副作用：
            无。
        """
        rows = self._query_all(MENU_LIST_SQL, {})
        if rows is not None:
            return rows
        _ = user_id
        return self._fallback_menus()

    def fetch_user_menus(self, user_id: str) -> list[dict[str, Any]]:
        """
        读取用户常用菜单编码列表。

        参数：
            user_id: 用户编码。

        返回值：
            list[dict[str, Any]]: 用户菜单编码列表。
        """
        rows = self._query_all(USER_MENU_SQL, {"user_id": user_id})
        if rows is not None:
            return rows
        return [{"MenuCd": "M002"}]

    def get_menu_by_code(self, menu_code: str, user_id: str) -> dict[str, Any] | None:
        """
        根据菜单编码读取菜单详情。

        参数：
            menu_code: 菜单编码。
            user_id: 用户编码。

        返回值：
            dict[str, Any] | None: 菜单详情或空。
        """
        row = self._query_one(OPEN_OBJECT_SQL, {"menu_code": menu_code})
        if row is not None:
            return row

        menus = self.fetch_menus(user_id=user_id)
        for menu in menus:
            if menu["MenuCd"] == menu_code:
                return menu
        return None

    def _get_oracle_config(self) -> dict[str, str] | None:
        """
        解析 Oracle 连接配置。

        返回值：
            dict[str, str] | None: Oracle 连接参数，缺项时返回空。
        """
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
        """
        执行查询并返回多行结果。

        参数：
            sql: 查询 SQL。
            params: 命名参数。

        返回值：
            list[dict[str, Any]] | None: 查询结果；失败返回空。
        """
        if oracledb is None:
            logger.warning("未安装 oracledb，回退占位数据")
            return None

        config = self._get_oracle_config()
        if config is None:
            logger.warning("Oracle 连接环境变量不完整，回退占位数据")
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
            logger.exception("菜单查询失败，回退占位数据")
            return None

    def _query_one(self, sql: str, params: dict[str, Any]) -> dict[str, Any] | None:
        """
        执行查询并返回单行结果。

        参数：
            sql: 查询 SQL。
            params: 命名参数。

        返回值：
            dict[str, Any] | None: 单行结果；失败或无记录返回空。
        """
        rows = self._query_all(sql, params)
        if rows is None or len(rows) == 0:
            return None
        return rows[0]

    def _fallback_menus(self) -> list[dict[str, Any]]:
        """
        返回占位菜单数据。

        返回值：
            list[dict[str, Any]]: 占位菜单列表。
        """
        return [
            {
                "MenuCd": "M001",
                "MenuNm": "系统管理",
                "Parent": "",
                "LevelCd": 1,
                "ChildFlg": "1",
                "OrdNo": 1,
                "PicName": "Resource\\Menus.ico",
                "ExePath": "",
                "OpenFlg": "0",
            },
            {
                "MenuCd": "M002",
                "MenuNm": "用户管理",
                "Parent": "M001",
                "LevelCd": 2,
                "ChildFlg": "0",
                "OrdNo": 1,
                "PicName": "Resource\\Forward.ico",
                "ExePath": "w_r_mc_user",
                "OpenFlg": "1",
            },
        ]
