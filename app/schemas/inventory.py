"""库存预警与价格管理模块请求/响应 Schema。"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class InventoryLimitCreate(BaseModel):
    """创建库存预警。"""

    itemcd: str = Field(..., max_length=8, description="物料编码")
    invlow: Decimal | None = Field(None, description="库存下限")
    invhigh: Decimal | None = Field(None, description="库存上限")
    daylow: int | None = Field(None, description="天数下限")
    dayhigh: int | None = Field(None, description="天数上限")


class InventoryLimitUpdate(BaseModel):
    """更新库存预警。"""

    invlow: Decimal | None = Field(None, description="库存下限")
    invhigh: Decimal | None = Field(None, description="库存上限")
    daylow: int | None = Field(None, description="天数下限")
    dayhigh: int | None = Field(None, description="天数上限")


class PriceCreate(BaseModel):
    """创建价格规则。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    busityp: str = Field(..., max_length=6, description="业务类型")
    unitcd: str | None = Field(None, max_length=6, description="单位")
    itemprice: Decimal | None = Field(None, description="物料单价")


class PriceUpdate(BaseModel):
    """更新价格规则。"""

    unitcd: str | None = Field(None, max_length=6, description="单位")
    itemprice: Decimal | None = Field(None, description="物料单价")


class AdjustPriceCreate(BaseModel):
    """创建调价记录。"""

    pabillid: str | None = Field(None, max_length=8, description="调价单号")
    lineno: int = Field(..., description="行号")
    itemcd: str = Field(..., max_length=6, description="物料编码")
    busityp: str | None = Field(None, max_length=2, description="业务类型")
    oldprice: Decimal | None = Field(None, description="原价")
    newprice: Decimal | None = Field(None, description="新价")
