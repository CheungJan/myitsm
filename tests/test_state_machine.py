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
