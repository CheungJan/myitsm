"""SLA 服务级别管理模块请求/响应 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SlaDefinitionCreate(BaseModel):
    """创建SLA定义。"""

    sla_name: str = Field(..., max_length=60, description="SLA名称")
    levels: str | None = Field(None, max_length=2, description="关联响应等级")
    priority: str = Field(..., max_length=1, description="优先级（1高/2中/3低）")
    response_minutes: int = Field(..., ge=1, description="响应时限（分钟）")
    resolve_minutes: int = Field(..., ge=1, description="解决时限（分钟）")
    escalation_minutes: int | None = Field(None, description="升级时限（分钟）")
    business_hours_only: bool = Field(True, description="是否仅计工作时间")
    description: str | None = Field(None, max_length=200, description="描述")


class SlaDefinitionUpdate(BaseModel):
    """更新SLA定义。"""

    sla_name: str | None = Field(None, max_length=60)
    response_minutes: int | None = Field(None, ge=1)
    resolve_minutes: int | None = Field(None, ge=1)
    escalation_minutes: int | None = None
    business_hours_only: bool | None = None
    description: str | None = Field(None, max_length=200)


class SlaAttachRequest(BaseModel):
    """为工单绑定SLA。"""

    maintenance_id: str = Field(..., max_length=8, description="维护单ID")
    maintenance_type: str = Field(..., max_length=10, description="单据类型")
    priority: str = Field(..., max_length=1, description="优先级")


class SlaResponseRequest(BaseModel):
    """记录SLA首次响应。"""

    maintenance_id: str = Field(..., max_length=8, description="维护单ID")
    maintenance_type: str = Field(..., max_length=10, description="单据类型")


class SlaTicketQuery(BaseModel):
    """SLA工单查询参数。"""

    sla_status: str | None = Field(None, max_length=2)
    sla_id: str | None = Field(None, max_length=8)
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
