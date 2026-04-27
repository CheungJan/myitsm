# -*- coding: utf-8 -*-
"""
旧机翻新计划（ex_gh）仓储。
文件说明：对接 TSL01_EXTEND / TSL02_EXTENDDT，提供列表、详情、明细、新增、送审与作废能力。
作者：Cascade
创建时间：2026-04-20

关联表：
- TSL01_EXTEND：旧机翻新计划主表（sltyp='GH'）
- TSL02_EXTENDDT：旧机翻新计划明细表
- TSL10_SLBILL：销售单主表（作废后回写 planqty）
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class ExGhRepository:
    """旧机翻新计划仓储类。"""

    def list_ex_ghs(
        self,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        custcd: Optional[str] = None,
        auditflg: Optional[str] = None,
        useflg: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询旧机翻新计划列表（对应 d_ex_gh_browse + oe_retrieve）。"""
        where_clauses: List[str] = ["SLTYP = 'GH'"]
        params: Dict[str, Any] = {}

        if begin_date:
            where_clauses.append("TO_CHAR(GENDATE, 'YYYY-MM-DD') >= :begin_date")
            params["begin_date"] = begin_date
        if end_date:
            where_clauses.append("TO_CHAR(GENDATE, 'YYYY-MM-DD') <= :end_date")
            params["end_date"] = end_date
        if custcd:
            where_clauses.append("CUSTCD = :custcd")
            params["custcd"] = custcd
        if auditflg:
            where_clauses.append("AUDITFLG = :auditflg")
            params["auditflg"] = auditflg
        if useflg:
            where_clauses.append("USEFLG = :useflg")
            params["useflg"] = useflg

        where_sql = " AND ".join(where_clauses)

        count_sql = f"SELECT COUNT(*) FROM TSL01_EXTEND WHERE {where_sql}"
        list_sql = f"""
            SELECT
                OPBILLID,
                SLBILLID,
                CUSTCD,
                IMPDATE,
                TRAINDATE,
                BUSITYP,
                SLTYP,
                ITEMCD,
                OPERCD,
                BACKUP,
                GENDATE,
                USEFLG,
                AUDITFLG,
                AUDITMAN,
                AUDITDATE
            FROM TSL01_EXTEND
            WHERE {where_sql}
            ORDER BY OPBILLID DESC, IMPDATE DESC
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
            logger.error("查询旧机翻新计划列表失败: %s", exc)
            raise

    def get_ex_gh(self, opbillid: str) -> Optional[Dict[str, Any]]:
        """查询旧机翻新计划主表详情。"""
        sql = """
            SELECT
                OPBILLID,
                CUSTCD,
                IMPDATE,
                TRAINDATE,
                BUSITYP,
                SLTYP,
                ITEMCD,
                OPERCD,
                BACKUP,
                GENDATE,
                USEFLG,
                AUDITFLG,
                AUDITMAN,
                AUDITDATE,
                SLBILLID
            FROM TSL01_EXTEND
            WHERE OPBILLID = :opbillid
              AND SLTYP = 'GH'
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"opbillid": opbillid})
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as exc:
            logger.error("查询旧机翻新计划详情失败: %s", exc)
            raise

    def list_ex_gh_details(self, opbillid: str) -> List[Dict[str, Any]]:
        """查询旧机翻新计划明细。"""
        sql = """
            SELECT
                OPBILLID,
                CUSTCD,
                PLANQTY,
                OPQTY,
                CLQTY,
                USEFLG,
                IMPDATE,
                TRAINDATE,
                NEWADDRESS,
                NEWCUSTCD,
                EID,
                ADDRESS,
                NEWCUSTCARD,
                CUSTCARD
            FROM TSL02_EXTENDDT
            WHERE OPBILLID = :opbillid
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"opbillid": opbillid})
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:
            logger.error("查询旧机翻新计划明细失败: %s", exc)
            raise

    def create_ex_gh(
        self,
        opbillid: str,
        slbillid: str,
        custcd: str,
        opercd: str,
        busityp: Optional[str] = None,
        itemcd: Optional[str] = None,
        impdate: Optional[str] = None,
        traindate: Optional[str] = None,
        backup: Optional[str] = None,
    ) -> bool:
        """新增旧机翻新计划主表记录。"""
        sql = """
            INSERT INTO TSL01_EXTEND (
                OPBILLID,
                SLBILLID,
                CUSTCD,
                IMPDATE,
                TRAINDATE,
                BUSITYP,
                SLTYP,
                ITEMCD,
                OPERCD,
                BACKUP,
                GENDATE,
                USEFLG,
                AUDITFLG
            ) VALUES (
                :opbillid,
                :slbillid,
                :custcd,
                :impdate,
                :traindate,
                :busityp,
                'GH',
                :itemcd,
                :opercd,
                :backup,
                SYSDATE,
                '1',
                '0'
            )
        """
        params: Dict[str, Any] = {
            "opbillid": opbillid,
            "slbillid": slbillid,
            "custcd": custcd,
            "impdate": impdate,
            "traindate": traindate,
            "busityp": busityp,
            "itemcd": itemcd,
            "opercd": opercd,
            "backup": backup,
        }
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
        except Exception as exc:
            logger.error("新增旧机翻新计划失败: %s", exc)
            raise

    def create_ex_gh_detail(
        self,
        opbillid: str,
        custcd: str,
        planqty: int,
        opercd: str,
        opqty: int = 0,
        clqty: int = 0,
        useflg: str = "0",
        impdate: Optional[str] = None,
        traindate: Optional[str] = None,
        newaddress: Optional[str] = None,
        newcustcd: Optional[str] = None,
        eid: Optional[str] = None,
        address: Optional[str] = None,
        newcustcard: Optional[str] = None,
        custcard: Optional[str] = None,
    ) -> bool:
        """新增旧机翻新计划明细记录。"""
        sql = """
            INSERT INTO TSL02_EXTENDDT (
                OPBILLID,
                CUSTCD,
                PLANQTY,
                OPQTY,
                CLQTY,
                USEFLG,
                IMPDATE,
                TRAINDATE,
                NEWADDRESS,
                NEWCUSTCD,
                EID,
                ADDRESS,
                NEWCUSTCARD,
                CUSTCARD
            ) VALUES (
                :opbillid,
                :custcd,
                :planqty,
                :opqty,
                :clqty,
                :useflg,
                TO_DATE(:impdate, 'YYYY-MM-DD HH24:MI:SS'),
                TO_DATE(:traindate, 'YYYY-MM-DD HH24:MI:SS'),
                :newaddress,
                :newcustcd,
                :eid,
                :address,
                :newcustcard,
                :custcard
            )
        """
        params = {
            "opbillid": opbillid,
            "custcd": custcd,
            "planqty": planqty,
            "opqty": opqty,
            "clqty": clqty,
            "useflg": useflg,
            "impdate": impdate,
            "traindate": traindate,
            "newaddress": newaddress,
            "newcustcd": newcustcd,
            "eid": eid,
            "address": address,
            "newcustcard": newcustcard,
            "custcard": custcard,
            "opercd": opercd,
        }
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
        except Exception as exc:
            logger.error("新增旧机翻新计划明细失败: %s", exc)
            raise

    def submit_audit(self, opbillids: List[str], opercd: str) -> int:
        """批量送审：auditflg 0->1。"""
        if not opbillids:
            return 0

        placeholders = ",".join([f":opbillid_{idx}" for idx, _ in enumerate(opbillids)])
        sql = f"""
            UPDATE TSL01_EXTEND
            SET AUDITFLG = '1',
                OPERCD = :opercd,
                AUDITDATE = SYSDATE,
                AUDITMAN = :opercd
            WHERE OPBILLID IN ({placeholders})
              AND SLTYP = 'GH'
              AND AUDITFLG = '0'
              AND NVL(USEFLG, '1') = '1'
        """
        params: Dict[str, Any] = {"opercd": opercd}
        for idx, opbillid in enumerate(opbillids):
            params[f"opbillid_{idx}"] = opbillid

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    affected = int(cursor.rowcount)
                    conn.commit()
                    return affected
        except Exception as exc:
            logger.error("批量送审旧机翻新计划失败: %s", exc)
            raise

    def invalidate_ex_gh(self, opbillid: str, slbillid: str) -> bool:
        """作废旧机翻新计划，并回写销售单 planqty。"""
        invalid_sql = """
            UPDATE TSL01_EXTEND
            SET USEFLG = '9'
            WHERE OPBILLID = :opbillid
              AND SLTYP = 'GH'
              AND NVL(USEFLG, '1') <> '9'
        """
        planqty_sql = """
            SELECT NVL(SUM(PLANQTY), 0)
            FROM TSL02_EXTENDDT
            WHERE OPBILLID = :opbillid
        """
        rollback_planqty_sql = """
            UPDATE TSL10_SLBILL
            SET PLANQTY = NVL(PLANQTY, 0) - :planqty
            WHERE SLBILLID = :slbillid
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(invalid_sql, {"opbillid": opbillid})
                    if cursor.rowcount <= 0:
                        conn.rollback()
                        return False

                    cursor.execute(planqty_sql, {"opbillid": opbillid})
                    planqty = int(cursor.fetchone()[0])

                    cursor.execute(
                        rollback_planqty_sql,
                        {
                            "planqty": planqty,
                            "slbillid": slbillid,
                        },
                    )
                    conn.commit()
                    return True
        except Exception as exc:
            logger.error("作废旧机翻新计划失败: %s", exc)
            raise
