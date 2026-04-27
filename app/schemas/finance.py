"""财务应收应付模块请求/响应 Schema（Tier-2 G5）。"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 会计科目
# ---------------------------------------------------------------------------


class AccountCreate(BaseModel):
    """创建会计科目。"""

    account_cd: str = Field(..., max_length=20, description="科目编码")
    account_nm: str = Field(..., max_length=100, description="科目名称")
    account_type: str = Field(..., max_length=10, description="类型")
    parent_cd: str | None = Field(None, max_length=20, description="上级科目")
    remark: str | None = Field(None, max_length=200, description="备注")


class AccountUpdate(BaseModel):
    """更新会计科目。"""

    account_nm: str | None = Field(None, max_length=100, description="科目名称")
    parent_cd: str | None = Field(None, max_length=20, description="上级科目")
    useflg: str | None = Field(None, max_length=1, description="有效标志")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 应收记录
# ---------------------------------------------------------------------------


class ReceivableCreate(BaseModel):
    """创建应收记录。"""

    ar_id: str = Field(..., max_length=20, description="应收编号")
    custcd: str = Field(..., max_length=10, description="客户编码")
    account_cd: str | None = Field(None, max_length=20, description="科目编码")
    bill_id: str | None = Field(None, max_length=20, description="关联账单")
    fpbh: str | None = Field(None, max_length=30, description="关联发票")
    htbh: str | None = Field(None, max_length=20, description="关联合同")
    ar_date: date = Field(..., description="应收日期")
    due_date: date | None = Field(None, description="到期日")
    amount: Decimal = Field(..., description="应收金额")
    remark: str | None = Field(None, max_length=200, description="备注")


class ReceivableUpdate(BaseModel):
    """更新应收记录。"""

    due_date: date | None = Field(None, description="到期日")
    paid_amount: Decimal | None = Field(None, description="已收金额")
    balance: Decimal | None = Field(None, description="余额")
    status: str | None = Field(None, max_length=10, description="状态")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 应付记录
# ---------------------------------------------------------------------------


class PayableCreate(BaseModel):
    """创建应付记录。"""

    ap_id: str = Field(..., max_length=20, description="应付编号")
    supp_cd: str = Field(..., max_length=20, description="供应商编码")
    account_cd: str | None = Field(None, max_length=20, description="科目编码")
    po_id: str | None = Field(None, max_length=20, description="关联采购单号")
    ap_date: date = Field(..., description="应付日期")
    due_date: date | None = Field(None, description="到期日")
    amount: Decimal = Field(..., description="应付金额")
    remark: str | None = Field(None, max_length=200, description="备注")


class PayableUpdate(BaseModel):
    """更新应付记录。"""

    due_date: date | None = Field(None, description="到期日")
    paid_amount: Decimal | None = Field(None, description="已付金额")
    balance: Decimal | None = Field(None, description="余额")
    status: str | None = Field(None, max_length=10, description="状态")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 收付款记录
# ---------------------------------------------------------------------------


class PaymentCreate(BaseModel):
    """创建收付款记录。"""

    pay_id: str = Field(..., max_length=20, description="收付款编号")
    pay_type: str = Field(..., max_length=10, description="类型")
    ref_id: str | None = Field(None, max_length=20, description="关联编号")
    custcd: str | None = Field(None, max_length=10, description="客户编码")
    supp_cd: str | None = Field(None, max_length=20, description="供应商编码")
    pay_date: date = Field(..., description="收付款日期")
    amount: Decimal = Field(..., description="收付款金额")
    pay_method: str | None = Field(None, max_length=10, description="支付方式")
    bank_account: str | None = Field(None, max_length=30, description="银行账号")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 设备折旧
# ---------------------------------------------------------------------------


class DepreciationCreate(BaseModel):
    """创建折旧记录。"""

    eid: str = Field(..., max_length=50, description="设备序列号")
    item_cd: str | None = Field(None, max_length=20, description="物料编码")
    original_value: Decimal | None = Field(None, description="原值")
    salvage_value: Decimal | None = Field(None, description="残值")
    useful_life_months: int | None = Field(None, description="使用年限月")
    method: str | None = Field("SL", max_length=10, description="折旧方法")
    start_date: date | None = Field(None, description="折旧起始日")


class DepreciationUpdate(BaseModel):
    """更新折旧记录。"""

    monthly_amount: Decimal | None = Field(None, description="月折旧额")
    accumulated: Decimal | None = Field(None, description="累计折旧")
    net_value: Decimal | None = Field(None, description="净值")
    last_calc_date: date | None = Field(None, description="最后计算日期")
