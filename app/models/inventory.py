"""
库存预警与价格管理模型。

阶段4：库存上下限预警 + 价格体系 + 调价。

对应数据库表：
  库存预警：TIV01_INVLIMIT / TIV02_INVLIMIT_HI
  价格规则：TIP01_PRICE / TIP03_ADJPRICE
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 库存预警
# ---------------------------------------------------------------------------


class InventoryLimit(BaseModel):
    """库存上下限预警（TIV01_INVLIMIT）。"""

    __tablename__ = "tiv01_invlimit"

    itemcd = db.Column(db.String(8), primary_key=True, comment="物料编码")
    invlow = db.Column(db.Numeric(12, 4), comment="库存下限")
    invhigh = db.Column(db.Numeric(12, 4), comment="库存上限")
    daylow = db.Column(db.Integer, comment="天数下限")
    dayhigh = db.Column(db.Integer, comment="天数上限")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class InventoryLimitHistory(BaseModel):
    """库存预警历史（TIV02_INVLIMIT_HI）。"""

    __tablename__ = "tiv02_invlimit_hi"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itemcd = db.Column(db.String(8), nullable=False, comment="物料编码")
    lineid = db.Column(db.Numeric(12, 4), comment="行号")
    invlow = db.Column(db.Numeric(12, 4), comment="库存下限")
    invhigh = db.Column(db.Numeric(12, 4), comment="库存上限")
    daylow = db.Column(db.Integer, comment="天数下限")
    dayhigh = db.Column(db.Integer, comment="天数上限")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


# ---------------------------------------------------------------------------
# 价格规则
# ---------------------------------------------------------------------------


class Price(BaseModel):
    """价格规则（TIP01_PRICE）。"""

    __tablename__ = "tip01_price"
    __table_args__ = (db.PrimaryKeyConstraint("itemcd", "busityp"),)

    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    busityp = db.Column(db.String(6), nullable=False, comment="业务类型")
    unitcd = db.Column(db.String(6), comment="单位")
    itemprice = db.Column(db.Numeric(16, 8), comment="物料单价")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class AdjustPrice(BaseModel):
    """调价记录（TIP03_ADJPRICE）。"""

    __tablename__ = "tip03_adjprice"
    __table_args__ = (db.PrimaryKeyConstraint("pabillid", "lineno"),)

    pabillid = db.Column(db.String(8), nullable=False, comment="调价单号")
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemcd = db.Column(db.String(6), comment="物料编码")
    busityp = db.Column(db.String(2), comment="业务类型")
    oldprice = db.Column(db.Numeric(16, 8), comment="原价")
    newprice = db.Column(db.Numeric(16, 8), comment="新价")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志（AdjustPrice）")


# ---------------------------------------------------------------------------
# 库存明细（TIV11/TIV12）— Oracle 业务必须表，用于库存预警模块
# ---------------------------------------------------------------------------


class InventoryDetail(BaseModel):
    """库存明细（TIV11_DETAIL）。"""

    __tablename__ = "tiv11_detail"

    itemcd = db.Column(db.String(8), primary_key=True, comment="物料编码")
    whcd = db.Column(db.String(2), comment="仓库编码")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    storeqty = db.Column(db.Numeric(12, 0), comment="库存数量")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    detail_logs = db.relationship(
        "InventoryDetailDt", back_populates="inventory_detail", lazy="dynamic"
    )


class InventoryDetailDt(BaseModel):
    """库存明细流水（TIV12_DETAILDT）。"""

    __tablename__ = "tiv12_detaildt"

    seqno = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="流水号")
    itemcd = db.Column(
        db.String(8),
        db.ForeignKey("tiv11_detail.itemcd"),
        comment="物料编码",
    )
    whcd = db.Column(db.String(2), comment="仓库编码")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    billid = db.Column(db.String(8), comment="单号")
    invdate = db.Column(db.DateTime, comment="库存日期")
    invtyp = db.Column(db.String(1), comment="出入库类型")
    itemqty = db.Column(db.Numeric(12, 0), comment="本次数量")
    storeqty = db.Column(db.Numeric(12, 0), comment="库存数量")
    opercd = db.Column(db.String(6), comment="操作员")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    inventory_detail = db.relationship("InventoryDetail", back_populates="detail_logs")
