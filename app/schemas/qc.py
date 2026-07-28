"""质检管理请求/响应 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class QcCreate(BaseModel):
    """创建质检单。"""

    refbillid: str | None = Field(None, max_length=30, description="关联单号")
    itemcd: str = Field(..., max_length=6, description="物料编码")
    eid: str | None = Field(None, max_length=13, description="设备序列号")
    optyp: str | None = Field(None, max_length=2, description="操作类型(C1/YH/PJ/C2)")
    qcstatus: str | None = Field(None, max_length=2, description="质检状态")
    memo: str | None = Field(None, max_length=200, description="备注")
    details: list[dict[str, object]] | None = Field(None, description="质检明细-按产品")
    eid_details: list[dict[str, object]] | None = Field(None, description="质检明细-按设备")


class QcAudit(BaseModel):
    """质检审核请求。"""

    auditflg: str = Field("1", max_length=1, description="审核标志: 1=通过, 8=退回")
    checkmemo: str | None = Field(None, max_length=200, description="审核备注")
