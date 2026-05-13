"""
押金管理模型。

阶段4：押金主记录 + 变更明细 + 出入记录 + 清单 + 设备型号押金标准。

对应数据库表：
  押金主记录：TMM61_DEPOSIT
  押金变更明细：TMM61_DEPOSIT_DTL
  押金出入记录：TMM61_DEPOSIT_IO
  押金清单：TMM61_DEPOSIT_LIST
  设备型号押金标准：TMM61_DEPOSIT_POSMODEL
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 押金主记录
# ---------------------------------------------------------------------------


class Deposit(BaseModel):
    """押金主记录（TMM61_DEPOSIT）。"""

    __tablename__ = "tmm61_deposit"

    custcd = db.Column(db.String(10), primary_key=True, comment="客户编码")
    amount_money = db.Column(db.Numeric(12, 2), comment="押金余额")
    updatetime = db.Column(db.DateTime, comment="更新时间")
    r_billid = db.Column(db.String(20), comment="关联单号")
    modelcd = db.Column(db.String(20), comment="型号编码")
    modelnm = db.Column(db.String(20), comment="型号名称")

    details = db.relationship("DepositDetail", back_populates="deposit", lazy="dynamic")


# ---------------------------------------------------------------------------
# 押金变更明细
# ---------------------------------------------------------------------------


class DepositDetail(BaseModel):
    """押金变更明细（TMM61_DEPOSIT_DTL）。"""

    __tablename__ = "tmm61_deposit_dtl"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    custcd = db.Column(
        db.String(10),
        db.ForeignKey("tmm61_deposit.custcd"),
        nullable=False,
        comment="客户编码",
    )
    c_type = db.Column(db.String(10), comment="变更类型")
    old_a = db.Column(db.Numeric(12, 2), comment="原金额")
    new_a = db.Column(db.Numeric(12, 2), comment="新金额")
    change_a = db.Column(db.Numeric(12, 2), comment="变更金额")
    updatetime = db.Column(db.DateTime, comment="更新时间")
    r_billid = db.Column(db.String(10), comment="关联单号")
    confirm_a = db.Column(db.Numeric(12, 2), comment="确认金额")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    remark = db.Column(db.String(200), comment="备注")
    gendate = db.Column(db.DateTime, comment="创建日期")

    deposit = db.relationship("Deposit", back_populates="details")


# ---------------------------------------------------------------------------
# 押金出入记录
# ---------------------------------------------------------------------------


class DepositIO(BaseModel):
    """押金出入记录（TMM61_DEPOSIT_IO）。"""

    __tablename__ = "tmm61_deposit_io"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    custcd = db.Column(db.String(10), nullable=False, comment="客户编码")
    r_billid = db.Column(db.Integer, comment="关联单号")
    new_a = db.Column(db.Numeric(12, 2), comment="新金额")
    old_a = db.Column(db.Numeric(12, 2), comment="原金额")
    change_a = db.Column(db.Numeric(12, 2), comment="变更金额")
    update_time = db.Column(db.DateTime, comment="更新时间")


# ---------------------------------------------------------------------------
# 押金清单
# ---------------------------------------------------------------------------


class DepositList(BaseModel):
    """押金清单（TMM61_DEPOSIT_LIST）。"""

    __tablename__ = "tmm61_deposit_list"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    custcd = db.Column(db.String(10), nullable=False, comment="客户编码")
    billid = db.Column(db.String(30), comment="单据编号")
    updatetime = db.Column(db.DateTime, comment="更新时间")
    remark = db.Column(db.String(100), comment="备注")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    c_money = db.Column(db.Numeric(12, 2), comment="金额")
    c_a = db.Column(db.String(150), comment="字段A")
    c_b = db.Column(db.String(150), comment="字段B")
    c_c = db.Column(db.String(150), comment="字段C")
    c_d = db.Column(db.String(150), comment="字段D")
    c_e = db.Column(db.String(150), comment="字段E")
    c_f = db.Column(db.String(150), comment="字段F")
    c_g = db.Column(db.String(150), comment="字段G")
    c_h = db.Column(db.String(150), comment="字段H")
    c_i = db.Column(db.String(150), comment="字段I")
    c_j = db.Column(db.String(150), comment="字段J")
    c_k = db.Column(db.String(150), comment="字段K")
    c_l = db.Column(db.String(150), comment="字段L")
    c_m = db.Column(db.String(150), comment="字段M")
    c_n = db.Column(db.String(150), comment="字段N")
    c_o = db.Column(db.String(150), comment="字段O")
    c_p = db.Column(db.String(150), comment="字段P")
    c_q = db.Column(db.String(150), comment="字段Q")
    c_r = db.Column(db.String(150), comment="字段R")
    c_s = db.Column(db.String(150), comment="字段S")
    c_t = db.Column(db.String(150), comment="字段T")
    c_u = db.Column(db.String(150), comment="字段U")
    c_v = db.Column(db.String(150), comment="字段V")
    c_w = db.Column(db.String(150), comment="字段W")
    c_x = db.Column(db.String(150), comment="字段X")
    c_y = db.Column(db.String(150), comment="字段Y")
    c_z = db.Column(db.String(150), comment="字段Z")


# ---------------------------------------------------------------------------
# 设备型号押金标准
# ---------------------------------------------------------------------------


class DepositPosModel(BaseModel):
    """设备型号押金标准（TMM61_DEPOSIT_POSMODEL）。"""

    __tablename__ = "tmm61_deposit_posmodel"

    model_cd = db.Column(db.String(8), primary_key=True, comment="型号编码")
    model_nm = db.Column(db.String(20), comment="型号名称")
    rent_money = db.Column(db.Numeric(10, 2), comment="租金")
    sale_money = db.Column(db.Numeric(10, 2), comment="售价")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
