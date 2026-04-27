# -*- coding: utf-8 -*-
"""
免责处理仓储。
文件说明：对接 TIT10_MAINTENANCE_LIABILITY 及关联表，提供列表、详情、保存与字典查询能力。
作者：Cascade
创建时间：2026-04-20

关联表：
- TIT10_MAINTENANCE_LIABILITY：单据豁免信息表
- TIT10_MAINTENANCEDAY：日常维护单主表（列表联合展示）
- TIT02_LIABILITYREG / TIT02_LIABILITYREGDT：免责条例字典
"""

import logging
from typing import Any, Dict, List, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class LiabilityRepository:
    """免责处理仓储类。"""

    def list_liabilities(
        self,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        maintenance_id: Optional[str] = None,
        exemptflg: Optional[str] = None,
        liability_type: Optional[str] = None,
        is_finish: Optional[str] = None,
        include_finished: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询免责处理列表（对应 PB 主列表查询）。"""
        where_clauses: List[str] = [
            "D.MAINTENANCE_ID = A.MAINTENANCE_ID",
            "D.CURRENT_STATUS <> '9'",
            "NVL(A.USEFLG, '1') <> '0'",
        ]
        params: Dict[str, Any] = {}

        if begin_date:
            where_clauses.append(
                "D.REQUEST_TIME >= TO_DATE(:begin_date, 'YYYY-MM-DD HH24:MI:SS')"
            )
            params["begin_date"] = begin_date
        if end_date:
            where_clauses.append(
                "D.REQUEST_TIME <= TO_DATE(:end_date, 'YYYY-MM-DD HH24:MI:SS')"
            )
            params["end_date"] = end_date
        if maintenance_id:
            where_clauses.append("D.MAINTENANCE_ID LIKE :maintenance_id")
            params["maintenance_id"] = f"%{maintenance_id}%"
        if exemptflg:
            where_clauses.append("A.EXEMPTFLG = :exemptflg")
            params["exemptflg"] = exemptflg
        if liability_type:
            where_clauses.append("A.TYPE = :liability_type")
            params["liability_type"] = liability_type
        if is_finish:
            where_clauses.append("A.IS_FINISH = :is_finish")
            params["is_finish"] = is_finish
        elif not include_finished:
            where_clauses.append("A.IS_FINISH NOT IN ('2', '3')")

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
                A.EXCEPTIONSCD,
                A.EXCEPTIONSNM,
                A.DEPTNM,
                A.UPDDATE,
                A.OPERCD,
                A.ASSESSFLG,
                A.EXEMPTFLG,
                A.TYPE,
                A.IS_FINISH,
                A.USEFLG
            FROM TIT10_MAINTENANCEDAY D, TIT10_MAINTENANCE_LIABILITY A
            WHERE {where_sql}
            ORDER BY A.IS_FINISH, A.EXEMPTFLG, D.MAINTENANCE_ID
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
            logger.error("查询免责处理列表失败: %s", exc)
            raise

    def get_liability(
        self, maintenance_id: str, liability_type: str
    ) -> Optional[Dict[str, Any]]:
        """查询免责处理详情。"""
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
                IS_FINISH,
                TYPE,
                SETFROM
            FROM TIT10_MAINTENANCE_LIABILITY
            WHERE MAINTENANCE_ID = :maintenance_id
              AND TYPE = :liability_type
              AND NVL(USEFLG, '1') <> '0'
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
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as exc:
            logger.error("查询免责处理详情失败: %s", exc)
            raise

    def save_liability(
        self,
        maintenance_id: str,
        liability_type: str,
        oper_cd: str,
        is_finish: str,
        exceptionscd: Optional[str] = None,
        exceptionsnm: Optional[str] = None,
        deptnm: Optional[str] = None,
        assessflg: str = "N",
        exemptflg: str = "N",
        useflg: str = "1",
        setfrom: Optional[str] = None,
    ) -> bool:
        """保存免责处理记录（存在则更新，不存在则新增）。"""
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
                    T.EXEMPTFLG = :exemptflg,
                    T.IS_FINISH = :is_finish,
                    T.USEFLG = :useflg,
                    T.SETFROM = :setfrom
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
                    TYPE,
                    SETFROM
                ) VALUES (
                    :maintenance_id,
                    :exceptionscd,
                    :exceptionsnm,
                    :deptnm,
                    SYSDATE,
                    :oper_cd,
                    :assessflg,
                    :exemptflg,
                    :useflg,
                    :is_finish,
                    :liability_type,
                    :setfrom
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
            "is_finish": is_finish,
            "useflg": useflg,
            "setfrom": setfrom,
        }
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(merge_sql, params)
                    conn.commit()
                    return True
        except Exception as exc:
            logger.error("保存免责处理记录失败: %s", exc)
            raise

    def batch_update_is_finish(
        self,
        maintenance_ids: List[str],
        from_is_finish: str,
        to_is_finish: str,
        oper_cd: str,
    ) -> int:
        """批量更新处理状态。"""
        if not maintenance_ids:
            return 0

        placeholders = ",".join(
            [f":mid_{idx}" for idx, _ in enumerate(maintenance_ids)]
        )
        sql = f"""
            UPDATE TIT10_MAINTENANCE_LIABILITY
               SET IS_FINISH = :to_is_finish,
                   OPERCD = :oper_cd,
                   UPDDATE = SYSDATE
             WHERE MAINTENANCE_ID IN ({placeholders})
               AND IS_FINISH = :from_is_finish
               AND NVL(USEFLG, '1') <> '0'
        """
        params: Dict[str, Any] = {
            "from_is_finish": from_is_finish,
            "to_is_finish": to_is_finish,
            "oper_cd": oper_cd,
        }
        for idx, mid in enumerate(maintenance_ids):
            params[f"mid_{idx}"] = mid

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    affected = cursor.rowcount
                    conn.commit()
                    return int(affected)
        except Exception as exc:
            logger.error("批量更新免责处理状态失败: %s", exc)
            raise

    def list_liability_dictionary(
        self, class_code_like: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """查询免责科目字典（对应 PB 选择科目逻辑）。"""
        where_sql = "A.LIABCD = B.LIABCD AND A.USEFLG = '1' AND B.USEFLG = '1'"
        params: Dict[str, Any] = {}
        if class_code_like:
            where_sql += " AND B.LIABCD LIKE :class_code_like"
            params["class_code_like"] = f"%{class_code_like}%"

        sql = f"""
            SELECT
                B.LIABCD,
                A.LIABNM,
                B.DEFINE
            FROM TIT02_LIABILITYREG A, TIT02_LIABILITYREGDT B
            WHERE {where_sql}
            ORDER BY B.LIABCD
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:
            logger.error("查询免责科目字典失败: %s", exc)
            raise
