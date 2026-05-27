"""采购管理模块请求/响应 Schema。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class PurchasePlanCreate(BaseModel):
    """创建采购计划。"""

    pctyp: str | None = Field(None, max_length=2, description="采购类型")
    slbillid: str | None = Field(None, max_length=8, description="关联销售单号")
    plandate: datetime | None = Field(None, description="计划日期")
    memo: str | None = Field(None, max_length=255, description="备注")


class PurchasePlanDetailCreate(BaseModel):
    """采购计划明细。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    rgstqty: int = Field(..., ge=1, description="登记数量")
    units: str | None = Field(None, max_length=4, description="单位")


class PurchaseRegisterCreate(BaseModel):
    """创建采购登记。"""

    suppliercd: str = Field(..., max_length=8, description="供应商编码")
    pcrep: str | None = Field(None, max_length=6, description="采购代表")
    rgstdate: datetime | None = Field(None, description="登记日期")
    memo: str | None = Field(None, max_length=255, description="备注")


class PurchaseRegisterDetailCreate(BaseModel):
    """采购登记明细。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    rgsqty: int = Field(..., ge=1, description="登记数量")
    units: str | None = Field(None, max_length=4, description="单位")
    rgstprice: float | None = Field(None, description="单价")
    deliverdate: datetime | None = Field(None, description="交付日期")


class PurchaseBillCreate(BaseModel):
    """创建采购结算单。"""

    suppliercd: str = Field(..., max_length=8, description="供应商编码")
    pay_type: str = Field("COD", max_length=3, description="付款方式 COD/PIA/DEP/MON/INS")
    invoice_no: str | None = Field(None, max_length=50, description="发票号码")
    invoice_date: date | None = Field(None, description="发票日期")
    pcdate: date | None = Field(None, description="结算日期")
    whcd: str | None = Field(None, max_length=50, description="入库仓库")
    memo: str | None = Field(None, max_length=255, description="备注")
    settlement_period: str | None = Field(None, max_length=7, description="月结周期(YYYY-MM)")
    settle_stage: str | None = Field("final", max_length=10, description="结算阶段(deposit=预付/final=尾款)")
    installment_no: int | None = Field(None, description="分期序号")
    total_installments: int | None = Field(None, description="分期总期数")
    due_date: date | None = Field(None, description="付款到期日")
    details: list["PurchaseBillDetailCreate"] = Field(..., min_length=1, description="结算明细")

    @field_validator("invoice_date", "pcdate", "due_date", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        if v == "" or v is None:
            return None
        return v


class PurchaseBillDetailCreate(BaseModel):
    """结算明细行。"""

    ref_rgstbillid: str = Field(..., max_length=8, description="来源采购订单号")
    ref_rgstlineno: int = Field(..., description="来源订单行号")
    itemcd: str = Field(..., max_length=6, description="物料编码")
    settle_qty: float = Field(..., gt=0, description="本次结算数量")
    settle_price: float = Field(..., gt=0, description="结算单价")


class PurchaseBillUpdate(BaseModel):
    """编辑采购结算单。"""

    suppliercd: str | None = Field(None, max_length=8)
    pay_type: str | None = Field(None, max_length=3)
    invoice_no: str | None = Field(None, max_length=50)
    invoice_date: date | None = Field(None)
    pcdate: date | None = Field(None)
    whcd: str | None = Field(None, max_length=50)
    memo: str | None = Field(None, max_length=255)
    settlement_period: str | None = Field(None, max_length=7)
    settle_stage: str | None = Field(None, max_length=10)
    installment_no: int | None = Field(None)
    total_installments: int | None = Field(None)
    due_date: date | None = Field(None)
    details: list["PurchaseBillDetailCreate"] | None = Field(None, description="结算明细（全量替换）")

    @field_validator("invoice_date", "pcdate", "due_date", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        if v == "" or v is None:
            return None
        return v


class SupplierAppraisalCreate(BaseModel):
    """创建供应商评价。"""

    sdate: datetime | None = Field(None, description="开始日期")
    edate: datetime | None = Field(None, description="结束日期")
    memo: str | None = Field(None, max_length=255, description="备注")


class SupplierAppraisalDetailCreate(BaseModel):
    """供应商评价明细。"""

    supplierid: str = Field(..., max_length=8, description="供应商编码")
    appcode: str | None = Field(None, max_length=2, description="评价代码")
    appscore: int | None = Field(None, description="评分")


class ReturnPurchaseBillCreate(BaseModel):
    """创建采购退货单。"""

    ref_rgstbillid: str = Field(..., max_length=8, description="来源采购订单号")
    return_reason: str = Field(..., max_length=20, description="退货原因")
    pcdate: date | None = Field(None, description="退货日期")
    whcd: str | None = Field(None, max_length=2, description="仓库编码")
    memo: str | None = Field(None, max_length=255, description="备注")
    details: list["ReturnPurchaseBillDetailCreate"] = Field(..., min_length=1, description="退货明细")


class ReturnPurchaseBillDetailCreate(BaseModel):
    """采购退货明细。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    ref_rgstlineno: int = Field(..., description="来源订单行号")
    rpcqty: int = Field(..., gt=0, description="退货数量")
    return_price: float | None = Field(None, description="退货单价")
    eid: str | None = Field(None, max_length=13, description="设备EID")
    seid: str | None = Field(None, max_length=30, description="序列号")
    units: str | None = Field(None, max_length=4, description="单位")
    line_reason: str | None = Field(None, max_length=100, description="行级退货原因")


