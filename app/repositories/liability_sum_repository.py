# -*- coding: utf-8 -*-
"""
免责汇总仓储。
文件说明：对接 TIT10_MAINTENANCE_LIABILITY 与 TIT10_MAINTENANCEDAY，
提供免责汇总列表、明细与批量审核能力。
作者：Cascade
创建时间：2026-04-20

关联表：
- TIT10_MAINTENANCE_LIABILITY：免责处理表
- TIT10_MAINTENANCEDAY：维护单主表
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class LiabilitySumRepository:
    """免责汇总仓储类。"""

    def list_liability_summaries(
        self,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        store_id: Optional[str] = None,
        maintenance_id: Optional[str] = None,
        deptnm: Optional[str] = None,
        exemptflg: Optional[str] = None,
        liability_type: Optional[str] = None,
        is_finish: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询免责汇总列表。"""
        where_clauses: List[str] = [
            "D.MAINTENANCE_ID = A.MAINTENANCE_ID",
            "D.CURRENT_STATUS <> '9'",
            "NVL(A.USEFLG, '1') <> '0'",
        ]
        params: Dict[str, Any] = {}

        if begin_date:
            where_clauses.append("TO_CHAR(D.CREATE_TIME,'YYYY-MM-DD') >= :begin_date")
            params["begin_date"] = begin_date
        if end_date:
            where_clauses.append("TO_CHAR(D.CREATE_TIME,'YYYY-MM-DD') <= :end_date")
            params["end_date"] = end_date
        if store_id:
            where_clauses.append("D.STORE_ID = :store_id")
            params["store_id"] = store_id
        if maintenance_id:
            where_clauses.append("D.MAINTENANCE_ID LIKE :maintenance_id")
            params["maintenance_id"] = f"%{maintenance_id}%"
        if deptnm:
            where_clauses.append("A.DEPTNM LIKE :deptnm")
            params["deptnm"] = deptnm
        if exemptflg:
            where_clauses.append("A.EXEMPTFLG LIKE :exemptflg")
            params["exemptflg"] = exemptflg
        if liability_type:
            where_clauses.append("A.TYPE LIKE :liability_type")
            params["liability_type"] = liability_type
        if is_finish:
            where_clauses.append("A.IS_FINISH LIKE :is_finish")
            params["is_finish"] = is_finish

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM TIT10_MAINTENANCEDAY D, TIT10_MAINTENANCE_LIABILITY A
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT
                D.MAINTENANCE_ID,
                D.COMPANY_ID,
                D.STORE_ID,
                D.REQUEST_TIME,
                D.EXPECTED_COMPLETION_TIME,
                D.SHORT_DESCRIPTION,
                D.DETAIL_DESCRIPTION,
                D.CURRENT_STATUS,
                D.CREATE_TIME,
                D.CREATOR,
                D.CLOSE_TIME,
                D.REVISIT_TIME,
                A.EXEMPTFLG,
                A.IS_FINISH,
                A.TYPE,
                A.DEPTNM
            FROM TIT10_MAINTENANCEDAY D, TIT10_MAINTENANCE_LIABILITY A
            WHERE {where_sql}
            ORDER BY A.EXEMPTFLG, D.MAINTENANCE_ID
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
            logger.error("查询免责汇总列表失败: %s", exc)
            raise

    def list_liability_details(
        self, maintenance_id: str, liability_type: str
    ) -> List[Dict[str, Any]]:
        """查询免责汇总明细（对应 d_itsm_liability_list）。"""
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
                TYPE,
                CASE WHEN USEFLG = '1' THEN '修改' ELSE '' END AS XG
            FROM TIT10_MAINTENANCE_LIABILITY
            WHERE MAINTENANCE_ID = :maintenance_id
              AND TYPE = :liability_type
            ORDER BY UPDDATE DESC
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
            logger.error("查询免责汇总明细失败: %s", exc)
            raise

    def batch_audit(self, records: List[Dict[str, str]], oper_cd: str) -> int:
        """批量审核（更新 IS_FINISH=3）。"""
        sql = """
            UPDATE TIT10_MAINTENANCE_LIABILITY
            SET IS_FINISH = '3',
                OPERCD = :oper_cd,
                UPDDATE = SYSDATE
            WHERE MAINTENANCE_ID = :maintenance_id
              AND TYPE = :liability_type
              AND NVL(USEFLG, '1') <> '0'
              AND NVL(IS_FINISH, '0') <> '3'
        """
        affected = 0

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    for record in records:
                        cursor.execute(
                            sql,
                            {
                                "oper_cd": oper_cd,
                                "maintenance_id": record["maintenance_id"],
                                "liability_type": record["liability_type"],
                            },
                        )
                        affected += int(cursor.rowcount)
                    conn.commit()
            return affected
        except Exception as exc:
            logger.error("批量审核免责汇总失败: %s", exc)
            raise
