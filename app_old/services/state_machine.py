"""
ITSM 维修单统一状态机（优化2）。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

注意事项：
    - 统一维修单状态流转逻辑
    - 对应 itsm.pbl 的 u_itsm_open, u_itsm_renovate, u_itsm_archive
"""

from __future__ import annotations

from enum import Enum
from typing import Any

__all__ = ["MaintenanceState", "StateMachine"]


class MaintenanceState(Enum):
    """
    维修单生命周期状态。

    状态定义（对应数据库 CURRENT_STATUS 字段）：
        DRAFT = "00"       # 草稿/预计划
        PLANNED = "01"     # 已计划
        DISPATCHED = "04"  # 已派工
        IN_PROGRESS = "02" # 实施中
        COMPLETED = "05"   # 已完成
        CANCELLED = "09"   # 已取消
    """

    DRAFT = "00"
    PLANNED = "01"
    DISPATCHED = "04"
    IN_PROGRESS = "02"
    COMPLETED = "05"
    CANCELLED = "09"

    @classmethod
    def from_code(cls, code: str) -> "MaintenanceState | None":
        """从状态码获取枚举。"""
        for state in cls:
            if state.value == code:
                return state
        return None

    @property
    def display_name(self) -> str:
        """获取显示名称。"""
        names = {
            "00": "草稿",
            "01": "已计划",
            "04": "已派工",
            "02": "实施中",
            "05": "已完成",
            "09": "已取消",
        }
        return names.get(self.value, "未知")


class StateMachine:
    """
    维修单统一状态机。

    功能概述：
        - 统一管理维修单状态流转规则
        - 支持状态合法性校验
        - 记录状态变更历史

    状态流转规则：
        DRAFT → PLANNED / CANCELLED
        PLANNED → DISPATCHED / CANCELLED
        DISPATCHED → IN_PROGRESS / CANCELLED
        IN_PROGRESS → COMPLETED / CANCELLED
    """

    # 定义合法的状态流转
    TRANSITIONS: dict[MaintenanceState, list[MaintenanceState]] = {
        MaintenanceState.DRAFT: [
            MaintenanceState.PLANNED,
            MaintenanceState.CANCELLED,
        ],
        MaintenanceState.PLANNED: [
            MaintenanceState.DISPATCHED,
            MaintenanceState.CANCELLED,
        ],
        MaintenanceState.DISPATCHED: [
            MaintenanceState.IN_PROGRESS,
            MaintenanceState.CANCELLED,
        ],
        MaintenanceState.IN_PROGRESS: [
            MaintenanceState.COMPLETED,
            MaintenanceState.CANCELLED,
        ],
    }

    # 终态（不可再流转）
    TERMINAL_STATES: set[MaintenanceState] = {
        MaintenanceState.COMPLETED,
        MaintenanceState.CANCELLED,
    }

    @classmethod
    def can_transition(
        cls,
        from_state: MaintenanceState,
        to_state: MaintenanceState,
    ) -> bool:
        """
        检查状态流转是否合法。

        参数：
            from_state: 原状态
            to_state: 目标状态

        返回值：
            bool: 是否允许流转
        """
        # 相同状态，无需流转
        if from_state == to_state:
            return False

        # 检查目标状态是否在允许列表中
        allowed_states = cls.TRANSITIONS.get(from_state, [])
        return to_state in allowed_states

    @classmethod
    def get_allowed_transitions(
        cls,
        current_state: MaintenanceState,
    ) -> list[MaintenanceState]:
        """
        获取当前状态允许流转的目标状态列表。

        参数：
            current_state: 当前状态

        返回值：
            list[MaintenanceState]: 允许的目标状态列表
        """
        return cls.TRANSITIONS.get(current_state, [])

    @classmethod
    def is_terminal(cls, state: MaintenanceState) -> bool:
        """
        检查是否为终态。

        参数：
            state: 状态

        返回值：
            bool: 是否为终态
        """
        return state in cls.TERMINAL_STATES

    @classmethod
    def validate_transition(
        cls,
        from_state_code: str,
        to_state_code: str,
    ) -> dict[str, Any]:
        """
        验证状态流转并返回详细信息。

        参数：
            from_state_code: 原状态码
            to_state_code: 目标状态码

        返回值：
            dict[str, Any]: 验证结果
        """
        from_state = MaintenanceState.from_code(from_state_code)
        to_state = MaintenanceState.from_code(to_state_code)

        if from_state is None:
            return {
                "valid": False,
                "error": f"Invalid from_state: {from_state_code}",
            }

        if to_state is None:
            return {
                "valid": False,
                "error": f"Invalid to_state: {to_state_code}",
            }

        if cls.is_terminal(from_state):
            return {
                "valid": False,
                "error": f"Cannot transition from terminal state: {from_state.display_name}",
            }

        if not cls.can_transition(from_state, to_state):
            allowed = [s.value for s in cls.get_allowed_transitions(from_state)]
            return {
                "valid": False,
                "error": f"Transition from {from_state.display_name} to {to_state.display_name} not allowed",
                "allowed_transitions": allowed,
            }

        return {
            "valid": True,
            "from_state": from_state.display_name,
            "to_state": to_state.display_name,
        }
