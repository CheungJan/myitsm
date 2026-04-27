# -*- coding: utf-8 -*-
"""
资产作废审核仓储。
文件说明：对接 TWH19_ASSET_C_A / TWH20_ASSET_C_A_DTL，提供待审核列表、明细、审批与作废能力。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class AssetAuditRepository:
    """资产作废审核仓储类。"""

    def __init__(self) -> None:
        self.main_table = "TWH19_ASSET_C_A"
        self.detail_table = "TWH20_ASSET_C_A_DTL"

    def list_pending_audits(
        self,
        opbillid: Optional[str] = None,
        custcd: Optional[str] = None,
        custcard: Optional[str] = None,
        sltyp: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询待审核作废单（auditflg=1）。"""
        where_clauses = ["A.USEFLG <> '9'", "A.AUDITFLG = '1'"]
        params: Dict[str, Any] = {}

        if opbillid:
            where_clauses.append("A.OPBILLID LIKE :opbillid")
            params["opbillid"] = f"%{opbillid}%"
        if custcd:
            where_clauses.append("A.CUSTCD LIKE :custcd")
            params["custcd"] = f"%{custcd}%"
        if custcard:
            where_clauses.append("C.CUSTCARD LIKE :custcard")
            params["custcard"] = f"%{custcard}%"
        if sltyp:
            where_clauses.append("A.SLTYP = :sltyp")
            params["sltyp"] = sltyp

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM {self.main_table} A
            LEFT JOIN TMM22_CUSTOMERS C ON C.CUSTCD = A.CUSTCD
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT
                A.OPBILLID,
                A.SLBILLID,
                A.CUSTCD,
                C.CUSTCARD,
                A.IMPDATE,
                A.TRAINDATE,
                A.BUSITYP,
                A.SLTYP,
                A.ITEMCD,
                A.OPERCD,
                A.BACKUP,
                A.GENDATE,
                A.USEFLG,
                A.AUDITFLG,
                A.AUDITMAN,
                A.AUDITDATE
            FROM {self.main_table} A
            LEFT JOIN TMM22_CUSTOMERS C ON C.CUSTCD = A.CUSTCD
            WHERE {where_sql}
            ORDER BY A.GENDATE DESC, A.OPBILLID DESC
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
            logger.error("查询资产作废待审核列表失败: %s", exc)
            raise

    def list_audit_details(
        self,
        opbillid: str,
        custcd_like: str = "%",
    ) -> list[Dict[str, Any]]:
        """查询作废单明细。"""
        sql = f"""
            SELECT
                D.OPBILLID,
                D.CUSTCARD,
                D.CUSTCD,
                C.CUSTNM,
                D.EID,
                E.ITEMCD,
                I.ITEMNM,
                D.PLANQTY,
                D.OPQTY,
                D.CLQTY,
                D.USEFLG,
                D.IMPDATE,
                D.TRAINDATE,
                D.NEWADDRESS,
                D.NEWCUSTCARD,
                D.NEWCUSTCD,
                D.ADDRESS
            FROM {self.detail_table} D
            JOIN TMM43_EID E ON E.EID = D.EID
            JOIN TMM12_ITEMS I ON I.ITEMCD = E.ITEMCD
            JOIN TMM22_CUSTOMERS C ON C.CUSTCD = D.CUSTCD
            WHERE D.OPBILLID = :opbillid
              AND D.CUSTCD LIKE :custcd_like
            ORDER BY D.EID
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "opbillid": opbillid,
                            "custcd_like": custcd_like,
                        },
                    )
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:
            logger.error("查询资产作废单明细失败: %s", exc)
            raise

    def approve_audit(self, opbillid: str, custcd: str, opercd: str) -> bool:
        """审批作废单并调用库存处理过程。"""
        update_sql = f"""
            UPDATE {self.main_table}
            SET AUDITFLG = '2',
                AUDITMAN = :opercd,
                AUDITDATE = SYSDATE
            WHERE OPBILLID = :opbillid
              AND AUDITFLG = '1'
              AND USEFLG <> '9'
        """

        proc_sql = "BEGIN usp_asset_c_a(:opbillid, :custcd, :opercd); END;"

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        update_sql,
                        {"opbillid": opbillid, "opercd": opercd},
                    )
                    if cursor.rowcount <= 0:
                        conn.rollback()
                        return False

                    cursor.execute(
                        proc_sql,
                        {
                            "opbillid": opbillid,
                            "custcd": custcd,
                            "opercd": opercd,
                        },
                    )
                    conn.commit()
                    return True
        except Exception as exc:
            logger.error("审批资产作废单失败: %s", exc)
            raise

    def invalidate_audit(self, opbillid: str, opercd: str) -> bool:
        """作废作废单（PB按钮语义）。"""
        sql = f"""
            UPDATE {self.main_table}
            SET USEFLG = '9',
                AUDITMAN = :opercd,
                AUDITDATE = SYSDATE
            WHERE OPBILLID = :opbillid
              AND USEFLG <> '9'
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"opbillid": opbillid, "opercd": opercd})
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as exc:
            logger.error("作废资产作废单失败: %s", exc)
            raise
