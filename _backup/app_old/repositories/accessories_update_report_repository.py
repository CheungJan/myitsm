# -*- coding: utf-8 -*-
"""
配件更新报表仓储。
文件说明：提供配件更新报表查询能力。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class AccessoriesUpdateReportRepository:
    """配件更新报表仓储类。"""

    def list_reports(
        self,
        start_date: str,
        end_date: str,
        maintenance_id: Optional[str] = None,
        store_id: Optional[str] = None,
        custcard: Optional[str] = None,
        itemcd: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询配件更新报表。"""
        where_clauses = [
            "U.MAINTENANCE_ID = M.MAINTENANCE_ID",
            "C.CUSTCD = M.STORE_ID",
            "U.CREATE_TIME >= TO_DATE(:start_date, 'YYYY-MM-DD')",
            "U.CREATE_TIME < TO_DATE(:end_date, 'YYYY-MM-DD') + 1",
        ]
        params: Dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
        }

        if maintenance_id:
            where_clauses.append("M.MAINTENANCE_ID LIKE :maintenance_id")
            params["maintenance_id"] = f"%{maintenance_id}%"
        if store_id:
            where_clauses.append("M.STORE_ID LIKE :store_id")
            params["store_id"] = f"%{store_id}%"
        if custcard:
            where_clauses.append("C.CUSTCARD LIKE :custcard")
            params["custcard"] = f"%{custcard}%"
        if itemcd:
            where_clauses.append("R.ITEMCD = :itemcd")
            params["itemcd"] = itemcd

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM TIT25_ACCESSORIES_UPDATE U,
                 TIT10_MAINTENANCEDAY M,
                 TMM22_CUSTOMERS C,
                 TMM35_CUST_POS_RL R
            WHERE {where_sql}
              AND R.EID = U.DEVICE_ID
        """

        list_sql = f"""
            SELECT
                M.MAINTENANCE_ID,
                C.CLASSCD,
                C.CUSTCARD,
                C.BUSITYP,
                C.CUSTNM,
                C.PHONENO,
                C.ADDRESS,
                M.REQUEST_TIME,
                M.SHORT_DESCRIPTION,
                M.DETAIL_DESCRIPTION,
                U.ENGINEER_ID,
                U.ACCESSORIES_TYPE,
                R.ITEMCD,
                U.OLD_ACCESSORIES_ID,
                U.NEW_ACCESSORIES_ID,
                U.PRICE,
                U.AUDITFLG,
                M.CREATOR,
                M.CREATE_TIME,
                M.STORE_ID
            FROM TIT25_ACCESSORIES_UPDATE U,
                 TIT10_MAINTENANCEDAY M,
                 TMM22_CUSTOMERS C,
                 TMM35_CUST_POS_RL R
            WHERE {where_sql}
              AND R.EID = U.DEVICE_ID
            ORDER BY U.CREATE_TIME DESC, M.MAINTENANCE_ID DESC
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
            logger.error("查询配件更新报表失败: %s", exc)
            raise
