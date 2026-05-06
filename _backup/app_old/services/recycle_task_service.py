"""
旧机回收任务服务。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 回收任务独立于日常维护单
    - 对应优化4：旧机回收任务独立化
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from app.repositories.recycle_task_repository import RecycleTaskRepository
from app.services.asset_service import AssetService, RecycleStatus

logger = logging.getLogger(__name__)

__all__ = ["RecycleTaskService", "RecycleType", "TaskStatus", "DispositionType"]


class RecycleType(Enum):
    """回收类型。"""

    RENOVATE = "01"  # 旧机翻新
    CLOSE = "02"  # 关门回收
    UPGRADE = "03"  # 设备升级


class TaskStatus(Enum):
    """任务状态。"""

    PENDING = "00"  # 待分配
    ASSIGNED = "01"  # 已分配
    IN_PROGRESS = "02"  # 回收中
    COMPLETED = "03"  # 已完成
    CANCELLED = "09"  # 已取消


class DispositionType(Enum):
    """处置方式。"""

    RENOVATE = "01"  # 翻新
    SCRAP = "02"  # 报废
    TRANSFER = "03"  # 调拨


class RecycleTaskService:
    """
    旧机回收任务管理服务。

    功能概述：
        - 回收任务全生命周期管理
        - 预计划自动触发
        - 回收统计分析
    """

    def __init__(
        self,
        recycle_task_repository: RecycleTaskRepository | None = None,
        asset_service: AssetService | None = None,
    ) -> None:
        """
        初始化服务。

        参数：
            recycle_task_repository: 回收任务仓储实例
            asset_service: 资产服务实例
        """
        self._repo = recycle_task_repository or RecycleTaskRepository()
        self._asset_svc = asset_service or AssetService()

    def create_from_plan(
        self,
        plan_no: str,
        plan_type: str,
        cust_cd: str,
        oper_cd: str,
    ) -> dict[str, Any] | None:
        """
        从预计划创建回收任务。

        触发条件：
            - PLAN_TYPE in ('01', '02')
            - 门店有可回收资产

        参数：
            plan_no: 预计划单号
            plan_type: 计划类型（01旧机翻新/02关门）
            cust_cd: 门店代码
            oper_cd: 操作员代码

        返回值：
            dict[str, Any] | None: 回收任务信息或空
        """
        # 检查是否需要创建
        should_create, asset_count = self._asset_svc.should_create_recycle_task(
            cust_cd, plan_type
        )
        if not should_create:
            logger.info("门店 %s 无可回收资产，无需创建回收任务", cust_cd)
            return None

        # 标记可回收资产
        marked_count = self._asset_svc.mark_recyclable(cust_cd, plan_type)
        if marked_count == 0:
            logger.warning("标记可回收资产失败，cust_cd=%s", cust_cd)
            return None

        # 获取可回收资产列表
        assets = self._asset_svc.get_recyclable_assets(cust_cd)

        # 创建回收任务
        recycle_id = self._repo.create_task(
            recycle_type=plan_type,
            plan_no=plan_no,
            cust_cd=cust_cd,
            assets=assets,
            oper_cd=oper_cd,
            remark=f"预计划 {plan_no} 自动触发",
        )

        if recycle_id is None:
            return None

        return {
            "recycle_id": recycle_id,
            "plan_no": plan_no,
            "cust_cd": cust_cd,
            "asset_count": len(assets),
            "task_status": TaskStatus.PENDING.value,
        }

    def get_task_list(
        self,
        cust_cd: str | None = None,
        plan_no: str | None = None,
        task_status: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取回收任务列表。

        参数：
            cust_cd: 门店代码过滤
            plan_no: 预计划单号过滤
            task_status: 任务状态过滤

        返回值：
            list[dict[str, Any]]: 任务列表
        """
        return self._repo.list_tasks(cust_cd, plan_no, task_status)

    def get_task_detail(self, recycle_id: str) -> dict[str, Any] | None:
        """
        获取回收任务详情。

        参数：
            recycle_id: 回收任务ID

        返回值：
            dict[str, Any] | None: 任务详情或空
        """
        return self._repo.get_task_detail(recycle_id)

    def assign_task(self, recycle_id: str, user_id: str) -> bool:
        """
        分配回收任务给人员。

        参数：
            recycle_id: 回收任务ID
            user_id: 用户ID

        返回值：
            bool: 是否成功
        """
        return self._repo.assign_task(recycle_id, user_id)

    def start_recycle(self, recycle_id: str) -> bool:
        """
        开始回收任务。

        参数：
            recycle_id: 回收任务ID

        返回值：
            bool: 是否成功
        """
        return self._repo.start_recycle(recycle_id)

    def complete_recycle(
        self,
        recycle_id: str,
        actual_assets: list[str],
        disposition: DispositionType,
        target_warehouse: str,
    ) -> bool:
        """
        完成回收任务。

        参数：
            recycle_id: 回收任务ID
            actual_assets: 实际回收的资产ID列表
            disposition: 处置方式
            target_warehouse: 目标仓库

        返回值：
            bool: 是否成功
        """
        # 更新任务状态
        success = self._repo.complete_recycle(
            recycle_id,
            actual_assets,
            disposition.value,
            target_warehouse,
        )
        if not success:
            return False

        # 更新资产状态
        task = self._repo.get_task_detail(recycle_id)
        if task:
            cust_cd = task.get("cust_cd")
            self._asset_svc.batch_update_recycle_status(
                cust_cd,
                actual_assets,
                RecycleStatus.COMPLETED,
            )

        return True

    def cancel_task(self, recycle_id: str, reason: str) -> bool:
        """
        取消回收任务。

        参数：
            recycle_id: 回收任务ID
            reason: 取消原因

        返回值：
            bool: 是否成功
        """
        return self._repo.cancel_task(recycle_id, reason)

    def get_recycle_stats(
        self,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """
        获取回收统计分析。

        参数：
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        返回值：
            dict[str, Any]: 统计结果
        """
        return self._repo.get_recycle_stats(start_date, end_date)
