"""
采购管理模型。

阶段3：采购计划→登记→单据→退货→供应商评价全链路。

对应数据库表：
  采购计划：TPC01_PCPLAN / TPC02_PCPLANDT / TPC03_PCPLANSTATUS
  采购登记：TPC12_REGISTER / TPC13_REGISTERDT
  采购单据：TPC14_PCBILL
  退货单据：TPC16_RPCBILL / TPC17_RPCBILLDT
  供应商评价：TPC20_SUPPAPPRAISAL / TPC21_SUPPAPPRAISALDT
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 采购计划
# ---------------------------------------------------------------------------


class PurchasePlan(BaseModel):
    """采购计划主表（TPC01_PCPLAN）。"""

    __tablename__ = "tpc01_pcplan"

    pcplanid = db.Column(db.String(8), primary_key=True, comment="采购计划号")
    slbillid = db.Column(db.String(8), comment="关联销售单号")
    pctyp = db.Column(db.String(1), comment="采购类型")
    ptimes = db.Column(db.Integer, comment="打印次数")
    opercd = db.Column(db.String(6), comment="操作员")
    memo = db.Column(db.String(255), comment="备注")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    plandate = db.Column(db.DateTime, comment="计划日期")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")
    checkmemo = db.Column(db.String(255), comment="审核备注")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    type = db.Column(db.String(1), comment="类型")

    details = db.relationship("PurchasePlanDt", back_populates="plan", lazy="dynamic")


class PurchasePlanDt(BaseModel):
    """采购计划明细（TPC02_PCPLANDT）。"""

    __tablename__ = "tpc02_pcplandt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pcplanid = db.Column(
        db.String(8),
        db.ForeignKey("tpc01_pcplan.pcplanid"),
        nullable=False,
        comment="采购计划号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    rgstqty = db.Column(db.Integer, default=0, comment="登记数量")
    units = db.Column(db.String(4), comment="单位")
    storeqty = db.Column(db.Integer, default=0, comment="库存数量")
    lowlimit = db.Column(db.Integer, default=0, comment="库存下限")
    upperlimit = db.Column(db.Integer, default=0, comment="库存上限")
    auditqty = db.Column(db.Integer, default=0, comment="审批数量")

    plan = db.relationship("PurchasePlan", back_populates="details")


class PurchasePlanStatus(BaseModel):
    """采购计划状态汇总（TPC03_PCPLANSTATUS）。"""

    __tablename__ = "tpc03_pcplanstatus"

    itemcd = db.Column(db.String(6), primary_key=True, comment="物料编码")
    rgstqty = db.Column(db.Integer, default=0, comment="登记数量")
    auditqty = db.Column(db.Integer, default=0, comment="审批数量")
    pcqty = db.Column(db.Integer, default=0, comment="采购数量")
    opercd = db.Column(db.String(6), comment="操作员")
    memo = db.Column(db.String(255), comment="备注")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    upddate = db.Column(db.DateTime, comment="更新日期")
    refbillid = db.Column(db.String(8), comment="关联单号")


# ---------------------------------------------------------------------------
# 采购登记
# ---------------------------------------------------------------------------


class PurchaseRegister(BaseModel):
    """采购登记主表（TPC12_REGISTER）。"""

    __tablename__ = "tpc12_register"

    rgstbillid = db.Column(db.String(8), primary_key=True, comment="登记单号")
    suppliercd = db.Column(db.String(8), comment="供应商编码")
    pcrep = db.Column(db.String(6), comment="采购代表")
    ptimes = db.Column(db.Integer, comment="打印次数")
    opercd = db.Column(db.String(6), comment="操作员")
    memo = db.Column(db.String(255), comment="备注")
    gendate = db.Column(db.DateTime, comment="创建日期")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")
    checkmemo = db.Column(db.String(255), comment="审核备注")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    rgstdate = db.Column(db.DateTime, comment="登记日期")
    rgstamt = db.Column(db.Numeric(12, 2), comment="登记金额")

    details = db.relationship("PurchaseRegisterDt", back_populates="register", lazy="dynamic")


class PurchaseRegisterDt(BaseModel):
    """采购登记明细（TPC13_REGISTERDT）。"""

    __tablename__ = "tpc13_registerdt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rgstbillid = db.Column(
        db.String(8),
        db.ForeignKey("tpc12_register.rgstbillid"),
        nullable=False,
        comment="登记单号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    rgsqty = db.Column(db.Integer, default=0, comment="登记数量")
    memo = db.Column(db.String(255), comment="备注")
    units = db.Column(db.String(4), comment="单位")
    rgstprice = db.Column(db.Numeric(16, 8), comment="登记单价")
    deliverdate = db.Column(db.DateTime, comment="交付日期")
    inqty = db.Column(db.Integer, default=0, comment="已入库数量")
    auditqty = db.Column(db.Integer, default=0, comment="审批数量")

    register = db.relationship("PurchaseRegister", back_populates="details")


# ---------------------------------------------------------------------------
# 采购单据
# ---------------------------------------------------------------------------


class PurchaseBill(BaseModel):
    """采购单据（TPC14_PCBILL）。"""

    __tablename__ = "tpc14_pcbill"

    pcbillid = db.Column(db.String(8), primary_key=True, comment="采购单号")
    pctyp = db.Column(db.String(2), comment="采购类型")
    custcd = db.Column(db.String(8), comment="客户编码")
    refbillid = db.Column(db.String(8), comment="关联单号")
    pcdate = db.Column(db.DateTime, comment="采购日期")
    pcamt = db.Column(db.Numeric(16, 4), comment="采购金额")
    whcd = db.Column(db.String(2), comment="入库仓库")
    invoiceflg = db.Column(db.String(1), comment="发票标志")
    ptimes = db.Column(db.Integer, comment="打印次数")
    opercd = db.Column(db.String(6), comment="操作员")
    memo = db.Column(db.String(255), comment="备注")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


# ---------------------------------------------------------------------------
# 退货单据
# ---------------------------------------------------------------------------


class ReturnPurchaseBill(BaseModel):
    """采购退货单（TPC16_RPCBILL）。"""

    __tablename__ = "tpc16_rpcbill"

    pcbillid = db.Column(db.String(8), primary_key=True, comment="退货单号")
    custcd = db.Column(db.String(8), comment="客户编码")
    pcdate = db.Column(db.DateTime, comment="退货日期")
    pcamt = db.Column(db.Integer, comment="退货金额")
    whcd = db.Column(db.String(2), comment="仓库编码")
    invoiceflg = db.Column(db.String(2), comment="发票标志")
    ptimes = db.Column(db.Integer, comment="打印次数")
    opercd = db.Column(db.String(6), comment="操作员")
    memo = db.Column(db.String(255), comment="备注")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    gendate = db.Column(db.DateTime, comment="创建日期")

    details = db.relationship("ReturnPurchaseBillDt", back_populates="bill", lazy="dynamic")


class ReturnPurchaseBillDt(BaseModel):
    """采购退货明细（TPC17_RPCBILLDT）。"""

    __tablename__ = "tpc17_rpcbilldt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pcbillid = db.Column(
        db.String(8),
        db.ForeignKey("tpc16_rpcbill.pcbillid"),
        nullable=False,
        comment="退货单号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    eid = db.Column(db.String(13), comment="设备EID")
    seid = db.Column(db.String(30), comment="序列号")
    rpcqty = db.Column(db.Integer, default=0, comment="退货数量")
    invoiceqty = db.Column(db.Integer, default=0, comment="发票数量")
    units = db.Column(db.String(4), comment="单位")

    bill = db.relationship("ReturnPurchaseBill", back_populates="details")


# ---------------------------------------------------------------------------
# 供应商评价
# ---------------------------------------------------------------------------


class SupplierAppraisal(BaseModel):
    """供应商评价主表（TPC20_SUPPAPPRAISAL）。"""

    __tablename__ = "tpc20_suppappraisal"

    appid = db.Column(db.String(8), primary_key=True, comment="评价单号")
    sdate = db.Column(db.DateTime, comment="开始日期")
    edate = db.Column(db.DateTime, comment="结束日期")
    memo = db.Column(db.String(255), comment="备注")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    details = db.relationship("SupplierAppraisalDt", back_populates="appraisal", lazy="dynamic")


class SupplierAppraisalDt(BaseModel):
    """供应商评价明细（TPC21_SUPPAPPRAISALDT）。"""

    __tablename__ = "tpc21_suppappraisaldt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    appid = db.Column(
        db.String(8),
        db.ForeignKey("tpc20_suppappraisal.appid"),
        nullable=False,
        comment="评价单号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    supplierid = db.Column(db.String(8), nullable=False, comment="供应商编码")
    appcode = db.Column(db.String(2), comment="评价代码")
    appscore = db.Column(db.Integer, comment="评分")
    appflg = db.Column(db.String(1), comment="评价标志")

    appraisal = db.relationship("SupplierAppraisal", back_populates="details")
