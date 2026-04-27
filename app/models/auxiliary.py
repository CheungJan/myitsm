"""
合同与发票管理模型（Tier-1 扩展）。

阶段4：合同管理(THT01) + 发票管理(TAC01)。
基于已有数据库表结构扩展完整 CRUD 和流程管理。

对应数据库表：
  合同：THT01_HTGL
  发票：TAC01_FPSK
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 合同管理
# ---------------------------------------------------------------------------


class Contract(BaseModel):
    """合同管理（THT01_HTGL）。"""

    __tablename__ = "tht01_htgl"

    htbh = db.Column(db.String(20), primary_key=True, comment="合同编号")
    years = db.Column(db.String(4), comment="年份")
    classcd = db.Column(db.String(6), comment="区域")
    busityp = db.Column(db.String(2), comment="合同属性")
    feetyp = db.Column(db.String(2), comment="费用类型")
    qdis = db.Column(db.String(1), comment="签订与否")
    qddate = db.Column(db.Date, comment="签订日期")
    htbgr = db.Column(db.String(20), comment="合同保管人")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="更新人")
    upddate = db.Column(db.DateTime, comment="更新日期")
    yxqfrom = db.Column(db.Date, comment="有效期起始")
    yxqto = db.Column(db.Date, comment="有效期截止")
    htamount = db.Column(db.Numeric(10, 2), comment="合同金额")

    invoices = db.relationship("Invoice", back_populates="contract", lazy="dynamic")


# ---------------------------------------------------------------------------
# 发票管理
# ---------------------------------------------------------------------------


class Invoice(BaseModel):
    """发票/收款管理（TAC01_FPSK）。"""

    __tablename__ = "tac01_fpsk"

    fpbh = db.Column(db.String(30), primary_key=True, comment="发票编号")
    years = db.Column(db.String(4), comment="年份")
    classcd = db.Column(db.String(6), comment="区域")
    busityp = db.Column(db.String(2), comment="合同属性")
    feetyp = db.Column(db.String(2), comment="费用类型")
    htbh = db.Column(
        db.String(20),
        db.ForeignKey("tht01_htgl.htbh"),
        comment="合同编号",
    )
    htq = db.Column(db.String(2), comment="合同期")
    qsr = db.Column(db.String(10), comment="签收人")
    lsh = db.Column(db.String(30), comment="流水号")
    kpdate = db.Column(db.Date, comment="开票日期")
    kpamount = db.Column(db.Numeric(10, 2), comment="开票金额")
    hkdate = db.Column(db.Date, comment="回款日期")
    hkamount = db.Column(db.Numeric(10, 2), comment="回款金额")
    sptype = db.Column(db.String(6), comment="送票方式")
    spr = db.Column(db.String(6), comment="送票人")
    htqdis = db.Column(db.String(1), comment="合同签订与否")
    htamount = db.Column(db.Numeric(10, 2), comment="合同金额")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="更新人")
    upddate = db.Column(db.DateTime, comment="更新日期")

    contract = db.relationship("Contract", back_populates="invoices")
