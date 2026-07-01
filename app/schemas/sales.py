"""销售管理模块请求/响应 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlanCustCreate(BaseModel):
    """创建预计划。"""

    plantyp: str = Field(..., max_length=2, description="计划类型")
    custcd: str | None = Field(None, max_length=8, description="客户编码")
    custnm: str | None = Field(None, max_length=80, description="客户名称")
    custcard: str | None = Field(None, max_length=20, description="磁卡号")
    custrnm: str | None = Field(None, max_length=80, description="客户实名")
    busityp: str | None = Field(None, max_length=2, description="业务类型")
    address: str | None = Field(None, max_length=80, description="地址")
    contactor: str | None = Field(None, max_length=10, description="联系人")
    phoneno: str | None = Field(None, max_length=60, description="电话")
    pos_item: str | None = Field(None, max_length=6, description="POS物料/机型")
    is_rent: str | None = Field(None, max_length=1, description="是否租赁(Y/N)")
    deposit: float | None = Field(None, description="押金金额")
    yun_type: str | None = Field(None, max_length=2, description="运营类型")
    # PB 补充字段（按 plantyp 条件显示）
    cust_useflg: str | None = Field(None, max_length=2, description="客户无效化勾选")
    pos_from: str | None = Field(None, max_length=2, description="设备来源(00建议/01移机/02返修)")
    new_custcard: str | None = Field(None, max_length=20, description="新磁卡号")
    new_positem: str | None = Field(None, max_length=6, description="新机型")
    new_posid: str | None = Field(None, max_length=13, description="新设备EID")
    new_custcd: str | None = Field(None, max_length=8, description="新客户编码")
    new_custnm: str | None = Field(None, max_length=80, description="新客户名称")
    new_address: str | None = Field(None, max_length=80, description="新地址")
    new_phoneno: str | None = Field(None, max_length=60, description="新电话")
    propo_item: str | None = Field(None, max_length=20, description="推荐物料")
    solve_type: str | None = Field(None, max_length=2, description="解决方式")
    classcd: str | None = Field(None, max_length=6, description="客户分类")
    pptcode: str | None = Field(None, max_length=10, description="属性代码")
    is_contract: str | None = Field(None, max_length=2, description="是否合同")
    commmode: str | None = Field(None, max_length=4, description="通讯方式")
    custnew: str | None = Field(None, max_length=2, description="新旧客户标志")
    upload_type: str | None = Field(None, max_length=2, description="上传类型")
    posid: str | None = Field(None, max_length=13, description="设备EID")
    jl_contactor: str | None = Field(None, max_length=10, description="经理联系人")
    jl_phoneno: str | None = Field(None, max_length=60, description="经理电话")
    # PB cbx_serve 勾选:保存时同步生成预计划呼出单(servetyp=1)
    call_serve: bool = Field(False, description="保存时触发请求呼出(对齐 PB cbx_serve)")
    serve_task: str | None = Field(None, max_length=200, description="呼出任务描述(对齐 PB sle_task)")


class PlanCustUpdate(BaseModel):
    """更新预计划。"""

    plantyp: str | None = Field(None, max_length=2)
    custnm: str | None = Field(None, max_length=80)
    custcard: str | None = Field(None, max_length=20)
    custrnm: str | None = Field(None, max_length=80)
    busityp: str | None = Field(None, max_length=2)
    address: str | None = Field(None, max_length=80)
    contactor: str | None = Field(None, max_length=10)
    phoneno: str | None = Field(None, max_length=60)
    pos_item: str | None = Field(None, max_length=6)
    is_rent: str | None = Field(None, max_length=1)
    deposit: float | None = Field(None)
    yun_type: str | None = Field(None, max_length=2)
    plan_status: str | None = Field(None, max_length=2)
    imple_status: str | None = Field(None, max_length=2)
    serve_status: str | None = Field(None, max_length=2)
    imple_date: str | None = Field(None)
    imple_mark: str | None = Field(None, max_length=200)
    imple_result: str | None = Field(None, max_length=10)
    fail_reason: str | None = Field(None, max_length=200)
    # PB 补充字段
    cust_useflg: str | None = Field(None, max_length=2)
    pos_from: str | None = Field(None, max_length=2)
    new_custcard: str | None = Field(None, max_length=20)
    new_positem: str | None = Field(None, max_length=6)
    new_posid: str | None = Field(None, max_length=13)
    new_custcd: str | None = Field(None, max_length=8)
    new_custnm: str | None = Field(None, max_length=80)
    new_address: str | None = Field(None, max_length=80)
    new_phoneno: str | None = Field(None, max_length=60)
    propo_item: str | None = Field(None, max_length=20)
    solve_type: str | None = Field(None, max_length=2)
    classcd: str | None = Field(None, max_length=6)
    pptcode: str | None = Field(None, max_length=10)
    is_contract: str | None = Field(None, max_length=2)
    commmode: str | None = Field(None, max_length=4)
    custnew: str | None = Field(None, max_length=2)
    upload_type: str | None = Field(None, max_length=2)
    posid: str | None = Field(None, max_length=13)
    jl_contactor: str | None = Field(None, max_length=10)
    jl_phoneno: str | None = Field(None, max_length=60)


class SalesBillCreate(BaseModel):
    """创建销售单据。"""

    sltyp: str = Field(..., max_length=2, description="销售类型")
    custcd: str = Field(..., max_length=8, description="客户编码")
    busityp: str | None = Field(None, max_length=2, description="业务类型")
    itemcd: str | None = Field(None, max_length=6, description="物料编码")
    rgsqty: int | None = Field(None, description="登记数量")
    memo: str | None = Field(None, max_length=255, description="备注")


class SalesExtendCreate(BaseModel):
    """创建延期。"""

    slbillid: str = Field(..., max_length=8, description="关联销售单号")
    custcd: str = Field(..., max_length=8, description="客户编码")
    busityp: str | None = Field(None, max_length=2, description="业务类型")
    sltyp: str | None = Field(None, max_length=2, description="销售类型")
    itemcd: str | None = Field(None, max_length=6, description="物料编码")
    backup: str | None = Field(None, max_length=255, description="备注")


class SalesExtendDetailCreate(BaseModel):
    """延期明细。"""

    custcd: str = Field(..., max_length=8, description="客户编码")
    custcard: str | None = Field(None, max_length=20, description="客户磁卡号")
    eid: str | None = Field(None, max_length=13, description="设备EID")
    planqty: int | None = Field(None, description="计划数量")


class PlanTransition(BaseModel):
    """预计划状态流转。"""

    to_status: str = Field(..., max_length=2, description="目标状态码")
    remark: str | None = Field(None, max_length=200, description="备注")


class PlanVoid(BaseModel):
    """预计划作废。"""

    remark: str | None = Field(None, max_length=200, description="作废原因")


class PlanServeCreate(BaseModel):
    """创建呼出单。"""

    planno: str = Field(..., max_length=10, description="关联预计划单号")
    plantyp: str | None = Field(None, max_length=2)
    servetyp: str = Field("0", max_length=2, description="服务类型")
    serve_task: str | None = Field(None, max_length=200, description="服务任务")
    serve_back: str | None = Field(None, max_length=200, description="客户反馈/呼出结果")
    serve_mark: str | None = Field(None, max_length=200, description="服务备注")
    commmode: str | None = Field(None, max_length=4, description="通讯方式")


class PlanServeUpdate(BaseModel):
    """更新呼出单（反馈呼出结果）。"""

    serve_back: str | None = Field(None, max_length=200, description="客户反馈")
    serve_mark: str | None = Field(None, max_length=200, description="服务备注")
    status: str | None = Field(None, max_length=2, description="状态")


class SalesQuery(BaseModel):
    """销售查询参数。"""

    plantyp: str | None = Field(None, max_length=2)
    plan_status: str | None = Field(None, max_length=2)
    sltyp: str | None = Field(None, max_length=2)
    planno: str | None = Field(None, max_length=10, description="计划单号（模糊）")
    custcd: str | None = Field(None, max_length=8)
    custnm: str | None = Field(None, max_length=50, description="客户名称（模糊）")
    custcard: str | None = Field(None, max_length=20, description="客户磁卡号（模糊）")
    date_from: str | None = Field(None, description="计划日期起（YYYY-MM-DD）")
    date_to: str | None = Field(None, description="计划日期止（YYYY-MM-DD）")
    serve_status: str | None = Field(None, max_length=2, description="呼出状态：01=呼出中")
    auditflg: str | None = Field(None, max_length=1)
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