class ReturnPurchaseBillUpdate(BaseModel):
    """编辑采购退货单。"""

    return_reason: str | None = Field(None, max_length=20)
    pcdate: date | None = Field(None)
    whcd: str | None = Field(None, max_length=2)
    memo: str | None = Field(None, max_length=255)
    details: list["ReturnPurchaseBillDetailCreate"] | None = Field(None, description="退货明细（全量替换）")


class PurchasePlanStatusCreate(BaseModel):
    """创建采购计划状态汇总。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    rgstqty: int = Field(0, description="登记数量")
    auditqty: int = Field(0, description="审批数量")
    pcqty: int = Field(0, description="采购数量")
    memo: str | None = Field(None, max_length=255, description="备注")
    refbillid: str | None = Field(None, max_length=8, description="关联单号")


class PurchasePlanStatusUpdate(BaseModel):
    """更新采购计划状态汇总。"""

    rgstqty: int | None = Field(None)
    auditqty: int | None = Field(None)
    pcqty: int | None = Field(None)
    memo: str | None = Field(None, max_length=255)
    refbillid: str | None = Field(None, max_length=8)


class ProcurementQuery(BaseModel):
    """采购查询参数。"""

    auditflg: str | None = Field(None, max_length=1)
    suppliercd: str | None = Field(None, max_length=8)
    pcplanid: str | None = Field(None, max_length=20, description="需求单号模糊搜索")
    rgstbillid: str | None = Field(None, max_length=8, description="订单号模糊搜索")
    ref_rgstbillid: str | None = Field(None, max_length=8, description="退货来源订单号模糊搜索")
    ref_pcplanid: str | None = Field(None, max_length=20, description="关联需求单号模糊搜索")
    pctyp: str | None = Field(None, max_length=2)
    whcd: str | None = Field(None, max_length=2)
    start_date: datetime | None = Field(None, description="计划日期起始")
    end_date: datetime | None = Field(None, description="计划日期截止")
    exclude_completed: bool = Field(False, description="排除已完成的需求单")
    execution_status: str | None = Field(None, description="执行状态筛选")
    overdue_only: bool = Field(False, description="仅显示逾期需求")
    hide_unavailable: bool = Field(False, description="隐藏无可订余额的需求")
    show_voided: bool = Field(False, description="是否显示已作废订单")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
