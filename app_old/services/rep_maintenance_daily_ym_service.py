# -*- coding: utf-8 -*-
"""
日常维护年月汇总报表服务。
文件说明：封装日常维护年月汇总报表查询业务逻辑。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict

from app.repositories.rep_maintenance_daily_ym_repository import (
    RepMaintenanceDailyYmRepository,
)

logger = logging.getLogger(__name__)

_YM_PATTERN = re.compile(r"^\d{6}$")


class RepMaintenanceDailyYmService:
    """日常维护年月汇总报表服务类。"""

    def __init__(self) -> None:
        self.repo = RepMaintenanceDailyYmRepository()

    def list_reports(
        self,
        in_ym: str,
    ) -> Dict[str, Any]:
        """按年月(YYYYMM)查询日常维护汇总报表。"""
        if not _YM_PATTERN.match((in_ym or "").strip()):
            return {
                "success": False,
                "error": "in_ym 格式错误，须为6位数字如 202403",
                "items": [],
                "total": 0,
            }
        try:
            result = self.repo.list_reports(in_ym=in_ym.strip())
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询日常维护年月汇总报表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
            }
