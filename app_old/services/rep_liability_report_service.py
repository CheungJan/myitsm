# -*- coding: utf-8 -*-
"""
责任认定报表服务。
文件说明：封装责任认定报表主列表与明细查询逻辑。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.rep_liability_report_repository import (
    RepLiabilityReportRepository,
)

logger = logging.getLogger(__name__)


class RepLiabilityReportService:
    """责任认定报表服务类。"""

    def __init__(self) -> None:
        self.repo = RepLiabilityReportRepository()

    def list_reports(
        self,
        start_date: str,
        end_date: str,
        maintenance_id: Optional[str] = None,
        store_id: Optional[str] = None,
        liability_type: Optional[str] = None,
        exemptflg: Optional[str] = None,
        is_finish: Optional[str] = None,
        deptnm: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询责任认定报表主列表。"""
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
                store_id=(store_id or "").strip() or None,
                liability_type=(liability_type or "").strip() or None,
                exemptflg=(exemptflg or "").strip() or None,
                is_finish=(is_finish or "").strip() or None,
                deptnm=(deptnm or "").strip() or None,
                page=page,
                page_size=page_size,
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询责任认定报表主列表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

    def list_report_details(
        self, maintenance_id: str, liability_type: str
    ) -> Dict[str, Any]:
        """查询责任认定报表明细。"""
        if not maintenance_id.strip() or not liability_type.strip():
            return {"success": False, "error": "maintenance_id/liability_type 不能为空"}

        try:
            items = self.repo.list_report_details(
                maintenance_id=maintenance_id.strip(),
                liability_type=liability_type.strip(),
            )
            return {"success": True, "items": items, "total": len(items)}
        except Exception as exc:
            logger.error("查询责任认定报表明细失败: %s", exc)
            return {"success": False, "error": str(exc)}
