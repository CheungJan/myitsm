"""租金/费用结算模块请求/响应 Schema（Tier-2 G4）。"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 结算规则
# ---------------------------------------------------------------------------


class BillingRuleCreate(BaseModel):
    """创建结算规则。"""

    rule_id: str = Field(..., max_length=20, description="规则编号")
    rule_name: str = Field(..., max_length=100, description="规则名称")
    billing_type: str = Field(..., max_length=10, description="结算类型")
    cycle_type: str | None = Field("MONTHLY", max_length=10, description="结算周期")
    price_source: str | None = Field("MODEL", max_length=10, description="价格来源")
    tax_rate: Decimal | None = Field(None, description="税率")
    late_fee_rate: Decimal | None = Field(None, description="滞纳金日费率")
    remark: str | None = Field(None, max_length=200, description="备注")


class BillingRuleUpdate(BaseModel):
    """更新结算规则。"""

    rule_name: str | None = Field(None, max_length=100, description="规则名称")
    billing_type: str | None = Field(None, max_length=10, description="结算类型")
    cycle_type: str | None = Field(None, max_length=10, description="结算周期")
    price_source: str | None = Field(None, max_length=10, description="价格来源")
    tax_rate: Decimal | None = Field(None, description="税率")
    late_fee_rate: Decimal | None = Field(None, description="滞纳金日费率")
    remark: str | None = Field(None, max_length=200, description="备注")
    useflg: str | None = Field(None, max_length=1, description="有效标志")


# ---------------------------------------------------------------------------
# 账单
# ---------------------------------------------------------------------------


class BillDetailCreate(BaseModel):
    """账单明细。"""

    item_cd: str | None = Field(None, max_length=20, description="物料编码")
    model_cd: str | None = Field(None, max_length=8, description="型号编码")
    eid: str | None = Field(None, max_length=50, description="设备序列号")
    description: str | None = Field(None, max_length=200, description="费用说明")
    quantity: int | None = Field(1, description="数量")
    unit_price: Decimal | None = Field(None, description="单价")
    amount: Decimal | None = Field(None, description="金额")
    period_from: date | None = Field(None, description="计费起始日")
    period_to: date | None = Field(None, description="计费截止日")


class BillCreate(BaseModel):
    """创建账单。"""

    bill_id: str = Field(..., max_length=20, description="账单编号")
    custcd: str = Field(..., max_length=10, description="客户编码")
    billing_type: str = Field(..., max_length=10, description="结算类型")
    bill_period: str | None = Field(None, max_length=10, description="账单周期")
    bill_date: date = Field(..., description="账单日期")
    due_date: date | None = Field(None, description="到期日")
    total_amount: Decimal | None = Field(None, description="账单总额")
    tax_amount: Decimal | None = Field(None, description="税额")
    htbh: str | None = Field(None, max_length=20, description="合同编号")
    batch_id: str | None = Field(None, max_length=20, description="批次号")
    remark: str | None = Field(None, max_length=200, description="备注")
    details: list[BillDetailCreate] | None = Field(None, description="账单明细")


class BillUpdate(BaseModel):
    """更新账单。"""

    due_date: date | None = Field(None, description="到期日")
    total_amount: Decimal | None = Field(None, description="账单总额")
    tax_amount: Decimal | None = Field(None, description="税额")
    paid_amount: Decimal | None = Field(None, description="已付金额")
    status: str | None = Field(None, max_length=10, description="状态")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 结算批次
# ---------------------------------------------------------------------------


class BillingBatchCreate(BaseModel):
    """创建结算批次。"""

    batch_id: str = Field(..., max_length=20, description="批次编号")
    batch_date: date = Field(..., description="批次日期")
    billing_type: str | None = Field(None, max_length=10, description="结算类型")
    bill_period: str | None = Field(None, max_length=10, description="账单周期")
    remark: str | None = Field(None, max_length=200, description="备注")


class BillingBatchUpdate(BaseModel):
    """更新结算批次。"""

    total_bills: int | None = Field(None, description="账单数量")
    total_amount: Decimal | None = Field(None, description="总金额")
    status: str | None = Field(None, max_length=10, description="状态")
    remark: str | None = Field(None, max_length=200, description="备注")
