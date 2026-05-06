# -*- coding: utf-8 -*-
"""
客户信息报表服务。
文件说明：封装客户信息报表查询业务逻辑。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.rep_cust_info_repository import RepCustInfoRepository

logger = logging.getLogger(__name__)


class RepCustInfoService:
    """客户信息报表服务类。"""

    def __init__(self) -> None:
        self.repo = RepCustInfoRepository()

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
        try:
            result = self.repo.list_reports(
                custcard=custcard,
                classcd=classcd,
                custnm=custnm,
                busityp=busityp,
                useflg=useflg,
                opendate_from=opendate_from,
                opendate_to=opendate_to,
                pptcode=pptcode,
                zftype=zftype,
                page=page,
                page_size=page_size,
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询客户信息报表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }
