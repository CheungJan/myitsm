"""ITSM 维修单统一状态机（优化方案5）。"""

from __future__ import annotations

from enum import Enum

__all__ = ["MaintenanceState", "StateMachine"]


class MaintenanceState(Enum):
    """
    维修单生命周期状态（对应 CURRENT_STATUS 字段）。

    状态码与 PB 原系统保持一致。
    """

    DRAFT = "00"
    PLANNED = "01"
    IN_PROGRESS = "02"
    DISPATCHED = "04"
    COMPLETED = "05"
    CANCELLED = "09"

    @classmethod
    def from_code(cls, code: str) -> MaintenanceState | None:
        """从状态码获取枚举。"""
        for state in cls:
            if state.value == code:
                return state
        return None

    @property
    def display_name(self) -> str:
        """状态中文显示名。"""
        names: dict[str, str] = {
            "00": "草稿",
            "01": "已计划",
            "02": "实施中",
            "04": "已派工",
            "05": "已完成",
            "09": "已取消",
        }
        return names.get(self.value, "未知")


class StateMachine:
    """
    统一状态机。

    流转规则：
        DRAFT → PLANNED / CANCELLED
        PLANNED → DISPATCHED / CANCELLED
        DISPATCHED → IN_PROGRESS / CANCELLED
        IN_PROGRESS → COMPLETED / CANCELLED
    """

    TRANSITIONS: dict[MaintenanceState, list[MaintenanceState]] = {
        MaintenanceState.DRAFT: [MaintenanceState.PLANNED, MaintenanceState.CANCELLED],
        MaintenanceState.PLANNED: [MaintenanceState.DISPATCHED, MaintenanceState.CANCELLED],
        MaintenanceState.DISPATCHED: [MaintenanceState.IN_PROGRESS, MaintenanceState.CANCELLED],
        MaintenanceState.IN_PROGRESS: [MaintenanceState.COMPLETED, MaintenanceState.CANCELLED],
    }

    TERMINAL_STATES: set[MaintenanceState] = {
        MaintenanceState.COMPLETED,
        MaintenanceState.CANCELLED,
    }

    @classmethod
    def can_transition(cls, from_state: MaintenanceState, to_state: MaintenanceState) -> bool:
        """检查状态流转是否合法。"""
        if from_state == to_state:
            return False
        return to_state in cls.TRANSITIONS.get(from_state, [])

    @classmethod
    def get_allowed_transitions(cls, current_state: MaintenanceState) -> list[MaintenanceState]:
        """获取当前状态允许的目标状态。"""
        return cls.TRANSITIONS.get(current_state, [])

    @classmethod
    def is_terminal(cls, state: MaintenanceState) -> bool:
        """是否为终态。"""
        return state in cls.TERMINAL_STATES

    @classmethod
    def validate_transition(cls, from_code: str, to_code: str) -> dict[str, object]:
        """验证状态流转并返回详细信息。"""
        from_state = MaintenanceState.from_code(from_code)
        to_state = MaintenanceState.from_code(to_code)

        if from_state is None:
            return {"valid": False, "error": f"无效的原状态码: {from_code}"}
        if to_state is None:
            return {"valid": False, "error": f"无效的目标状态码: {to_code}"}
        if cls.is_terminal(from_state):
            return {"valid": False, "error": f"终态不可流转: {from_state.display_name}"}
        if not cls.can_transition(from_state, to_state):
            allowed = [s.value for s in cls.get_allowed_transitions(from_state)]
            return {
                "valid": False,
                "error": f"不允许从{from_state.display_name}流转到{to_state.display_name}",
                "allowed_transitions": allowed,
            }

        return {
            "valid": True,
            "from_state": from_state.display_name,
            "to_state": to_state.display_name,
        }
