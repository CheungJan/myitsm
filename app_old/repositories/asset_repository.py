"""
门店资产仓储。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 基于 TMM35_CUST_POS_RL 扩展资产属性管理
    - 对应优化4：资产属性与回收任务
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None

__all__ = ["AssetRepository"]

logger = logging.getLogger(__name__)

# 门店资产列表查询
ASSET_LIST_SQL = """
SELECT
    CUSTCD AS "CustCd",
    EID AS "Eid",
    ITEMCD AS "ItemCd",
    STARTDATE AS "StartDate",
    SYSINFO AS "SysInfo",
    SOFTINFO AS "SoftInfo",
    STATUS AS "Status",
    TYPFLG AS "TypFlg",
    MAINTENANCEDATE AS "MaintenanceDate",
    USEFLG AS "UseFlg",
    ASSET_TYPE AS "AssetType",
    RECYCLABLE_FLAG AS "RecyclableFlag",
    RECYCLE_STATUS AS "RecycleStatus",
    CREATED_FROM AS "CreatedFrom",
    SOURCE_ID AS "SourceId",
    WARRANTY_EXPIRE AS "WarrantyExpire",
    ASSET_STATUS AS "AssetStatus"
FROM TMM35_CUST_POS_RL
WHERE 1=1
  AND (:cust_cd IS NULL OR CUSTCD = :cust_cd)
  AND (:eid IS NULL OR EID = :eid)
  AND USEFLG = '1'
ORDER BY STARTDATE DESC
""".strip()

# 可回收资产查询
RECYCLABLE_ASSETS_SQL = """
SELECT
    CUSTCD AS "CustCd",
    EID AS "Eid",
    ITEMCD AS "ItemCd",
    STARTDATE AS "StartDate",
    ASSET_TYPE AS "AssetType",
    TYPFLG AS "TypFlg"
FROM TMM35_CUST_POS_RL
WHERE CUSTCD = :cust_cd
  AND ASSET_TYPE IN ('OLD', 'RENOVATED')
  AND RECYCLABLE_FLAG = '1'
  AND RECYCLE_STATUS = 'NONE'
  AND USEFLG = '1'
  AND ASSET_STATUS = 'ACTIVE'
ORDER BY STARTDATE
""".strip()

# 标记资产为可回收
MARK_RECYCLABLE_SQL = """
UPDATE TMM35_CUST_POS_RL
SET RECYCLABLE_FLAG = '1',
    RECYCLE_STATUS = 'PENDING',
    UPDDATE = SYSDATE
WHERE CUSTCD = :cust_cd
  AND ASSET_STATUS = 'ACTIVE'
  AND (:plan_type != '02' OR TYPFLG IN ('1', '2'))  -- 旧机翻新时只标记POS/视频机
""".strip()

# 更新资产回收状态
UPDATE_RECYCLE_STATUS_SQL = """
UPDATE TMM35_CUST_POS_RL
SET RECYCLE_STATUS = :recycle_status,
    ASSET_STATUS = CASE 
        WHEN :recycle_status = 'COMPLETED' THEN 'RETURNED'
        ELSE ASSET_STATUS
    END,
    UPDDATE = SYSDATE
WHERE CUSTCD = :cust_cd
  AND EID = :eid
""".strip()

# 从预计划创建新资产
CREATE_ASSET_FROM_PLAN_SQL = """
INSERT INTO TMM35_CUST_POS_RL (
    CUSTCD, EID, ITEMCD, STARTDATE,
    SYSINFO, SOFTINFO, POSINFO, AREA,
    STATUS, TYPFLG, MAINTENANCEDATE,
    USEFLG, GENDATE, OPERCD,
    ASSET_TYPE, CREATED_FROM, SOURCE_ID,
    RECYCLABLE_FLAG, RECYCLE_STATUS, ASSET_STATUS
) VALUES (
    :cust_cd, :eid, :itemcd, SYSDATE,
    :sys_info, :soft_info, :pos_info, :area,
    '1', :typ_flg, NULL,
    '1', SYSDATE, :oper_cd,
    'NEW', 'PLAN_CUST', :plan_no,
    '0', 'NONE', 'ACTIVE'
)
""".strip()

# 批量更新资产回收状态
BATCH_UPDATE_RECYCLE_SQL = """
UPDATE TMM35_CUST_POS_RL
SET RECYCLE_STATUS = :recycle_status,
    ASSET_STATUS = CASE 
        WHEN :recycle_status = 'COMPLETED' THEN 'RETURNED'
        ELSE ASSET_STATUS
    END,
    UPDDATE = SYSDATE
WHERE CUSTCD = :cust_cd
  AND EID IN (SELECT COLUMN_VALUE FROM TABLE(:eid_list))
