"""销售管理模块请求/响应 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlanCustCreate(BaseModel):
    """创建预计划。"""

    plantyp: str = Field(..., max_length=2, description="计划类型")
    custcd: str | None = Field(None, max_length=8, description="客户编码")
    custnm: str | None = Field(None, max_length=80, description="客户名称")
    busityp: str | None = Field(None, max_length=2, description="业务类型")
    address: str | None = Field(None, max_length=80, description="地址")
    contactor: str | None = Field(None, max_length=10, description="联系人")
    phoneno: str | None = Field(None, max_length=60, description="电话")
    pos_item: str | None = Field(None, max_length=6, description="POS物料")
    is_rent: str | None = Field(None, max_length=1, description="是否租赁")


class PlanCustUpdate(BaseModel):
    """更新预计划。"""

    plan_status: str | None = Field(None, max_length=2)
    imple_status: str | None = Field(None, max_length=2)
    serve_status: str | None = Field(None, max_length=2)
    imple_date: str | None = Field(None)
    imple_mark: str | None = Field(None, max_length=200)
    imple_result: str | None = Field(None, max_length=10)
    fail_reason: str | None = Field(None, max_length=200)


class SalesBillCreate(BaseModel):
    """创建销售单据。"""

    sltyp: str = Field(..., max_length=2, description="销售类型")
    custcd: str = Field(..., max_length=8, description="客户编码")
    busityp: str | None = Field(None, max_length=2, description="业务类型")
    itemcd: str | None = Field(None, max_length=6, description="物料编码")
    rgsqty: int | None = Field(None, description="登记数量")
    memo: str | None = Field(None, max_length=255, description="备注")


class SalesExtendCreate(BaseModel):
    """创建延期。"""

    slbillid: str = Field(..., max_length=8, description="关联销售单号")
    custcd: str = Field(..., max_length=8, description="客户编码")
    busityp: str | None = Field(None, max_length=2, description="业务类型")
    sltyp: str | None = Field(None, max_length=2, description="销售类型")
    itemcd: str | None = Field(None, max_length=6, description="物料编码")
    backup: str | None = Field(None, max_length=255, description="备注")


class SalesExtendDetailCreate(BaseModel):
    """延期明细。"""

    custcd: str = Field(..., max_length=8, description="客户编码")
    custcard: str | None = Field(None, max_length=20, description="客户磁卡号")
    eid: str | None = Field(None, max_length=13, description="设备EID")
    planqty: int | None = Field(None, description="计划数量")


class SalesQuery(BaseModel):
    """销售查询参数。"""

    plantyp: str | None = Field(None, max_length=2)
    plan_status: str | None = Field(None, max_length=2)
    sltyp: str | None = Field(None, max_length=2)
    custcd: str | None = Field(None, max_length=8)
    auditflg: str | None = Field(None, max_length=1)
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
