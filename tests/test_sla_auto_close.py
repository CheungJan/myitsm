"""SLA 超时自动关单测试。

验证：
  - status=5 且 close_time 超过 SLA 配置天数 → 自动 transition(3)
  - status=5 且 close_time 未超时 → 不关单
  - status=3（已关闭）→ 不处理
  - tmm31_syscodes SLA/close_days 配置生效
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from flask import Flask

from app.extensions import db
from app.models.itsm import MaintenanceDaily
from app.models.master import SysCode
from app.repositories.itsm_repository import MaintenanceDailyRepository
from app.services.itsm_service import MaintenanceDailyService
from app.services.sla_auto_close_service import (
    DEFAULT_SLA_CLOSE_DAYS,
    SLA_CLOSE_DAYS_CD,
    SLA_CODE_TYP,
    SlaAutoCloseService,
)


def _seed_daily(store_id: str = "CUSTV2") -> MaintenanceDaily:
    record = MaintenanceDailyRepository.create(
        {
            "store_id": store_id,
            "fault_type": "01",
            "short_description": "测试 SLA 自动关单",
        },
        "T00001",
    )
    # 流转 1→2→5
    MaintenanceDailyService().transition(record.maintenance_id, "2", "T00001")
    MaintenanceDailyService().transition(record.maintenance_id, "5", "T00001")
    return record


def _set_sla_close_days(days: int) -> None:
    code = (
        db.session.query(SysCode)
        .filter_by(code_typ=SLA_CODE_TYP, code_cd=SLA_CLOSE_DAYS_CD)
        .first()
    )
    if code is None:
        code = SysCode(
            code_typ=SLA_CODE_TYP,
            code_cd=SLA_CLOSE_DAYS_CD,
            code_nm="回访超时自动关单天数",
            memo=str(days),
            useflg="1",
        )
        db.session.add(code)
    else:
        code.memo = str(days)
    db.session.commit()


class TestSlaAutoClose:
    """SLA 超时自动关单。"""

    def test_overdue_closed(self, app: Flask) -> None:
        """超时未回访 → 自动关单。"""
        with app.app_context():
            _set_sla_close_days(3)
            daily = _seed_daily()
            # 模拟 close_time 为 5 天前（超过 3 天）
            db.session.refresh(daily)
            daily.close_time = datetime.now(UTC) - timedelta(days=5)
            db.session.commit()

            result = SlaAutoCloseService.scan_and_close()

            assert result["scanned"] >= 1
            assert result["closed"] >= 1
            db.session.refresh(daily)
            assert daily.current_status == "3", "超时应自动关单为 3"

    def test_not_overdue_not_closed(self, app: Flask) -> None:
        """未超时 → 不关单。"""
        with app.app_context():
            _set_sla_close_days(3)
            daily = _seed_daily()
            db.session.refresh(daily)
            daily.close_time = datetime.now(UTC) - timedelta(days=1)
            db.session.commit()

            SlaAutoCloseService.scan_and_close()

            db.session.refresh(daily)
            assert daily.current_status == "5", "未超时应保持 5"

    def test_already_closed_not_processed(self, app: Flask) -> None:
        """status=3（已关闭）→ 不处理。"""
        with app.app_context():
            _set_sla_close_days(3)
            daily = _seed_daily()
            MaintenanceDailyService().transition(daily.maintenance_id, "3", "T00001")
            db.session.refresh(daily)
            daily.close_time = datetime.now(UTC) - timedelta(days=10)
            db.session.commit()

            SlaAutoCloseService.scan_and_close()

            db.session.refresh(daily)
            assert daily.current_status == "3", "已关闭应保持 3"

    def test_syscode_config_effective(self, app: Flask) -> None:
        """tmm31_syscodes SLA/close_days 配置生效。"""
        with app.app_context():
            _set_sla_close_days(10)
            daily = _seed_daily()
            db.session.refresh(daily)
            daily.close_time = datetime.now(UTC) - timedelta(days=5)
            db.session.commit()

            SlaAutoCloseService.scan_and_close()

            db.session.refresh(daily)
            assert daily.current_status == "5", "5天未超10天配置，应保持 5"

    def test_default_days_when_no_syscode(self, app: Flask) -> None:
        """无 SLA/close_days 时使用默认 3 天。"""
        with app.app_context():
            code = (
                db.session.query(SysCode)
                .filter_by(code_typ=SLA_CODE_TYP, code_cd=SLA_CLOSE_DAYS_CD)
                .first()
            )
            if code is not None:
                db.session.delete(code)
                db.session.commit()

            days = SlaAutoCloseService._get_sla_close_days()
            assert days == DEFAULT_SLA_CLOSE_DAYS

    def test_preview_overdue(self, app: Flask) -> None:
        """preview_overdue 返回超时单据列表。"""
        with app.app_context():
            _set_sla_close_days(3)
            daily = _seed_daily()
            db.session.refresh(daily)
            daily.close_time = datetime.now(UTC) - timedelta(days=5)
            db.session.commit()

            preview = SlaAutoCloseService.preview_overdue()

            assert len(preview) >= 1
            item = next(p for p in preview if p["maintenance_id"] == daily.maintenance_id)
            assert item["overdue_days"] >= 5
            assert item["sla_close_days"] == 3
