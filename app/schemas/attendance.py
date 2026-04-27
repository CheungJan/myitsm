"""考勤管理模块请求/响应 Schema。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class AttendanceCreate(BaseModel):
    """创建考勤记录。"""

    amonth: str = Field(..., max_length=6, description="考勤月份")
    adate: date = Field(..., description="考勤日期")
    operid: str = Field(..., max_length=6, description="员工ID")
    opernm: str | None = Field(None, max_length=12, description="员工姓名")
    arr_time: datetime | None = Field(None, description="上班时间")
    leave_time: datetime | None = Field(None, description="下班时间")
    latecount: int | None = Field(None, description="迟到时长(分钟)")
    leavecount: int | None = Field(None, description="早退时长(分钟)")
    punchnum: int | None = Field(None, description="打卡次数")
    punchdetail: str | None = Field(None, max_length=100, description="打卡明细")
    week: str | None = Field(None, max_length=2, description="星期")
