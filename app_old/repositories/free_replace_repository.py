# -*- coding: utf-8 -*-
"""
免费更换单仓储。
文件说明：对接 TIT28_FREE_REPLACE/TIT28_FREE_REPLACE_DT，并提供关单约束校验所需数据访问。
作者：Cascade
创建时间：2026-04-20

关联表：
- TIT28_FREE_REPLACE：免费更换单主表
- TIT28_FREE_REPLACE_DT：免费更换设备明细子表
- TIT24_MAINTENANCE_RV：回访记录（关单前校验）
- TIT27_CLOSE_BILLS：关单记录
"""

import logging
from typing import Any, Dict, List, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class FreeReplaceRepository:
    """免费更换单仓储类。"""

    def __init__(self) -> None:
        self.table = "TIT28_FREE_REPLACE"
        self.pk_field = "RENEW_ID"

    def get_by_id(self, renew_id: str) -> Optional[Dict[str, Any]]:
        """根据主键查询免费更换单详情。"""
        sql = f"""
            SELECT
                RENEW_ID,
                COMPANY_ID,
                STORE_ID,
                REQUEST_TIME,
                REQUSET_PAPER_ID,
                OLD_DEVICE_ID,
                NEW_DEVICE_ID,
                DELIVER_NO,
                COUNT,
                EXPECTED_COMPLETION_TIME,
                SHORT_DESCRIPTION,
                DETAIL_DESCRIPTION,
                CURRENT_STATUS,
                IS_SUCCESS,
                IS_OLD,
                IS_BACK,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                FIRSTOR,
                FIRST_TIME,
                LEAVE_TIME,
                CLOSE_TIME,
                REVISIT_TIME
            FROM {self.table}
            WHERE {self.pk_field} = :renew_id
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"renew_id": renew_id})
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as exc:
            logger.error("查询免费更换单详情失败: %s", exc)
            raise

    def list_free_replaces(
        self,
        store_id: Optional[str] = None,
        current_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询免费更换单列表。"""
        where_clauses: List[str] = ["1 = 1"]
        params: Dict[str, Any] = {}

        if store_id:
            where_clauses.append("STORE_ID = :store_id")
            params["store_id"] = store_id
        if current_status:
            where_clauses.append("CURRENT_STATUS = :current_status")
            params["current_status"] = current_status

        where_sql = " AND ".join(where_clauses)
        count_sql = f"SELECT COUNT(*) FROM {self.table} WHERE {where_sql}"
        list_sql = f"""
            SELECT
                RENEW_ID,
                STORE_ID,
                REQUEST_TIME,
                OLD_DEVICE_ID,
                NEW_DEVICE_ID,
                CURRENT_STATUS,
                IS_SUCCESS,
                IS_OLD,
                CREATE_TIME,
                CREATOR
            FROM {self.table}
            WHERE {where_sql}
            ORDER BY CREATE_TIME DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, params)
                    total = cursor.fetchone()[0]

                    query_params = {
                        **params,
                        "offset": (page - 1) * page_size,
                        "limit": page_size,
                    }
                    cursor.execute(list_sql, query_params)
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    items = [dict(zip(columns, row)) for row in rows]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as exc:
            logger.error("查询免费更换单列表失败: %s", exc)
            raise

    def create_free_replace(
        self,
        renew_id: str,
        store_id: str,
        creator: str,
        company_id: Optional[str] = None,
        request_time: Optional[str] = None,
        request_paper_id: Optional[str] = None,
        old_device_id: Optional[str] = None,
        new_device_id: Optional[str] = None,
        deliver_no: Optional[str] = None,
        count: Optional[int] = None,
        expected_completion_time: Optional[str] = None,
        short_description: Optional[str] = None,
        detail_description: Optional[str] = None,
        current_status: str = "1",
        is_success: Optional[str] = None,
        is_old: str = "0",
        is_back: Optional[str] = None,
    ) -> bool:
        """新增免费更换单主表记录。"""
        sql = f"""
            INSERT INTO {self.table} (
                RENEW_ID,
                COMPANY_ID,
                STORE_ID,
                REQUEST_TIME,
                REQUSET_PAPER_ID,
                OLD_DEVICE_ID,
                NEW_DEVICE_ID,
                DELIVER_NO,
                COUNT,
                EXPECTED_COMPLETION_TIME,
                SHORT_DESCRIPTION,
                DETAIL_DESCRIPTION,
                CURRENT_STATUS,
                IS_SUCCESS,
                IS_OLD,
                IS_BACK,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                FIRSTOR
            ) VALUES (
                :renew_id,
                :company_id,
                :store_id,
                TO_DATE(:request_time, 'YYYY-MM-DD HH24:MI:SS'),
                :request_paper_id,
                :old_device_id,
                :new_device_id,
                :deliver_no,
                :count,
                TO_DATE(:expected_completion_time, 'YYYY-MM-DD HH24:MI:SS'),
                :short_description,
                :detail_description,
                :current_status,
                :is_success,
                :is_old,
                :is_back,
                SYSDATE,
                :creator,
                SYSDATE,
                :creator,
                :creator
            )
        """

        params: Dict[str, Any] = {
            "renew_id": renew_id,
            "company_id": company_id,
            "store_id": store_id,
            "request_time": request_time,
            "request_paper_id": request_paper_id,
            "old_device_id": old_device_id,
            "new_device_id": new_device_id,
            "deliver_no": deliver_no,
            "count": count,
            "expected_completion_time": expected_completion_time,
            "short_description": short_description,
            "detail_description": detail_description,
            "current_status": current_status,
            "is_success": is_success,
            "is_old": is_old,
            "is_back": is_back,
            "creator": creator,
        }

        for key in ["request_time", "expected_completion_time"]:
            if not params[key]:
                params[key] = None

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
            return True
        except Exception as exc:
            logger.error("新增免费更换单失败: %s", exc)
            raise

    def list_free_replace_details(self, renew_id: str) -> List[Dict[str, Any]]:
        """查询免费更换单设备明细。"""
        sql = """
            SELECT
                RENOVATE_ID,
                BUSINESS_OPERATION_ID,
                DEVICE_ID,
                NEW_DEVICE_ID,
                DELIVERYID,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                IS_FINISH
            FROM TIT28_FREE_REPLACE_DT
            WHERE RENOVATE_ID = :renew_id
            ORDER BY BUSINESS_OPERATION_ID DESC, CREATE_TIME DESC
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"renew_id": renew_id})
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:
            logger.error("查询免费更换设备明细失败: %s", exc)
            raise

    def create_free_replace_detail(
        self,
        renew_id: str,
        business_operation_id: int,
        creator: str,
        device_id: Optional[str] = None,
        new_device_id: Optional[str] = None,
        delivery_id: Optional[str] = None,
        is_finish: str = "0",
    ) -> bool:
        """新增免费更换设备明细。"""
        sql = """
            INSERT INTO TIT28_FREE_REPLACE_DT (
                RENOVATE_ID,
                BUSINESS_OPERATION_ID,
                DEVICE_ID,
                NEW_DEVICE_ID,
                DELIVERYID,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR,
                IS_FINISH
            ) VALUES (
                :renew_id,
                :business_operation_id,
                :device_id,
                :new_device_id,
                :delivery_id,
                SYSDATE,
                :creator,
                SYSDATE,
                :creator,
                :is_finish
            )
        """
        params = {
            "renew_id": renew_id,
            "business_operation_id": business_operation_id,
            "device_id": device_id,
            "new_device_id": new_device_id,
            "delivery_id": delivery_id,
            "creator": creator,
            "is_finish": is_finish,
        }
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
            return True
        except Exception as exc:
            logger.error("新增免费更换设备明细失败: %s", exc)
            raise

    def count_details_by_finish(self, renew_id: str, is_finish: str) -> int:
        """按提交状态统计设备明细数量。"""
        sql = """
            SELECT COUNT(*)
            FROM TIT28_FREE_REPLACE_DT
            WHERE RENOVATE_ID = :renew_id
              AND IS_FINISH = :is_finish
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"renew_id": renew_id, "is_finish": is_finish})
                    return int(cursor.fetchone()[0])
        except Exception as exc:
            logger.error("统计免费更换设备明细失败: %s", exc)
            raise

    def count_revisit_records(self, renew_id: str) -> int:
        """统计免费更换单回访记录数量。"""
        sql = """
            SELECT COUNT(*)
            FROM TIT24_MAINTENANCE_RV
            WHERE MAINTENANCE_ID = :renew_id
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"renew_id": renew_id})
                    return int(cursor.fetchone()[0])
        except Exception as exc:
            logger.error("统计回访记录失败: %s", exc)
            raise

    def update_status(
        self,
        renew_id: str,
        old_status: str,
        new_status: str,
        updator: str,
        close_time: Optional[str] = None,
    ) -> bool:
        """更新免费更换单状态（带乐观锁）。"""
        if close_time:
            sql = f"""
                UPDATE {self.table}
                SET CURRENT_STATUS = :new_status,
                    CLOSE_TIME = TO_DATE(:close_time, 'YYYY-MM-DD HH24:MI:SS'),
                    UPDATE_TIME = SYSDATE,
                    UPDATOR = :updator
                WHERE {self.pk_field} = :renew_id
                  AND CURRENT_STATUS = :old_status
            """
            params = {
                "new_status": new_status,
                "close_time": close_time,
                "updator": updator,
                "renew_id": renew_id,
                "old_status": old_status,
            }
        else:
            sql = f"""
                UPDATE {self.table}
                SET CURRENT_STATUS = :new_status,
                    UPDATE_TIME = SYSDATE,
                    UPDATOR = :updator
                WHERE {self.pk_field} = :renew_id
                  AND CURRENT_STATUS = :old_status
            """
            params = {
                "new_status": new_status,
                "updator": updator,
                "renew_id": renew_id,
                "old_status": old_status,
            }

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as exc:
            logger.error("更新免费更换单状态失败: %s", exc)
            raise

    def next_close_business_operation_id(self, renew_id: str) -> int:
        """获取关单记录下一业务流水号。"""
        sql = """
            SELECT NVL(MAX(BUSINESS_OPERATION_ID), 0) + 1
            FROM TIT27_CLOSE_BILLS
            WHERE MAINTENANCE_ID = :renew_id
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"renew_id": renew_id})
                    return int(cursor.fetchone()[0])
        except Exception as exc:
            logger.error("获取关单流水号失败: %s", exc)
            raise

    def insert_close_bill(
        self,
        renew_id: str,
        business_operation_id: int,
        close_time: str,
        close_type: str,
        is_old: Optional[str],
        creator: str,
    ) -> bool:
        """写入关单记录。"""
        sql = """
            INSERT INTO TIT27_CLOSE_BILLS (
                MAINTENANCE_ID,
                BUSINESS_OPERATION_ID,
                CLOSE_TIME,
                CLOSE_TYPE,
                IS_OLD,
                CREATE_TIME,
                CREATOR
            ) VALUES (
                :renew_id,
                :business_operation_id,
                TO_DATE(:close_time, 'YYYY-MM-DD HH24:MI:SS'),
                :close_type,
                :is_old,
                TO_DATE(:close_time, 'YYYY-MM-DD HH24:MI:SS'),
                :creator
            )
        """
        params = {
            "renew_id": renew_id,
            "business_operation_id": business_operation_id,
            "close_time": close_time,
            "close_type": close_type,
            "is_old": is_old,
            "creator": creator,
        }
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
        except Exception as exc:
            logger.error("写入关单记录失败: %s", exc)
            raise
