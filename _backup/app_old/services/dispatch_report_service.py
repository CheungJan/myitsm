# -*- coding: utf-8 -*-
"""
分派报表服务。
文件说明：封装分派报表查询业务逻辑。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.dispatch_report_repository import DispatchReportRepository

logger = logging.getLogger(__name__)


class DispatchReportService:
    """分派报表服务类。"""

    def __init__(self) -> None:
        self.repo = DispatchReportRepository()

    def list_reports(
        self,
        start_date: str,
        end_date: str,
        maintenance_id: Optional[str] = None,
        custcard: Optional[str] = None,
        custnm: Optional[str] = None,
        accpectd_group: Optional[str] = None,
        accpectder: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询分派报表。"""
        if not start_date.strip() or not end_date.strip():
            return {
                "success": False,
                "error": "start_date/end_date 不能为空",
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

        try:
            result = self.repo.list_reports(
                start_date=start_date.strip(),
                end_date=end_date.strip(),
                maintenance_id=(maintenance_id or "").strip() or None,
                custcard=(custcard or "").strip() or None,
                custnm=(custnm or "").strip() or None,
                accpectd_group=(accpectd_group or "").strip() or None,
                accpectder=(accpectder or "").strip() or None,
                page=page,
                page_size=page_size,
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询分派报表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }
