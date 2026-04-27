"""押金管理模块请求/响应 Schema。"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class DepositCreate(BaseModel):
    """创建押金记录。"""

    custcd: str = Field(..., max_length=10, description="客户编码")
    amount_money: Decimal | None = Field(None, description="押金余额")
    r_billid: str | None = Field(None, max_length=20, description="关联单号")
    modelcd: str | None = Field(None, max_length=20, description="型号编码")
    modelnm: str | None = Field(None, max_length=20, description="型号名称")


class DepositUpdate(BaseModel):
    """更新押金记录。"""

    amount_money: Decimal | None = Field(None, description="押金余额")
    r_billid: str | None = Field(None, max_length=20, description="关联单号")
    modelcd: str | None = Field(None, max_length=20, description="型号编码")
    modelnm: str | None = Field(None, max_length=20, description="型号名称")


class DepositDetailCreate(BaseModel):
    """创建押金变更明细。"""

    custcd: str = Field(..., max_length=10, description="客户编码")
    c_type: str | None = Field(None, max_length=10, description="变更类型")
    old_a: Decimal | None = Field(None, description="原金额")
    new_a: Decimal | None = Field(None, description="新金额")
    change_a: Decimal | None = Field(None, description="变更金额")
    r_billid: str | None = Field(None, max_length=10, description="关联单号")
    confirm_a: Decimal | None = Field(None, description="确认金额")
    remark: str | None = Field(None, max_length=200, description="备注")


class DepositPosModelCreate(BaseModel):
    """创建设备型号押金标准。"""

    model_cd: str = Field(..., max_length=8, description="型号编码")
    model_nm: str | None = Field(None, max_length=20, description="型号名称")
    rent_money: Decimal | None = Field(None, description="租金")
    sale_money: Decimal | None = Field(None, description="售价")


class DepositPosModelUpdate(BaseModel):
    """更新设备型号押金标准。"""

    model_nm: str | None = Field(None, max_length=20, description="型号名称")
    rent_money: Decimal | None = Field(None, description="租金")
    sale_money: Decimal | None = Field(None, description="售价")
