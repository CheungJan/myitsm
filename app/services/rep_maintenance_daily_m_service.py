# -*- coding: utf-8 -*-
"""
日常维护月度汇总报表服务。
文件说明：封装日常维护月度汇总报表查询业务逻辑。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.repositories.rep_maintenance_daily_m_repository import (
    RepMaintenanceDailyMRepository,
)

logger = logging.getLogger(__name__)


class RepMaintenanceDailyMService:
    """日常维护月度汇总报表服务类。"""

    def __init__(self) -> None:
        self.repo = RepMaintenanceDailyMRepository()

    def list_reports(
        self,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """按日期区间查询日常维护月度汇总报表。"""
        if not start_date.strip() or not end_date.strip():
            return {
                "success": False,
                "error": "start_date/end_date 不能为空",
                "items": [],
                "total": 0,
            }
        try:
            result = self.repo.list_reports(
                start_date=start_date.strip(),
                end_date=end_date.strip(),
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询日常维护月度汇总报表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
            }
