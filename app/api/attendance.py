"""
考勤管理 API。

路由前缀：/api/v1/attendance
"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.schemas.attendance import AttendanceCreate
from app.services.attendance_service import AttendanceCountService, AttendanceService
from app.utils.response import error_response, success_response

__all__ = ["attendance_bp"]

attendance_bp = Blueprint("attendance", __name__)


# ---- 考勤记录 ----


@attendance_bp.get("/attendance")
@login_required
def list_attendance():  # type: ignore[no-untyped-def]
    """按月查询考勤记录。"""
    from datetime import datetime
    amonth = request.args.get("amonth", datetime.now().strftime("%Y%m"))
    operid = request.args.get("operid")
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "20"))
    data = AttendanceService.list_by_month(amonth, operid, page, per_page)
    return success_response(data=data)


@attendance_bp.post("/attendance")
@login_required
def create_attendance():  # type: ignore[no-untyped-def]
    """创建考勤记录。"""
    body = AttendanceCreate(**request.get_json(force=True))
    data = AttendanceService.create(body.model_dump(exclude_none=True))
    return success_response(data=data, message="创建成功", code=201)


@attendance_bp.post("/attendance/batch")
@login_required
def batch_import_attendance():  # type: ignore[no-untyped-def]
    """批量导入考勤记录。"""
    items = request.get_json(force=True)
    if not isinstance(items, list):
        return error_response(message="请求体为数组格式", code=400)
    created = []
    for item in items:
        body = AttendanceCreate(**item)
        record = AttendanceService.create(body.model_dump(exclude_none=True))
        created.append(record)
    return success_response(data={"created": len(created)}, message=f"成功导入 {len(created)} 条", code=201)


# ---- 考勤汇总 ----


@attendance_bp.get("/attendance/summary")
@login_required
def list_attendance_summary():  # type: ignore[no-untyped-def]
    """按月查询考勤汇总。"""
    amonth = request.args.get("amonth", "")
    if not amonth:
        return error_response(message="amonth 必填", code=400)
    data = AttendanceCountService.list_by_month(amonth)
    return success_response(data=data)
