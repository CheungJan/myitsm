# -*- coding: utf-8 -*-
"""
客户信息报表仓储。
文件说明：实现 d_cust_info DataWindow 对应的客户基本信息报表查询。
来源：itsm02.pbl / u_itsm_rep_cust_info / d_cust_info.srd
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.extensions.db import get_connection

logger = logging.getLogger(__name__)

_BASE_SQL = """
SELECT t.custcd,
       t.custcard,
       c.classnm,
       t.custnm,
       t.address,
       t.phoneno,
       CASE WHEN t.busityp = 'ZS' THEN '直属' ELSE '延伸' END AS busityp,
       N.eid,
       N.itemcd,
       a.name AS areanm,
       t.location,
       t.opersystem,
       t.data_base,
       t.opendate,
       t.pptcode,
       t.zftype,
       t.jl_contactor,
       t.jl_phoneno,
       t.useflg,
       t.commmode,
       t.card3g,
       t.systemcode,
       t.replacedate,
       t.posstatus,
       t.posstatus1
  FROM tmm21_custclass c,
       tmm22_customers t,
       tmm46_area a,
       (SELECT p.custcd AS custcd,
               MAX(p.itemcd) AS itemcd,
               MAX(p.eid) AS eid
          FROM tmm35_cust_pos_rl p
         WHERE p.useflg = '1'
         GROUP BY p.custcd) n
 WHERE n.custcd(+) = t.custcd
   AND t.classcd = c.classcd
   AND t.area = a.id
   AND 1=1
"""


class RepCustInfoRepository:
    """客户信息报表仓储类。"""

    def list_reports(
        self,
        custcard: Optional[str] = None,
        classcd: Optional[str] = None,
        custnm: Optional[str] = None,
        busityp: Optional[str] = None,
        useflg: Optional[str] = None,
        opendate_from: Optional[str] = None,
        opendate_to: Optional[str] = None,
        pptcode: Optional[str] = None,
        zftype: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """查询客户信息报表。"""
        where_parts: List[str] = []
        params: Dict[str, Any] = {}

        if custcard and custcard.strip():
            where_parts.append("t.custcard LIKE :custcard")
            params["custcard"] = f"%{custcard.strip()}%"
        if classcd and classcd.strip():
            where_parts.append("t.classcd LIKE :classcd")
            params["classcd"] = f"%{classcd.strip()}%"
        if custnm and custnm.strip():
            where_parts.append("t.custnm LIKE :custnm")
            params["custnm"] = f"%{custnm.strip()}%"
        if busityp and busityp.strip():
            where_parts.append("t.busityp = :busityp")
            params["busityp"] = busityp.strip()
        if useflg and useflg.strip():
            where_parts.append("NVL(t.useflg,'1') = :useflg")
            params["useflg"] = useflg.strip()
        if opendate_from and opendate_from.strip():
            where_parts.append("t.opendate >= TO_DATE(:opendate_from,'YYYY-MM-DD')")
            params["opendate_from"] = opendate_from.strip()
        if opendate_to and opendate_to.strip():
            where_parts.append("t.opendate < TO_DATE(:opendate_to,'YYYY-MM-DD') + 1")
            params["opendate_to"] = opendate_to.strip()
        if pptcode and pptcode.strip():
            where_parts.append("t.pptcode = :pptcode")
            params["pptcode"] = pptcode.strip()
        if zftype and zftype.strip():
            where_parts.append("t.zftype = :zftype")
            params["zftype"] = zftype.strip()

        extra = (" AND " + " AND ".join(where_parts)) if where_parts else ""
        data_sql = (
            _BASE_SQL.replace("AND 1=1", "AND 1=1" + extra) + " ORDER BY t.classcd"
        )

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
