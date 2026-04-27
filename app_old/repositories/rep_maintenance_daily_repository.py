# -*- coding: utf-8 -*-
"""
日常保养报表仓储。
文件说明：实现 d_itsm_maintenance_daily_report DataWindow 对应的日常保养单报表查询。
来源：itsm02.pbl / u_itsm_rep_maintenance_daily / d_itsm_maintenance_daily_report.srd
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.extensions.db import get_connection

logger = logging.getLogger(__name__)

_BASE_SQL = """
SELECT m.daily_maintenance_id AS maintenance_id,
       MAX(c.classcd)              AS classcd,
       MAX(c.custcd)               AS store_id,
       MAX(c.custcard)             AS custcard,
       MAX(c.custnm)               AS custnm,
       MAX(c.phoneno)              AS phoneno,
       MAX(c.address)              AS address,
       MAX(m.create_time)          AS create_time,
       MAX(m.create_date)          AS create_date,
       MAX(m.creator)              AS creator,
       MAX(m.request_enginner_id)  AS request_enginner_id,
       MAX(m.current_status)       AS current_status,
       MAX(m.short_description)    AS short_description,
       MAX(m.detail_description)   AS detail_description,
       MAX(m.updator)              AS updator,
       MAX(m.update_time)          AS update_time,
       MAX(p.itemcd)               AS itemcd
  FROM tit17_maintenance m,
       tmm22_customers c,
       tit17_cust_pos_daily p
 WHERE m.store_id = c.custcd
   AND m.daily_maintenance_id = p.daily_maintenance_id(+)
   AND 1=1
 GROUP BY m.daily_maintenance_id
 ORDER BY m.daily_maintenance_id
"""


class RepMaintenanceDailyRepository:
    """日常保养报表仓储类。"""

    def list_reports(
        self,
        start_date: str,
        end_date: str,
        custcard: Optional[str] = None,
        classcd: Optional[str] = None,
        engineer_id: Optional[str] = None,
        current_status: Optional[str] = None,
        itemcd: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """查询日常保养报表。"""
        where_parts: List[str] = []
        params: Dict[str, Any] = {}

        where_parts.append("m.create_time >= TO_DATE(:start_date,'YYYY-MM-DD')")
        where_parts.append("m.create_time < TO_DATE(:end_date,'YYYY-MM-DD') + 1")
        params["start_date"] = start_date
        params["end_date"] = end_date

        if custcard and custcard.strip():
            where_parts.append("c.custcard LIKE :custcard")
            params["custcard"] = f"%{custcard.strip()}%"
        if classcd and classcd.strip():
            where_parts.append("c.classcd LIKE :classcd")
            params["classcd"] = f"%{classcd.strip()}%"
        if engineer_id and engineer_id.strip():
            where_parts.append("m.request_enginner_id = :engineer_id")
            params["engineer_id"] = engineer_id.strip()
        if current_status and current_status.strip():
            where_parts.append("m.current_status = :current_status")
            params["current_status"] = current_status.strip()
        if itemcd and itemcd.strip():
            where_parts.append("p.itemcd = :itemcd")
            params["itemcd"] = itemcd.strip()

        extra = " AND ".join(where_parts)
        data_sql = _BASE_SQL.replace("AND 1=1", "AND " + extra)

        count_sql = f"SELECT COUNT(*) AS cnt FROM ({data_sql.rstrip()}) q"
        offset = (page - 1) * page_size
        paged_sql = (
            f"SELECT * FROM (SELECT q.*, ROWNUM rn FROM ({data_sql}) q WHERE ROWNUM <= :_end) "
            f"WHERE rn > :_offset"
        )
        params["_end"] = offset + page_size
        params["_offset"] = offset

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                count_sql, {k: v for k, v in params.items() if not k.startswith("_")}
            )
            total = (cur.fetchone() or [0])[0]

            cur.execute(paged_sql, params)
            cols = [d[0].lower() for d in cur.description]
            items = [dict(zip(cols, row)) for row in cur.fetchall()]

        return {"items": items, "total": total, "page": page, "page_size": page_size}
