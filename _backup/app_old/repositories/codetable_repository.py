# -*- coding: utf-8 -*-
"""
代码表仓储。
文件说明：对接 TIT03_SYSCODES，提供代码项列表、详情、保存与作废能力。
作者：Cascade
创建时间：2026-04-20

关联表：
- TIT03_SYSCODES：系统代码表
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class CodeTableRepository:
    """代码表仓储类。"""

    def __init__(self) -> None:
        self.table = "TIT03_SYSCODES"

    def list_codes(
        self,
        codetyp: str,
        include_invalid: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """按代码类别分页查询代码项。"""
        where_clauses = ["CODETYP = :codetyp"]
        params: Dict[str, Any] = {"codetyp": codetyp}

        if not include_invalid:
            where_clauses.append("NVL(USEFLG, '1') = '1'")

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM {self.table}
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT
                CODETYP,
                CODECD,
                CODENM,
                MEMO,
                SYSFLG,
                OPERCD,
                GENDATE,
                UPDDATE,
                USEFLG,
                WHTRANSFLG,
                STTRANSFLG
            FROM {self.table}
            WHERE {where_sql}
            ORDER BY CODECD
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
            logger.error("查询代码项失败: %s", exc)
            raise

    def get_code(self, codetyp: str, codecd: str) -> Optional[Dict[str, Any]]:
        """查询单个代码项。"""
        sql = f"""
            SELECT
                CODETYP,
                CODECD,
                CODENM,
                SYSFLG,
                OPERCD,
                GENDATE,
                UPDDATE,
                USEFLG,
                WHTRANSFLG,
                STTRANSFLG
            FROM {self.table}
            WHERE CODETYP = :codetyp
              AND CODECD = :codecd
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"codetyp": codetyp, "codecd": codecd})
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as exc:
            logger.error("查询代码项详情失败: %s", exc)
            raise

    def save_code(
        self,
        codetyp: str,
        codecd: str,
        codenm: str,
        opercd: str,
        useflg: str = "1",
        memo: Optional[str] = None,
    ) -> bool:
        """保存代码项（存在则更新，不存在则新增）。"""
        merge_sql = f"""
            MERGE INTO {self.table} T
            USING (
                SELECT :codetyp AS CODETYP, :codecd AS CODECD FROM DUAL
            ) S
            ON (T.CODETYP = S.CODETYP AND T.CODECD = S.CODECD)
            WHEN MATCHED THEN
                UPDATE SET
                    T.CODENM = :codenm,
                    T.MEMO = :memo,
                    T.OPERCD = :opercd,
                    T.UPDDATE = SYSDATE,
                    T.USEFLG = :useflg
            WHEN NOT MATCHED THEN
                INSERT (
                    CODETYP,
                    CODECD,
                    CODENM,
                    MEMO,
                    SYSFLG,
                    OPERCD,
                    GENDATE,
                    UPDDATE,
                    USEFLG
                ) VALUES (
                    :codetyp,
                    :codecd,
                    :codenm,
                    :memo,
                    'N',
                    :opercd,
                    SYSDATE,
                    SYSDATE,
                    :useflg
                )
        """
        params = {
            "codetyp": codetyp,
            "codecd": codecd,
            "codenm": codenm,
            "memo": memo,
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
            logger.error("保存代码项失败: %s", exc)
            raise

    def invalidate_code(self, codetyp: str, codecd: str, opercd: str) -> bool:
        """作废代码项（仅允许非系统代码）。"""
        check_sql = f"""
            SELECT SYSFLG
            FROM {self.table}
            WHERE CODETYP = :codetyp
              AND CODECD = :codecd
        """

        update_sql = f"""
            UPDATE {self.table}
            SET USEFLG = '0',
                OPERCD = :opercd,
                UPDDATE = SYSDATE
            WHERE CODETYP = :codetyp
              AND CODECD = :codecd
              AND NVL(SYSFLG, 'N') <> 'Y'
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(check_sql, {"codetyp": codetyp, "codecd": codecd})
                    row = cursor.fetchone()
                    if not row:
                        return False
                    if str(row[0] or "N") == "Y":
                        raise ValueError("系统定义的数据不允许删除")

                    cursor.execute(
                        update_sql,
                        {
                            "codetyp": codetyp,
                            "codecd": codecd,
                            "opercd": opercd,
                        },
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as exc:
            logger.error("作废代码项失败: %s", exc)
            raise
