# -*- coding: utf-8 -*-
"""
保养计划仓储。
文件说明：对接 TIT17_MAINTENANCE_PLAN，提供列表、增删改与按年生成功能。
作者：Cascade
创建时间：2026-04-20

关联表：
- TIT17_MAINTENANCE_PLAN：保养计划表
- TMM46_AREA：区域字典（按年生成计划时使用）
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.extensions import get_oracle_connection

logger = logging.getLogger(__name__)


class MaintenancePlanRepository:
    """保养计划仓储类。"""

    def list_plans(
        self,
        plan_yymm: Optional[str] = None,
        page: int = 1,
        page_size: int = 200,
    ) -> Dict[str, Any]:
        """分页查询保养计划。"""
        where_clauses: List[str] = ["1 = 1"]
        params: Dict[str, Any] = {}

        if plan_yymm:
            where_clauses.append("PLAN_YYMM = :plan_yymm")
            params["plan_yymm"] = plan_yymm

        where_sql = " AND ".join(where_clauses)

        count_sql = f"SELECT COUNT(*) FROM TIT17_MAINTENANCE_PLAN WHERE {where_sql}"
        list_sql = f"""
            SELECT
                PLAN_Y,
                PLAN_YYMM,
                AREA_ID,
                PLAN_QTY,
                CREATE_TIME,
                CREATOR
            FROM TIT17_MAINTENANCE_PLAN
            WHERE {where_sql}
            ORDER BY PLAN_YYMM, AREA_ID
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
            logger.error("查询保养计划列表失败: %s", exc)
            raise

    def get_plan(self, plan_yymm: str, area_id: int) -> Optional[Dict[str, Any]]:
        """查询单条保养计划。"""
        sql = """
            SELECT
                PLAN_Y,
                PLAN_YYMM,
                AREA_ID,
                PLAN_QTY,
                CREATE_TIME,
                CREATOR
            FROM TIT17_MAINTENANCE_PLAN
            WHERE PLAN_YYMM = :plan_yymm
              AND AREA_ID = :area_id
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"plan_yymm": plan_yymm, "area_id": area_id})
                    row = cursor.fetchone()
                    if not row:
                        return None
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
        except Exception as exc:
            logger.error("查询保养计划详情失败: %s", exc)
            raise

    def create_plan(
        self, plan_yymm: str, area_id: int, plan_qty: int, creator: str
    ) -> bool:
        """新增保养计划。"""
        sql = """
            INSERT INTO TIT17_MAINTENANCE_PLAN (
                PLAN_Y,
                PLAN_YYMM,
                AREA_ID,
                PLAN_QTY,
                CREATE_TIME,
                CREATOR
            ) VALUES (
                SUBSTR(:plan_yymm, 1, 4),
                :plan_yymm,
                :area_id,
                :plan_qty,
                SYSDATE,
                :creator
            )
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "plan_yymm": plan_yymm,
                            "area_id": area_id,
                            "plan_qty": plan_qty,
                            "creator": creator,
                        },
                    )
                    conn.commit()
                    return True
        except Exception as exc:
            logger.error("新增保养计划失败: %s", exc)
            raise

    def update_plan_qty(self, plan_yymm: str, area_id: int, plan_qty: int) -> bool:
        """更新保养计划数量。"""
        sql = """
            UPDATE TIT17_MAINTENANCE_PLAN
            SET PLAN_QTY = :plan_qty
            WHERE PLAN_YYMM = :plan_yymm
              AND AREA_ID = :area_id
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "plan_qty": plan_qty,
                            "plan_yymm": plan_yymm,
                            "area_id": area_id,
                        },
                    )
                    affected = cursor.rowcount
                    conn.commit()
                    return int(affected) > 0
        except Exception as exc:
            logger.error("更新保养计划失败: %s", exc)
            raise

    def delete_plan(self, plan_yymm: str, area_id: int) -> bool:
        """删除保养计划。"""
        sql = """
            DELETE FROM TIT17_MAINTENANCE_PLAN
            WHERE PLAN_YYMM = :plan_yymm
              AND AREA_ID = :area_id
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"plan_yymm": plan_yymm, "area_id": area_id})
                    affected = cursor.rowcount
                    conn.commit()
                    return int(affected) > 0
        except Exception as exc:
            logger.error("删除保养计划失败: %s", exc)
            raise

    def exists_by_yymm(self, plan_yymm: str) -> bool:
        """判断指定年月是否已有计划。"""
        sql = """
            SELECT 1
            FROM TIT17_MAINTENANCE_PLAN
            WHERE PLAN_YYMM = :plan_yymm
              AND ROWNUM = 1
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, {"plan_yymm": plan_yymm})
                    return cursor.fetchone() is not None
        except Exception as exc:
            logger.error("查询保养计划年月是否存在失败: %s", exc)
            raise

    def generate_month_plans(self, plan_y: str, plan_yymm: str, creator: str) -> int:
        """按单月生成计划（从区域表初始化，已存在则不生成）。"""
        sql = """
            INSERT INTO TIT17_MAINTENANCE_PLAN (
                PLAN_Y,
                PLAN_YYMM,
                AREA_ID,
                PLAN_QTY,
                CREATE_TIME,
                CREATOR
            )
            SELECT
                :plan_y,
                :plan_yymm,
                ID,
                0,
                SYSDATE,
                :creator
            FROM TMM46_AREA A
            WHERE NOT EXISTS (
                SELECT 1
                FROM TIT17_MAINTENANCE_PLAN P
                WHERE P.PLAN_YYMM = :plan_yymm
                  AND P.AREA_ID = A.ID
            )
        """
        try:
            with get_oracle_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql,
                        {
                            "plan_y": plan_y,
                            "plan_yymm": plan_yymm,
                            "creator": creator,
                        },
                    )
                    affected = int(cursor.rowcount)
                    conn.commit()
                    return affected
        except Exception as exc:
            logger.error("生成保养计划失败: %s", exc)
            raise
