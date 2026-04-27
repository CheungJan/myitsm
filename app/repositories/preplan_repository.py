"""
预计划管理仓储。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 对接 PLAN_CUST 表（预计划主表）
    - 实现与M006客户/资产联动
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None

__all__ = ["PreplanRepository"]

logger = logging.getLogger(__name__)

# 预计划查询
PREPLAN_BY_NO_SQL = """
SELECT
    PLANNO AS "PlanNo",
    PLANTYP AS "PlanType",
    CUSTNEW AS "CustNew",
    CUSTCARD AS "CustCard",
    CUSTCD AS "CustCd",
    CUSTNM AS "CustNm",
    CLASSCD AS "ClassCd",
    BUSITYP AS "BusiTyp",
    ADDRESS AS "Address",
    PHONENO AS "PhoneNo",
    CONTACTOR AS "Contactor",
    SOLVE_TYPE AS "SolveType",
    PLAN_STATUS AS "PlanStatus",
    IMPLE_STATUS AS "ImpleStatus",
    SERVETYP AS "ServeType",
    GENDATE AS "GenDate",
    OPERCD AS "OperCd"
FROM PLAN_CUST
WHERE PLANNO = :plan_no
""".strip()

# 预计划列表查询
PREPLAN_LIST_SQL = """
SELECT
    PLANNO AS "PlanNo",
    PLANTYP AS "PlanType",
    CUSTNEW AS "CustNew",
    CUSTCARD AS "CustCard",
    CUSTCD AS "CustCd",
    CUSTNM AS "CustNm",
    PLAN_STATUS AS "PlanStatus",
    IMPLE_STATUS AS "ImpleStatus",
    GENDATE AS "GenDate"
FROM PLAN_CUST
WHERE 1=1
  AND (:plan_status IS NULL OR PLAN_STATUS = :plan_status)
  AND (:imple_status IS NULL OR IMPLE_STATUS = :imple_status)
  AND (:cust_cd IS NULL OR CUSTCD = :cust_cd)
ORDER BY GENDATE DESC
""".strip()

# 更新预计划客户代码
UPDATE_PREPLAN_CUST_SQL = """
UPDATE PLAN_CUST
SET CUSTCD = :cust_cd,
    CUST_USEFLG = '1',
    UPDDATE = SYSDATE
WHERE PLANNO = :plan_no
""".strip()

# 更新预计划状态
UPDATE_PREPLAN_STATUS_SQL = """
UPDATE PLAN_CUST
SET PLAN_STATUS = :plan_status,
    IMPLE_STATUS = :imple_status,
    UPDDATE = SYSDATE,
    OPERCD = :oper_cd
WHERE PLANNO = :plan_no
""".strip()

# 更新实施状态
UPDATE_IMPLE_STATUS_SQL = """
UPDATE PLAN_CUST
SET IMPLE_STATUS = :imple_status,
    UPDDATE = SYSDATE,
    OPERCD = :oper_cd
WHERE PLANNO = :plan_no
""".strip()


class PreplanRepository:
    """
    预计划数据访问仓储。
    """

    def __init__(self) -> None:
        """初始化仓储。"""
        pass

    def get_by_no(self, plan_no: str) -> dict[str, Any] | None:
        """
        按预计划号查询详情。

        参数：
            plan_no: 预计划号

        返回值：
            dict[str, Any] | None: 预计划详情或空
        """
        rows = self._query_all(PREPLAN_BY_NO_SQL, {"plan_no": plan_no})
        if not rows:
            return None
        row = rows[0]
        return {
            "plan_no": row["PlanNo"],
            "plan_type": row["PlanType"],
            "cust_new": row["CustNew"],
            "cust_card": row["CustCard"],
            "cust_cd": row.get("CustCd"),
            "cust_nm": row["CustNm"],
            "class_cd": row.get("ClassCd"),
            "busi_typ": row.get("BusiTyp"),
            "address": row.get("Address"),
            "phone_no": row.get("PhoneNo"),
            "contactor": row.get("Contactor"),
            "solve_type": row.get("SolveType"),
            "plan_status": row["PlanStatus"],
            "imple_status": row.get("ImpleStatus"),
            "serve_type": row.get("ServeType"),
            "gen_date": row["GenDate"],
            "oper_cd": row.get("OperCd"),
        }

    def list_preplans(
        self,
        plan_status: str | None = None,
        imple_status: str | None = None,
        cust_cd: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取预计划列表。

        参数：
            plan_status: 计划状态
            imple_status: 实施状态
            cust_cd: 客户代码

        返回值：
            list[dict[str, Any]]: 预计划列表
        """
        rows = self._query_all(PREPLAN_LIST_SQL, {
            "plan_status": plan_status,
            "imple_status": imple_status,
            "cust_cd": cust_cd,
        })
        if rows is None:
            return []
        return [
            {
                "plan_no": row["PlanNo"],
                "plan_type": row["PlanType"],
                "cust_new": row["CustNew"],
                "cust_card": row["CustCard"],
                "cust_cd": row.get("CustCd"),
                "cust_nm": row["CustNm"],
                "plan_status": row["PlanStatus"],
                "imple_status": row.get("ImpleStatus"),
                "gen_date": row["GenDate"],
            }
            for row in rows
        ]

    def update_cust_cd(self, plan_no: str, cust_cd: str) -> bool:
        """
        更新预计划的客户代码。

        参数：
            plan_no: 预计划号
            cust_cd: 客户代码

        返回值：
            bool: 是否成功
        """
        return self._execute(UPDATE_PREPLAN_CUST_SQL, {
            "plan_no": plan_no,
            "cust_cd": cust_cd,
        })

    def update_status(
        self,
        plan_no: str,
        plan_status: str,
        imple_status: str,
        oper_cd: str,
    ) -> bool:
        """
        更新预计划状态。

        参数：
            plan_no: 预计划号
            plan_status: 计划状态
            imple_status: 实施状态
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        return self._execute(UPDATE_PREPLAN_STATUS_SQL, {
            "plan_no": plan_no,
            "plan_status": plan_status,
            "imple_status": imple_status,
            "oper_cd": oper_cd,
        })

    def update_imple_status(
        self,
        plan_no: str,
        imple_status: str,
        oper_cd: str,
    ) -> bool:
        """
        更新实施状态。

        参数：
            plan_no: 预计划号
            imple_status: 实施状态
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        return self._execute(UPDATE_IMPLE_STATUS_SQL, {
            "plan_no": plan_no,
            "imple_status": imple_status,
            "oper_cd": oper_cd,
        })

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
            logger.exception("预计划查询失败")
            return None

    def _execute(self, sql: str, params: dict[str, Any]) -> bool:
        """执行 DML 语句。"""
        if oracledb is None:
            logger.warning("未安装 oracledb")
            return False

        config = self._get_oracle_config()
        if config is None:
            logger.warning("Oracle 连接环境变量不完整")
            return False

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
                    conn.commit()
                    return True
        except Exception:
            logger.exception("预计划数据更新失败")
            return False
