"""
维修单仓储（ITSM核心）。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 对接 TIT10_MAINTENANCEDAY, TIT13_MAINTENANCE_OPEN, TIT15_MAINTENANCE_RENOVATE 等表
    - 统一维修单状态管理
    - 对应优化2：ITSM状态机重构
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None

__all__ = ["MaintenanceRepository"]

logger = logging.getLogger(__name__)

# 日常维护单查询
MAINTENANCE_DAY_SQL = """
SELECT
    MAINTENANCE_ID AS "MaintenanceId",
    COMPANY_ID AS "CompanyId",
    STORE_ID AS "StoreId",
    CUSTCD AS "CustCd",
    TEMP_CONTRACT AS "TempContract",
    SHORT_DESCRIPTION AS "ShortDescription",
    DETAIL_DESCRIPTION AS "DetailDescription",
    DEVICE_ID AS "DeviceId",
    CURRENT_STATUS AS "CurrentStatus",
    IS_SUCCESS AS "IsSuccess",
    IS_OLD AS "IsOld",
    FAULTCODE AS "FaultCode",
    CREATE_TIME AS "CreateTime",
    OPERCD AS "OperCd"
FROM TIT10_MAINTENANCEDAY
WHERE MAINTENANCE_ID = :maintenance_id
  AND USEFLG = '1'
""".strip()

# 更新维护单状态
UPDATE_STATUS_SQL = """
UPDATE TIT10_MAINTENANCEDAY
SET CURRENT_STATUS = :new_status,
    UPDDATE = SYSDATE,
    OPERCD = :oper_cd
WHERE MAINTENANCE_ID = :maintenance_id
  AND CURRENT_STATUS = :old_status
""".strip()

# 创建维护单
CREATE_MAINTENANCE_SQL = """
INSERT INTO TIT10_MAINTENANCEDAY (
    MAINTENANCE_ID, COMPANY_ID, STORE_ID, CUSTCD,
    TEMP_CONTRACT, SHORT_DESCRIPTION, DETAIL_DESCRIPTION,
    DEVICE_ID, CURRENT_STATUS, IS_SUCCESS, IS_OLD,
    CREATE_TIME, OPERCD, USEFLG
) VALUES (
    :maintenance_id, :company_id, :store_id, :cust_cd,
    :temp_contract, :short_description, :detail_description,
    :device_id, :current_status, '0', '0',
    SYSDATE, :oper_cd, '1'
)
""".strip()

# 维护单配件明细（TIT10_POS_DETAIL）查询
LIST_POS_DETAILS_SQL = """
SELECT
    BILL_ID AS "BillId",
    SM_ID AS "SmId",
    NOFLG AS "Noflg",
    DEVICE_ID AS "DeviceId",
    ITEMCD AS "ItemCd",
    ACCESSORIES_ID AS "AccessoriesId",
    CREATE_TIME AS "CreateTime",
    CREATOR AS "Creator",
    STATUS AS "Status"
FROM TIT10_POS_DETAIL
WHERE BILL_ID = :maintenance_id
ORDER BY CREATE_TIME DESC, SM_ID DESC
""".strip()

# 维护单配件明细（TIT10_POS_DETAIL）新增
CREATE_POS_DETAIL_SQL = """
INSERT INTO TIT10_POS_DETAIL (
    BILL_ID,
    SM_ID,
    NOFLG,
    DEVICE_ID,
    ITEMCD,
    ACCESSORIES_ID,
    CREATE_TIME,
    CREATOR,
    STATUS
) VALUES (
    :maintenance_id,
    :sm_id,
    :noflg,
    :device_id,
    :item_cd,
    :accessories_id,
    SYSDATE,
    :creator,
    :status
)
""".strip()

# 维护单列表查询
MAINTENANCE_LIST_SQL = """
SELECT
    MAINTENANCE_ID AS "MaintenanceId",
    CUSTCD AS "CustCd",
    SHORT_DESCRIPTION AS "ShortDescription",
    CURRENT_STATUS AS "CurrentStatus",
    CREATE_TIME AS "CreateTime"
FROM TIT10_MAINTENANCEDAY
WHERE 1=1
  AND (:cust_cd IS NULL OR CUSTCD = :cust_cd)
  AND (:status IS NULL OR CURRENT_STATUS = :status)
  AND USEFLG = '1'
