"""
租金/费用自动结算模型（Tier-2 G4）。

结算引擎基于 TMM61_DEPOSIT_POSMODEL（RENT_MONEY/SALE_MONEY）按客户+设备+合同期
自动生成账单。

对应新增数据库表：
  结算规则：TBL01_BILLING_RULE
  账单主表：TBL02_BILL
  账单明细：TBL03_BILL_DETAIL
  结算批次：TBL04_BILLING_BATCH
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 结算规则
# ---------------------------------------------------------------------------


class BillingRule(BaseModel):
    """结算规则（TBL01_BILLING_RULE）。"""

    __tablename__ = "tbl01_billing_rule"

    rule_id = db.Column(db.String(20), primary_key=True, comment="规则编号")
    rule_name = db.Column(db.String(100), nullable=False, comment="规则名称")
    billing_type = db.Column(
        db.String(10),
        nullable=False,
        comment="结算类型（RENT=租金/SALE=销售/SERVICE=服务费）",
    )
    cycle_type = db.Column(
        db.String(10),
        nullable=False,
        default="MONTHLY",
        comment="结算周期（MONTHLY/QUARTERLY/YEARLY/ONETIME）",
    )
    price_source = db.Column(
        db.String(10),
        default="MODEL",
        comment="价格来源（MODEL=型号标准/CONTRACT=合同约定/CUSTOM=自定义）",
    )
    tax_rate = db.Column(db.Numeric(5, 2), default=0, comment="税率（百分比）")
    late_fee_rate = db.Column(db.Numeric(5, 4), default=0, comment="滞纳金日费率")
    remark = db.Column(db.String(200), comment="备注")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 账单主表
# ---------------------------------------------------------------------------


class Bill(BaseModel):
    """账单主表（TBL02_BILL）。"""

    __tablename__ = "tbl02_bill"

    bill_id = db.Column(db.String(20), primary_key=True, comment="账单编号")
    custcd = db.Column(db.String(10), nullable=False, comment="客户编码")
    billing_type = db.Column(db.String(10), nullable=False, comment="结算类型")
    bill_period = db.Column(db.String(10), comment="账单周期（如202604）")
    bill_date = db.Column(db.Date, nullable=False, comment="账单日期")
    due_date = db.Column(db.Date, comment="到期日")
    total_amount = db.Column(db.Numeric(12, 2), default=0, comment="账单总额")
    tax_amount = db.Column(db.Numeric(12, 2), default=0, comment="税额")
    paid_amount = db.Column(db.Numeric(12, 2), default=0, comment="已付金额")
    status = db.Column(
        db.String(10),
        default="PENDING",
        comment="状态（PENDING/SENT/PARTIAL/PAID/OVERDUE/CANCELLED）",
    )
    htbh = db.Column(db.String(20), comment="关联合同编号")
    batch_id = db.Column(db.String(20), comment="生成批次号")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")

    details = db.relationship("BillDetail", back_populates="bill", lazy="dynamic")


# ---------------------------------------------------------------------------
# 账单明细
# ---------------------------------------------------------------------------


class BillDetail(BaseModel):
    """账单明细（TBL03_BILL_DETAIL）。"""

    __tablename__ = "tbl03_bill_detail"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bill_id = db.Column(
        db.String(20),
        db.ForeignKey("tbl02_bill.bill_id"),
        nullable=False,
        comment="账单编号",
    )
    item_cd = db.Column(db.String(20), comment="物料/设备编码")
    model_cd = db.Column(db.String(8), comment="型号编码")
    eid = db.Column(db.String(50), comment="设备序列号")
    description = db.Column(db.String(200), comment="费用说明")
    quantity = db.Column(db.Integer, default=1, comment="数量")
    unit_price = db.Column(db.Numeric(10, 2), comment="单价")
    amount = db.Column(db.Numeric(12, 2), comment="金额")
    period_from = db.Column(db.Date, comment="计费起始日")
    period_to = db.Column(db.Date, comment="计费截止日")

    bill = db.relationship("Bill", back_populates="details")


# ---------------------------------------------------------------------------
# 结算批次
# ---------------------------------------------------------------------------


class BillingBatch(BaseModel):
    """结算批次（TBL04_BILLING_BATCH）。"""

    __tablename__ = "tbl04_billing_batch"

    batch_id = db.Column(db.String(20), primary_key=True, comment="批次编号")
    batch_date = db.Column(db.Date, nullable=False, comment="批次日期")
    billing_type = db.Column(db.String(10), comment="结算类型")
    bill_period = db.Column(db.String(10), comment="账单周期")
    total_bills = db.Column(db.Integer, default=0, comment="账单数量")
    total_amount = db.Column(db.Numeric(14, 2), default=0, comment="总金额")
    status = db.Column(
        db.String(10),
        default="RUNNING",
        comment="状态（RUNNING/COMPLETED/FAILED）",
    )
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")