""".strip()


class AssetRepository:
    """
    门店资产数据访问仓储。

    功能概述：
        - 门店资产查询（基于 TMM35_CUST_POS_RL）
        - 可回收资产管理
        - 资产回收状态流转
    """

    def __init__(self) -> None:
        """初始化仓储。"""
        pass

    def list_assets(
        self,
        cust_cd: str | None = None,
        eid: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取门店资产列表。

        参数：
            cust_cd: 门店代码
            eid: 设备编码

        返回值：
            list[dict[str, Any]]: 资产列表
        """
        rows = self._query_all(
            ASSET_LIST_SQL,
            {"cust_cd": cust_cd, "eid": eid},
        )
        if rows is None:
            return []
        return [
            {
                "cust_cd": row["CustCd"],
                "eid": row["Eid"],
                "item_cd": row["ItemCd"],
                "start_date": row["StartDate"],
                "sys_info": row.get("SysInfo"),
                "soft_info": row.get("SoftInfo"),
                "status": row["Status"],
                "typ_flg": row["TypFlg"],
                "maintenance_date": row.get("MaintenanceDate"),
                "use_flg": row["UseFlg"],
                "asset_type": row.get("AssetType", "OLD"),
                "recyclable_flag": row.get("RecyclableFlag", "0"),
                "recycle_status": row.get("RecycleStatus", "NONE"),
                "created_from": row.get("CreatedFrom", "MANUAL"),
                "source_id": row.get("SourceId"),
                "warranty_expire": row.get("WarrantyExpire"),
                "asset_status": row.get("AssetStatus", "ACTIVE"),
            }
            for row in rows
        ]

    def get_recyclable_assets(self, cust_cd: str) -> list[dict[str, Any]]:
        """
        获取门店可回收资产列表。

        参数：
            cust_cd: 门店代码

        返回值：
            list[dict[str, Any]]: 可回收资产列表
        """
        rows = self._query_all(RECYCLABLE_ASSETS_SQL, {"cust_cd": cust_cd})
        if rows is None:
            return []
        return [
            {
                "cust_cd": row["CustCd"],
                "eid": row["Eid"],
                "item_cd": row["ItemCd"],
                "start_date": row["StartDate"],
                "asset_type": row.get("AssetType", "OLD"),
                "typ_flg": row["TypFlg"],
            }
            for row in rows
        ]

    def mark_recyclable(self, cust_cd: str, plan_type: str) -> int:
        """
        标记门店可回收资产。

        参数：
            cust_cd: 门店代码
            plan_type: 计划类型（02关门/01旧机翻新）

        返回值：
            int: 标记的资产数量
        """
        return self._execute_rowcount(MARK_RECYCLABLE_SQL, {
            "cust_cd": cust_cd,
            "plan_type": plan_type,
        })

    def update_recycle_status(
        self,
        cust_cd: str,
        eid: str,
        recycle_status: str,
    ) -> bool:
        """
        更新单个资产回收状态。

        参数：
            cust_cd: 门店代码
            eid: 设备编码
            recycle_status: 回收状态

        返回值：
            bool: 是否成功
        """
        return self._execute(UPDATE_RECYCLE_STATUS_SQL, {
            "cust_cd": cust_cd,
            "eid": eid,
            "recycle_status": recycle_status,
        })

    def batch_update_recycle_status(
        self,
        cust_cd: str,
        eids: list[str],
        recycle_status: str,
    ) -> bool:
        """
        批量更新资产回收状态。

        参数：
            cust_cd: 门店代码
            eids: 设备编码列表
            recycle_status: 回收状态

        返回值：
            bool: 是否成功
        """
        # 构建IN条件
        placeholders = ", ".join([f":eid_{i}" for i in range(len(eids))])
        sql = f"""
        UPDATE TMM35_CUST_POS_RL
        SET RECYCLE_STATUS = :recycle_status,
            ASSET_STATUS = CASE 
                WHEN :recycle_status = 'COMPLETED' THEN 'RETURNED'
                ELSE ASSET_STATUS
            END,
            UPDDATE = SYSDATE
        WHERE CUSTCD = :cust_cd
          AND EID IN ({placeholders})
        """
        params = {
            "cust_cd": cust_cd,
            "recycle_status": recycle_status,
        }
        for i, eid in enumerate(eids):
            params[f"eid_{i}"] = eid
        return self._execute(sql, params)

    def create_from_plan(
        self,
        cust_cd: str,
        eid: str,
        item_cd: str,
        plan_no: str,
        asset_info: dict[str, Any],
        oper_cd: str,
    ) -> bool:
        """
        从预计划创建新资产。

        参数：
            cust_cd: 门店代码
            eid: 设备编码
            item_cd: 物料代码
            plan_no: 预计划单号
            asset_info: 资产信息
            oper_cd: 操作员代码

        返回值：
            bool: 是否成功
        """
        params = {
            "cust_cd": cust_cd,
            "eid": eid,
            "item_cd": item_cd,
            "plan_no": plan_no,
            "sys_info": asset_info.get("sys_info", ""),
            "soft_info": asset_info.get("soft_info", ""),
            "pos_info": asset_info.get("pos_info", ""),
            "area": asset_info.get("area", ""),
            "typ_flg": asset_info.get("typ_flg", "1"),
            "oper_cd": oper_cd,
        }
        return self._execute(CREATE_ASSET_FROM_PLAN_SQL, params)

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
            logger.exception("资产查询失败")
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
            logger.exception("资产数据更新失败")
            return False

    def _execute_rowcount(self, sql: str, params: dict[str, Any]) -> int:
        """执行 DML 语句并返回影响行数。"""
        if oracledb is None:
            logger.warning("未安装 oracledb")
            return 0

        config = self._get_oracle_config()
        if config is None:
            logger.warning("Oracle 连接环境变量不完整")
            return 0

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
                    rowcount = cursor.rowcount
                    conn.commit()
                    return rowcount
        except Exception:
            logger.exception("资产数据更新失败")
            return 0
