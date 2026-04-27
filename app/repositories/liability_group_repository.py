# -*- coding: utf-8 -*-
"""
免责分部门处理仓储。
文件说明：对接 TIT10_MAINTENANCE_LIABILITY 与 TIT10_MAINTENANCEDAY，
提供按部门过滤的列表、明细与保存能力。
作者：Cascade
创建时间：2026-04-20

关联表：
- TIT10_MAINTENANCE_LIABILITY：免责处理表
- TIT10_MAINTENANCEDAY：维护单主表
- TMC13_USERS：用户部门映射
- TIT02_LIABILITYREG：部门到免责编码映射
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class LiabilityGroupRepository:
    """免责分部门处理仓储类。"""

    def get_dept_liabcd_by_user(self, user_cd: str) -> Optional[str]:
        """按用户查询部门对应的免责编码。"""
        sql = """
            SELECT C.LIABCD
            FROM TIT02_LIABILITYREG C
            WHERE C.DESCRIBE = (
                SELECT U.DEPTCD
                FROM TMC13_USERS U
                WHERE U.USERCD = :user_cd
            )
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"user_cd": user_cd})
                    row = cursor.fetchone()
                    return str(row[0]) if row and row[0] else None
        except Exception as exc:
            logger.error("查询部门免责编码失败: %s", exc)
            raise

    def list_liability_groups(
        self,
        dept_liabcd: str,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        store_id: Optional[str] = None,
        maintenance_id: Optional[str] = None,
        exemptflg: str = "%",
        liability_type: str = "%",
        is_finish: str = "1",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询分部门免责处理列表。"""
        where_clauses: List[str] = [
            "D.MAINTENANCE_ID = A.MAINTENANCE_ID",
            "D.CURRENT_STATUS <> '9'",
            "NVL(A.USEFLG,'1') <> '0'",
            "A.DEPTNM = :dept_liabcd",
            "A.IS_FINISH IN ('1','2')",
        ]
        params: Dict[str, Any] = {"dept_liabcd": dept_liabcd}

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

        where_clauses.append("A.EXEMPTFLG LIKE :exemptflg")
        where_clauses.append("A.TYPE LIKE :liability_type")
        where_clauses.append("A.IS_FINISH LIKE :is_finish")
        params["exemptflg"] = exemptflg
        params["liability_type"] = liability_type
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
                D.CREATE_TIME,
                A.EXEMPTFLG,
                A.IS_FINISH,
                A.TYPE,
                A.DEPTNM
            FROM TIT10_MAINTENANCEDAY D, TIT10_MAINTENANCE_LIABILITY A
            WHERE {where_sql}
            ORDER BY A.EXEMPTFLG
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
            logger.error("查询分部门免责列表失败: %s", exc)
            raise

    def list_details(
        self, maintenance_id: str, liability_type: str
    ) -> List[Dict[str, Any]]:
        """查询免责明细（对应 d_itsm_liability_list）。"""
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
                IS_FINISH,
                (CASE WHEN USEFLG = '1' THEN '修改' ELSE '' END) AS XG
            FROM TIT10_MAINTENANCE_LIABILITY
            WHERE MAINTENANCE_ID = :maintenance_id
              AND TYPE = :liability_type
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
            logger.error("查询免责明细失败: %s", exc)
            raise

    def get_is_finish(self, maintenance_id: str, liability_type: str) -> Optional[str]:
        """查询当前记录处理标志。"""
        sql = """
            SELECT IS_FINISH
            FROM TIT10_MAINTENANCE_LIABILITY
            WHERE MAINTENANCE_ID = :maintenance_id
              AND TYPE = :liability_type
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
                    row = cursor.fetchone()
                    return str(row[0]) if row and row[0] is not None else None
        except Exception as exc:
            logger.error("查询处理标志失败: %s", exc)
            raise

    def save_detail(
        self,
        maintenance_id: str,
        liability_type: str,
        oper_cd: str,
        exceptionscd: Optional[str],
        exceptionsnm: Optional[str],
        deptnm: Optional[str],
        assessflg: str,
        exemptflg: str,
    ) -> bool:
        """保存免责明细。"""
        merge_sql = """
            MERGE INTO TIT10_MAINTENANCE_LIABILITY T
            USING (
                SELECT :maintenance_id AS MAINTENANCE_ID, :liability_type AS TYPE FROM DUAL
            ) S
            ON (T.MAINTENANCE_ID = S.MAINTENANCE_ID AND T.TYPE = S.TYPE)
            WHEN MATCHED THEN
                UPDATE SET
                    T.EXCEPTIONSCD = :exceptionscd,
                    T.EXCEPTIONSNM = :exceptionsnm,
                    T.DEPTNM = :deptnm,
                    T.UPDDATE = SYSDATE,
                    T.OPERCD = :oper_cd,
                    T.ASSESSFLG = :assessflg,
                    T.EXEMPTFLG = :exemptflg
            WHEN NOT MATCHED THEN
                INSERT (
                    MAINTENANCE_ID,
                    EXCEPTIONSCD,
                    EXCEPTIONSNM,
                    DEPTNM,
                    UPDDATE,
                    OPERCD,
                    ASSESSFLG,
                    EXEMPTFLG,
                    USEFLG,
                    IS_FINISH,
                    TYPE
                ) VALUES (
                    :maintenance_id,
                    :exceptionscd,
                    :exceptionsnm,
                    :deptnm,
                    SYSDATE,
                    :oper_cd,
                    :assessflg,
                    :exemptflg,
                    '1',
                    '1',
                    :liability_type
                )
        """

        params: Dict[str, Any] = {
            "maintenance_id": maintenance_id,
            "liability_type": liability_type,
            "exceptionscd": exceptionscd,
            "exceptionsnm": exceptionsnm,
            "deptnm": deptnm,
            "oper_cd": oper_cd,
            "assessflg": assessflg,
            "exemptflg": exemptflg,
        }
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(merge_sql, params)
                    conn.commit()
                    return True
        except Exception as exc:
            logger.error("保存免责明细失败: %s", exc)
            raise
