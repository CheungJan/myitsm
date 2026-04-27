# -*- coding: utf-8 -*-
"""
日常维护月度汇总报表仓储。
文件说明：实现 d_itsm_maintenance_plan_report DataWindow 对应的日常维护月度汇总。
来源：itsm02.pbl / u_itsm_rep_maintenance_daily_m / d_itsm_maintenance_plan_report.srd
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
       a.store_sum,
       a.store_sum1,
       a.count_sum,
       a.store_sum0,
       b.double_count
  FROM (
        SELECT area,
               SUM(store_sum)  AS store_sum,
               SUM(store_sum1) AS store_sum1,
               SUM(store_sum0) AS store_sum0,
               SUM(count_sum)  AS count_sum
          FROM v_itsm_md_sum
         WHERE NVL(close_date, :start_date) >= :start_date
           AND NVL(close_date, :end_date)   <= :end_date + 1
         GROUP BY area
       ) a,
       (
        SELECT MAX(v.area)         AS area,
               SUM(v.count_sum) - 1 AS double_count
          FROM v_itsm_md_sum v
         WHERE NVL(close_date, :start_date) >= :start_date
           AND NVL(close_date, :end_date)   <= :end_date + 1
         GROUP BY v.store_id
        HAVING SUM(v.count_sum) > 1
       ) b
 WHERE a.area = b.area(+)
 ORDER BY a.area
"""


class RepMaintenanceDailyMRepository:
    """日常维护月度汇总报表仓储类。"""

    def list_reports(
        self,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """按日期区间查询日常维护月度汇总报表。"""
        params = {
            "start_date": start_date,
            "end_date": end_date,
        }
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(_SQL, params)
            cols = [d[0].lower() for d in cur.description]
            items = [dict(zip(cols, row)) for row in cur.fetchall()]

        return {"items": items, "total": len(items)}