ORDER BY CREATE_TIME DESC
""".strip()

# 记录状态变更日志
LOG_STATUS_CHANGE_SQL = """
INSERT INTO TIT10_MAIN_TRACK (
    MAINTENANCE_ID, DEP_CD, MEMO, UPDATETIME
) VALUES (
    :maintenance_id, :dep_cd,
    :memo,
    SYSDATE
)
""".strip()


class MaintenanceRepository:
    """
    维修单数据访问仓储。

    功能概述：
        - 维修单CRUD操作
        - 状态流转管理
        - 状态变更日志记录
    """

    def __init__(self) -> None:
        """初始化仓储。"""
        pass

    def get_by_id(self, maintenance_id: str) -> dict[str, Any] | None:
        """
        按维修单ID查询详情。

        参数：
            maintenance_id: 维修单ID

        返回值：
            dict[str, Any] | None: 维修单详情或空
        """
        rows = self._query_all(MAINTENANCE_DAY_SQL, {"maintenance_id": maintenance_id})
        if not rows:
            return None
        row = rows[0]
        return {
            "maintenance_id": row["MaintenanceId"],
            "company_id": row.get("CompanyId"),
            "store_id": row.get("StoreId"),
            "cust_cd": row.get("CustCd"),
            "temp_contract": row.get("TempContract"),
            "short_description": row["ShortDescription"],
            "detail_description": row.get("DetailDescription"),
            "device_id": row.get("DeviceId"),
            "current_status": row["CurrentStatus"],
            "is_success": row.get("IsSuccess"),
            "is_old": row.get("IsOld"),
            "fault_code": row.get("FaultCode"),
            "create_time": row["CreateTime"],
            "oper_cd": row.get("OperCd"),
        }

    def list_maintenances(
        self,
        cust_cd: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取维修单列表。

        参数：
            cust_cd: 客户代码过滤
            status: 状态过滤

        返回值：
            list[dict[str, Any]]: 维修单列表
        """
        rows = self._query_all(
            MAINTENANCE_LIST_SQL,
            {"cust_cd": cust_cd, "status": status},
        )
        if rows is None:
            return []
        return [
            {
                "maintenance_id": row["MaintenanceId"],
                "cust_cd": row.get("CustCd"),
                "short_description": row["ShortDescription"],
                "current_status": row["CurrentStatus"],
                "create_time": row["CreateTime"],
            }
            for row in rows
        ]

    def update_status(
        self,
        maintenance_id: str,
        old_status: str,
        new_status: str,
        oper_cd: str,
    ) -> bool:
        """
        更新维修单状态（带乐观锁）。

        参数：
            maintenance_id: 维修单ID
            old_status: 原状态（乐观锁校验）
            new_status: 新状态
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        params = {
            "maintenance_id": maintenance_id,
            "old_status": old_status,
            "new_status": new_status,
            "oper_cd": oper_cd,
        }
        return self._execute(UPDATE_STATUS_SQL, params)

    def create_maintenance(
        self,
        maintenance_info: dict[str, Any],
        oper_cd: str,
    ) -> str | None:
        """
        创建维修单。

        参数：
            maintenance_info: 维修单信息
            oper_cd: 操作员代码

        返回值：
            str | None: 维修单ID或空
        """
        # 生成维修单ID（简化版，实际可能需要更复杂的生成逻辑）
        maintenance_id = self._generate_maintenance_id()
        if maintenance_id is None:
            return None

        params = {
            "maintenance_id": maintenance_id,
            "company_id": maintenance_info.get("company_id", ""),
            "store_id": maintenance_info.get("store_id", ""),
            "cust_cd": maintenance_info.get("cust_cd", ""),
            "temp_contract": maintenance_info.get("temp_contract", ""),
            "short_description": maintenance_info.get("short_description", ""),
            "detail_description": maintenance_info.get("detail_description", ""),
            "device_id": maintenance_info.get("device_id", ""),
            "current_status": maintenance_info.get("current_status", "00"),
            "oper_cd": oper_cd,
        }

        if self._execute(CREATE_MAINTENANCE_SQL, params):
            return maintenance_id
        return None

    def log_status_change(
        self,
        maintenance_id: str,
        dep_cd: str,
        memo: str,
    ) -> bool:
        """
        记录状态变更日志。

        参数：
            maintenance_id: 维修单ID
            dep_cd: 部门代码
            memo: 备注信息

        返回值：
            bool: 是否成功
        """
        params = {
            "maintenance_id": maintenance_id,
            "dep_cd": dep_cd,
            "memo": memo,
        }
        return self._execute(LOG_STATUS_CHANGE_SQL, params)

    def list_pos_details(self, maintenance_id: str) -> list[dict[str, Any]]:
        """
        获取维护单配件明细。

        参数：
            maintenance_id: 维护单ID（对应 BILL_ID）

        返回值：
            list[dict[str, Any]]: 配件明细列表
        """
        rows = self._query_all(LIST_POS_DETAILS_SQL, {"maintenance_id": maintenance_id})
        if rows is None:
            return []

        return [
            {
                "maintenance_id": row["BillId"],
                "sm_id": row["SmId"],
                "noflg": row.get("Noflg"),
                "device_id": row["DeviceId"],
                "item_cd": row.get("ItemCd"),
                "accessories_id": row["AccessoriesId"],
                "create_time": row.get("CreateTime"),
                "creator": row.get("Creator"),
                "status": row.get("Status"),
            }
            for row in rows
        ]

    def create_pos_detail(
        self,
        maintenance_id: str,
        sm_id: int,
        device_id: str,
        accessories_id: str,
        creator: str,
        item_cd: str = "",
        noflg: str = "N",
        status: str = "1",
    ) -> bool:
        """
        新增维护单配件明细。

        参数：
            maintenance_id: 维护单ID（对应 BILL_ID）
            sm_id: 业务操作流水ID
            device_id: 整机ID
            accessories_id: 配件编号
            creator: 创建人
            item_cd: 配件类型
            noflg: 新旧设备标记
            status: 状态

        返回值：
            bool: 是否新增成功
        """
        params = {
            "maintenance_id": maintenance_id,
            "sm_id": sm_id,
            "noflg": noflg,
            "device_id": device_id,
            "item_cd": item_cd,
            "accessories_id": accessories_id,
            "creator": creator,
            "status": status,
        }
        return self._execute(CREATE_POS_DETAIL_SQL, params)

    def _generate_maintenance_id(self) -> str | None:
        """生成维修单ID（8位数字）。"""
        sql = """
        SELECT LPAD(TO_CHAR(NVL(MAX(TO_NUMBER(MAINTENANCE_ID)), 0) + 1), 8, '0') AS "NewId"
        FROM TIT10_MAINTENANCEDAY
        WHERE REGEXP_LIKE(MAINTENANCE_ID, '^[0-9]+$')
        """
        rows = self._query_all(sql, {})
        if not rows:
            return None
        return rows[0]["NewId"]

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
            logger.exception("维修单查询失败")
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
            logger.exception("维修单数据更新失败")
            return False
