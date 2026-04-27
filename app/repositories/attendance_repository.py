"""考勤管理数据访问层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.attendance import Attendance, AttendanceCount


class AttendanceRepository:
    """考勤记录数据访问。"""

    @staticmethod
    def get_by_key(amonth: str, adate: str, operid: str) -> Attendance | None:
        return db.session.get(Attendance, (amonth, adate, operid))

    @staticmethod
    def list_by_month(
        amonth: str,
        operid: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Attendance], int]:
        query = db.session.query(Attendance).filter(
            Attendance.amonth == amonth,
            Attendance.useflg == "1",
        )
        if operid:
            query = query.filter(Attendance.operid == operid)
        query = query.order_by(Attendance.adate)
        total: int = query.count()
        items: list[Attendance] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def create(data: dict[str, Any]) -> Attendance:
        record = Attendance(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: Attendance, data: dict[str, Any]) -> Attendance:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        return record


class AttendanceCountRepository:
    """考勤汇总数据访问。"""

    @staticmethod
    def get_by_key(amonth: str, operid: str) -> AttendanceCount | None:
        return db.session.get(AttendanceCount, (amonth, operid))

    @staticmethod
    def list_by_month(amonth: str) -> list[AttendanceCount]:
        return (
            db.session.query(AttendanceCount)
            .filter(AttendanceCount.amonth == amonth, AttendanceCount.useflg == "1")
            .order_by(AttendanceCount.operid)
            .all()
        )

    @staticmethod
    def create(data: dict[str, Any]) -> AttendanceCount:
        record = AttendanceCount(**data)
        db.session.add(record)
        return record

    @staticmethod
    def update(record: AttendanceCount, data: dict[str, Any]) -> AttendanceCount:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        return record
