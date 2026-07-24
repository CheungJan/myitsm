"""
通知/消息系统模型（Tier-1 扩展，替代飞信 TIT22_FETION_SEND）。

阶段4：统一消息发送接口，支持短信/邮件/站内通知。

对应数据库表：
  通知模板：TNTF01_TEMPLATE（新建）
  通知记录：TNTF02_NOTIFICATION（新建，替代 TIT22_FETION_SEND）
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 通知模板
# ---------------------------------------------------------------------------


class NotificationTemplate(BaseModel):
    """通知模板（TNTF01_TEMPLATE）。"""

    __tablename__ = "tntf01_template"

    template_id = db.Column(db.String(8), primary_key=True, comment="模板ID")
    template_name = db.Column(db.String(50), nullable=False, comment="模板名称")
    channel = db.Column(db.String(10), nullable=False, comment="渠道: sms/email/internal")
    subject = db.Column(db.String(200), comment="标题模板")
    body = db.Column(db.Text, comment="正文模板")
    ref_type = db.Column(db.String(20), comment="业务类型: dispatch(派工通知)/maintenance(工单通知)")
    is_default = db.Column(db.String(1), default="0", comment="是否该 ref_type 下默认: 1=是/0=否")
    sort_no = db.Column(db.Integer, default=0, comment="排序号（小优先）")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


# ---------------------------------------------------------------------------
# 通知记录
# ---------------------------------------------------------------------------


class Notification(BaseModel):
    """通知记录（TNTF02_NOTIFICATION，替代 TIT22_FETION_SEND）。"""

    __tablename__ = "tntf02_notification"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_id = db.Column(db.String(8), comment="模板ID")
    channel = db.Column(db.String(10), nullable=False, comment="渠道: sms/email/internal")
    recipient = db.Column(db.String(100), nullable=False, comment="接收方(手机/邮箱/用户ID)")
    subject = db.Column(db.String(200), comment="标题")
    body = db.Column(db.Text, comment="正文")
    ref_type = db.Column(db.String(20), comment="关联业务类型")
    ref_id = db.Column(db.String(20), comment="关联业务ID（维护单号等）")
    dispatch_id = db.Column(db.Integer, comment="关联派工记录ID（tit21_maintenance_dispatch.id，区分同一工单多次派工）")
    send_status = db.Column(
        db.String(10), default="pending", comment="发送状态: pending/sent/failed"
    )
    send_time = db.Column(db.DateTime, comment="发送时间")
    error_msg = db.Column(db.String(500), comment="错误信息")
    retry_count = db.Column(db.Integer, default=0, comment="重试次数")
    read_status = db.Column(
        db.String(10), default="unread", comment="已读状态: unread/read（站内通知专用）"
    )
    read_time = db.Column(db.DateTime, comment="已读时间（站内通知专用）")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
