"""
旧机回收任务仓储。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 回收任务独立于日常维护单
    - 对应优化4：旧机回收任务独立化
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None

__all__ = ["RecycleTaskRepository"]

logger = logging.getLogger(__name__)

# 生成回收任务ID（R+日期+序号）
GENERATE_RECYCLE_ID_SQL = """
SELECT 'R' || TO_CHAR(SYSDATE, 'YYYYMMDD') || 
       LPAD(NVL(MAX(TO_NUMBER(SUBSTR(RECYCLE_ID, 10))), 0) + 1, 3, '0')
       AS "RecycleId"
FROM TIT20_RECYCLE_TASK
WHERE RECYCLE_ID LIKE 'R' || TO_CHAR(SYSDATE, 'YYYYMMDD') || '%'
""".strip()

# 创建回收任务
CREATE_RECYCLE_TASK_SQL = """
INSERT INTO TIT20_RECYCLE_TASK (
    RECYCLE_ID, RECYCLE_TYPE, PLANNO, CUSTCD,
    TASK_STATUS, ASSET_COUNT, ASSET_LIST,
    ASSIGNED_TO, ASSIGNED_DATE,
    USEFLG, GENDATE, OPERCD, REMARK
) VALUES (
    :recycle_id, :recycle_type, :plan_no, :cust_cd,
    '00', :asset_count, :asset_list,
    NULL, NULL,
    '1', SYSDATE, :oper_cd, :remark
)
""".strip()

# 创建回收任务明细
CREATE_TASK_DETAIL_SQL = """
INSERT INTO TIT20_RECYCLE_TASK_DTL (
    RECYCLE_ID, ASSET_ID, ASSET_TYPE,
    EXPECTED_STATUS, ACTUAL_STATUS,
    WAREHOUSE_CD, REMARK
) VALUES (
    :recycle_id, :asset_id, :asset_type,
    'NONE', 'NONE',
    NULL, NULL
)
""".strip()

# 查询任务列表
TASK_LIST_SQL = """
SELECT
    rt.RECYCLE_ID AS "RecycleId",
    rt.RECYCLE_TYPE AS "RecycleType",
    rt.PLANNO AS "PlanNo",
    rt.CUSTCD AS "CustCd",
    c.CUSTNM AS "CustNm",
    rt.TASK_STATUS AS "TaskStatus",
    rt.ASSET_COUNT AS "AssetCount",
    rt.ACTUAL_COUNT AS "ActualCount",
    rt.ASSIGNED_TO AS "AssignedTo",
    rt.ASSIGNED_DATE AS "AssignedDate",
    rt.COMPLETE_DATE AS "CompleteDate",
    rt.DISPOSITION AS "Disposition",
    rt.GENDATE AS "GenDate"
FROM TIT20_RECYCLE_TASK rt
LEFT JOIN TMM22_CUSTOMERS c ON rt.CUSTCD = c.CUSTCD
WHERE 1=1
  AND (:cust_cd IS NULL OR rt.CUSTCD = :cust_cd)
  AND (:plan_no IS NULL OR rt.PLANNO = :plan_no)
  AND (:task_status IS NULL OR rt.TASK_STATUS = :task_status)
  AND rt.USEFLG = '1'
ORDER BY rt.GENDATE DESC
""".strip()

# 查询任务详情（含明细）
TASK_DETAIL_SQL = """
SELECT
    rt.RECYCLE_ID AS "RecycleId",
    rt.RECYCLE_TYPE AS "RecycleType",
    rt.PLANNO AS "PlanNo",
    rt.CUSTCD AS "CustCd",
    c.CUSTNM AS "CustNm",
    rt.TASK_STATUS AS "TaskStatus",
    rt.ASSET_COUNT AS "AssetCount",
    rt.ASSET_LIST AS "AssetList",
    rt.ACTUAL_COUNT AS "ActualCount",
    rt.RECYCLED_ASSETS AS "RecycledAssets",
    rt.ASSIGNED_TO AS "AssignedTo",
    rt.ASSIGNED_DATE AS "AssignedDate",
    rt.START_DATE AS "StartDate",
    rt.COMPLETE_DATE AS "CompleteDate",
    rt.DISPOSITION AS "Disposition",
    rt.TARGET_WAREHOUSE AS "TargetWarehouse",
    rt.CANCEL_REASON AS "CancelReason",
    rt.REMARK AS "Remark"
FROM TIT20_RECYCLE_TASK rt
LEFT JOIN TMM22_CUSTOMERS c ON rt.CUSTCD = c.CUSTCD
WHERE rt.RECYCLE_ID = :recycle_id
  AND rt.USEFLG = '1'
""".strip()

# 查询任务明细列表
TASK_DTL_LIST_SQL = """
SELECT
    dtl.RECYCLE_ID AS "RecycleId",
    dtl.ASSET_ID AS "AssetId",
    dtl.ASSET_TYPE AS "AssetType",
    dtl.EXPECTED_STATUS AS "ExpectedStatus",
    dtl.ACTUAL_STATUS AS "ActualStatus",
    dtl.RECOVERED_DATE AS "RecoveredDate",
    dtl.WAREHOUSE_CD AS "WarehouseCd",
    dtl.REMARK AS "Remark",
    r.CUSTCD AS "CustCd",
    r.EID AS "Eid",
    r.ITEMCD AS "ItemCd"
FROM TIT20_RECYCLE_TASK_DTL dtl
JOIN TMM35_CUST_POS_RL r ON dtl.ASSET_ID = r.EID
WHERE dtl.RECYCLE_ID = :recycle_id
ORDER BY dtl.ASSET_ID
""".strip()

# 分配任务
ASSIGN_TASK_SQL = """
UPDATE TIT20_RECYCLE_TASK
SET TASK_STATUS = '01',
    ASSIGNED_TO = :assigned_to,
    ASSIGNED_DATE = SYSDATE,
    UPDDATE = SYSDATE
WHERE RECYCLE_ID = :recycle_id
  AND TASK_STATUS = '00'
""".strip()

# 开始回收
START_RECYCLE_SQL = """
UPDATE TIT20_RECYCLE_TASK
SET TASK_STATUS = '02',
    START_DATE = SYSDATE,
    UPDDATE = SYSDATE
WHERE RECYCLE_ID = :recycle_id
  AND TASK_STATUS = '01'
""".strip()

# 完成回收
COMPLETE_RECYCLE_SQL = """
UPDATE TIT20_RECYCLE_TASK
SET TASK_STATUS = '03',
    COMPLETE_DATE = SYSDATE,
    ACTUAL_COUNT = :actual_count,
    RECYCLED_ASSETS = :recycled_assets,
    DISPOSITION = :disposition,
    TARGET_WAREHOUSE = :target_warehouse,
    UPDDATE = SYSDATE
WHERE RECYCLE_ID = :recycle_id
  AND TASK_STATUS IN ('00', '01', '02')
""".strip()

# 取消任务
CANCEL_TASK_SQL = """
UPDATE TIT20_RECYCLE_TASK
SET TASK_STATUS = '09',
    CANCEL_REASON = :cancel_reason,
    UPDDATE = SYSDATE
WHERE RECYCLE_ID = :recycle_id
  AND TASK_STATUS IN ('00', '01')
""".strip()

# 更新明细实际状态
UPDATE_DTL_STATUS_SQL = """
UPDATE TIT20_RECYCLE_TASK_DTL
SET ACTUAL_STATUS = :actual_status,
    RECOVERED_DATE = CASE WHEN :actual_status = 'COMPLETED' THEN SYSDATE ELSE RECOVERED_DATE END,
    WAREHOUSE_CD = :warehouse_cd
