"""ITSM 维修单统一状态机（对齐 PB ZT 字典码值）。"""

from __future__ import annotations

from enum import Enum

__all__ = ["MaintenanceState", "StateMachine"]


class MaintenanceState(Enum):
    """
    维修单生命周期状态（对应 CURRENT_STATUS 字段）。

    码值对齐 PB tmm31_syscodes code_typ='ZT' 字典：
    1=新建, 2=分配, 3=关闭, 4=未解决, 5=已解决, 6=转修, 7=待配件, 9=作废

    注：6=转修、7=待配件为 §7.6 四要素结构化新增状态。
    """

    NEW = "1"
    ASSIGNED = "2"
    CLOSED = "3"
    UNRESOLVED = "4"
    RESOLVED = "5"
    TRANSFERRED = "6"
    WAITING_PARTS = "7"
    CANCELLED = "9"

    @classmethod
    def from_code(cls, code: str) -> MaintenanceState | None:
        """从状态码获取枚举（支持 1 位老码和 2 位兼容码）。"""
        # 老系统 1 位码优先
        for state in cls:
            if state.value == code:
                return state
        # 兼容 2 位历史码（防止脏数据）
        compat: dict[str, str] = {
            "00": "1", "01": "2", "02": "4", "04": "2",
            "05": "5", "09": "9",
        }
        mapped = compat.get(code)
        if mapped:
            for state in cls:
                if state.value == mapped:
                    return state
        return None

    @property
    def display_name(self) -> str:
        """状态中文显示名（对齐 PB ZT 字典）。"""
        names: dict[str, str] = {
            "1": "新建",
            "2": "分配",
            "3": "关闭",
            "4": "未解决",
            "5": "已解决",
            "6": "转修",
            "7": "待配件",
            "9": "作废",
        }
        return names.get(self.value, "未知")


class StateMachine:
    """
    统一状态机。

    流转规则（对齐 PB 老系统行为 + §7.6 四要素扩展）：
        NEW(1) → ASSIGNED(2) / CANCELLED(9)
        ASSIGNED(2) → RESOLVED(5) / UNRESOLVED(4) / TRANSFERRED(6) / WAITING_PARTS(7) / CANCELLED(9)
        UNRESOLVED(4) → ASSIGNED(2) / TRANSFERRED(6) / WAITING_PARTS(7) / CLOSED(3) / CANCELLED(9)
        TRANSFERRED(6) → CLOSED(3) / RESOLVED(5) / CANCELLED(9)
        WAITING_PARTS(7) → RESOLVED(5) / UNRESOLVED(4) / CLOSED(3) / CANCELLED(9)
        RESOLVED(5) → CLOSED(3) / CANCELLED(9)
    """

    TRANSITIONS: dict[MaintenanceState, list[MaintenanceState]] = {
        MaintenanceState.NEW: [
            MaintenanceState.ASSIGNED,
            MaintenanceState.CANCELLED,
        ],
        MaintenanceState.ASSIGNED: [
            MaintenanceState.RESOLVED,
            MaintenanceState.UNRESOLVED,
            MaintenanceState.TRANSFERRED,
            MaintenanceState.WAITING_PARTS,
            MaintenanceState.CANCELLED,
        ],
        MaintenanceState.UNRESOLVED: [
            MaintenanceState.ASSIGNED,
            MaintenanceState.TRANSFERRED,
            MaintenanceState.WAITING_PARTS,
            MaintenanceState.CLOSED,
            MaintenanceState.CANCELLED,
        ],
        MaintenanceState.TRANSFERRED: [
            MaintenanceState.CLOSED,
            MaintenanceState.RESOLVED,
            MaintenanceState.CANCELLED,
        ],
        MaintenanceState.WAITING_PARTS: [
            MaintenanceState.RESOLVED,
            MaintenanceState.UNRESOLVED,
            MaintenanceState.CLOSED,
            MaintenanceState.CANCELLED,
        ],
        MaintenanceState.RESOLVED: [
            MaintenanceState.CLOSED,
            MaintenanceState.CANCELLED,
        ],
    }

    TERMINAL_STATES: set[MaintenanceState] = {
        MaintenanceState.CLOSED,
        MaintenanceState.CANCELLED,
    }

    @classmethod
    def can_transition(
        cls, from_state: MaintenanceState, to_state: MaintenanceState
    ) -> bool:
        """检查状态流转是否合法。"""
        if from_state == to_state:
            return False
        return to_state in cls.TRANSITIONS.get(from_state, [])

    @classmethod
    def get_allowed_transitions(
        cls, current_state: MaintenanceState
    ) -> list[MaintenanceState]:
        """获取当前状态允许的目标状态。"""
        return cls.TRANSITIONS.get(current_state, [])

    @classmethod
    def is_terminal(cls, state: MaintenanceState) -> bool:
        """是否为终态。"""
        return state in cls.TERMINAL_STATES

    @classmethod
    def validate_transition(
        cls, from_code: str, to_code: str
    ) -> dict[str, object]:
        """验证状态流转并返回详细信息。"""
        from_state = MaintenanceState.from_code(from_code)
        to_state = MaintenanceState.from_code(to_code)

        if from_state is None:
            return {"valid": False, "error": f"无效的原状态码: {from_code}"}
        if to_state is None:
            return {"valid": False, "error": f"无效的目标状态码: {to_code}"}
        if cls.is_terminal(from_state):
            return {
                "valid": False,
                "error": f"终态不可流转: {from_state.display_name}",
            }
        if not cls.can_transition(from_state, to_state):
            allowed = [s.value for s in cls.get_allowed_transitions(from_state)]
            return {
                "valid": False,
                "error": (
                    f"不允许从{from_state.display_name}"
                    f"流转到{to_state.display_name}"
                ),
                "allowed_transitions": allowed,
            }

        return {
            "valid": True,
            "from_state": from_state.display_name,
            "to_state": to_state.display_name,
        }

    # ------------------------------------------------------------------
    # d2d_result / closure_reason → is_success 映射（§7.6 四要素结构化）
    # ------------------------------------------------------------------
    # d2d_result（ZT 字典码值）→ is_success 映射
    D2D_RESULT_TO_IS_SUCCESS: dict[str, str] = {
        "5": "1",  # 已解决
        "4": "0",  # 未解决
        "6": "0",  # 转修
        "7": "0",  # 待配件
        "3": "0",  # 关闭（is_success 由 closure_reason 决定）
    }

    # closure_reason → is_success 映射（仅 d2d_result='3' 时使用）
    CLOSURE_REASON_TO_IS_SUCCESS: dict[str, str] = {
        "1": "1",  # 正常解决
        "2": "0",  # 客户拒修
        "3": "1",  # 非设备问题
        "4": "0",  # 重复报修
        "5": "0",  # 转其他团队
    }

    # d2d_result → ZT 字典码值名称（用于拼句）
    D2D_RESULT_NM: dict[str, str] = {
        "5": "已解决",
        "4": "未解决",
        "6": "转修",
        "7": "待配件",
        "3": "关闭",
    }

    # closure_reason → 名称（用于拼句）
    CLOSURE_REASON_NM: dict[str, str] = {
        "1": "正常解决",
        "2": "客户拒修",
        "3": "非设备问题",
        "4": "重复报修",
        "5": "转其他团队",
    }

    @classmethod
    def resolve_is_success(
        cls, d2d_result: str | None, closure_reason: str | None = None
    ) -> str:
        """根据 d2d_result 和 closure_reason 派生 is_success。

        Args:
            d2d_result: 离店结果（ZT 字典码值：5/4/6/7/3）
            closure_reason: 关闭原因（仅 d2d_result='3' 时填，CLO_REASON 字典）

        Returns:
            is_success 码值（'1'=成功 / '0'=未成功）
        """
        if d2d_result == "3" and closure_reason:
            return cls.CLOSURE_REASON_TO_IS_SUCCESS.get(closure_reason, "0")
        return cls.D2D_RESULT_TO_IS_SUCCESS.get(d2d_result or "", "0")
