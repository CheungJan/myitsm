"""
仓储管理模型。

阶段3：仓储统一模型（优化5 — 16种出入库合并为StockMovement）。

对应数据库表：
  仓库主数据：TWH01_WAREHOUSE
  库存明细：TWH11_DETAIL / TWH12_DETAILDT
  入库：TWH13_IN / TWH14_CHECKINDT
  出库：TWH15_OUT / TWH16_OUTDTEID / TWH16_OUTDTPRD
  盘盈盘亏：TWH17_OVERLOST / TWH18_OVERLOSTDT / TWH18_OVERLOSTEID
  资产盘点：TWH19_ASSET_C_A / TWH20_ASSET_C_A_DTL
  POS设备变更：TWH21_POS_CHANGE / TWH22_POS_CHANGE_DT
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 仓库主数据
# ---------------------------------------------------------------------------


class Warehouse(BaseModel):
    """仓库主数据（TWH01_WAREHOUSE）。"""

    __tablename__ = "twh01_warehouse"

    whcd = db.Column(db.String(2), primary_key=True, comment="仓库编码")
    whnm = db.Column(db.String(60), comment="仓库名称")
    whtyp = db.Column(db.String(2), comment="仓库类型")
    address = db.Column(db.String(60), comment="地址")
    phoneno = db.Column(db.String(15), comment="电话")
    fax = db.Column(db.String(15), comment="传真")
    leader = db.Column(db.String(6), comment="负责人")
    defaultflg = db.Column(db.String(1), comment="默认仓库标志")
    remoteflg = db.Column(db.String(1), comment="远程仓库标志")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    whtransflg = db.Column(db.String(1), comment="仓储流转标志")


# ---------------------------------------------------------------------------
# 库存明细
# ---------------------------------------------------------------------------


class StockDetail(BaseModel):
    """库存明细（TWH11_DETAIL）。"""

    __tablename__ = "twh11_detail"

    seqno = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="序号")
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    prddate = db.Column(db.DateTime, comment="生产日期")
    itemqty = db.Column(db.Integer, default=0, comment="库存数量")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class StockDetailDt(BaseModel):
    """库存明细流水（TWH12_DETAILDT）。"""

    __tablename__ = "twh12_detaildt"

    seqno = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="序号")
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    prddate = db.Column(db.DateTime, comment="生产日期")
    billid = db.Column(db.String(8), comment="单据号")
    invdate = db.Column(db.DateTime, comment="库存日期")
    invtyp = db.Column(db.String(1), comment="出入库类型")
    itemqty = db.Column(db.Integer, default=0, comment="变动数量")
    storeqty = db.Column(db.Integer, default=0, comment="库存余量")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    iotyp = db.Column(db.String(1), comment="出入类型（I入/O出）")


# ---------------------------------------------------------------------------
# 入库（统一模型 — 优化5）
# ---------------------------------------------------------------------------


class StockIn(BaseModel):
    """入库单（TWH13_IN）。

    统一承载8种入库类型，通过 invtyp 区分：
    - 1: 采购入库  2: 销售退货入库  3: 服务返还入库
    - 4: 调拨入库  5: 借出归还入库  6: 翻新入库
    - 7: 回收入库  8: 其他入库
    """

    __tablename__ = "twh13_in"

    inbillid = db.Column(db.String(8), primary_key=True, comment="入库单号")
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    indate = db.Column(db.DateTime, comment="入库日期")
    invtyp = db.Column(db.String(1), nullable=False, comment="入库类型")
    refbillid = db.Column(db.String(8), comment="关联单据号")
    ptimes = db.Column(db.Integer, comment="打印次数")
    memo = db.Column(db.String(255), comment="备注")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    optyp = db.Column(db.String(1), comment="操作类型")
    suppcd = db.Column(db.String(8), comment="供应商编码")

    details = db.relationship("StockInDetail", back_populates="stock_in", lazy="dynamic")


class StockInDetail(BaseModel):
    """入库明细（TWH14_CHECKINDT）。"""

    __tablename__ = "twh14_checkindt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inbillid = db.Column(
        db.String(8),
        db.ForeignKey("twh13_in.inbillid"),
        nullable=False,
        comment="入库单号",
    )
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    prddate = db.Column(db.DateTime, comment="生产日期")
    batchid = db.Column(db.String(50), comment="批次号")
    inqty = db.Column(db.Integer, default=0, comment="入库数量")
    reflineno = db.Column(db.Integer, comment="关联行号")
    s_money = db.Column(db.Numeric(10, 2), comment="金额")

    stock_in = db.relationship("StockIn", back_populates="details")


# ---------------------------------------------------------------------------
# 出库（统一模型 — 优化5）
# ---------------------------------------------------------------------------


class StockOut(BaseModel):
    """出库单（TWH15_OUT）。

    统一承载8种出库类型，通过 invtyp 区分：
    - 1: 销售出库  2: 服务领用出库  3: 调拨出库
    - 4: 借出出库  5: 质检出库  6: 退货出库
    - 7: 报废出库  8: 其他出库
    """

    __tablename__ = "twh15_out"

    outbillid = db.Column(db.String(8), primary_key=True, comment="出库单号")
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    outdate = db.Column(db.DateTime, comment="出库日期")
    invtyp = db.Column(db.String(1), nullable=False, comment="出库类型")
    ptimes = db.Column(db.Integer, comment="打印次数")
    memo = db.Column(db.String(255), comment="备注")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")
    optyp = db.Column(db.String(2), comment="操作类型")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    targetwhcd = db.Column(db.String(2), comment="目标仓库（调拨）")
    suppcd = db.Column(db.String(8), comment="供应商编码（退货）")

    details_eid = db.relationship("StockOutDetailEid", back_populates="stock_out", lazy="dynamic")
    details_prd = db.relationship("StockOutDetailPrd", back_populates="stock_out", lazy="dynamic")


class StockOutDetailEid(BaseModel):
    """出库明细-按EID（TWH16_OUTDTEID）。"""

    __tablename__ = "twh16_outdteid"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    outbillid = db.Column(
        db.String(8),
        db.ForeignKey("twh15_out.outbillid"),
        nullable=False,
        comment="出库单号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    prddate = db.Column(db.DateTime, comment="生产日期")
    eid = db.Column(db.String(13), comment="设备唯一标识")
    outqty = db.Column(db.Integer, default=0, comment="出库数量")
    qcqty = db.Column(db.Integer, default=0, comment="质检数量")
    reflineno = db.Column(db.Integer, comment="关联行号")
    s_money = db.Column(db.Numeric(10, 2), comment="金额")

    stock_out = db.relationship("StockOut", back_populates="details_eid")


class StockOutDetailPrd(BaseModel):
    """出库明细-按批次（TWH16_OUTDTPRD）。"""

    __tablename__ = "twh16_outdtprd"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    outbillid = db.Column(
        db.String(8),
        db.ForeignKey("twh15_out.outbillid"),
        nullable=False,
        comment="出库单号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    prddate = db.Column(db.DateTime, comment="生产日期")
    outqty = db.Column(db.Integer, default=0, comment="出库数量")
    qcqty = db.Column(db.Integer, default=0, comment="质检数量")
    reflineno = db.Column(db.Integer, comment="关联行号")
    s_money = db.Column(db.Numeric(10, 2), comment="金额")

    stock_out = db.relationship("StockOut", back_populates="details_prd")


# ---------------------------------------------------------------------------
# 盘盈盘亏
# ---------------------------------------------------------------------------


class OverLost(BaseModel):
    """盘盈盘亏主表（TWH17_OVERLOST）。"""

    __tablename__ = "twh17_overlost"

    olbillid = db.Column(db.String(8), primary_key=True, comment="盘点单号")
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    oltyp = db.Column(db.String(2), comment="盘点类型")
    oldate = db.Column(db.DateTime, comment="盘点日期")
    cfdate = db.Column(db.DateTime, comment="确认日期")
    memo = db.Column(db.String(60), comment="备注")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    cfercd = db.Column(db.String(6), comment="确认人")
    optyp = db.Column(db.String(2), comment="操作类型")
    olreason = db.Column(db.String(100), comment="盘点原因")
    olsign = db.Column(db.String(1), comment="盘盈盘亏标志（+盈/-亏）")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")

    details = db.relationship("OverLostDt", back_populates="overlost", lazy="dynamic")
    details_eid = db.relationship("OverLostEid", back_populates="overlost", lazy="dynamic")


class OverLostDt(BaseModel):
    """盘盈盘亏明细（TWH18_OVERLOSTDT）。"""

    __tablename__ = "twh18_overlostdt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    olbillid = db.Column(
        db.String(8),
        db.ForeignKey("twh17_overlost.olbillid"),
        nullable=False,
        comment="盘点单号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    olqty = db.Column(db.Numeric(12, 4), default=0, comment="盘点差异数量")
    prddate = db.Column(db.DateTime, comment="生产日期")
    memo = db.Column(db.String(255), comment="备注")

    overlost = db.relationship("OverLost", back_populates="details")


class OverLostEid(BaseModel):
    """盘盈盘亏明细-按EID（TWH18_OVERLOSTEID）。"""

    __tablename__ = "twh18_overlosteid"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    whcd = db.Column(db.String(2), nullable=False, comment="仓库编码")
    olbillid = db.Column(
        db.String(8),
        db.ForeignKey("twh17_overlost.olbillid"),
        nullable=False,
        comment="盘点单号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    olqty = db.Column(db.Numeric(12, 4), default=0, comment="差异数量")
    prddate = db.Column(db.DateTime, comment="生产日期")
    memo = db.Column(db.String(255), comment="备注")
    eid = db.Column(db.String(13), comment="设备唯一标识")

    overlost = db.relationship("OverLost", back_populates="details_eid")


# ---------------------------------------------------------------------------
# 资产盘点
# ---------------------------------------------------------------------------


class AssetCheckAccept(BaseModel):
    """资产盘点主表（TWH19_ASSET_C_A）。"""

    __tablename__ = "twh19_asset_c_a"

    opbillid = db.Column(db.String(8), primary_key=True, comment="盘点单号")
    slbillid = db.Column(db.String(8), comment="关联销售单号")
    custcd = db.Column(db.String(8), nullable=False, comment="客户编码")
    impdate = db.Column(db.String(6), comment="实施日期")
    traindate = db.Column(db.String(6), comment="培训日期")
    busityp = db.Column(db.String(2), comment="业务类型")
    sltyp = db.Column(db.String(2), comment="销售类型")
    itemcd = db.Column(db.String(6), comment="物料编码")
    opercd = db.Column(db.String(6), comment="操作员")
    backup = db.Column(db.String(255), comment="备注")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")

    details = db.relationship("AssetCheckAcceptDtl", back_populates="asset_ca", lazy="dynamic")


class AssetCheckAcceptDtl(BaseModel):
    """资产盘点明细（TWH20_ASSET_C_A_DTL）。"""

    __tablename__ = "twh20_asset_c_a_dtl"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    opbillid = db.Column(
        db.String(8),
        db.ForeignKey("twh19_asset_c_a.opbillid"),
        nullable=False,
        comment="盘点单号",
    )
    custcard = db.Column(db.String(20), comment="客户磁卡号")
    custcd = db.Column(db.String(8), nullable=False, comment="客户编码")
    planqty = db.Column(db.Integer, default=0, comment="计划数量")
    opqty = db.Column(db.Integer, default=0, comment="实际数量")
    clqty = db.Column(db.Integer, default=0, comment="差异数量")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    impdate = db.Column(db.DateTime, comment="实施日期")
    traindate = db.Column(db.DateTime, comment="培训日期")
    newaddress = db.Column(db.String(255), comment="新地址")
    newcustcard = db.Column(db.String(20), comment="新磁卡号")
    address = db.Column(db.String(255), comment="原地址")
    newcustcd = db.Column(db.String(8), comment="新客户编码")
    eid = db.Column(db.String(13), comment="设备EID")
    o_name = db.Column(db.String(100), comment="原名称")
    n_name = db.Column(db.String(100), comment="新名称")
    o_phoneno = db.Column(db.String(60), comment="原电话")
    n_phoneno = db.Column(db.String(60), comment="新电话")
    o_contactor = db.Column(db.String(10), comment="原联系人")
    n_contactor = db.Column(db.String(10), comment="新联系人")

    asset_ca = db.relationship("AssetCheckAccept", back_populates="details")


# ---------------------------------------------------------------------------
# POS设备变更
# ---------------------------------------------------------------------------


class PosChange(BaseModel):
    """POS设备变更主表（TWH21_POS_CHANGE）。"""

    __tablename__ = "twh21_pos_change"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    poseid = db.Column(db.String(20), comment="POS设备EID")
    opercd = db.Column(db.String(6), comment="操作员")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    remark = db.Column(db.String(200), comment="备注")

    details = db.relationship("PosChangeDt", back_populates="pos_change", lazy="dynamic")


class PosChangeDt(BaseModel):
    """POS设备变更明细（TWH22_POS_CHANGE_DT）。"""

    __tablename__ = "twh22_pos_change_dt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    operation_id = db.Column(
        db.Integer,
        db.ForeignKey("twh21_pos_change.id"),
        nullable=False,
        comment="变更操作ID",
    )
    poseid = db.Column(db.String(20), comment="POS设备EID")
    changetype = db.Column(db.Integer, comment="变更类型")
    old_eid = db.Column(db.String(20), comment="旧EID")
    new_eid = db.Column(db.String(20), comment="新EID")
    opercd = db.Column(db.String(6), comment="操作员")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    remark = db.Column(db.String(100), comment="备注")

    pos_change = db.relationship("PosChange", back_populates="details")


# ---------------------------------------------------------------------------
# 质检管理（TQC*）— Oracle 业务必须表
# ---------------------------------------------------------------------------


class QcResult(BaseModel):
    """质检结果主表（TQC10_RESULT）。"""

    __tablename__ = "tqc10_result"

    qcbillid = db.Column(db.String(8), primary_key=True, comment="质检单号")
    optyp = db.Column(db.String(2), comment="操作类型")
    refbillid = db.Column(db.String(8), comment="关联单号")
    itemcd = db.Column(db.String(6), comment="物料编码")
    eid = db.Column(db.String(13), comment="设备序列号")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    auditman = db.Column(db.String(6), comment="审核人")
    auditflg = db.Column(db.String(1), comment="审核标志")
    auditdate = db.Column(db.DateTime, comment="审核日期")
    qcstatus = db.Column(db.String(2), comment="质检状态")

    detail_items = db.relationship("QcResultDt", back_populates="qc_result", lazy="dynamic")
    detail_eids = db.relationship("QcResultEid", back_populates="qc_result", lazy="dynamic")


class QcResultDt(BaseModel):
    """质检结果明细-按产品（TQC11_RESULTDT）。"""

    __tablename__ = "tqc11_resultdt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    qcbillid = db.Column(
        db.String(8),
        db.ForeignKey("tqc10_result.qcbillid"),
        nullable=False,
        comment="质检单号",
    )
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    prddate = db.Column(db.DateTime, comment="生产日期")
    qcqty = db.Column(db.Numeric(12, 0), comment="质检数量")
    qcstatus = db.Column(db.String(2), comment="质检状态")
    inqty = db.Column(db.Numeric(12, 0), comment="入库数量")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    lineno = db.Column(db.Integer, comment="行号")
    fault_desc = db.Column(db.String(50), comment="故障描述")
    maintain_desc = db.Column(db.String(50), comment="维修描述")
    inspector = db.Column(db.String(8), comment="检验员")
    qc_source = db.Column(db.String(1), comment="质检来源")
    remark = db.Column(db.String(100), comment="备注")

    qc_result = db.relationship("QcResult", back_populates="detail_items")


class QcResultEid(BaseModel):
    """质检结果明细-按设备序列号（TQC11_RESULTEID）。"""

    __tablename__ = "tqc11_resulteid"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    qcbillid = db.Column(
        db.String(8),
        db.ForeignKey("tqc10_result.qcbillid"),
        nullable=False,
        comment="质检单号",
    )
    itemcd = db.Column(db.String(6), comment="物料编码")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    prddate = db.Column(db.DateTime, comment="生产日期")
    qcqty = db.Column(db.Numeric(12, 0), comment="质检数量")
    qcstatus = db.Column(db.String(2), comment="质检状态")
    inqty = db.Column(db.Numeric(12, 0), comment="入库数量")
    eid = db.Column(db.String(13), nullable=False, comment="设备序列号")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    opercd = db.Column(db.String(6), comment="操作员")
    lineno = db.Column(db.Integer, comment="行号")
    fault_desc = db.Column(db.String(100), comment="故障描述")
    maintain_desc = db.Column(db.String(100), comment="维修描述")
    inspector = db.Column(db.String(8), comment="检验员")
    qc_source = db.Column(db.String(1), comment="质检来源")
    remark = db.Column(db.String(100), comment="备注")
    manuf_seq = db.Column(db.String(100), comment="制造序列号")

    qc_result = db.relationship("QcResult", back_populates="detail_eids")


# ---------------------------------------------------------------------------
# 调拨科目管理（TTX01_TXKMG）
# ---------------------------------------------------------------------------


class TransferAccount(BaseModel):
    """调拨科目管理（TTX01_TXKMG）。"""

    __tablename__ = "ttx01_txkmg"

    txkno = db.Column(db.String(30), primary_key=True, comment="调拨科目编号")
    commmode = db.Column(db.String(10), comment="通讯方式")
    remark = db.Column(db.String(100), comment="备注")
    by1 = db.Column(db.String(10), comment="备用字段1")
    by2 = db.Column(db.String(10), comment="备用字段2")
    opercd = db.Column(db.String(6), comment="操作员")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
