# -*- coding: utf-8 -*-
"""
免费更换配置更新仓储。
文件说明：对接 TIT28_FREE_REPLACE_DT、TIT19_ON_CHOOSEDT、TMM44_POS_R_EID，
提供列表查询、旧新配件查询与确认更新能力。
作者：Cascade
创建时间：2026-04-20

关联表：
- TIT28_FREE_REPLACE_DT：免费更换设备明细
- TIT19_ON_CHOOSEDT：旧新配件选取明细
- TMM44_POS_R_EID：设备配置关系
- TMM12_ITEMS：物料字典
- TMM22_CUSTOMERS：客户主数据（磁卡号反查门店）
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class PosREidUpdateRepository:
    """免费更换配置更新仓储类。"""

    def list_updates(
        self,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        custcard: Optional[str] = None,
        renew_id: Optional[str] = None,
        is_finish: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询配置更新待确认列表。"""
        where_clauses: List[str] = ["T.IS_FINISH <> '0'"]
        params: Dict[str, Any] = {}

        if custcard:
            where_clauses.append(
                "(SELECT C.CUSTCARD FROM TMM22_CUSTOMERS C "
                " WHERE C.CUSTCD = (SELECT D.STORE_ID FROM TIT28_FREE_REPLACE D"
                " WHERE D.RENEW_ID = T.RENOVATE_ID)) LIKE :custcard"
            )
            params["custcard"] = f"%{custcard}%"
        if renew_id:
            where_clauses.append("T.RENOVATE_ID LIKE :renew_id")
            params["renew_id"] = f"%{renew_id}%"
        if begin_date:
            where_clauses.append("TO_CHAR(T.CREATE_TIME,'YYYY-MM-DD') >= :begin_date")
            params["begin_date"] = begin_date
        if end_date:
            where_clauses.append("TO_CHAR(T.CREATE_TIME,'YYYY-MM-DD') <= :end_date")
            params["end_date"] = end_date
        if is_finish:
            where_clauses.append("T.IS_FINISH LIKE :is_finish")
            params["is_finish"] = is_finish

        where_sql = " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM TIT28_FREE_REPLACE_DT T
            WHERE {where_sql}
        """

        list_sql = f"""
            SELECT
                T.RENOVATE_ID,
                T.BUSINESS_OPERATION_ID,
                (SELECT C.CUSTCARD FROM TMM22_CUSTOMERS C WHERE C.CUSTCD =
                    (SELECT D.STORE_ID FROM TIT28_FREE_REPLACE D WHERE D.RENEW_ID = T.RENOVATE_ID)
                ) AS CUSTCARD,
                (SELECT C.CUSTNM FROM TMM22_CUSTOMERS C WHERE C.CUSTCD =
                    (SELECT D.STORE_ID FROM TIT28_FREE_REPLACE D WHERE D.RENEW_ID = T.RENOVATE_ID)
                ) AS CUSTNM,
                T.DEVICE_ID,
                (SELECT E.ITEMCD FROM TMM43_EID E WHERE E.EID = T.DEVICE_ID) AS ITEMCD,
                T.DELIVERYID,
                T.NEW_DEVICE_ID,
                (SELECT E.ITEMCD FROM TMM43_EID E WHERE E.EID = T.NEW_DEVICE_ID) AS NEW_ITEMCD,
                T.CREATE_TIME,
                T.CREATOR,
                T.UPDATE_TIME,
                T.UPDATOR,
                T.IS_FINISH
            FROM TIT28_FREE_REPLACE_DT T
            WHERE {where_sql}
            ORDER BY T.IS_FINISH, T.RENOVATE_ID
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
            logger.error("查询配置更新列表失败: %s", exc)
            raise

    def get_update(
        self, renew_id: str, business_operation_id: int
    ) -> Optional[Dict[str, Any]]:
        """按主键查询配置更新记录。"""
        sql = """
            SELECT
                RENOVATE_ID,
                BUSINESS_OPERATION_ID,
                DEVICE_ID,
                NEW_DEVICE_ID,
                DELIVERYID,
                IS_FINISH,
                CREATE_TIME,
                CREATOR,
                UPDATE_TIME,
                UPDATOR
            FROM TIT28_FREE_REPLACE_DT
            WHERE RENOVATE_ID = :renew_id
              AND BUSINESS_OPERATION_ID = :business_operation_id
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "renew_id": renew_id,
                            "business_operation_id": business_operation_id,
                        },
                    )
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as exc:
            logger.error("查询配置更新记录失败: %s", exc)
            raise

    def get_custcd_by_custcard(self, custcard: str) -> Optional[str]:
        """通过磁卡号反查门店代码。"""
        sql = """
            SELECT CUSTCD
            FROM TMM22_CUSTOMERS
            WHERE CUSTCARD = :custcard
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"custcard": custcard})
                    row = cursor.fetchone()
                    return str(row[0]) if row and row[0] else None
        except Exception as exc:
            logger.error("反查门店代码失败: %s", exc)
            raise

    def list_old_choices(
        self, bill_id: str, business_id: int, device_id: str
    ) -> List[Dict[str, Any]]:
        """查询旧设备选取明细。"""
        sql = """
            SELECT
                T.BILL_ID,
                T.BUSINESS_ID,
                T.OLDFLG,
                T.DEVICE_ID,
                T.ITEMCD,
                T.ACCESSORIES_ID,
                M.ITEMNM,
                T.CHOOSEFLG,
                T.CREATE_TIME,
                T.CREATOR
            FROM TIT19_ON_CHOOSEDT T, TMM12_ITEMS M
            WHERE T.ITEMCD = M.ITEMCD
              AND T.OLDFLG = 'O'
              AND T.BILL_ID = :bill_id
              AND T.BUSINESS_ID = :business_id
              AND T.DEVICE_ID = :device_id
            ORDER BY T.ITEMCD, T.ACCESSORIES_ID
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "bill_id": bill_id,
                            "business_id": business_id,
                            "device_id": device_id,
                        },
                    )
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:
            logger.error("查询旧设备选取明细失败: %s", exc)
            raise

    def list_new_choices(
        self, bill_id: str, business_id: int, device_id: str
    ) -> List[Dict[str, Any]]:
        """查询新设备选取明细。"""
        sql = """
            SELECT
                T.BILL_ID,
                T.BUSINESS_ID,
                T.OLDFLG,
                T.DEVICE_ID,
                T.ITEMCD,
                T.ACCESSORIES_ID,
                M.ITEMNM,
                T.CHOOSEFLG,
                T.CREATE_TIME,
                T.CREATOR
            FROM TIT19_ON_CHOOSEDT T, TMM12_ITEMS M
            WHERE T.ITEMCD = M.ITEMCD
              AND T.OLDFLG = 'N'
              AND T.BILL_ID = :bill_id
              AND T.BUSINESS_ID = :business_id
              AND T.DEVICE_ID = :device_id
            ORDER BY T.ITEMCD, T.ACCESSORIES_ID
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "bill_id": bill_id,
                            "business_id": business_id,
                            "device_id": device_id,
                        },
                    )
                    rows = cursor.fetchall()
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:
            logger.error("查询新设备选取明细失败: %s", exc)
            raise

    def confirm_update(
        self,
        renew_id: str,
        business_operation_id: int,
        old_eid: str,
        new_eid: str,
        oper_cd: str,
    ) -> Dict[str, Any]:
        """确认配置更新并回写明细状态。"""
        selected_sql = """
            SELECT ITEMCD, ACCESSORIES_ID
            FROM TIT19_ON_CHOOSEDT
            WHERE BILL_ID = :renew_id
              AND BUSINESS_ID = :business_operation_id
              AND OLDFLG = 'O'
              AND DEVICE_ID = :old_eid
              AND CHOOSEFLG = '1'
        """
        exists_sql = """
            SELECT 1
            FROM TMM44_POS_R_EID
            WHERE POSID = :new_eid
              AND ITEMCD = :itemcd
              AND EID = :accessories_id
        """
        update_pos_sql = """
            UPDATE TMM44_POS_R_EID
            SET POSID = :new_eid
            WHERE POSID = :old_eid
              AND ITEMCD = :itemcd
              AND EID = :accessories_id
        """
        update_finish_sql = """
            UPDATE TIT28_FREE_REPLACE_DT
            SET IS_FINISH = '2',
                UPDATE_TIME = SYSDATE,
                UPDATOR = :oper_cd
            WHERE RENOVATE_ID = :renew_id
              AND BUSINESS_OPERATION_ID = :business_operation_id
        """

        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        selected_sql,
                        {
                            "renew_id": renew_id,
                            "business_operation_id": business_operation_id,
                            "old_eid": old_eid,
                        },
                    )
                    selected_rows = cursor.fetchall()
                    if not selected_rows:
                        return {
                            "updated_count": 0,
                            "message": "未选择任何旧设备配件",
                        }

                    updated_count = 0
                    for itemcd, accessories_id in selected_rows:
                        cursor.execute(
                            exists_sql,
                            {
                                "new_eid": new_eid,
                                "itemcd": itemcd,
                                "accessories_id": accessories_id,
                            },
                        )
                        if cursor.fetchone():
                            conn.rollback()
                            raise ValueError(f"新设备配置中已经存在设备{itemcd}")

                        cursor.execute(
                            update_pos_sql,
                            {
                                "new_eid": new_eid,
                                "old_eid": old_eid,
                                "itemcd": itemcd,
                                "accessories_id": accessories_id,
                            },
                        )
                        updated_count += int(cursor.rowcount)

                    cursor.execute(
                        update_finish_sql,
                        {
                            "oper_cd": oper_cd,
                            "renew_id": renew_id,
                            "business_operation_id": business_operation_id,
                        },
                    )

                    conn.commit()
                    return {
                        "updated_count": updated_count,
                        "detail_confirmed": int(cursor.rowcount),
                        "message": "配置确认成功",
                    }
        except Exception as exc:
            logger.error("确认配置更新失败: %s", exc)
            raise
