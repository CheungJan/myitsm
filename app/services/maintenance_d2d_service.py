# -*- coding: utf-8 -*-
"""
上门服务记录公用服务（TIT23_MAINTENANCE_D2D）。

文件说明：提供上门服务记录的查询与新增能力，作为公用服务被多单据复用。
作者：Cascade
创建时间：2026-04-14
"""

import logging
from typing import Any, Dict, Optional

from app.repositories.maintenance_d2d_repository import MaintenanceD2DRepository

logger = logging.getLogger(__name__)


class MaintenanceD2DService:
    """上门服务记录公用服务。"""

    def __init__(self) -> None:
        self.repo = MaintenanceD2DRepository()

    def list_d2d_records(
        self,
        maintenance_id: str,
        d2d_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取上门服务记录列表。

        Args:
            maintenance_id: 维护单ID（关联主表）
            d2d_type: 上门类型过滤（可选）

        Returns:
            统一结果
        """
        try:
            items = self.repo.list_d2d_records(
                maintenance_id=maintenance_id,
                d2d_type=d2d_type,
            )
            return {
                "success": True,
                "maintenance_id": maintenance_id,
                "d2d_type": d2d_type,
                "items": items,
                "count": len(items),
            }
        except Exception as e:
            logger.error(f"获取上门服务记录失败: {e}")
            return {"success": False, "error": str(e)}

    def create_d2d_record(
        self,
        maintenance_id: str,
        business_operation_id: int,
        creator: str,
        d2d_engineer: Optional[str] = None,
        arrive_time: Optional[str] = None,
        leave_time: Optional[str] = None,
        jjbz: Optional[str] = None,
        d2d_description: Optional[str] = None,
        d2d_phone: Optional[str] = None,
        old_business_id: Optional[int] = None,
        d2d_group: Optional[int] = None,
        d2d_type: Optional[str] = None,
        pos_status: Optional[str] = None,
        pos_status1: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        新增上门服务记录。

        Returns:
            统一结果
        """
        try:
            success = self.repo.create_d2d_record(
                maintenance_id=maintenance_id,
                business_operation_id=business_operation_id,
                creator=creator,
                d2d_engineer=d2d_engineer,
                arrive_time=arrive_time,
                leave_time=leave_time,
                jjbz=jjbz,
                d2d_description=d2d_description,
                d2d_phone=d2d_phone,
                old_business_id=old_business_id,
                d2d_group=d2d_group,
                d2d_type=d2d_type,
                pos_status=pos_status,
                pos_status1=pos_status1,
            )
            if not success:
                return {"success": False, "error": "Failed to create D2D record"}

            return {
                "success": True,
                "maintenance_id": maintenance_id,
                "business_operation_id": business_operation_id,
                "d2d_type": d2d_type,
                "d2d_engineer": d2d_engineer,
            }
        except Exception as e:
            logger.error(f"新增上门服务记录失败: {e}")
            return {"success": False, "error": str(e)}
