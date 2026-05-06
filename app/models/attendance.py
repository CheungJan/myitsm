"""
考勤管理模型。

阶段4：考勤记录 + 考勤汇总报表。

对应数据库表：
  考勤记录：TKQ01_ATTENDANCE
  考勤汇总：TKQ02_ATTENDANCECOUNT
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 考勤记录
# ---------------------------------------------------------------------------


class Attendance(BaseModel):
    """考勤记录（TKQ01_ATTENDANCE）。"""

    __tablename__ = "tkq01_attendance"
    __table_args__ = (db.PrimaryKeyConstraint("amonth", "adate", "operid"),)

    amonth = db.Column(db.String(6), nullable=False, comment="考勤月份")
    adate = db.Column(db.Date, nullable=False, comment="考勤日期")
    operid = db.Column(db.String(6), nullable=False, comment="员工ID")
    opernm = db.Column(db.String(12), comment="员工姓名")
    arr_time = db.Column(db.DateTime, comment="上班时间")
    leave_time = db.Column(db.DateTime, comment="下班时间")
    latecount = db.Column(db.Integer, default=0, comment="迟到时长(分钟)")
    leavecount = db.Column(db.Integer, default=0, comment="早退时长(分钟)")
    punchnum = db.Column(db.Integer, default=0, comment="打卡次数")
    punchdetail = db.Column(db.String(100), comment="打卡明细")
    imp_num = db.Column(db.Integer, default=0, comment="导入次数")
    week = db.Column(db.String(2), comment="星期")
    useflg = db.Column(db.String(1), default="1", comment="有效标记")
    imp_date = db.Column(db.DateTime, comment="导入日期")
    # --- Oracle 原表恢复字段 ---
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(10), comment="更新人")


# ---------------------------------------------------------------------------
# 考勤汇总
# ---------------------------------------------------------------------------


class AttendanceCount(BaseModel):
    """考勤汇总报表（TKQ02_ATTENDANCECOUNT）。"""

    __tablename__ = "tkq02_attendancecount"
    __table_args__ = (db.PrimaryKeyConstraint("amonth", "operid"),)

    amonth = db.Column(db.String(6), nullable=False, comment="考勤月份")
    operid = db.Column(db.String(6), nullable=False, comment="员工ID")
    opernm = db.Column(db.String(12), comment="员工姓名")
    d1 = db.Column(db.String(12), comment="1号")
    d2 = db.Column(db.String(12), comment="2号")
    d3 = db.Column(db.String(12), comment="3号")
    d4 = db.Column(db.String(12), comment="4号")
    d5 = db.Column(db.String(12), comment="5号")
    d6 = db.Column(db.String(12), comment="6号")
    d7 = db.Column(db.String(12), comment="7号")
    d8 = db.Column(db.String(12), comment="8号")
    d9 = db.Column(db.String(12), comment="9号")
    d10 = db.Column(db.String(12), comment="10号")
    d11 = db.Column(db.String(12), comment="11号")
    d12 = db.Column(db.String(12), comment="12号")
    d13 = db.Column(db.String(12), comment="13号")
    d14 = db.Column(db.String(12), comment="14号")
    d15 = db.Column(db.String(12), comment="15号")
    d16 = db.Column(db.String(12), comment="16号")
    d17 = db.Column(db.String(12), comment="17号")
    d18 = db.Column(db.String(12), comment="18号")
    d19 = db.Column(db.String(12), comment="19号")
    d20 = db.Column(db.String(12), comment="20号")
    d21 = db.Column(db.String(12), comment="21号")
    d22 = db.Column(db.String(12), comment="22号")
    d23 = db.Column(db.String(12), comment="23号")
    d24 = db.Column(db.String(12), comment="24号")
    d25 = db.Column(db.String(12), comment="25号")
    d26 = db.Column(db.String(12), comment="26号")
    d27 = db.Column(db.String(12), comment="27号")
    d28 = db.Column(db.String(12), comment="28号")
    d29 = db.Column(db.String(12), comment="29号")
    d30 = db.Column(db.String(12), comment="30号")
    d31 = db.Column(db.String(12), comment="31号")
    latecount = db.Column(db.Integer, default=0, comment="迟到次数")
    leavecount = db.Column(db.Integer, default=0, comment="早退次数")
    absentcount = db.Column(db.Integer, default=0, comment="缺勤次数")
    useflg = db.Column(db.String(1), default="1", comment="有效标记")
    # --- Oracle 原表恢复字段（5个） ---
    memo = db.Column(db.String(200), comment="备注")
    imp_num = db.Column(db.Integer, comment="导入次数")
    imp_date = db.Column(db.DateTime, comment="导入日期")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(10), comment="更新人")
