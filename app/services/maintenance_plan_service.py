# -*- coding: utf-8 -*-
"""
保养计划服务。
文件说明：编排 TIT17_MAINTENANCE_PLAN 业务逻辑，并对齐 PB 历史数据不可改规则。
作者：Cascade
创建时间：2026-04-20

PB 关键规则：
- 查询按 PLAN_YYMM 过滤。
- 历史数据（PLAN_YYMM < 当前YYYYMM）不允许新增/修改/删除。
- 年度生成功能：按年逐月生成，已存在月份跳过。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.repositories.maintenance_plan_repository import MaintenancePlanRepository

logger = logging.getLogger(__name__)


class MaintenancePlanService:
    """保养计划服务类。"""

    def __init__(self) -> None:
        self.repo = MaintenancePlanRepository()

    def list_plans(
        self,
        plan_yymm: Optional[str] = None,
        page: int = 1,
        page_size: int = 200,
    ) -> Dict[str, Any]:
        """分页查询保养计划。"""
        try:
            return self.repo.list_plans(
                plan_yymm=plan_yymm, page=page, page_size=page_size
            )
        except Exception as exc:
            logger.error("查询保养计划列表失败: %s", exc)
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def get_plan(self, plan_yymm: str, area_id: int) -> Optional[Dict[str, Any]]:
        """查询保养计划详情。"""
        try:
            return self.repo.get_plan(plan_yymm=plan_yymm, area_id=area_id)
        except Exception as exc:
            logger.error("查询保养计划详情失败: %s", exc)
            return None

    def create_plan(
        self, plan_yymm: str, area_id: int, plan_qty: int, creator: str
    ) -> Dict[str, Any]:
        """新增保养计划。"""
        if not self._is_valid_yymm(plan_yymm):
            return {"success": False, "error": "plan_yymm格式错误，应为YYYYMM"}
        if area_id <= 0:
            return {"success": False, "error": "area_id必须大于0"}
        if plan_qty < 0:
            return {"success": False, "error": "plan_qty不能小于0"}
        if not creator.strip():
            return {"success": False, "error": "creator is required"}

        if self._is_history_month(plan_yymm):
            return {"success": False, "error": "历史数据，不允许新增信息"}

        try:
            existing = self.repo.get_plan(plan_yymm=plan_yymm, area_id=area_id)
            if existing:
                return {"success": False, "error": "该计划已存在"}

            success = self.repo.create_plan(
                plan_yymm=plan_yymm,
                area_id=area_id,
                plan_qty=plan_qty,
                creator=creator.strip(),
            )
            if not success:
                return {"success": False, "error": "新增保养计划失败"}

            return {
                "success": True,
                "plan_yymm": plan_yymm,
                "area_id": area_id,
                "message": "新增保养计划成功",
            }
        except Exception as exc:
            logger.error("新增保养计划失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def update_plan_qty(
        self, plan_yymm: str, area_id: int, plan_qty: int
    ) -> Dict[str, Any]:
        """更新保养计划数量。"""
        if not self._is_valid_yymm(plan_yymm):
            return {"success": False, "error": "plan_yymm格式错误，应为YYYYMM"}
        if area_id <= 0:
            return {"success": False, "error": "area_id必须大于0"}
        if plan_qty < 0:
            return {"success": False, "error": "plan_qty不能小于0"}

        if self._is_history_month(plan_yymm):
            return {"success": False, "error": "历史数据，不允许修改"}

        try:
            updated = self.repo.update_plan_qty(
                plan_yymm=plan_yymm, area_id=area_id, plan_qty=plan_qty
            )
            if not updated:
                return {"success": False, "error": "计划不存在或未更新"}
            return {
                "success": True,
                "plan_yymm": plan_yymm,
                "area_id": area_id,
                "plan_qty": plan_qty,
            }
        except Exception as exc:
            logger.error("更新保养计划失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def delete_plan(self, plan_yymm: str, area_id: int) -> Dict[str, Any]:
        """删除保养计划。"""
        if not self._is_valid_yymm(plan_yymm):
            return {"success": False, "error": "plan_yymm格式错误，应为YYYYMM"}
        if area_id <= 0:
            return {"success": False, "error": "area_id必须大于0"}

        if self._is_history_month(plan_yymm):
            return {"success": False, "error": "历史数据，不允许删除"}

        try:
            deleted = self.repo.delete_plan(plan_yymm=plan_yymm, area_id=area_id)
            if not deleted:
                return {"success": False, "error": "计划不存在或已删除"}
            return {"success": True, "plan_yymm": plan_yymm, "area_id": area_id}
        except Exception as exc:
            logger.error("删除保养计划失败: %s", exc)
            return {"success": False, "error": str(exc)}

    def generate_year(self, plan_y: str, creator: str) -> Dict[str, Any]:
        """按年生成保养计划（12个月）。"""
        if not plan_y or len(plan_y) != 4 or not plan_y.isdigit():
            return {"success": False, "error": "年份有误，请输入4位数字"}
        if int(plan_y) < int(datetime.now().strftime("%Y")):
            return {"success": False, "error": "年份有误，不能小于当前年"}
        if not creator.strip():
            return {"success": False, "error": "creator is required"}

        created_months = 0
        created_rows = 0

        try:
            for month in range(1, 13):
                yymm = f"{plan_y}{month:02d}"
                if self.repo.exists_by_yymm(yymm):
                    continue
                rows = self.repo.generate_month_plans(
                    plan_y=plan_y,
                    plan_yymm=yymm,
                    creator=creator.strip(),
                )
                created_months += 1
                created_rows += rows

            return {
                "success": True,
                "plan_y": plan_y,
                "created_months": created_months,
                "created_rows": created_rows,
                "message": f"生成{plan_y}年份数据成功",
            }
        except Exception as exc:
            logger.error("按年生成保养计划失败: %s", exc)
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _is_valid_yymm(plan_yymm: str) -> bool:
        """校验年月字符串。"""
        if not plan_yymm or len(plan_yymm) != 6 or not plan_yymm.isdigit():
            return False
        month = int(plan_yymm[4:6])
        return 1 <= month <= 12

    @staticmethod
    def _is_history_month(plan_yymm: str) -> bool:
        """判断是否历史月份。"""
        current_yymm = datetime.now().strftime("%Y%m")
        return plan_yymm < current_yymm
