"""
ITSM 业务模型。

对应数据库表：TIT10_MAINTENANCEDAY, TIT10_MAIN_TRACK, TIT10_POS_DETAIL,
TIT13_MAINTENANCE_OPEN, TIT15_MAINTENANCE_RENOVATE,
TIT16_DEVICE_CHANGE, TIT18_STORE_CLOSE

主子表关系参见 AGENTS.md「ITSM业务表结构约定」。
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class MaintenanceDaily(BaseModel):
    """
    日常维护单主表（TIT10_MAINTENANCEDAY）。

    CURRENT_STATUS 状态码：
        00=草稿, 01=已计划, 04=已派工, 02=实施中, 05=已完成, 09=已取消
    """

    __tablename__ = "tit10_maintenanceday"

    maintenance_id = db.Column(db.String(30), primary_key=True, comment="维护单号")
    plan_id = db.Column(db.String(30), comment="关联计划单号")
    plan_typ = db.Column(db.String(10), comment="计划类型")
    cust_cd = db.Column(db.String(20), comment="客户编码")
    area_cd = db.Column(db.String(20), comment="区域编码")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    source_type = db.Column(
        db.String(10),
        comment="来源类型（DAILY=日常维护/RECYCLE=取机回收）",
    )
    oper_cd = db.Column(db.String(20), comment="操作员")
    oper_date = db.Column(db.DateTime, comment="操作时间")
    dispatch_cd = db.Column(db.String(20), comment="派工人员")
    dispatch_date = db.Column(db.DateTime, comment="派工时间")
    complete_date = db.Column(db.DateTime, comment="完成时间")
    remark = db.Column(db.Text, comment="备注")

    tracks = db.relationship("MaintenanceDailyTrack", back_populates="maintenance", lazy="dynamic")
    pos_details = db.relationship("PosDetail", back_populates="maintenance", lazy="dynamic")


class MaintenanceDailyTrack(BaseModel):
    """日常维护单状态变更轨迹（TIT10_MAIN_TRACK）。"""

    __tablename__ = "tit10_main_track"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(
        db.String(30),
        db.ForeignKey("tit10_maintenanceday.maintenance_id"),
        nullable=False,
    )
    from_status = db.Column(db.String(2), comment="原状态")
    to_status = db.Column(db.String(2), comment="目标状态")
    oper_cd = db.Column(db.String(20), comment="操作员")
    oper_date = db.Column(db.DateTime, comment="操作时间")
    remark = db.Column(db.String(200), comment="备注")

    maintenance = db.relationship("MaintenanceDaily", back_populates="tracks")


class PosDetail(BaseModel):
    """维护单换机配件明细（TIT10_POS_DETAIL）。"""

    __tablename__ = "tit10_pos_detail"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(
        db.String(30),
        db.ForeignKey("tit10_maintenanceday.maintenance_id"),
        nullable=False,
    )
    item_cd = db.Column(db.String(20), comment="物料编码")
    item_nm = db.Column(db.String(100), comment="物料名称")
    old_eid = db.Column(db.String(50), comment="旧设备序列号")
    new_eid = db.Column(db.String(50), comment="新设备序列号")
    qty = db.Column(db.Numeric(10, 2), default=1, comment="数量")

    maintenance = db.relationship("MaintenanceDaily", back_populates="pos_details")


class MaintenanceOpen(BaseModel):
    """新机开通维护单表（TIT13_MAINTENANCE_OPEN）。"""

    __tablename__ = "tit13_maintenance_open"

    opening_id = db.Column(db.String(30), primary_key=True, comment="开通单号")
    plan_id = db.Column(db.String(30), comment="关联计划单号")
    cust_cd = db.Column(db.String(20), comment="客户编码")
    area_cd = db.Column(db.String(20), comment="区域编码")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    oper_cd = db.Column(db.String(20), comment="操作员")
    oper_date = db.Column(db.DateTime, comment="操作时间")
    complete_date = db.Column(db.DateTime, comment="完成时间")
    remark = db.Column(db.Text, comment="备注")


class MaintenanceRenovate(BaseModel):
    """旧机翻新维护单（TIT15_MAINTENANCE_RENOVATE）。"""

    __tablename__ = "tit15_maintenance_renovate"

    renovate_id = db.Column(db.String(30), primary_key=True, comment="翻新单号")
    plan_id = db.Column(db.String(30), comment="关联计划单号")
    cust_cd = db.Column(db.String(20), comment="客户编码")
    area_cd = db.Column(db.String(20), comment="区域编码")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    oper_cd = db.Column(db.String(20), comment="操作员")
    oper_date = db.Column(db.DateTime, comment="操作时间")
    complete_date = db.Column(db.DateTime, comment="完成时间")
    remark = db.Column(db.Text, comment="备注")


class DeviceChange(BaseModel):
    """
    设备变更单（TIT16_DEVICE_CHANGE）。

    CHANGE_TYPE: CK=改磁卡号, BQ=信息变更, BG=设备变更
    """

    __tablename__ = "tit16_device_change"

    change_id = db.Column(db.String(30), primary_key=True, comment="变更单号")
    cust_cd = db.Column(db.String(20), comment="客户编码")
    change_type = db.Column(db.String(10), comment="变更类型（CK/BQ/BG）")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    oper_cd = db.Column(db.String(20), comment="操作员")
    oper_date = db.Column(db.DateTime, comment="操作时间")
    complete_date = db.Column(db.DateTime, comment="完成时间")
    remark = db.Column(db.Text, comment="备注")


class StoreClose(BaseModel):
    """门店关闭表（TIT18_STORE_CLOSE）。"""

    __tablename__ = "tit18_store_close"

    close_id = db.Column(db.String(30), primary_key=True, comment="关闭单号")
    cust_cd = db.Column(db.String(20), comment="客户编码")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    close_reason = db.Column(db.String(200), comment="关闭原因")
    oper_cd = db.Column(db.String(20), comment="操作员")
    oper_date = db.Column(db.DateTime, comment="操作时间")
    complete_date = db.Column(db.DateTime, comment="完成时间")
    remark = db.Column(db.Text, comment="备注")
