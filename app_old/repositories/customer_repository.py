"""
客户主数据仓储。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 客户生命周期管理，支持 TEMP/PENDING/ACTIVE/INVALID 状态流转
    - 对应 base_cust.pbl 的 u_mm_customer 等对象
    - 结合优化1：预计划客户生命周期管理
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None

__all__ = ["CustomerRepository"]

logger = logging.getLogger(__name__)

# 客户列表查询（支持状态过滤）
CUSTOMER_LIST_SQL = """
SELECT
    CUSTCD AS "CustCd",
    CUSTNM AS "CustNm",
    CUSTCARD AS "CustCard",
    CLASSCD AS "ClassCd",
    BUSITYP AS "BusiTyp",
    STATUS AS "Status",
    USEFLG AS "UseFlg",
    CUSTOMER_STATUS AS "CustomerStatus",
    SOURCE_TYPE AS "SourceType",
    PREPLAN_ID AS "PreplanId",
    VERIFIED_AT AS "VerifiedAt",
    GENDATE AS "GenDate"
FROM TMM22_CUSTOMERS
WHERE 1=1
  AND (:status IS NULL OR CUSTOMER_STATUS = :status)
  AND (:use_flg IS NULL OR USEFLG = :use_flg)
ORDER BY GENDATE DESC
""".strip()

# 按代码查询客户
CUSTOMER_BY_CODE_SQL = """
SELECT
    CUSTCD AS "CustCd",
    CUSTNM AS "CustNm",
    CUSTCARD AS "CustCard",
    CLASSCD AS "ClassCd",
    ADDRESS AS "Address",
    PHONENO AS "PhoneNo",
    CONTACTOR AS "Contactor",
    BUSITYP AS "BusiTyp",
    STATUS AS "Status",
    USEFLG AS "UseFlg",
    CUSTOMER_STATUS AS "CustomerStatus",
    SOURCE_TYPE AS "SourceType",
    PREPLAN_ID AS "PreplanId",
    VERIFIED_AT AS "VerifiedAt",
    GENDATE AS "GenDate",
    OPERCD AS "OperCd"
FROM TMM22_CUSTOMERS
WHERE CUSTCD = :cust_cd
""".strip()

# 按磁卡号查询客户
CUSTOMER_BY_CARD_SQL = """
SELECT
    CUSTCD AS "CustCd",
    CUSTNM AS "CustNm",
    CUSTCARD AS "CustCard",
    STATUS AS "Status",
    USEFLG AS "UseFlg",
    CUSTOMER_STATUS AS "CustomerStatus"
FROM TMM22_CUSTOMERS
WHERE CUSTCARD = :cust_card
""".strip()

# 生成新客户代码（8位数字，前导补零）
GENERATE_CUSTCD_SQL = """
SELECT LPAD(TO_CHAR(NVL(MAX(TO_NUMBER(CUSTCD)), 0) + 1), 8, '0') AS "NewCustCd"
FROM TMM22_CUSTOMERS
WHERE REGEXP_LIKE(CUSTCD, '^[0-9]+$')
""".strip()

# 创建临时客户（从预计划）
CREATE_TEMP_CUSTOMER_SQL = """
INSERT INTO TMM22_CUSTOMERS (
    CUSTCD, CUSTNM, CUSTCARD, ADDRESS, PHONENO, CONTACTOR,
    CLASSCD, BUSITYP, STATUS, USEFLG,
    CUSTOMER_STATUS, SOURCE_TYPE, PREPLAN_ID,
    GENDATE, OPERCD
) VALUES (
    :cust_cd, :cust_nm, :cust_card, :address, :phone_no, :contactor,
    :class_cd, :busi_typ, '1', '1',
    'TEMP', 'PREPLAN', :preplan_id,
    SYSDATE, :oper_cd
)
""".strip()

# 客户状态流转
UPDATE_CUSTOMER_STATUS_SQL = """
UPDATE TMM22_CUSTOMERS
SET CUSTOMER_STATUS = :new_status,
    VERIFIED_AT = CASE WHEN :new_status = 'ACTIVE' THEN SYSDATE ELSE VERIFIED_AT END,
    USEFLG = CASE 
        WHEN :new_status = 'INVALID' THEN '0'
        WHEN :new_status = 'ACTIVE' THEN '1'
        ELSE USEFLG
    END,
    UPDDATE = SYSDATE,
    OPERCD = :oper_cd
WHERE CUSTCD = :cust_cd
  AND CUSTOMER_STATUS = :old_status
""".strip()

# 更新客户信息
UPDATE_CUSTOMER_SQL = """
UPDATE TMM22_CUSTOMERS
SET CUSTNM = :cust_nm,
    ADDRESS = :address,
    PHONENO = :phone_no,
    CONTACTOR = :contactor,
    UPDDATE = SYSDATE,
    OPERCD = :oper_cd
