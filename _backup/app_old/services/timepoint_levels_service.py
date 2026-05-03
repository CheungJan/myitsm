# -*- coding: utf-8 -*-
"""
时间点等级服务。
文件说明：封装等级维护及客户等级分配业务逻辑。
作者：Cascade
创建时间：2026-04-20
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.timepoint_levels_repository import TimepointLevelsRepository

logger = logging.getLogger(__name__)


class TimepointLevelsService:
    """时间点等级服务类。"""

    def __init__(self) -> None:
        self.repo = TimepointLevelsRepository()

    def list_levels(
        self,
        include_invalid: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询等级定义列表。"""
        try:
            result = self.repo.list_levels(
                include_invalid=include_invalid,
                page=page,
                page_size=page_size,
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("查询等级定义列表失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

    def save_level(
        self,
        levels: str,
        explain: str,
        opercd: str,
        timepoint: Optional[str] = None,
        beforetm: Optional[float] = None,
        aftertm: Optional[float] = None,
        useflg: str = "1",
    ) -> Dict[str, Any]:
        """保存等级定义。"""
        if not levels.strip() or not explain.strip():
            return {"success": False, "error": "levels/explain 不能为空"}
        if not opercd.strip():
            return {"success": False, "error": "opercd 不能为空"}
        if useflg not in {"0", "1"}:
            return {"success": False, "error": "useflg 仅允许 0/1"}

        try:
            saved = self.repo.save_level(
                levels=levels.strip(),
                explain=explain.strip(),
                timepoint=(timepoint or "").strip() or None,
                beforetm=beforetm,
                aftertm=aftertm,
                opercd=opercd.strip(),
                useflg=useflg,
            )
            if not saved:
                return {"success": False, "error": "保存失败"}
            return {
                "success": True,
                "levels": levels.strip(),
                "message": "等级定义保存成功",
            }
        except Exception as exc:
            logger.error("保存等级定义失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def list_customers_by_level(
        self,
        levels: str,
        custcd: Optional[str] = None,
        custnm: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """按等级查询客户。"""
        if not levels.strip():
            return {
                "success": False,
                "error": "levels 不能为空",
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

        try:
            result = self.repo.list_customers_by_level(
                levels=levels.strip(),
                custcd=(custcd or "").strip() or None,
                custnm=(custnm or "").strip() or None,
                page=page,
                page_size=page_size,
            )
            return {"success": True, **result}
        except Exception as exc:
            logger.error("按等级查询客户失败: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

    def assign_level_to_customers(
        self,
        levels: str,
        custcd_list: list[str],
        opercd: str,
    ) -> Dict[str, Any]:
        """批量分配客户等级。"""
        if not levels.strip():
            return {"success": False, "error": "levels 不能为空"}
        if not custcd_list:
            return {"success": False, "error": "custcd_list 不能为空"}
        if not opercd.strip():
            return {"success": False, "error": "opercd 不能为空"}

        try:
            updated = self.repo.assign_level_to_customers(
                levels=levels.strip(),
                custcd_list=[item.strip() for item in custcd_list if str(item).strip()],
                opercd=opercd.strip(),
            )
            return {
                "success": True,
                "levels": levels.strip(),
                "updated_count": updated,
                "message": "客户等级分配完成",
            }
        except Exception as exc:
            logger.error("批量分配客户等级失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def clear_customer_levels(
        self, custcd_list: list[str], opercd: str
    ) -> Dict[str, Any]:
        """批量清空客户等级。"""
        if not custcd_list:
            return {"success": False, "error": "custcd_list 不能为空"}
        if not opercd.strip():
            return {"success": False, "error": "opercd 不能为空"}

        try:
            updated = self.repo.clear_customer_levels(
                custcd_list=[item.strip() for item in custcd_list if str(item).strip()],
                opercd=opercd.strip(),
            )
            return {
                "success": True,
                "updated_count": updated,
                "message": "客户等级清空完成",
            }
        except Exception as exc:
            logger.error("批量清空客户等级失败: %s", exc)
            return {"success": False, "error": str(exc)}
