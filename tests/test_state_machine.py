"""状态机单元测试（对齐 PB ZT 字典码值）。"""

from __future__ import annotations

from app.services.state_machine import MaintenanceState, StateMachine


def test_valid_transition() -> None:
    """测试合法状态流转。"""
    assert StateMachine.can_transition(MaintenanceState.NEW, MaintenanceState.ASSIGNED)
    assert StateMachine.can_transition(MaintenanceState.ASSIGNED, MaintenanceState.RESOLVED)
    assert StateMachine.can_transition(MaintenanceState.ASSIGNED, MaintenanceState.UNRESOLVED)
    assert StateMachine.can_transition(MaintenanceState.RESOLVED, MaintenanceState.CLOSED)
    assert StateMachine.can_transition(MaintenanceState.UNRESOLVED, MaintenanceState.ASSIGNED)
    # P1-3: RESOLVED → ASSIGNED（重新打开）
    assert StateMachine.can_transition(MaintenanceState.RESOLVED, MaintenanceState.ASSIGNED)


def test_cancel_from_any_non_terminal() -> None:
    """测试任意非终态可取消。"""
    for state in [
        MaintenanceState.NEW,
        MaintenanceState.ASSIGNED,
        MaintenanceState.UNRESOLVED,
        MaintenanceState.RESOLVED,
    ]:
        assert StateMachine.can_transition(state, MaintenanceState.CANCELLED)


def test_invalid_transition() -> None:
    """测试非法状态流转。"""
    assert not StateMachine.can_transition(MaintenanceState.NEW, MaintenanceState.CLOSED)
    assert not StateMachine.can_transition(MaintenanceState.CLOSED, MaintenanceState.NEW)


def test_terminal_states() -> None:
    """测试终态识别。"""
    assert StateMachine.is_terminal(MaintenanceState.CLOSED)
    assert StateMachine.is_terminal(MaintenanceState.CANCELLED)
    assert not StateMachine.is_terminal(MaintenanceState.NEW)


def test_from_code() -> None:
    """测试从状态码获取枚举（PB 1 位码）。"""
    assert MaintenanceState.from_code("1") == MaintenanceState.NEW
    assert MaintenanceState.from_code("3") == MaintenanceState.CLOSED
    assert MaintenanceState.from_code("5") == MaintenanceState.RESOLVED
    assert MaintenanceState.from_code("9") == MaintenanceState.CANCELLED
    assert MaintenanceState.from_code("99") is None
    # 兼容旧 2 位码
    assert MaintenanceState.from_code("00") == MaintenanceState.NEW
    assert MaintenanceState.from_code("05") == MaintenanceState.RESOLVED


def test_validate_transition() -> None:
    """测试完整流转验证（PB 1 位码）。"""
    result = StateMachine.validate_transition("1", "2")
    assert result["valid"] is True

    result = StateMachine.validate_transition("3", "1")
    assert result["valid"] is False

    result = StateMachine.validate_transition("99", "1")
    assert result["valid"] is False


# ---------------------------------------------------------------------------
# 阶段 3 回归测试：P0-1/P0-2/P1-3 修正后状态机行为
# ---------------------------------------------------------------------------


def test_resolved_to_assigned_reopen() -> None:
    """P1-3: RESOLVED(5) → ASSIGNED(2) 重新打开合法。"""
    assert StateMachine.can_transition(MaintenanceState.RESOLVED, MaintenanceState.ASSIGNED)
    result = StateMachine.validate_transition("5", "2")
    assert result["valid"] is True


def test_resolved_to_cancelled() -> None:
    """RESOLVED(5) → CANCELLED(9) 作废合法。"""
    assert StateMachine.can_transition(MaintenanceState.RESOLVED, MaintenanceState.CANCELLED)
    result = StateMachine.validate_transition("5", "9")
    assert result["valid"] is True


def test_assigned_to_resolved_complete() -> None:
    """ASSIGNED(2) → RESOLVED(5) 完成维修合法（唯一关单入口）。"""
    assert StateMachine.can_transition(MaintenanceState.ASSIGNED, MaintenanceState.RESOLVED)
    result = StateMachine.validate_transition("2", "5")
    assert result["valid"] is True


def test_closed_terminal_protection() -> None:
    """PB 历史 status='3'（CLOSED）终态保护，不可流转。"""
    # 3→5 不可（终态）
    assert not StateMachine.can_transition(MaintenanceState.CLOSED, MaintenanceState.RESOLVED)
    result = StateMachine.validate_transition("3", "5")
    assert result["valid"] is False
    # 3→2 不可（终态）
    result = StateMachine.validate_transition("3", "2")
    assert result["valid"] is False
    # 3→9 不可（终态）
    result = StateMachine.validate_transition("3", "9")
    assert result["valid"] is False


def test_cancelled_terminal_protection() -> None:
    """status='9'（CANCELLED）终态保护，不可流转。"""
    result = StateMachine.validate_transition("9", "5")
    assert result["valid"] is False
    result = StateMachine.validate_transition("9", "2")
    assert result["valid"] is False


def test_resolved_not_terminal() -> None:
    """P0-2: RESOLVED(5) 不是终态（可重新打开/作废）。"""
    assert not StateMachine.is_terminal(MaintenanceState.RESOLVED)


def test_pb_history_status_3_compatible() -> None:
    """PB 历史数据兼容：status='3' 保留原值，ZT 字典翻译为'已关单'。"""
    # from_code('3') 仍返回 CLOSED
    assert MaintenanceState.from_code("3") == MaintenanceState.CLOSED
    # CLOSED 是终态
    assert StateMachine.is_terminal(MaintenanceState.CLOSED)
    # display_name 对齐 PB ZT 字典
    assert MaintenanceState.CLOSED.display_name == "关闭"


def test_resolved_allowed_transitions() -> None:
    """P1-3: RESOLVED 允许的目标状态 = [ASSIGNED, CLOSED, CANCELLED]。"""
    allowed = StateMachine.get_allowed_transitions(MaintenanceState.RESOLVED)
    assert set(allowed) == {
        MaintenanceState.ASSIGNED,
        MaintenanceState.CLOSED,
        MaintenanceState.CANCELLED,
    }
