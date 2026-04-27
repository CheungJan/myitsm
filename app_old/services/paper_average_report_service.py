# -*- coding: utf-8 -*-
"""
纸张平均报表服务。
文件说明：封装工程师达标率/纸张平均报表查询逻辑。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.repositories.paper_average_report_repository import (
    PaperAverageReportRepository,
)

logger = logging.getLogger(__name__)


class PaperAverageReportService:
    """纸张平均报表服务类。"""

    def __init__(self) -> None:
        self.repo = PaperAverageReportRepository()

    def list_reports(
        self,
        start_date: str,
        end_date: str,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """查询纸张平均报表。"""
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
                page=page,
                page_size=page_size,
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询纸张平均报表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }
