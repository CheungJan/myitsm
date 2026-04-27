"""
SLA 服务级别管理模型（Tier-1 扩展）。

基于 TIT01_TIMEPOINT_AREA 已有响应时间等级表，扩展完整 SLA 管理体系：
- SLA 定义（服务级别协议模板）
- SLA 工单监控（跟踪响应/解决时间达标率）

注：TIT01_TIMEPOINT_AREA 已在 itsm.py 中定义（TimepointArea），此处复用不重复定义。
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# SLA 定义
# ---------------------------------------------------------------------------


class SlaDefinition(BaseModel):
    """SLA 服务级别定义。

    基于 TIT01_TIMEPOINT_AREA 的响应等级，定义完整的 SLA 协议。
    包含响应时间、解决时间上限，以及违约处理规则。
    """

    __tablename__ = "sla_definition"

    sla_id = db.Column(db.String(8), primary_key=True, comment="SLA编号")
    sla_name = db.Column(db.String(60), nullable=False, comment="SLA名称")
    levels = db.Column(db.String(2), comment="关联响应等级（TIT01.LEVELS）")
    priority = db.Column(db.String(1), comment="优先级（1高/2中/3低）")
    response_minutes = db.Column(db.Integer, nullable=False, comment="响应时限（分钟）")
    resolve_minutes = db.Column(db.Integer, nullable=False, comment="解决时限（分钟）")
    escalation_minutes = db.Column(db.Integer, comment="升级时限（分钟）")
    business_hours_only = db.Column(db.Boolean, default=True, comment="是否仅计算工作时间")
    description = db.Column(db.String(200), comment="SLA描述")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    tickets = db.relationship("SlaTicket", back_populates="sla_def", lazy="dynamic")


# ---------------------------------------------------------------------------
# SLA 工单监控
# ---------------------------------------------------------------------------


class SlaTicket(BaseModel):
    """SLA 工单监控记录。

    每个 ITSM 工单创建时自动关联 SLA 定义，跟踪响应/解决时间。
    """

    __tablename__ = "sla_ticket"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sla_id = db.Column(
        db.String(8),
        db.ForeignKey("sla_definition.sla_id"),
        nullable=False,
        comment="SLA编号",
    )
    maintenance_id = db.Column(db.String(8), nullable=False, comment="维护单ID")
    maintenance_type = db.Column(db.String(10), nullable=False, comment="单据类型")
    sla_status = db.Column(
        db.String(2), default="00", comment="SLA状态（00正常/01预警/02违约/99关闭）"
    )
    created_time = db.Column(db.DateTime, nullable=False, comment="工单创建时间")
    first_response_time = db.Column(db.DateTime, comment="首次响应时间")
    resolved_time = db.Column(db.DateTime, comment="解决时间")
    response_met = db.Column(db.Boolean, comment="响应是否达标")
    resolve_met = db.Column(db.Boolean, comment="解决是否达标")
    response_elapsed_minutes = db.Column(db.Integer, comment="响应耗时（分钟）")
    resolve_elapsed_minutes = db.Column(db.Integer, comment="解决耗时（分钟）")
    escalated = db.Column(db.Boolean, default=False, comment="是否已升级")
    escalation_time = db.Column(db.DateTime, comment="升级时间")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    sla_def = db.relationship("SlaDefinition", back_populates="tickets")
