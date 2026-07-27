"""通知/消息系统模块请求/响应 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class NotificationTemplateCreate(BaseModel):
    """创建通知模板。"""

    template_id: str | None = Field(None, max_length=8, description="模板ID")
    template_name: str = Field(..., max_length=50, description="模板名称")
    channel: str = Field(..., max_length=10, description="渠道: sms/email/internal")
    subject: str | None = Field(None, max_length=200, description="标题模板")
    body: str | None = Field(None, description="正文模板")
    ref_type: str | None = Field(None, max_length=20, description="业务类型: dispatch/maintenance/renovate/open/change/recycle")
    is_default: str | None = Field(None, max_length=1, description="是否默认: 1/0")
    sort_no: int | None = Field(None, description="排序号")


class NotificationTemplateUpdate(BaseModel):
    """更新通知模板。"""

    template_name: str | None = Field(None, max_length=50, description="模板名称")
    channel: str | None = Field(None, max_length=10, description="渠道")
    subject: str | None = Field(None, max_length=200, description="标题模板")
    body: str | None = Field(None, description="正文模板")
    ref_type: str | None = Field(None, max_length=20, description="业务类型")
    is_default: str | None = Field(None, max_length=1, description="是否默认: 1/0")
    sort_no: int | None = Field(None, description="排序号")
    useflg: str | None = Field(None, max_length=1, description="有效标志: 1/0")


class NotificationCreate(BaseModel):
    """创建通知记录。"""

    template_id: str | None = Field(None, max_length=8, description="模板ID")
    channel: str = Field(..., max_length=10, description="渠道: sms/email/internal")
    recipient: str = Field(..., max_length=100, description="接收方")
    subject: str | None = Field(None, max_length=200, description="标题")
    body: str | None = Field(None, description="正文")
    ref_type: str | None = Field(None, max_length=20, description="关联业务类型")
    ref_id: str | None = Field(None, max_length=20, description="关联业务ID")