WHERE CUSTCD = :cust_cd
""".strip()


class CustomerRepository:
    """
    客户主数据访问仓储。

    功能概述：
        - 客户CRUD操作
        - 客户生命周期状态管理（TEMP→PENDING→ACTIVE/INVALID）
        - 与预计划单关联
    """

    def __init__(self) -> None:
        """初始化仓储。"""
        pass

    def list_customers(
        self,
        status: str | None = None,
        use_flg: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取客户列表，支持状态过滤。

        参数：
            status: 客户生命周期状态（TEMP/PENDING/ACTIVE/INVALID）
            use_flg: 有效标志（'1'有效/'0'无效）

        返回值：
            list[dict[str, Any]]: 客户列表
        """
        rows = self._query_all(
            CUSTOMER_LIST_SQL,
            {"status": status, "use_flg": use_flg},
        )
        if rows is None:
            return []
        return [
            {
                "cust_cd": row["CustCd"],
                "cust_nm": row["CustNm"],
                "cust_card": row["CustCard"],
                "class_cd": row["ClassCd"],
                "busi_typ": row["BusiTyp"],
                "status": row["Status"],
                "use_flg": row["UseFlg"],
                "customer_status": row.get("CustomerStatus", "ACTIVE"),
                "source_type": row.get("SourceType", "MANUAL"),
                "preplan_id": row.get("PreplanId"),
                "verified_at": row.get("VerifiedAt"),
                "gen_date": row["GenDate"],
            }
            for row in rows
        ]

    def get_by_code(self, cust_cd: str) -> dict[str, Any] | None:
        """
        按客户代码查询详情。

        参数：
            cust_cd: 客户代码

        返回值：
            dict[str, Any] | None: 客户详情或空
        """
        rows = self._query_all(CUSTOMER_BY_CODE_SQL, {"cust_cd": cust_cd})
        if not rows:
            return None
        row = rows[0]
        return {
            "cust_cd": row["CustCd"],
            "cust_nm": row["CustNm"],
            "cust_card": row["CustCard"],
            "class_cd": row["ClassCd"],
            "address": row.get("Address"),
            "phone_no": row.get("PhoneNo"),
            "contactor": row.get("Contactor"),
            "busi_typ": row["BusiTyp"],
            "status": row["Status"],
            "use_flg": row["UseFlg"],
            "customer_status": row.get("CustomerStatus", "ACTIVE"),
            "source_type": row.get("SourceType", "MANUAL"),
            "preplan_id": row.get("PreplanId"),
            "verified_at": row.get("VerifiedAt"),
            "gen_date": row["GenDate"],
            "oper_cd": row.get("OperCd"),
        }

    def get_by_card(self, cust_card: str) -> dict[str, Any] | None:
        """
        按磁卡号查询客户。

        参数：
            cust_card: 磁卡号

        返回值：
            dict[str, Any] | None: 客户信息或空
        """
        rows = self._query_all(CUSTOMER_BY_CARD_SQL, {"cust_card": cust_card})
        if not rows:
            return None
        row = rows[0]
        return {
            "cust_cd": row["CustCd"],
            "cust_nm": row["CustNm"],
            "cust_card": row["CustCard"],
            "status": row["Status"],
            "use_flg": row["UseFlg"],
            "customer_status": row.get("CustomerStatus", "ACTIVE"),
        }

    def generate_custcd(self) -> str | None:
        """
        生成新客户代码（8位数字）。

        返回值：
            str | None: 新客户代码或空
        """
        rows = self._query_all(GENERATE_CUSTCD_SQL, {})
        if not rows:
            return None
        return rows[0]["NewCustCd"]

    def create_temp_from_plan(
        self,
        preplan_id: str,
        cust_info: dict[str, Any],
        oper_cd: str,
    ) -> str | None:
        """
        从预计划创建临时客户。

        参数：
            preplan_id: 预计划单号
            cust_info: 客户信息（cust_nm, cust_card, address, phone_no, contactor, class_cd, busi_typ）
            oper_cd: 操作员代码

        返回值：
            str | None: 新客户代码或空
        """
        # 生成客户代码
        cust_cd = self.generate_custcd()
        if cust_cd is None:
            logger.error("生成客户代码失败")
            return None

        params = {
            "cust_cd": cust_cd,
            "cust_nm": cust_info.get("cust_nm", ""),
            "cust_card": cust_info.get("cust_card", ""),
            "address": cust_info.get("address", ""),
            "phone_no": cust_info.get("phone_no", ""),
            "contactor": cust_info.get("contactor", ""),
            "class_cd": cust_info.get("class_cd", ""),
            "busi_typ": cust_info.get("busi_typ", ""),
            "preplan_id": preplan_id,
            "oper_cd": oper_cd,
        }

        if self._execute(CREATE_TEMP_CUSTOMER_SQL, params):
            return cust_cd
        return None

    def transition_status(
        self,
        cust_cd: str,
        old_status: str,
        new_status: str,
        oper_cd: str,
    ) -> bool:
        """
        客户状态流转。

        参数：
            cust_cd: 客户代码
            old_status: 原状态
            new_status: 新状态（TEMP/PENDING/ACTIVE/INVALID）
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        params = {
            "cust_cd": cust_cd,
            "old_status": old_status,
            "new_status": new_status,
            "oper_cd": oper_cd,
        }
        return self._execute(UPDATE_CUSTOMER_STATUS_SQL, params)

    def update_customer(
        self,
        cust_cd: str,
        cust_info: dict[str, Any],
        oper_cd: str,
    ) -> bool:
        """
        更新客户信息。

        参数：
            cust_cd: 客户代码
            cust_info: 客户信息（cust_nm, address, phone_no, contactor）
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        params = {
            "cust_cd": cust_cd,
            "cust_nm": cust_info.get("cust_nm", ""),
            "address": cust_info.get("address", ""),
            "phone_no": cust_info.get("phone_no", ""),
            "contactor": cust_info.get("contactor", ""),
            "oper_cd": oper_cd,
        }
        return self._execute(UPDATE_CUSTOMER_SQL, params)

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
            logger.exception("客户查询失败")
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
            logger.exception("客户数据更新失败")
            return False
