"""
维修单业务服务（ITSM核心）。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 集成统一状态机（优化2）
    - 对应 itsm.pbl 的维修单管理功能
"""

from __future__ import annotations

import logging
from typing import Any

from app.repositories.maintenance_repository import MaintenanceRepository
from app.services.state_machine import MaintenanceState, StateMachine

logger = logging.getLogger(__name__)

__all__ = ["MaintenanceService"]


class MaintenanceService:
    """
    维修单业务服务。

    功能概述：
        - 维修单全生命周期管理
        - 统一状态机驱动状态流转
        - 事件驱动扩展点
    """

    def __init__(
        self,
        maintenance_repository: MaintenanceRepository | None = None,
    ) -> None:
        """
        初始化服务。

        参数：
            maintenance_repository: 维修单仓储实例
        """
        self._repo = maintenance_repository or MaintenanceRepository()

    def get_maintenance_detail(
        self,
        maintenance_id: str,
    ) -> dict[str, Any] | None:
        """
        获取维修单详情。

        参数：
            maintenance_id: 维修单ID

        返回值：
            dict[str, Any] | None: 维修单详情或空
        """
        maintenance = self._repo.get_by_id(maintenance_id)
        if maintenance is None:
            return None

        # 添加状态显示名称
        status_code = maintenance.get("current_status", "00")
        state = MaintenanceState.from_code(status_code)
        if state:
            maintenance["status_display"] = state.display_name
            maintenance["is_terminal"] = StateMachine.is_terminal(state)

        return maintenance

    def list_maintenances(
        self,
        cust_cd: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取维修单列表。

        参数：
            cust_cd: 客户代码过滤
            status: 状态过滤

        返回值：
            list[dict[str, Any]]: 维修单列表
        """
        return self._repo.list_maintenances(cust_cd, status)

    def create_maintenance(
        self,
        maintenance_info: dict[str, Any],
        oper_cd: str,
    ) -> dict[str, Any] | None:
        """
        创建维修单（初始状态为 DRAFT）。

        参数：
            maintenance_info: 维修单信息
            oper_cd: 操作员代码

        返回值：
            dict[str, Any] | None: 创建的维修单信息或空
        """
        # 设置初始状态为草稿
        maintenance_info["current_status"] = MaintenanceState.DRAFT.value

        maintenance_id = self._repo.create_maintenance(maintenance_info, oper_cd)
        if maintenance_id is None:
            return None

        # 记录创建日志
        self._repo.log_status_change(
            maintenance_id,
            maintenance_info.get("company_id", ""),
            f"Maintenance order created by {oper_cd}",
        )

        return self.get_maintenance_detail(maintenance_id)

    def transition_state(
        self,
        maintenance_id: str,
        to_state_code: str,
        oper_cd: str,
        remark: str = "",
    ) -> dict[str, Any]:
        """
        执行维修单状态流转（核心方法）。

        参数：
            maintenance_id: 维修单ID
            to_state_code: 目标状态码
            oper_cd: 操作员代码
            remark: 备注

        返回值：
            dict[str, Any]: 操作结果
        """
        # 1. 查询当前维修单
        maintenance = self._repo.get_by_id(maintenance_id)
        if maintenance is None:
            return {
                "success": False,
                "error": "Maintenance order not found",
            }

        from_state_code = maintenance.get("current_status", "00")

        # 2. 验证状态流转合法性
        validation = StateMachine.validate_transition(
            from_state_code,
            to_state_code,
        )
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "allowed_transitions": validation.get("allowed_transitions", []),
            }

        # 3. 执行状态更新
        success = self._repo.update_status(
            maintenance_id,
            from_state_code,
            to_state_code,
            oper_cd,
        )
        if not success:
            return {
                "success": False,
                "error": "Failed to update status, possibly concurrent modification",
            }

        # 4. 记录状态变更日志
        from_state = MaintenanceState.from_code(from_state_code)
        to_state = MaintenanceState.from_code(to_state_code)
        memo = (
            f"Status changed from {from_state.display_name if from_state else from_state_code} "
            f"to {to_state.display_name if to_state else to_state_code} by {oper_cd}"
        )
        if remark:
            memo += f". Remark: {remark}"

        self._repo.log_status_change(
            maintenance_id,
            maintenance.get("company_id", ""),
            memo,
        )

        # 5. 触发事件处理（扩展点）
        self._on_state_changed(maintenance_id, from_state_code, to_state_code, oper_cd)

        return {
            "success": True,
            "maintenance_id": maintenance_id,
            "from_status": from_state_code,
            "to_status": to_state_code,
            "message": f"Status transitioned to {to_state.display_name if to_state else to_state_code}",
        }

    def dispatch(
        self,
        maintenance_id: str,
        engineer_id: str,
        oper_cd: str,
    ) -> dict[str, Any]:
        """
        派工（PLANNED → DISPATCHED）。

        参数：
            maintenance_id: 维修单ID
            engineer_id: 工程师ID
            oper_cd: 操作员代码

        返回值：
            dict[str, Any]: 操作结果
        """
        result = self.transition_state(
            maintenance_id,
            MaintenanceState.DISPATCHED.value,
            oper_cd,
            f"Assigned to engineer {engineer_id}",
        )

        if result["success"]:
            # 扩展：发送通知给工程师
            self._notify_engineer(engineer_id, maintenance_id)

        return result

    def start_work(
        self,
        maintenance_id: str,
        oper_cd: str,
    ) -> dict[str, Any]:
        """
        开始实施（DISPATCHED → IN_PROGRESS）。

        参数：
            maintenance_id: 维修单ID
            oper_cd: 操作员代码

        返回值：
            dict[str, Any]: 操作结果
        """
        return self.transition_state(
            maintenance_id,
            MaintenanceState.IN_PROGRESS.value,
            oper_cd,
            "Work started",
        )

    def complete(
        self,
        maintenance_id: str,
        oper_cd: str,
    ) -> dict[str, Any]:
        """
        完成维修（IN_PROGRESS → COMPLETED）。

        参数：
            maintenance_id: 维修单ID
            oper_cd: 操作员代码

        返回值：
            dict[str, Any]: 操作结果
        """
        result = self.transition_state(
            maintenance_id,
            MaintenanceState.COMPLETED.value,
            oper_cd,
            "Work completed",
        )

        if result["success"]:
            # 扩展：触发回访任务
            self._trigger_followup_task(maintenance_id)

        return result

    def cancel(
        self,
        maintenance_id: str,
        reason: str,
        oper_cd: str,
    ) -> dict[str, Any]:
        """
        取消维修单。

        参数：
            maintenance_id: 维修单ID
            reason: 取消原因
            oper_cd: 操作员代码

        返回值：
            dict[str, Any]: 操作结果
        """
        maintenance = self._repo.get_by_id(maintenance_id)
        if maintenance is None:
            return {
                "success": False,
                "error": "Maintenance order not found",
            }

        current_status = maintenance.get("current_status", "00")

        # 检查是否为终态
        state = MaintenanceState.from_code(current_status)
        if state and StateMachine.is_terminal(state):
            return {
                "success": False,
                "error": f"Cannot cancel order in terminal state: {state.display_name}",
            }

        return self.transition_state(
            maintenance_id,
            MaintenanceState.CANCELLED.value,
            oper_cd,
            f"Cancelled: {reason}",
        )

    def get_allowed_transitions(self, maintenance_id: str) -> list[dict[str, Any]]:
        """
        获取维修单允许的状态流转。

        参数：
            maintenance_id: 维修单ID

        返回值：
            list[dict[str, Any]]: 允许的流转列表
        """
        maintenance = self._repo.get_by_id(maintenance_id)
        if maintenance is None:
            return []

        current_status = maintenance.get("current_status", "00")
        current_state = MaintenanceState.from_code(current_status)
        if current_state is None:
            return []

        allowed_states = StateMachine.get_allowed_transitions(current_state)
        return [
            {
                "state_code": state.value,
                "state_name": state.display_name,
            }
            for state in allowed_states
        ]

    def list_pos_details(self, maintenance_id: str) -> list[dict[str, Any]]:
        """
        获取维护单配件明细（TIT10_POS_DETAIL）。

        参数：
            maintenance_id: 维护单ID

        返回值：
            list[dict[str, Any]]: 配件明细列表
        """
        return self._repo.list_pos_details(maintenance_id)

    def create_pos_detail(
        self,
        maintenance_id: str,
        sm_id: int,
        device_id: str,
        accessories_id: str,
        creator: str,
        item_cd: str = "",
        noflg: str = "N",
        status: str = "1",
    ) -> dict[str, Any]:
        """
        新增维护单配件明细（TIT10_POS_DETAIL）。

        参数：
            maintenance_id: 维护单ID
            sm_id: 业务操作流水ID
            device_id: 整机ID
            accessories_id: 配件编号
            creator: 创建人
            item_cd: 配件类型
            noflg: 新旧设备标记
            status: 状态

        返回值：
            dict[str, Any]: 新增结果
        """
        maintenance = self._repo.get_by_id(maintenance_id)
        if maintenance is None:
            return {
                "success": False,
                "error": "Maintenance order not found",
            }

        success = self._repo.create_pos_detail(
            maintenance_id=maintenance_id,
            sm_id=sm_id,
            device_id=device_id,
            accessories_id=accessories_id,
            creator=creator,
            item_cd=item_cd,
            noflg=noflg,
            status=status,
        )
        if not success:
            return {
                "success": False,
                "error": "Failed to create pos detail",
            }

        return {
            "success": True,
            "maintenance_id": maintenance_id,
            "sm_id": sm_id,
            "device_id": device_id,
            "accessories_id": accessories_id,
            "item_cd": item_cd,
            "noflg": noflg,
            "status": status,
        }

    def _on_state_changed(
        self,
        maintenance_id: str,
        from_state: str,
        to_state: str,
        oper_cd: str,
    ) -> None:
        """
        状态变更事件处理（扩展点）。

        参数：
            maintenance_id: 维修单ID
            from_state: 原状态
            to_state: 新状态
            oper_cd: 操作员代码
        """
        logger.info(
            "Maintenance %s state changed: %s -> %s by %s",
            maintenance_id,
            from_state,
            to_state,
            oper_cd,
        )

    def _notify_engineer(self, engineer_id: str, maintenance_id: str) -> None:
        """通知工程师（扩展实现）。"""
        logger.info("Notify engineer %s about maintenance %s", engineer_id, maintenance_id)

    def _trigger_followup_task(self, maintenance_id: str) -> None:
        """触发回访任务（扩展实现）。"""
        logger.info("Trigger followup task for maintenance %s", maintenance_id)