WHERE RECYCLE_ID = :recycle_id
  AND ASSET_ID = :asset_id
""".strip()

# 回收统计
RECYCLE_STATS_SQL = """
SELECT
    COUNT(*) AS "TotalTasks",
    SUM(CASE WHEN TASK_STATUS = '03' THEN 1 ELSE 0 END) AS "CompletedTasks",
    SUM(CASE WHEN TASK_STATUS = '09' THEN 1 ELSE 0 END) AS "CancelledTasks",
    SUM(ASSET_COUNT) AS "TotalAssets",
    SUM(ACTUAL_COUNT) AS "RecycledAssets",
    SUM(CASE WHEN DISPOSITION = '01' THEN ACTUAL_COUNT ELSE 0 END) AS "RenovatedCount",
    SUM(CASE WHEN DISPOSITION = '02' THEN ACTUAL_COUNT ELSE 0 END) AS "ScrappedCount",
    SUM(CASE WHEN DISPOSITION = '03' THEN ACTUAL_COUNT ELSE 0 END) AS "TransferredCount"
FROM TIT20_RECYCLE_TASK
WHERE GENDATE BETWEEN :start_date AND :end_date
  AND USEFLG = '1'
""".strip()


class RecycleTaskRepository:
    """
    回收任务数据访问仓储。
    """

    def __init__(self) -> None:
        """初始化仓储。"""
        pass

    def generate_recycle_id(self) -> str | None:
        """生成回收任务ID。"""
        rows = self._query_all(GENERATE_RECYCLE_ID_SQL, {})
        if not rows:
            return None
        return rows[0]["RecycleId"]

    def create_task(
        self,
        recycle_type: str,
        plan_no: str,
        cust_cd: str,
        assets: list[dict[str, Any]],
        oper_cd: str,
        remark: str = "",
    ) -> str | None:
        """
        创建回收任务。

        参数：
            recycle_type: 回收类型（01旧机翻新/02关门回收）
            plan_no: 预计划单号
            cust_cd: 门店代码
            assets: 资产列表
            oper_cd: 操作员代码
            remark: 备注

        返回值：
            str | None: 回收任务ID或空
        """
        recycle_id = self.generate_recycle_id()
        if recycle_id is None:
            return None

        # 创建主表
        asset_list = ",".join([a["eid"] for a in assets])
        if not self._execute(CREATE_RECYCLE_TASK_SQL, {
            "recycle_id": recycle_id,
            "recycle_type": recycle_type,
            "plan_no": plan_no,
            "cust_cd": cust_cd,
            "asset_count": len(assets),
            "asset_list": asset_list,
            "oper_cd": oper_cd,
            "remark": remark,
        }):
            return None

        # 创建明细
        for asset in assets:
            self._execute(CREATE_TASK_DETAIL_SQL, {
                "recycle_id": recycle_id,
                "asset_id": asset["eid"],
                "asset_type": asset.get("asset_type", "OLD"),
            })

        return recycle_id

    def list_tasks(
        self,
        cust_cd: str | None = None,
        plan_no: str | None = None,
        task_status: str | None = None,
    ) -> list[dict[str, Any]]:
        """查询回收任务列表。"""
        rows = self._query_all(TASK_LIST_SQL, {
            "cust_cd": cust_cd,
            "plan_no": plan_no,
            "task_status": task_status,
        })
        if rows is None:
            return []
        return [
            {
                "recycle_id": row["RecycleId"],
                "recycle_type": row["RecycleType"],
                "plan_no": row["PlanNo"],
                "cust_cd": row["CustCd"],
                "cust_nm": row.get("CustNm"),
                "task_status": row["TaskStatus"],
                "asset_count": row["AssetCount"],
                "actual_count": row.get("ActualCount", 0),
                "assigned_to": row.get("AssignedTo"),
                "assigned_date": row.get("AssignedDate"),
                "complete_date": row.get("CompleteDate"),
                "disposition": row.get("Disposition"),
                "gen_date": row["GenDate"],
            }
            for row in rows
        ]

    def get_task_detail(self, recycle_id: str) -> dict[str, Any] | None:
        """获取回收任务详情。"""
        rows = self._query_all(TASK_DETAIL_SQL, {"recycle_id": recycle_id})
        if not rows:
            return None
        row = rows[0]
        return {
            "recycle_id": row["RecycleId"],
            "recycle_type": row["RecycleType"],
            "plan_no": row["PlanNo"],
            "cust_cd": row["CustCd"],
            "cust_nm": row.get("CustNm"),
            "task_status": row["TaskStatus"],
            "asset_count": row["AssetCount"],
            "asset_list": row.get("AssetList", "").split(",") if row.get("AssetList") else [],
            "actual_count": row.get("ActualCount", 0),
            "recycled_assets": row.get("RecycledAssets", "").split(",") if row.get("RecycledAssets") else [],
            "assigned_to": row.get("AssignedTo"),
            "assigned_date": row.get("AssignedDate"),
            "start_date": row.get("StartDate"),
            "complete_date": row.get("CompleteDate"),
            "disposition": row.get("Disposition"),
            "target_warehouse": row.get("TargetWarehouse"),
            "cancel_reason": row.get("CancelReason"),
            "remark": row.get("Remark"),
        }

    def assign_task(self, recycle_id: str, user_id: str) -> bool:
        """分配任务。"""
        return self._execute(ASSIGN_TASK_SQL, {
            "recycle_id": recycle_id,
            "assigned_to": user_id,
        })

    def start_recycle(self, recycle_id: str) -> bool:
        """开始回收。"""
        return self._execute(START_RECYCLE_SQL, {"recycle_id": recycle_id})

    def complete_recycle(
        self,
        recycle_id: str,
        actual_assets: list[str],
        disposition: str,
        target_warehouse: str,
    ) -> bool:
        """完成回收。"""
        return self._execute(COMPLETE_RECYCLE_SQL, {
            "recycle_id": recycle_id,
            "actual_count": len(actual_assets),
            "recycled_assets": ",".join(actual_assets),
            "disposition": disposition,
            "target_warehouse": target_warehouse,
        })

    def cancel_task(self, recycle_id: str, reason: str) -> bool:
        """取消任务。"""
        return self._execute(CANCEL_TASK_SQL, {
            "recycle_id": recycle_id,
            "cancel_reason": reason,
        })

    def update_asset_status(
        self,
        recycle_id: str,
        eid: str,
        actual_status: str,
        warehouse_cd: str,
    ) -> bool:
        """更新资产回收状态。"""
        return self._execute(UPDATE_DTL_STATUS_SQL, {
            "recycle_id": recycle_id,
            "asset_id": eid,
            "actual_status": actual_status,
            "warehouse_cd": warehouse_cd,
        })

    def get_recycle_stats(
        self,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """获取回收统计。"""
        rows = self._query_all(RECYCLE_STATS_SQL, {
            "start_date": start_date,
            "end_date": end_date,
        })
        if not rows:
            return {}
        row = rows[0]
        total = row.get("TotalAssets", 0)
        actual = row.get("RecycledAssets", 0)
        return {
            "total_tasks": row.get("TotalTasks", 0),
            "completed_tasks": row.get("CompletedTasks", 0),
            "cancelled_tasks": row.get("CancelledTasks", 0),
            "total_assets": total,
            "recycled_assets": actual,
            "recycle_rate": round(actual / total * 100, 2) if total > 0 else 0,
            "renovated_count": row.get("RenovatedCount", 0),
            "scrapped_count": row.get("ScrappedCount", 0),
            "transferred_count": row.get("TransferredCount", 0),
        }

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
            logger.exception("回收任务查询失败")
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
            logger.exception("回收任务更新失败")
            return False
