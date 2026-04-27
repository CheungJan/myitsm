"""采购管理模块请求/响应 Schema。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PurchasePlanCreate(BaseModel):
    """创建采购计划。"""

    pctyp: str | None = Field(None, max_length=1, description="采购类型")
    slbillid: str | None = Field(None, max_length=8, description="关联销售单号")
    plandate: datetime | None = Field(None, description="计划日期")
    memo: str | None = Field(None, max_length=255, description="备注")


class PurchasePlanDetailCreate(BaseModel):
    """采购计划明细。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    rgstqty: int = Field(..., ge=1, description="登记数量")
    units: str | None = Field(None, max_length=4, description="单位")


class PurchaseRegisterCreate(BaseModel):
    """创建采购登记。"""

    suppliercd: str = Field(..., max_length=8, description="供应商编码")
    pcrep: str | None = Field(None, max_length=6, description="采购代表")
    rgstdate: datetime | None = Field(None, description="登记日期")
    memo: str | None = Field(None, max_length=255, description="备注")


class PurchaseRegisterDetailCreate(BaseModel):
    """采购登记明细。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    rgsqty: int = Field(..., ge=1, description="登记数量")
    units: str | None = Field(None, max_length=4, description="单位")
    rgstprice: float | None = Field(None, description="单价")
    deliverdate: datetime | None = Field(None, description="交付日期")


class PurchaseBillCreate(BaseModel):
    """创建采购单据。"""

    pctyp: str | None = Field(None, max_length=2, description="采购类型")
    custcd: str | None = Field(None, max_length=8, description="客户编码")
    refbillid: str | None = Field(None, max_length=8, description="关联单号")
    pcdate: datetime | None = Field(None, description="采购日期")
    whcd: str | None = Field(None, max_length=2, description="入库仓库")
    memo: str | None = Field(None, max_length=255, description="备注")


class SupplierAppraisalCreate(BaseModel):
    """创建供应商评价。"""

    sdate: datetime | None = Field(None, description="开始日期")
    edate: datetime | None = Field(None, description="结束日期")
    memo: str | None = Field(None, max_length=255, description="备注")


class SupplierAppraisalDetailCreate(BaseModel):
    """供应商评价明细。"""

    supplierid: str = Field(..., max_length=8, description="供应商编码")
    appcode: str | None = Field(None, max_length=2, description="评价代码")
    appscore: int | None = Field(None, description="评分")


class ProcurementQuery(BaseModel):
    """采购查询参数。"""

    auditflg: str | None = Field(None, max_length=1)
    suppliercd: str | None = Field(None, max_length=8)
    pctyp: str | None = Field(None, max_length=2)
    whcd: str | None = Field(None, max_length=2)
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
