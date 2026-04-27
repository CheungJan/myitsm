# -*- coding: utf-8 -*-
"""
日常保养报表服务。
文件说明：封装日常保养单报表查询业务逻辑。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.rep_maintenance_daily_repository import (
    RepMaintenanceDailyRepository,
)

logger = logging.getLogger(__name__)


class RepMaintenanceDailyService:
    """日常保养报表服务类。"""

    def __init__(self) -> None:
        self.repo = RepMaintenanceDailyRepository()

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
                custcard=custcard,
                classcd=classcd,
                engineer_id=engineer_id,
                current_status=current_status,
                itemcd=itemcd,
                page=page,
                page_size=page_size,
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询日常保养报表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }
