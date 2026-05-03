# -*- coding: utf-8 -*-
"""
日常维护年月汇总报表仓储。
文件说明：实现 d_itsm_maintenance_plan_ym_report DataWindow 对应的年月汇总报表。
来源：itsm02.pbl / u_itsm_rep_maintenance_daily_ym / d_itsm_maintenance_plan_ym_report.srd
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.extensions.db import get_connection

logger = logging.getLogger(__name__)

_SQL = """
SELECT a.area,
       a.plan_qty,
       b.count_sum
  FROM (
        SELECT p.area_id AS area,
               p.plan_qty
          FROM tit17_maintenance_plan p
         WHERE plan_yymm = :in_ym
       ) a,
       (
        SELECT c.area         AS area,
               COUNT(*)       AS count_sum
          FROM tit17_maintenance m,
               tmm22_customers c
         WHERE m.current_status = '3'
           AND m.store_id = c.custcd
           AND m.close_time > TO_DATE(:in_ym, 'YYYYMM')
           AND m.close_time < LAST_DAY(TO_DATE(:in_ym, 'YYYYMM')) + 1
         GROUP BY c.area
       ) b
 WHERE a.area = b.area(+)
 ORDER BY a.area
"""


class RepMaintenanceDailyYmRepository:
    """日常维护年月汇总报表仓储类。"""

    def list_reports(
        self,
        in_ym: str,
    ) -> Dict[str, Any]:
        """按年月(YYYYMM)查询日常维护汇总报表。"""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(_SQL, {"in_ym": in_ym})
            cols = [d[0].lower() for d in cur.description]
            items = [dict(zip(cols, row)) for row in cur.fetchall()]

        return {"items": items, "total": len(items)}
