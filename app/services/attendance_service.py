"""考勤管理业务服务层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.repositories.attendance_repository import (
    AttendanceCountRepository,
    AttendanceRepository,
)


class AttendanceService:
    """考勤记录服务。"""

    @staticmethod
    def get(amonth: str, adate: str, operid: str) -> dict[str, Any] | None:
        record = AttendanceRepository.get_by_key(amonth, adate, operid)
        if record is None:
            return None
        return record.to_dict()

    @staticmethod
    def list_by_month(
        amonth: str,
        operid: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = AttendanceRepository.list_by_month(amonth, operid, page, per_page)
        return {
            "items": [r.to_dict() for r in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any]) -> dict[str, Any]:
        record = AttendanceRepository.create(data)
        db.session.commit()
        return record.to_dict()


class AttendanceCountService:
    """考勤汇总服务。"""

    @staticmethod
    def list_by_month(amonth: str) -> list[dict[str, Any]]:
        records = AttendanceCountRepository.list_by_month(amonth)
        return [r.to_dict() for r in records]
