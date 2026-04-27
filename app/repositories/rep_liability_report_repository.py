# -*- coding: utf-8 -*-
"""
责任认定报表仓储。
文件说明：提供责任认定报表主列表与明细查询能力。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class RepLiabilityReportRepository:
    """责任认定报表仓储类。"""

    def list_reports(
        self,
        start_date: str,
        end_date: str,
        maintenance_id: Optional[str] = None,
        store_id: Optional[str] = None,
        liability_type: Optional[str] = None,
        exemptflg: Optional[str] = None,
        is_finish: Optional[str] = None,
        deptnm: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询责任认定报表主列表。"""
        where_clauses = [
            "D.MAINTENANCE_ID = A.MAINTENANCE_ID",
            "D.CURRENT_STATUS <> '9'",
            "NVL(A.USEFLG, '1') <> '0'",
            "D.REQUEST_TIME >= TO_DATE(:start_date, 'YYYY-MM-DD')",
            "D.REQUEST_TIME < TO_DATE(:end_date, 'YYYY-MM-DD') + 1",
        ]
        params: Dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
        }

        if maintenance_id:
            where_clauses.append("D.MAINTENANCE_ID LIKE :maintenance_id")
            params["maintenance_id"] = f"%{maintenance_id}%"
        if store_id:
            where_clauses.append("D.STORE_ID LIKE :store_id")
            params["store_id"] = f"%{store_id}%"
        if liability_type:
            where_clauses.append("A.TYPE = :liability_type")
            params["liability_type"] = liability_type
        if exemptflg:
            where_clauses.append("A.EXEMPTFLG = :exemptflg")
            params["exemptflg"] = exemptflg
        if is_finish:
            where_clauses.append("A.IS_FINISH = :is_finish")
            params["is_finish"] = is_finish
        if deptnm:
            where_clauses.append("A.DEPTNM LIKE :deptnm")
            params["deptnm"] = f"%{deptnm}%"

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM TIT10_MAINTENANCEDAY D,
                 TIT10_MAINTENANCE_LIABILITY A
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT
                D.MAINTENANCE_ID,
                D.COMPANY_ID,
                D.STORE_ID,
                (SELECT C.CUSTNM FROM TMM22_CUSTOMERS C WHERE C.CUSTCD = D.STORE_ID) AS CUSTNM,
                D.REQUEST_TIME,
                D.SHORT_DESCRIPTION,
                D.DETAIL_DESCRIPTION,
                A.EXEMPTFLG,
                A.IS_FINISH,
                A.TYPE,
                A.DEPTNM,
                D.CREATOR,
                D.CREATE_TIME
            FROM TIT10_MAINTENANCEDAY D,
                 TIT10_MAINTENANCE_LIABILITY A
            WHERE {where_sql}
            ORDER BY D.REQUEST_TIME DESC, D.MAINTENANCE_ID DESC
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
            logger.error("查询责任认定报表主列表失败: %s", exc)
            raise

    def list_report_details(
        self, maintenance_id: str, liability_type: str
    ) -> list[Dict[str, Any]]:
        """查询责任认定报表明细。"""
        sql = """
            SELECT
                MAINTENANCE_ID,
                EXCEPTIONSCD,
                EXCEPTIONSNM,
                DEPTNM,
                UPDDATE,
                OPERCD,
                ASSESSFLG,
                EXEMPTFLG,
                USEFLG,
                TYPE
            FROM TIT10_MAINTENANCE_LIABILITY
            WHERE MAINTENANCE_ID = :maintenance_id
              AND TYPE = :liability_type
            ORDER BY UPDDATE DESC NULLS LAST
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "maintenance_id": maintenance_id,
                            "liability_type": liability_type,
                        },
                    )
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:
            logger.error("查询责任认定报表明细失败: %s", exc)
            raise
