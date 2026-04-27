# -*- coding: utf-8 -*-
"""
时间点等级仓储。
文件说明：对接 TIT01_TIMEPOINT_AREA 与 TMM22_CUSTOMERS，提供等级维护及客户等级分配能力。
作者：Cascade
创建时间：2026-04-20

关联表：
- TIT01_TIMEPOINT_AREA：时间点等级定义
- TMM22_CUSTOMERS：客户主数据（LEVELS 字段）
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class TimepointLevelsRepository:
    """时间点等级仓储类。"""

    def __init__(self) -> None:
        self.level_table = "TIT01_TIMEPOINT_AREA"
        self.customer_table = "TMM22_CUSTOMERS"

    def list_levels(
        self,
        include_invalid: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询等级定义。"""
        where_clauses = ["1 = 1"]
        params: Dict[str, Any] = {}

        if not include_invalid:
            where_clauses.append("NVL(USEFLG, '1') = '1'")

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM {self.level_table}
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT
                LEVELS,
                EXPLAIN,
                TIMEPOINT,
                BEFORETM,
                AFTERTM,
                OPERCD,
                GENDATE,
                UPDDATE,
                USEFLG
            FROM {self.level_table}
            WHERE {where_sql}
            ORDER BY LEVELS
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, params)
                    total = int(cursor.fetchone()[0])

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
            logger.error("查询等级定义失败: %s", exc)
            raise

    def save_level(
        self,
        levels: str,
        explain: str,
        timepoint: Optional[str],
        beforetm: Optional[float],
        aftertm: Optional[float],
        opercd: str,
        useflg: str = "1",
    ) -> bool:
        """保存等级定义（存在则更新，不存在则新增）。"""
        merge_sql = f"""
            MERGE INTO {self.level_table} T
            USING (
                SELECT :levels AS LEVELS FROM DUAL
            ) S
            ON (T.LEVELS = S.LEVELS)
            WHEN MATCHED THEN
                UPDATE SET
                    T.EXPLAIN = :explain,
                    T.TIMEPOINT = CASE WHEN :timepoint IS NULL THEN T.TIMEPOINT ELSE TO_DATE(:timepoint, 'HH24:MI:SS') END,
                    T.BEFORETM = :beforetm,
                    T.AFTERTM = :aftertm,
                    T.OPERCD = :opercd,
                    T.UPDDATE = SYSDATE,
                    T.USEFLG = :useflg
            WHEN NOT MATCHED THEN
                INSERT (
                    LEVELS,
                    EXPLAIN,
                    TIMEPOINT,
                    BEFORETM,
                    AFTERTM,
                    OPERCD,
                    GENDATE,
                    UPDDATE,
                    USEFLG
                ) VALUES (
                    :levels,
                    :explain,
                    CASE WHEN :timepoint IS NULL THEN NULL ELSE TO_DATE(:timepoint, 'HH24:MI:SS') END,
                    :beforetm,
                    :aftertm,
                    :opercd,
                    SYSDATE,
                    SYSDATE,
                    :useflg
                )
        """

        params = {
            "levels": levels,
            "explain": explain,
            "timepoint": timepoint,
            "beforetm": beforetm,
            "aftertm": aftertm,
            "opercd": opercd,
            "useflg": useflg,
        }

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(merge_sql, params)
                    conn.commit()
                    return True
        except Exception as exc:
            logger.error("保存等级定义失败: %s", exc)
            raise

    def list_customers_by_level(
        self,
        levels: str,
        custcd: Optional[str] = None,
        custnm: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """按等级查询客户。"""
        where_clauses = ["NVL(USEFLG, '1') = '1'", "NVL(LEVELS, '') = :levels"]
        params: Dict[str, Any] = {"levels": levels}

        if custcd:
            where_clauses.append("CUSTCD LIKE :custcd")
            params["custcd"] = f"%{custcd}%"
        if custnm:
            where_clauses.append("CUSTNM LIKE :custnm")
            params["custnm"] = f"%{custnm}%"

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM {self.customer_table}
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT
                CUSTCD,
                CUSTNM,
                CUSTCARD,
                PHONENO,
                ADDRESS,
                LEVELS,
                OPERCD,
                GENDATE,
                UPDDATE,
                USEFLG
            FROM {self.customer_table}
            WHERE {where_sql}
            ORDER BY CUSTCD
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, params)
                    total = int(cursor.fetchone()[0])

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
            logger.error("按等级查询客户失败: %s", exc)
            raise

    def assign_level_to_customers(
        self, levels: str, custcd_list: list[str], opercd: str
    ) -> int:
        """批量分配客户等级。"""
        update_sql = f"""
            UPDATE {self.customer_table}
            SET LEVELS = :levels,
                OPERCD = :opercd,
                UPDDATE = SYSDATE
            WHERE CUSTCD = :custcd
              AND NVL(USEFLG, '1') = '1'
        """

        updated = 0
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    for custcd in custcd_list:
                        cursor.execute(
                            update_sql,
                            {"levels": levels, "opercd": opercd, "custcd": custcd},
                        )
                        updated += int(cursor.rowcount or 0)
                    conn.commit()
            return updated
        except Exception as exc:
            logger.error("批量分配客户等级失败: %s", exc)
            raise

    def clear_customer_levels(self, custcd_list: list[str], opercd: str) -> int:
        """批量清空客户等级。"""
        update_sql = f"""
            UPDATE {self.customer_table}
            SET LEVELS = '',
                OPERCD = :opercd,
                UPDDATE = SYSDATE
            WHERE CUSTCD = :custcd
              AND NVL(USEFLG, '1') = '1'
        """

        updated = 0
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    for custcd in custcd_list:
                        cursor.execute(update_sql, {"opercd": opercd, "custcd": custcd})
                        updated += int(cursor.rowcount or 0)
                    conn.commit()
            return updated
        except Exception as exc:
            logger.error("批量清空客户等级失败: %s", exc)
            raise
