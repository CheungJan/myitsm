# -*- coding: utf-8 -*-
"""
纸张平均报表仓储。
文件说明：提供工程师达标率/纸张平均报表查询能力。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class PaperAverageReportRepository:
    """纸张平均报表仓储类。"""

    def list_reports(
        self,
        start_date: str,
        end_date: str,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """分页查询纸张平均报表。"""
        count_sql = """
            SELECT COUNT(*)
            FROM (
                SELECT
                    NVL(MAX((SELECT NAME FROM TMM46_AREA A WHERE A.ID = V.USEAREA)), 'ZZ') AS AREANM,
                    V.PAPER_ID
                FROM V_ITSM_PAPER_AVERAGEL_DB V
                WHERE V.CREATE_TIME >= TO_DATE(:start_date, 'YYYY-MM-DD')
                  AND V.CREATE_TIME < TO_DATE(:end_date, 'YYYY-MM-DD') + 1
                  AND V.FAULT_TYPE = '1'
                GROUP BY V.PAPER_ID
            ) T
        """

        list_sql = """
            SELECT
                T.AREANM,
                T.PAPER_ID,
                T.COUNT_ZS1,
                T.COUNT_YS1,
                T.COUNT_JQ1,
                T.COUNT_ZS0,
                T.COUNT_YS0,
                T.COUNT_JQ0,
                T.HMSL,
                T.CREATE_TIME
            FROM (
                SELECT
                    NVL(MAX((SELECT NAME FROM TMM46_AREA A WHERE A.ID = V.USEAREA)), 'ZZ') AS AREANM,
                    V.PAPER_ID,
                    SUM(CASE WHEN (D.JJBZ = '5' OR (D.JJBZ IS NULL AND V.CURRENT_STATUS = '3')) AND V.MD_TYPE = 'ZS' AND V.CLASSCD <> '08' THEN V.SUMCOUNT ELSE 0 END) AS COUNT_ZS1,
                    SUM(CASE WHEN (D.JJBZ = '5' OR (D.JJBZ IS NULL AND V.CURRENT_STATUS = '3')) AND V.MD_TYPE = 'YS' AND V.CLASSCD <> '08' THEN V.SUMCOUNT ELSE 0 END) AS COUNT_YS1,
                    SUM(CASE WHEN (D.JJBZ = '5' OR (D.JJBZ IS NULL AND V.CURRENT_STATUS = '3')) AND V.CLASSCD = '08' THEN V.SUMCOUNT ELSE 0 END) AS COUNT_JQ1,
                    SUM(CASE WHEN D.JJBZ = '4' AND V.MD_TYPE = 'ZS' AND V.CLASSCD <> '08' THEN V.SUMCOUNT ELSE 0 END) AS COUNT_ZS0,
                    SUM(CASE WHEN D.JJBZ = '4' AND V.MD_TYPE = 'YS' AND V.CLASSCD <> '08' THEN V.SUMCOUNT ELSE 0 END) AS COUNT_YS0,
                    SUM(CASE WHEN D.JJBZ = '4' AND V.CLASSCD = '08' THEN V.SUMCOUNT ELSE 0 END) AS COUNT_JQ0,
                    SUM(CASE WHEN L.EXEMPTFLG = 'Y' AND L.IS_FINISH = '3' THEN V.SUMCOUNT ELSE 0 END) AS HMSL,
                    MAX(V.CREATE_TIME) AS CREATE_TIME
                FROM V_ITSM_PAPER_AVERAGEL_DB V
                LEFT JOIN (
                    SELECT *
                    FROM TIT10_MAINTENANCE_LIABILITY
                    WHERE TYPE = '1'
                ) L ON V.MASTER_ID = L.MAINTENANCE_ID
                LEFT JOIN (
                    SELECT
                        ROW_NUMBER() OVER(PARTITION BY MAINTENANCE_ID ORDER BY JJBZ, UPDATE_TIME, BUSINESS_OPERATION_ID) AS RNUM,
                        C.*
                    FROM TIT23_MAINTENANCE_D2D C
                    WHERE C.D2D_TYPE = '2'
                      AND C.D2D_GROUP = 1
                ) D ON V.MASTER_ID = D.MAINTENANCE_ID
                   AND D.RNUM = 1
                WHERE V.CREATE_TIME >= TO_DATE(:start_date, 'YYYY-MM-DD')
                  AND V.CREATE_TIME < TO_DATE(:end_date, 'YYYY-MM-DD') + 1
                  AND V.FAULT_TYPE = '1'
                GROUP BY V.PAPER_ID
            ) T
            ORDER BY NVL(T.AREANM, 'ZZ'), LPAD(T.PAPER_ID, 10, '0')
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """

        params = {
            "start_date": start_date,
            "end_date": end_date,
        }

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
            logger.error("查询纸张平均报表失败: %s", exc)
            raise
