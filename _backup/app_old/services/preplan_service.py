"""
预计划管理服务。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 实现与M006客户/资产联动
    - 结合优化1客户生命周期 + 优化4回收任务
    - 对应 sale.pbl 的预计划管理功能
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from app.repositories.preplan_repository import PreplanRepository
from app.services.asset_service import AssetService
from app.services.customer_service import CustomerService
from app.services.recycle_task_service import RecycleTaskService

logger = logging.getLogger(__name__)

__all__ = ["PreplanService", "PlanType", "PlanStatus", "ImpleStatus"]


class PlanType(Enum):
    """预计划类型。"""

    RENOVATE = "01"  # 旧机翻新
    CLOSE = "02"  # 关门
    NEW_OPEN = "03"  # 新开
    UPGRADE = "04"  # 设备升级


class PlanStatus(Enum):
    """计划状态。"""

    DRAFT = "00"  # 草稿
    PENDING = "01"  # 待审批
    APPROVED = "02"  # 已审批
    REJECTED = "09"  # 已拒绝


class ImpleStatus(Enum):
    """实施状态。"""

    NOT_STARTED = "00"  # 未开始
    IN_PROGRESS = "01"  # 实施中
    COMPLETED = "02"  # 已完成
    CANCELLED = "09"  # 已取消


class PreplanService:
    """
    预计划管理服务。

    功能概述：
        - 预计划CRUD操作
        - 自动触发客户创建（新客户时）
        - 自动触发回收任务（旧机翻新/关门时）
        - 实施完成时客户转正
    """

    def __init__(
        self,
        preplan_repository: PreplanRepository | None = None,
        customer_service: CustomerService | None = None,
        asset_service: AssetService | None = None,
        recycle_task_service: RecycleTaskService | None = None,
    ) -> None:
        """
        初始化服务。

        参数：
            preplan_repository: 预计划仓储
            customer_service: 客户服务
            asset_service: 资产服务
            recycle_task_service: 回收任务服务
        """
        self._repo = preplan_repository or PreplanRepository()
        self._cust_svc = customer_service or CustomerService()
        self._asset_svc = asset_service or AssetService()
        self._recycle_svc = recycle_task_service or RecycleTaskService()

    def get_preplan_detail(self, plan_no: str) -> dict[str, Any] | None:
        """
        获取预计划详情。

        参数：
            plan_no: 预计划号

        返回值：
            dict[str, Any] | None: 预计划详情或空
        """
        return self._repo.get_by_no(plan_no)

    def list_preplans(
        self,
        plan_status: str | None = None,
        imple_status: str | None = None,
        cust_cd: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取预计划列表。

        参数：
            plan_status: 计划状态
            imple_status: 实施状态
            cust_cd: 客户代码

        返回值：
            list[dict[str, Any]]: 预计划列表
        """
        return self._repo.list_preplans(plan_status, imple_status, cust_cd)

    def submit_preplan(
        self,
        plan_no: str,
        oper_cd: str,
    ) -> dict[str, Any]:
        """
        提交预计划（审批通过时触发联动）。

        流程：
            1. 查询预计划详情
            2. 如果是新客户（cust_new='Y'），创建临时客户
            3. 如果是旧机翻新/关门（plan_type in 01/02），创建回收任务
            4. 更新预计划状态为已审批

        参数：
            plan_no: 预计划号
            oper_cd: 操作员代码

        返回值：
            dict[str, Any]: 处理结果
        """
        # 查询预计划
        preplan = self._repo.get_by_no(plan_no)
        if preplan is None:
            return {"success": False, "message": "预计划不存在"}

        result = {
            "plan_no": plan_no,
            "customer_created": False,
            "recycle_task_created": False,
            "errors": [],
        }

        # 1. 创建临时客户（新客户时）
        cust_cd = preplan.get("cust_cd")
        if preplan.get("cust_new") == "Y" and not cust_cd:
            cust_info = {
                "cust_nm": preplan.get("cust_nm", ""),
                "cust_card": preplan.get("cust_card", ""),
                "address": preplan.get("address", ""),
                "phone_no": preplan.get("phone_no", ""),
                "contactor": preplan.get("contactor", ""),
                "class_cd": preplan.get("class_cd", ""),
                "busi_typ": preplan.get("busi_typ", ""),
            }
            customer = self._cust_svc.create_temp_from_preplan(
                plan_no, cust_info, oper_cd
            )
            if customer:
                result["customer_created"] = True
                result["cust_cd"] = customer.get("cust_cd")
                cust_cd = customer.get("cust_cd")
                # 更新预计划的客户代码
                self._repo.update_cust_cd(plan_no, cust_cd)
            else:
                result["errors"].append("临时客户创建失败，可能磁卡号已存在")

        # 2. 创建回收任务（旧机翻新/关门时）
        plan_type = preplan.get("plan_type", "")
        if plan_type in (PlanType.RENOVATE.value, PlanType.CLOSE.value):
            if cust_cd:
                recycle_task = self._recycle_svc.create_from_plan(
                    plan_no, plan_type, cust_cd, oper_cd
                )
                if recycle_task:
                    result["recycle_task_created"] = True
                    result["recycle_id"] = recycle_task.get("recycle_id")
                else:
                    # 无可回收资产时不视为错误
                    result["recycle_info"] = "无可回收资产"
            else:
                result["errors"].append("无可关联客户，无法创建回收任务")

        # 3. 更新预计划状态
        self._repo.update_status(
            plan_no,
            PlanStatus.APPROVED.value,
            ImpleStatus.NOT_STARTED.value,
            oper_cd,
        )

        result["success"] = len(result["errors"]) == 0
        result["message"] = "预计划提交成功" if result["success"] else "预计划提交完成但有警告"
        return result

    def start_implementation(
        self,
        plan_no: str,
        oper_cd: str,
    ) -> dict[str, Any]:
        """
        开始实施。

        参数：
            plan_no: 预计划号
            oper_cd: 操作员代码

        返回值：
            dict[str, Any]: 处理结果
        """
        success = self._repo.update_imple_status(
            plan_no, ImpleStatus.IN_PROGRESS.value, oper_cd
        )
        return {
            "success": success,
            "message": "实施已启动" if success else "状态更新失败",
            "plan_no": plan_no,
            "imple_status": ImpleStatus.IN_PROGRESS.value,
        }

    def complete_implementation(
        self,
        plan_no: str,
        oper_cd: str,
    ) -> dict[str, Any]:
        """
        完成实施（临时客户转正）。

        参数：
            plan_no: 预计划号
            oper_cd: 操作员代码

        返回值：
            dict[str, Any]: 处理结果
        """
        # 查询预计划
        preplan = self._repo.get_by_no(plan_no)
        if preplan is None:
            return {"success": False, "message": "预计划不存在"}

        cust_cd = preplan.get("cust_cd")
        result = {
            "plan_no": plan_no,
            "cust_cd": cust_cd,
            "customer_promoted": False,
        }

        # 临时客户转正
        if cust_cd:
            promoted = self._cust_svc.promote_to_active(cust_cd, oper_cd)
            result["customer_promoted"] = promoted

        # 更新实施状态
        success = self._repo.update_imple_status(
            plan_no, ImpleStatus.COMPLETED.value, oper_cd
        )
        result["success"] = success
        result["message"] = "实施已完成" if success else "状态更新失败"
        result["imple_status"] = ImpleStatus.COMPLETED.value

        return result

    def cancel_preplan(
        self,
        plan_no: str,
        reason: str,
        oper_cd: str,
    ) -> dict[str, Any]:
        """
        取消预计划（标记客户无效）。

        参数：
            plan_no: 预计划号
            reason: 取消原因
            oper_cd: 操作员代码

        返回值：
            dict[str, Any]: 处理结果
        """
        # 查询预计划
        preplan = self._repo.get_by_no(plan_no)
        if preplan is None:
            return {"success": False, "message": "预计划不存在"}

        cust_cd = preplan.get("cust_cd")
        result = {
            "plan_no": plan_no,
            "cust_cd": cust_cd,
            "customer_invalidated": False,
        }

        # 标记客户无效
        if cust_cd:
            invalidated = self._cust_svc.mark_invalid(cust_cd, oper_cd)
            result["customer_invalidated"] = invalidated

        # 更新实施状态为已取消
        success = self._repo.update_imple_status(
            plan_no, ImpleStatus.CANCELLED.value, oper_cd
        )
        result["success"] = success
        result["message"] = "预计划已取消" if success else "状态更新失败"
        result["cancel_reason"] = reason

        return result

    def get_preplan_with_customer(self, plan_no: str) -> dict[str, Any] | None:
        """
        获取预计划详情（含客户信息）。

        参数：
            plan_no: 预计划号

        返回值：
            dict[str, Any] | None: 完整信息或空
        """
        preplan = self._repo.get_by_no(plan_no)
        if preplan is None:
            return None

        cust_cd = preplan.get("cust_cd")
        if cust_cd:
            customer = self._cust_svc.get_customer_detail(cust_cd)
            preplan["customer"] = customer

        return preplan

    def get_implementation_progress(self, plan_no: str) -> dict[str, Any]:
        """
        获取实施进度（含关联任务）。

        参数：
            plan_no: 预计划号

        返回值：
            dict[str, Any]: 实施进度
        """
        preplan = self._repo.get_by_no(plan_no)
        if preplan is None:
            return {"success": False, "message": "预计划不存在"}

        cust_cd = preplan.get("cust_cd")
        recycle_tasks = []

        if cust_cd:
            # 查询关联的回收任务
            tasks = self._recycle_svc.get_task_list(
                plan_no=plan_no, cust_cd=cust_cd
            )
            recycle_tasks = tasks

        return {
            "success": True,
            "plan_no": plan_no,
            "plan_status": preplan.get("plan_status"),
            "imple_status": preplan.get("imple_status"),
            "cust_cd": cust_cd,
            "recycle_tasks": recycle_tasks,
            "recycle_task_count": len(recycle_tasks),
        }
