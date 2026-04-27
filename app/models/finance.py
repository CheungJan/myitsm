"""
财务应收应付模型（Tier-2 G5）。

轻量级财务模块：应收/应付/科目/收付款记录/对账/设备折旧。

对应新增数据库表：
  会计科目：TFN01_ACCOUNT
  应收记录：TFN02_RECEIVABLE
  应付记录：TFN03_PAYABLE
  收付款记录：TFN04_PAYMENT
  设备折旧：TFN05_DEPRECIATION
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 会计科目
# ---------------------------------------------------------------------------


class Account(BaseModel):
    """会计科目（TFN01_ACCOUNT）。"""

    __tablename__ = "tfn01_account"

    account_cd = db.Column(db.String(20), primary_key=True, comment="科目编码")
    account_nm = db.Column(db.String(100), nullable=False, comment="科目名称")
    account_type = db.Column(
        db.String(10),
        nullable=False,
        comment="类型（AR=应收/AP=应付/INCOME=收入/EXPENSE=费用/ASSET=资产）",
    )
    parent_cd = db.Column(db.String(20), comment="上级科目")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 应收记录
# ---------------------------------------------------------------------------


class Receivable(BaseModel):
    """应收记录（TFN02_RECEIVABLE）。"""

    __tablename__ = "tfn02_receivable"

    ar_id = db.Column(db.String(20), primary_key=True, comment="应收编号")
    custcd = db.Column(db.String(10), nullable=False, comment="客户编码")
    account_cd = db.Column(db.String(20), comment="科目编码")
    bill_id = db.Column(db.String(20), comment="关联账单编号")
    fpbh = db.Column(db.String(30), comment="关联发票编号")
    htbh = db.Column(db.String(20), comment="关联合同编号")
    ar_date = db.Column(db.Date, nullable=False, comment="应收日期")
    due_date = db.Column(db.Date, comment="到期日")
    amount = db.Column(db.Numeric(12, 2), nullable=False, comment="应收金额")
    paid_amount = db.Column(db.Numeric(12, 2), default=0, comment="已收金额")
    balance = db.Column(db.Numeric(12, 2), default=0, comment="余额")
    status = db.Column(
        db.String(10),
        default="PENDING",
        comment="状态（PENDING/PARTIAL/PAID/OVERDUE/CANCELLED）",
    )
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 应付记录
# ---------------------------------------------------------------------------


class Payable(BaseModel):
    """应付记录（TFN03_PAYABLE）。"""

    __tablename__ = "tfn03_payable"

    ap_id = db.Column(db.String(20), primary_key=True, comment="应付编号")
    supp_cd = db.Column(db.String(20), nullable=False, comment="供应商编码")
    account_cd = db.Column(db.String(20), comment="科目编码")
    po_id = db.Column(db.String(20), comment="关联采购单号")
    ap_date = db.Column(db.Date, nullable=False, comment="应付日期")
    due_date = db.Column(db.Date, comment="到期日")
    amount = db.Column(db.Numeric(12, 2), nullable=False, comment="应付金额")
    paid_amount = db.Column(db.Numeric(12, 2), default=0, comment="已付金额")
    balance = db.Column(db.Numeric(12, 2), default=0, comment="余额")
    status = db.Column(
        db.String(10),
        default="PENDING",
        comment="状态（PENDING/PARTIAL/PAID/OVERDUE/CANCELLED）",
    )
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 收付款记录
# ---------------------------------------------------------------------------


class Payment(BaseModel):
    """收付款记录（TFN04_PAYMENT）。"""

    __tablename__ = "tfn04_payment"

    pay_id = db.Column(db.String(20), primary_key=True, comment="收付款编号")
    pay_type = db.Column(
        db.String(10),
        nullable=False,
        comment="类型（RECEIVE=收款/PAY=付款）",
    )
    ref_id = db.Column(db.String(20), comment="关联编号（应收ar_id或应付ap_id）")
    custcd = db.Column(db.String(10), comment="客户编码")
    supp_cd = db.Column(db.String(20), comment="供应商编码")
    pay_date = db.Column(db.Date, nullable=False, comment="收付款日期")
    amount = db.Column(db.Numeric(12, 2), nullable=False, comment="收付款金额")
    pay_method = db.Column(
        db.String(10),
        comment="支付方式（CASH/BANK/CHECK/DEPOSIT_OFFSET）",
    )
    bank_account = db.Column(db.String(30), comment="银行账号")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 设备折旧
# ---------------------------------------------------------------------------


class Depreciation(BaseModel):
    """设备折旧记录（TFN05_DEPRECIATION）。"""

    __tablename__ = "tfn05_depreciation"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    eid = db.Column(db.String(50), nullable=False, unique=True, comment="设备序列号")
    item_cd = db.Column(db.String(20), comment="物料编码")
    original_value = db.Column(db.Numeric(12, 2), comment="原值")
    salvage_value = db.Column(db.Numeric(12, 2), default=0, comment="残值")
    useful_life_months = db.Column(db.Integer, comment="使用年限（月）")
    method = db.Column(
        db.String(10),
        default="SL",
        comment="折旧方法（SL=直线法/DB=余额递减）",
    )
    start_date = db.Column(db.Date, comment="折旧起始日")
    monthly_amount = db.Column(db.Numeric(10, 2), comment="月折旧额")
    accumulated = db.Column(db.Numeric(12, 2), default=0, comment="累计折旧")
    net_value = db.Column(db.Numeric(12, 2), comment="净值")
    last_calc_date = db.Column(db.Date, comment="最后计算日期")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")
