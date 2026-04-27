"""客户自助服务门户模块请求/响应 Schema（Tier-2 G9）。"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 门户用户
# ---------------------------------------------------------------------------


class PortalUserCreate(BaseModel):
    """创建门户用户。"""

    portal_uid: str = Field(..., max_length=20, description="门户用户ID")
    custcd: str = Field(..., max_length=10, description="关联客户编码")
    login_name: str = Field(..., max_length=50, description="登录名")
    password: str = Field(..., max_length=128, description="密码")
    contact_name: str | None = Field(None, max_length=50, description="联系人")
    phone: str | None = Field(None, max_length=20, description="手机号")
    email: str | None = Field(None, max_length=100, description="邮箱")


class PortalUserUpdate(BaseModel):
    """更新门户用户。"""

    contact_name: str | None = Field(None, max_length=50, description="联系人")
    phone: str | None = Field(None, max_length=20, description="手机号")
    email: str | None = Field(None, max_length=100, description="邮箱")
    status: str | None = Field(None, max_length=10, description="状态")


# ---------------------------------------------------------------------------
# 自助报修
# ---------------------------------------------------------------------------


class RepairRequestCreate(BaseModel):
    """创建报修工单。"""

    request_id: str = Field(..., max_length=20, description="报修单号")
    portal_uid: str = Field(..., max_length=20, description="报修用户")
    custcd: str = Field(..., max_length=10, description="客户编码")
    eid: str | None = Field(None, max_length=50, description="设备序列号")
    fault_desc: str | None = Field(None, max_length=500, description="故障描述")
    urgency: str | None = Field("NORMAL", max_length=10, description="紧急程度")
    contact_name: str | None = Field(None, max_length=50, description="联系人")
    contact_phone: str | None = Field(None, max_length=20, description="联系电话")
    address: str | None = Field(None, max_length=200, description="服务地址")


class RepairRequestUpdate(BaseModel):
    """更新报修工单。"""

    status: str | None = Field(None, max_length=10, description="状态")
    maintenance_id: str | None = Field(None, max_length=20, description="关联维护单号")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 服务评价
# ---------------------------------------------------------------------------


class ServiceRatingCreate(BaseModel):
    """创建服务评价。"""

    request_id: str | None = Field(None, max_length=20, description="报修单号")
    maintenance_id: str | None = Field(None, max_length=20, description="维护单号")
    portal_uid: str | None = Field(None, max_length=20, description="评价用户")
    custcd: str | None = Field(None, max_length=10, description="客户编码")
    rating: int | None = Field(None, ge=1, le=5, description="评分")
    response_rating: int | None = Field(None, ge=1, le=5, description="响应速度评分")
    quality_rating: int | None = Field(None, ge=1, le=5, description="服务质量评分")
    attitude_rating: int | None = Field(None, ge=1, le=5, description="服务态度评分")
    comment: str | None = Field(None, max_length=500, description="评价内容")
