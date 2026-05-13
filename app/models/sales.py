"""
销售管理模型。

阶段3：预计划(PLAN_CUST) + 销售单据(TSL10) + 延期(TSL01/02)。

对应数据库表：
  预计划：PLAN_CUST
  销售单据：TSL10_SLBILL
  延期：TSL01_EXTEND / TSL02_EXTENDDT
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 预计划
# ---------------------------------------------------------------------------


class PlanCust(BaseModel):
    """预计划（PLAN_CUST）。"""

    __tablename__ = "plan_cust"

    planno = db.Column(db.String(10), primary_key=True, comment="计划编号")
    plantyp = db.Column(db.String(2), comment="计划类型")
    custnew = db.Column(db.String(2), comment="新旧客户标志")
    custcard = db.Column(db.String(20), comment="客户磁卡号")
    custcd = db.Column(db.String(8), comment="客户编码")
    custnm = db.Column(db.String(80), comment="客户名称")
    classcd = db.Column(db.String(6), comment="分类编码")
    busityp = db.Column(db.String(2), comment="业务类型")
    pptcode = db.Column(db.String(10), comment="属性代码")
    is_contract = db.Column(db.String(2), comment="是否合同")
    address = db.Column(db.String(80), comment="地址")
    contactor = db.Column(db.String(10), comment="联系人")
    phoneno = db.Column(db.String(60), comment="电话")
    custrnm = db.Column(db.String(80), comment="客户真实名称")
    jl_contactor = db.Column(db.String(10), comment="经理联系人")
    jl_phoneno = db.Column(db.String(60), comment="经理电话")
    pos_from = db.Column(db.String(6), comment="POS来源")
    pos_item = db.Column(db.String(6), comment="POS物料")
    posid = db.Column(db.String(13), comment="POS设备ID")
    new_custcard = db.Column(db.String(20), comment="新磁卡号")
    new_custcd = db.Column(db.String(8), comment="新客户编码")
    new_phoneno = db.Column(db.String(60), comment="新电话")
    new_address = db.Column(db.String(80), comment="新地址")
    new_custnm = db.Column(db.String(80), comment="新客户名称")
    new_positem = db.Column(db.String(6), comment="新POS物料")
    new_posid = db.Column(db.String(13), comment="新POS设备ID")
    solve_type = db.Column(db.String(2), comment="处理方式")
    back_status = db.Column(db.String(2), comment="回退状态")
    cust_useflg = db.Column(db.String(2), comment="客户有效标志")
    plan_status = db.Column(db.String(2), comment="计划状态")
    servetyp = db.Column(db.String(2), comment="服务类型")
    pl_serve_task = db.Column(db.String(200), comment="服务任务")
    imple_status = db.Column(db.String(2), comment="实施状态")
    commmode = db.Column(db.String(4), comment="通讯方式")
    serve_status = db.Column(db.String(2), comment="服务状态")
    plan_require = db.Column(db.String(200), comment="计划需求")
    imple_date = db.Column(db.DateTime, comment="实施日期")
    send_date = db.Column(db.DateTime, comment="发送日期")
    train_date = db.Column(db.DateTime, comment="培训日期")
    imple_mark = db.Column(db.String(200), comment="实施备注")
    imple_result = db.Column(db.String(10), comment="实施结果")
    fail_reason = db.Column(db.String(200), comment="失败原因")
    is_outflag = db.Column(db.String(2), comment="出库标志")
    status = db.Column(db.String(2), comment="状态")
    gendate = db.Column(db.DateTime, comment="创建日期")
    opercd = db.Column(db.String(6), comment="操作员")
    propo_item = db.Column(db.String(20), comment="推荐物料")
    serve_ercd = db.Column(db.String(6), comment="服务工程师")
    deposit = db.Column(db.Numeric(12, 2), comment="押金金额")
    is_rent = db.Column(db.String(1), comment="是否租赁")
    yun_type = db.Column(db.String(2), comment="运营类型")
    upload_type = db.Column(db.String(2), comment="上传类型")


# ---------------------------------------------------------------------------
# 销售单据
# ---------------------------------------------------------------------------


class SalesBill(BaseModel):
    """销售单据（TSL10_SLBILL）。"""

    __tablename__ = "tsl10_slbill"

    slbillid = db.Column(db.String(8), primary_key=True, comment="销售单号")
    custbillid = db.Column(db.String(20), comment="客户单号")
    sltyp = db.Column(db.String(2), comment="销售类型")
    custcd = db.Column(db.String(8), comment="客户编码")
    rgsdate = db.Column(db.DateTime, comment="登记日期")
    senddate = db.Column(db.DateTime, comment="发货日期")
    busityp = db.Column(db.String(2), comment="业务类型")
    ptimes = db.Column(db.Integer, comment="打印次数")
    opercd = db.Column(db.String(6), comment="操作员")
    memo = db.Column(db.String(255), comment="备注")
    gendate = db.Column(db.DateTime, comment="创建日期")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")
    checkmemo = db.Column(db.String(255), comment="审核备注")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    pcplanflg = db.Column(db.String(1), comment="采购计划标志")
    rfpcplanid = db.Column(db.String(8), comment="关联采购计划号")
    itemcd = db.Column(db.String(6), comment="物料编码")
    rgsqty = db.Column(db.Integer, default=0, comment="登记数量")
    planqty = db.Column(db.Integer, default=0, comment="计划数量")
    openqty = db.Column(db.Integer, default=0, comment="开通数量")
    clqty = db.Column(db.Integer, default=0, comment="关闭数量")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


# ---------------------------------------------------------------------------
# 延期
# ---------------------------------------------------------------------------


class SalesExtend(BaseModel):
    """延期主表（TSL01_EXTEND）。"""

    __tablename__ = "tsl01_extend"

    opbillid = db.Column(db.String(8), primary_key=True, comment="延期单号")
    slbillid = db.Column(db.String(8), comment="关联销售单号")
    custcd = db.Column(db.String(8), comment="客户编码")
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

    details = db.relationship("SalesExtendDt", back_populates="extend", lazy="dynamic")


class SalesExtendDt(BaseModel):
    """延期明细（TSL02_EXTENDDT）。"""

    __tablename__ = "tsl02_extenddt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    opbillid = db.Column(
        db.String(8),
        db.ForeignKey("tsl01_extend.opbillid"),
        nullable=False,
        comment="延期单号",
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
    is_back = db.Column(db.String(1), comment="是否退回")
    ufdate = db.Column(db.DateTime, comment="退回日期")
    mr = db.Column(db.String(1), comment="MR标志")

    extend = db.relationship("SalesExtend", back_populates="details")
