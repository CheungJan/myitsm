"""状态机单元测试。"""

from __future__ import annotations

from app.services.state_machine import MaintenanceState, StateMachine


def test_valid_transition() -> None:
    """测试合法状态流转。"""
    assert StateMachine.can_transition(MaintenanceState.DRAFT, MaintenanceState.PLANNED)
    assert StateMachine.can_transition(MaintenanceState.PLANNED, MaintenanceState.DISPATCHED)
    assert StateMachine.can_transition(MaintenanceState.DISPATCHED, MaintenanceState.IN_PROGRESS)
    assert StateMachine.can_transition(MaintenanceState.IN_PROGRESS, MaintenanceState.COMPLETED)


def test_cancel_from_any_non_terminal() -> None:
    """测试任意非终态可取消。"""
    for state in [
        MaintenanceState.DRAFT,
        MaintenanceState.PLANNED,
        MaintenanceState.DISPATCHED,
        MaintenanceState.IN_PROGRESS,
    ]:
        assert StateMachine.can_transition(state, MaintenanceState.CANCELLED)


def test_invalid_transition() -> None:
    """测试非法状态流转。"""
    assert not StateMachine.can_transition(MaintenanceState.DRAFT, MaintenanceState.COMPLETED)
    assert not StateMachine.can_transition(MaintenanceState.COMPLETED, MaintenanceState.DRAFT)


def test_terminal_states() -> None:
    """测试终态识别。"""
    assert StateMachine.is_terminal(MaintenanceState.COMPLETED)
    assert StateMachine.is_terminal(MaintenanceState.CANCELLED)
    assert not StateMachine.is_terminal(MaintenanceState.DRAFT)


def test_from_code() -> None:
    """测试从状态码获取枚举。"""
    assert MaintenanceState.from_code("00") == MaintenanceState.DRAFT
    assert MaintenanceState.from_code("05") == MaintenanceState.COMPLETED
    assert MaintenanceState.from_code("99") is None


def test_validate_transition() -> None:
    """测试完整流转验证。"""
    result = StateMachine.validate_transition("00", "01")
    assert result["valid"] is True

    result = StateMachine.validate_transition("05", "00")
    assert result["valid"] is False

    result = StateMachine.validate_transition("99", "00")
    assert result["valid"] is False
