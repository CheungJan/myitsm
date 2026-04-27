"""
客户自助服务门户模型（Tier-2 G9）。

客户侧自助操作：报修工单、费用查询、服务评价。
扩展用户认证，支持客户角色登录。

对应新增数据库表：
  客户用户：TPT01_PORTAL_USER
  自助报修工单：TPT02_REPAIR_REQUEST
  服务评价：TPT03_SERVICE_RATING
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 客户用户
# ---------------------------------------------------------------------------


class PortalUser(BaseModel):
    """客户门户用户（TPT01_PORTAL_USER）。"""

    __tablename__ = "tpt01_portal_user"

    portal_uid = db.Column(db.String(20), primary_key=True, comment="门户用户ID")
    custcd = db.Column(db.String(10), nullable=False, comment="关联客户编码")
    login_name = db.Column(db.String(50), nullable=False, unique=True, comment="登录名")
    password_hash = db.Column(db.String(128), nullable=False, comment="密码哈希")
    contact_name = db.Column(db.String(50), comment="联系人姓名")
    phone = db.Column(db.String(20), comment="手机号")
    email = db.Column(db.String(100), comment="邮箱")
    status = db.Column(
        db.String(10),
        default="ACTIVE",
        comment="状态（ACTIVE/DISABLED）",
    )
    last_login = db.Column(db.DateTime, comment="最后登录时间")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")

    _hidden_fields: set[str] = {"password_hash"}


# ---------------------------------------------------------------------------
# 自助报修工单
# ---------------------------------------------------------------------------


class RepairRequest(BaseModel):
    """客户自助报修工单（TPT02_REPAIR_REQUEST）。"""

    __tablename__ = "tpt02_repair_request"

    request_id = db.Column(db.String(20), primary_key=True, comment="报修单号")
    portal_uid = db.Column(db.String(20), nullable=False, comment="报修用户")
    custcd = db.Column(db.String(10), nullable=False, comment="客户编码")
    eid = db.Column(db.String(50), comment="设备序列号")
    fault_desc = db.Column(db.String(500), comment="故障描述")
    urgency = db.Column(
        db.String(10),
        default="NORMAL",
        comment="紧急程度（LOW/NORMAL/HIGH/URGENT）",
    )
    contact_name = db.Column(db.String(50), comment="联系人")
    contact_phone = db.Column(db.String(20), comment="联系电话")
    address = db.Column(db.String(200), comment="服务地址")
    status = db.Column(
        db.String(10),
        default="SUBMITTED",
        comment="状态（SUBMITTED/ACCEPTED/PROCESSING/COMPLETED/CANCELLED）",
    )
    maintenance_id = db.Column(db.String(20), comment="关联ITSM维护单号")
    submit_time = db.Column(db.DateTime, comment="提交时间")
    accept_time = db.Column(db.DateTime, comment="受理时间")
    complete_time = db.Column(db.DateTime, comment="完成时间")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 服务评价
# ---------------------------------------------------------------------------


class ServiceRating(BaseModel):
    """服务评价（TPT03_SERVICE_RATING）。"""

    __tablename__ = "tpt03_service_rating"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_id = db.Column(db.String(20), comment="关联报修单号")
    maintenance_id = db.Column(db.String(20), comment="关联维护单号")
    portal_uid = db.Column(db.String(20), comment="评价用户")
    custcd = db.Column(db.String(10), comment="客户编码")
    rating = db.Column(db.Integer, comment="评分（1-5星）")
    response_rating = db.Column(db.Integer, comment="响应速度评分（1-5）")
    quality_rating = db.Column(db.Integer, comment="服务质量评分（1-5）")
    attitude_rating = db.Column(db.Integer, comment="服务态度评分（1-5）")
    comment = db.Column(db.String(500), comment="评价内容")
    rating_time = db.Column(db.DateTime, comment="评价时间")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")
