"""ITSM 业务模块请求/响应 Schema。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 日常维护单 (TIT10)
# ---------------------------------------------------------------------------


class MaintenanceDailyCreate(BaseModel):
    """创建日常维护单。"""

    store_id: str = Field(..., max_length=8, description="门店ID")
    fault_type: str | None = Field(None, max_length=8, description="故障类型")
    servrity: str | None = Field(None, max_length=1, description="严重程度")
    emergency_level: str | None = Field(None, max_length=1, description="紧急程度")
    priority: str | None = Field(None, max_length=1, description="优先级")
    short_description: str | None = Field(None, max_length=80, description="故障简述")
    detail_description: str | None = Field(None, max_length=200, description="详细描述")
    device_id: str | None = Field(None, max_length=13, description="设备编号")
    source_type: str | None = Field(None, max_length=10, description="来源类型")
    temp_contract: str | None = Field(None, max_length=60, description="临时联系电话")


class MaintenanceDailyUpdate(BaseModel):
    """更新日常维护单。"""

    store_id: str | None = Field(None, max_length=8, description="门店ID")
    fault_type: str | None = Field(None, max_length=8, description="故障类型")
    servrity: str | None = Field(None, max_length=1, description="严重程度")
    emergency_level: str | None = Field(None, max_length=1, description="紧急程度")
    priority: str | None = Field(None, max_length=1, description="优先级")
    short_description: str | None = Field(None, max_length=80, description="故障简述")
    detail_description: str | None = Field(None, max_length=200, description="详细描述")
    device_id: str | None = Field(None, max_length=13, description="设备编号")
    temp_contract: str | None = Field(None, max_length=60, description="临时联系电话")
    memo: str | None = Field(None, max_length=200, description="关单分类")


class StatusTransition(BaseModel):
    """状态流转请求。"""

    to_status: str = Field(..., min_length=1, max_length=2, description="目标状态码")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 分派 (TIT21)
# ---------------------------------------------------------------------------


class DispatchCreate(BaseModel):
    """创建分派。"""

    maintenance_id: str = Field(..., max_length=8, description="维护单ID")
    maintenance_type: str | None = Field(None, max_length=2, description="维护类型（已废弃，保留兼容）")
    operator: str | None = Field(None, max_length=6, description="操作人")
    accpectd_group: str | None = Field(None, max_length=2, description="分派组")
    accpectder: str | None = Field(None, max_length=6, description="分派人")
    dispatch_time: datetime | None = Field(None, description="分派时间")


# ---------------------------------------------------------------------------
# 上门服务 (TIT23) — 公用
# ---------------------------------------------------------------------------


class D2DCreate(BaseModel):
    """创建上门服务记录。"""

    maintenance_id: str = Field(..., max_length=8, description="维护单ID（跨单据复用）")
    d2d_engineer: str = Field(..., max_length=6, description="上门工程师")
    d2d_type: str = Field(..., max_length=1, description="类型（1到店/2离店/3催单/4记录）")
    arrive_time: datetime | None = Field(None, description="到达时间")
    leave_time: datetime | None = Field(None, description="离店时间")
    # jjbz 字段已废弃（事项 18），保留 PB 数据迁移兼容，新数据用 d2d_result
    # jjbz: str | None = Field(None, max_length=1, description="解决标志（1已解决/0未解决）")
    d2d_descripiton: str | None = Field(None, max_length=200, description="处理过程描述（保留 PB 兼容，离店保存时后端自动拼句双写）")
    d2d_phone: str | None = Field(None, max_length=60, description="电话")
    # 离店解决四要素结构化字段（事项 18）
    d2d_phenomenon: str | None = Field(None, max_length=200, description="实际现象")
    d2d_reason: str | None = Field(None, max_length=200, description="原因")
    d2d_handling: str | None = Field(None, max_length=500, description="处理过程（工程师手输补充）")
    d2d_result: str | None = Field(None, max_length=2, description="结果（ZT 字典码值：5已解决/4未解决/6转修/7待配件/3关闭）")
    closure_reason: str | None = Field(None, max_length=1, description="关闭原因（仅 d2d_result=3 时填，CLO_REASON 字典）")
    d2d_note: str | None = Field(None, max_length=200, description="其他补充")
    # 故障代码与设备/配件追溯字段（事项 1 方案 B：只落 gzdm，大类/小类从 gzdm 派生或 join tit04）
    gzdm: str | None = Field(None, max_length=8, description="故障代码（= tit04_archivecode.arch_cd 值）")
    device_id: str | None = Field(None, max_length=13, description="本次处理设备")
    accessories_id: str | None = Field(None, max_length=13, description="本次处理配件")


class D2DArriveCreate(BaseModel):
    """到店登记（d2d_type='1'）。"""

    d2d_engineer: str = Field(..., max_length=6, description="上门工程师")
    arrive_time: datetime | None = Field(None, description="到达时间（默认当前）")
    d2d_phone: str | None = Field(None, max_length=60, description="电话")
    d2d_descripiton: str | None = Field(None, max_length=200, description="到场说明")


class D2DLeaveCreate(BaseModel):
    """离店登记（d2d_type='2'，四要素结构化）。

    必填：d2d_result（离店结果）
    d2d_result='3' 时 closure_reason 必填（Service 层校验）
    """

    d2d_engineer: str = Field(..., max_length=6, description="上门工程师")
    d2d_result: str = Field(..., max_length=2, description="结果（ZT 字典码值：5已解决/4未解决/6转修/7待配件/3关闭）")
    d2d_phenomenon: str | None = Field(None, max_length=200, description="实际现象")
    d2d_reason: str | None = Field(None, max_length=200, description="原因")
    d2d_handling: str | None = Field(None, max_length=500, description="处理过程（工程师手输补充）")
    closure_reason: str | None = Field(None, max_length=1, description="关闭原因（仅 d2d_result=3 时填）")
    d2d_note: str | None = Field(None, max_length=200, description="其他补充")
    gzdm: str | None = Field(None, max_length=8, description="故障代码")
    device_id: str | None = Field(None, max_length=13, description="本次处理设备")
    accessories_id: str | None = Field(None, max_length=13, description="本次处理配件")
    leave_time: datetime | None = Field(None, description="离店时间（默认当前）")
    d2d_phone: str | None = Field(None, max_length=60, description="电话")
    posstatus: str | None = Field(None, max_length=2, description="POS主状态（默认01=正常）")
    posstatus1: str | None = Field(None, max_length=2, description="POS子状态（默认11=正常使用）")


class D2DUrgeCreate(BaseModel):
    """催单（d2d_type='3'）。"""

    d2d_engineer: str = Field(..., max_length=6, description="上门工程师")
    d2d_descripiton: str | None = Field(None, max_length=200, description="催单说明")
    d2d_phone: str | None = Field(None, max_length=60, description="电话")


class D2DRecordCreate(BaseModel):
    """记录（d2d_type='4'，到场说明/客户反馈）。"""

    d2d_engineer: str | None = Field(None, max_length=6, description="上门工程师（记录类型可留空）")
    d2d_descripiton: str | None = Field(None, max_length=200, description="记录内容")
    d2d_phone: str | None = Field(None, max_length=60, description="电话")


# ---------------------------------------------------------------------------
# 回访 (TIT24) — 公用
# ---------------------------------------------------------------------------


class RVCreate(BaseModel):
    """创建回访记录。"""

    maintenance_id: str = Field(..., max_length=8, description="维护单ID")
    rv_operator: str = Field(..., max_length=20, description="回访人员")
    rv_time: datetime | None = Field(None, description="回访时间")
    feedback: str | None = Field(None, max_length=200, description="客户反馈")
    satisfaction: str | None = Field(None, max_length=1, description="满意度")


# ---------------------------------------------------------------------------
# 配件更新 (TIT25)
# ---------------------------------------------------------------------------


class AccessoriesUpdateCreate(BaseModel):
    """创建配件更新记录。"""

    maintenance_id: str = Field(..., max_length=8, description="维修单ID")
    store_id: str | None = Field(None, max_length=8, description="门店ID")
    device_id: str | None = Field(None, max_length=13, description="整机ID")
    old_accessories_id: str | None = Field(None, max_length=13, description="旧配件ID")
    new_accessories_id: str | None = Field(None, max_length=13, description="新配件ID")
    accessories_type: str | None = Field(None, max_length=60, description="配件类型名称")
    description: str | None = Field(None, max_length=200, description="过程描述")
    price: float | None = Field(None, description="价格")
    engineer_id: str | None = Field(None, max_length=6, description="工程师ID")
    c_type: str | None = Field(None, max_length=1, description="操作类型（C_TYPE 字典：1维修/2购买/3纯服务费/4整机更换/5耗材线材）")
    is_new: str | None = Field(None, max_length=1, description="是否新品（1=新品→old_degree=12/0=旧品→old_degree=3，对齐 PB IS_NEW）")
    # B3：配件更换关联故障代码
    itemcd: str | None = Field(None, max_length=13, description="配件物料编码（B3：关联故障代码用）")
    fault_cd: str | None = Field(None, max_length=8, description="故障代码（B3：配件更换时自动关联）")
    # 收费维度字段（事项 C1：合并 TIT26 功能）
    payje: float | None = Field(None, description="收款金额（c_type=3/5 时填，c_type=1/2/4 时与 price 同步）")
    paytype: str | None = Field(None, max_length=20, description="收费类型（c_type=3 用 PAY_SVC 字典，c_type=5 用 PAY_CONS 字典）")
    paydate: datetime | None = Field(None, description="收款日期")
    memo: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 关单 (TIT27)
# ---------------------------------------------------------------------------


class CloseBillCreate(BaseModel):
    """创建关单记录。"""

    maintenance_id: str = Field(..., max_length=8, description="任务单ID")
    close_time: datetime | None = Field(None, description="关单时间")
    close_type: str | None = Field(None, max_length=2, description="关单类型")
    description: str | None = Field(None, max_length=200, description="描述")
    is_old: str | None = Field(None, max_length=1, description="是否补关单")


# ---------------------------------------------------------------------------
# 磁卡号变更 (TIT16)
# ---------------------------------------------------------------------------


class DeviceChangeCreate(BaseModel):
    """创建磁卡号变更单。"""

    store_id: str = Field(..., max_length=8, description="门店ID")
    change_type: str = Field(..., max_length=8, description="变更类型（CK=仅磁卡号/BQ=信息变更/BG=磁卡号+设备）")
    device_id: str | None = Field(None, max_length=13, description="整机ID")
    new_contactor: str | None = Field(None, max_length=10, description="变更后联系人")
    new_tel: str | None = Field(None, max_length=60, description="变更后电话")
    new_address: str | None = Field(None, max_length=200, description="变更后地址")
    new_store_card: str | None = Field(None, max_length=20, description="变更后门店磁卡号")
    new_store_id: str | None = Field(None, max_length=8, description="变更后门店ID")
    is_store_inside_change: str | None = Field(None, max_length=1, description="是否店内移机")
    short_description: str | None = Field(None, max_length=80, description="简述")
    detail_description: str | None = Field(None, max_length=200, description="详细描述")


class DeviceChangeUpdate(BaseModel):
    """更新磁卡号变更单（所有字段可选）。"""

    device_id: str | None = Field(None, max_length=13)
    new_contactor: str | None = Field(None, max_length=10)
    new_tel: str | None = Field(None, max_length=60)
    new_address: str | None = Field(None, max_length=200)
    new_store_card: str | None = Field(None, max_length=20)
    new_store_id: str | None = Field(None, max_length=8)
    is_store_inside_change: str | None = Field(None, max_length=1)
    short_description: str | None = Field(None, max_length=80)
    detail_description: str | None = Field(None, max_length=200)


# ---------------------------------------------------------------------------
# 新机开通 (TIT13)
# ---------------------------------------------------------------------------


class MaintenanceOpenCreate(BaseModel):
    """创建新机开通单。"""

    store_id: str = Field(..., max_length=8, description="门店ID")
    device_id: str | None = Field(None, max_length=13, description="整机编号")
    count: int | None = Field(None, description="开通数量")
    short_description: str | None = Field(None, max_length=80, description="简述")
    detail_description: str | None = Field(None, max_length=200, description="详细描述")


class MaintenanceOpenUpdate(BaseModel):
    """更新新机开通单（所有字段可选）。"""

    device_id: str | None = Field(None, max_length=13)
    count: int | None = Field(None)
    short_description: str | None = Field(None, max_length=80)
    detail_description: str | None = Field(None, max_length=200)


# ---------------------------------------------------------------------------
# 旧机翻新 (TIT15)
# ---------------------------------------------------------------------------


class MaintenanceRenovateCreate(BaseModel):
    """创建旧机翻新单。"""

    store_id: str = Field(..., max_length=8, description="门店ID")
    old_device_id: str | None = Field(None, max_length=13, description="旧设备编号")
    new_device_id: str | None = Field(None, max_length=13, description="换新设备编号")
    count: int | None = Field(None, description="变更数量")
    short_description: str | None = Field(None, max_length=80, description="简述")
    detail_description: str | None = Field(None, max_length=200, description="详细描述")


class MaintenanceRenovateUpdate(BaseModel):
    """更新旧机翻新单（所有字段可选）。"""

    old_device_id: str | None = Field(None, max_length=13)
    new_device_id: str | None = Field(None, max_length=13)
    count: int | None = Field(None)
    short_description: str | None = Field(None, max_length=80)
    detail_description: str | None = Field(None, max_length=200)


# ---------------------------------------------------------------------------
# 门店关闭 (TIT18)
# ---------------------------------------------------------------------------


class StoreCloseCreate(BaseModel):
    """创建门店关闭单。"""

    store_id: str = Field(..., max_length=8, description="门店ID")
    close_type: str | None = Field(None, max_length=2, description="关闭类型")
    temp_close_date_begin: datetime | None = Field(None, description="临时关闭开始时间")
    temp_close_date_end: datetime | None = Field(None, description="临时关闭结束时间")
    short_description: str | None = Field(None, max_length=80, description="简述")
    detail_description: str | None = Field(None, max_length=200, description="详细描述")


class StoreCloseUpdate(BaseModel):
    """更新门店关闭单（所有字段可选）。"""

    close_type: str | None = Field(None, max_length=2)
    temp_close_date_begin: datetime | None = Field(None)
    temp_close_date_end: datetime | None = Field(None)
    short_description: str | None = Field(None, max_length=80)
    detail_description: str | None = Field(None, max_length=200)


# ---------------------------------------------------------------------------
# 回收任务 (TIT20) — P0-1/优化4.2
# ---------------------------------------------------------------------------


class RecycleTaskCreate(BaseModel):
    """创建回收任务。"""

    cust_cd: str = Field(..., max_length=8, description="门店代码")
    recycle_type: str | None = Field(None, max_length=2, description="回收类型")
    plan_no: str | None = Field(None, max_length=10, description="来源预计划单号")
    maintenance_id: str | None = Field(None, max_length=8, description="关联维护单号")
    asset_count: int | None = Field(None, ge=0, description="应回收资产数量")
    asset_list: str | None = Field(None, max_length=500, description="资产清单JSON")
    target_warehouse: str | None = Field(None, max_length=10, description="目标仓库")
    remark: str | None = Field(None, max_length=200, description="备注")


class RecycleTaskUpdate(BaseModel):
    """更新回收任务单（所有字段可选）。"""

    asset_count: int | None = Field(None, ge=0)
    asset_list: str | None = Field(None, max_length=500)
    target_warehouse: str | None = Field(None, max_length=10)
    remark: str | None = Field(None, max_length=200)


class RecycleTaskDtlCreate(BaseModel):
    """添加回收任务明细。"""

    asset_id: str = Field(..., max_length=20, description="资产ID")
    asset_type: str | None = Field(None, max_length=10, description="资产类型")
    expected_status: str | None = Field(None, max_length=10, description="预期状态")


class RecycleTaskQuery(BaseModel):
    """回收任务列表查询参数。"""

    task_status: str | None = Field(None, max_length=2, description="任务状态过滤")
    cust_cd: str | None = Field(None, max_length=8, description="门店代码过滤")
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页条数")


# ---------------------------------------------------------------------------
# 查询参数
# ---------------------------------------------------------------------------


class MaintenanceQuery(BaseModel):
    """维护单列表查询参数（对齐 PB u_itsm_rep_maintenanceday 报表查询条件）。"""

    status: str | None = Field(None, max_length=2, description="状态码过滤（多值逗号分隔，如 1,2,5）")
    current_status: str | None = Field(None, max_length=50, description="状态码过滤（兼容前端 current_status 参数）")
    store_id: str | None = Field(None, max_length=8, description="门店ID过滤")
    maintenance_id: str | None = Field(None, max_length=8, description="维护单号模糊过滤")
    company_id: str | None = Field(None, max_length=8, description="有限公司（上级公司）过滤")
    area_cd: str | None = Field(None, max_length=20, description="负责区域过滤")
    firstor: str | None = Field(None, max_length=6, description="上门工程师过滤")
    cust_card: str | None = Field(None, max_length=30, description="门店磁卡号模糊过滤")
    cust_nm: str | None = Field(None, max_length=100, description="店名模糊过滤")
    address: str | None = Field(None, max_length=200, description="地址模糊过滤")
    fault_type: str | None = Field(None, max_length=8, description="故障类型过滤")
    short_description: str | None = Field(None, max_length=80, description="维护分类（简述）模糊过滤")
    request_begin: str | None = Field(None, description="请求日期起始（YYYY-MM-DD）")
    request_end: str | None = Field(None, description="请求日期结束（YYYY-MM-DD）")
    first_begin: str | None = Field(None, description="上门日期起始（YYYY-MM-DD）")
    first_end: str | None = Field(None, description="上门日期结束（YYYY-MM-DD）")
    dispatch_to: str | None = Field(None, max_length=6, description="派给我：按派工人 accpectder 过滤")
    area_user: str | None = Field(None, max_length=6, description="本区域：按用户编码查其所属区域过滤")
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页条数")


# ---------------------------------------------------------------------------
# 保养计划 (TIT17_PLAN)
# ---------------------------------------------------------------------------


class MaintenancePlanCreate(BaseModel):
    """创建保养计划。"""

    plan_y: str = Field(..., max_length=4, description="计划年")
    plan_yymm: str = Field(..., max_length=6, description="计划年月")
    area_id: int = Field(..., description="区域ID")
    plan_qty: int | None = Field(None, ge=0, description="计划保养数量")


class MaintenancePlanUpdate(BaseModel):
    """更新保养计划。"""

    plan_qty: int | None = Field(None, ge=0, description="计划保养数量")


# ---------------------------------------------------------------------------
# 归档 (TIT12)
# ---------------------------------------------------------------------------


class ArchiveCreate(BaseModel):
    """创建归档记录。"""

    maintenance_id: str = Field(..., max_length=8, description="维护单ID")
    fault_cd: str | None = Field(None, max_length=10, description="故障编码")
    fault_cd_audit: str | None = Field(None, max_length=10, description="故障编码（审核后）")
    fault_type: str | None = Field(None, max_length=10, description="故障大类")
    fault_detail_type: str | None = Field(None, max_length=10, description="故障小类")
    description: str | None = Field(None, max_length=200, description="描述")
    is_audit: str | None = Field(None, max_length=1, description="审核标记")


class ArchiveUpdate(BaseModel):
    """更新归档记录。"""

    fault_cd: str | None = Field(None, max_length=10)
    fault_cd_audit: str | None = Field(None, max_length=10)
    fault_type: str | None = Field(None, max_length=10)
    fault_detail_type: str | None = Field(None, max_length=10)
    description: str | None = Field(None, max_length=200)
    is_audit: str | None = Field(None, max_length=1)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ITSM 附表 Schema（P1 补全）
# ---------------------------------------------------------------------------


class PayListCreate(BaseModel):
    """创建收费记录（TIT26）。"""

    maintenance_id: str = Field(..., max_length=8, description="维修单ID")
    store_id: str | None = Field(None, max_length=8, description="门店ID")
    engineer_id: str | None = Field(None, max_length=6, description="工程师ID")
    receipt_id: str | None = Field(None, max_length=8, description="收据号")
    delivery_id: str | None = Field(None, max_length=8, description="送货单号")
    paytype: str | None = Field(None, max_length=30, description="收费类型")
    payje: float | None = Field(None, description="收款金额")
    memo: str | None = Field(None, max_length=250, description="备注")
    paydate: str | None = Field(None, description="收款日期")


class MaintenanceLiabilityCreate(BaseModel):
    """创建维护单责任豁免（TIT10_LIABILITY）。"""

    maintenance_id: str = Field(..., max_length=8, description="维护单ID")
    exceptions_cd: str | None = Field(None, max_length=10, description="免责条款编码")
    exceptions_nm: str | None = Field(None, max_length=200, description="条款名称")
    dept_nm: str | None = Field(None, max_length=20, description="审核部门")
    assess_flg: str | None = Field(None, max_length=1, description="是否考核")
    exempt_flg: str | None = Field(None, max_length=1, description="是否豁免")
    type: str | None = Field(None, max_length=1, description="类型")
    is_finish: str | None = Field(None, max_length=1, description="处理状态")
    set_from: str | None = Field(None, max_length=10, description="来源")


class MaintenanceLiabilityUpdate(BaseModel):
    """更新维护单责任豁免。"""

    exceptions_cd: str | None = Field(None, max_length=10)
    exceptions_nm: str | None = Field(None, max_length=200)
    dept_nm: str | None = Field(None, max_length=20)
    assess_flg: str | None = Field(None, max_length=1)
    exempt_flg: str | None = Field(None, max_length=1)
    type: str | None = Field(None, max_length=1)
    is_finish: str | None = Field(None, max_length=1)


class LiabilityRegCreate(BaseModel):
    """创建责任豁免字典（TIT02）。"""

    liab_cd: str = Field(..., max_length=4, description="科目编码")
    liab_nm: str = Field(..., max_length=20, description="科目名称")
    describe: str | None = Field(None, max_length=200, description="描述")
    liab_type: str | None = Field(None, max_length=1, description="分类")
    parent: str | None = Field(None, max_length=4, description="上级编码")
    child_flg: str | None = Field(None, max_length=1, description="子类别标志")


class LiabilityRegDetailCreate(BaseModel):
    """创建责任豁免字典明细。"""

    lbdt_cd: str = Field(..., max_length=8, description="明细编码")
    define: str | None = Field(None, max_length=200, description="明细定义")


class MaintenanceAttcCreate(BaseModel):
    """创建附件（TIT11）。"""

    maintenance_id: str = Field(..., max_length=8, description="维护单ID")
    attc_id: str | None = Field(None, max_length=8, description="附件ID")
    attc_nm: str | None = Field(None, max_length=40, description="附件名称")
    business_operation_id: int | None = Field(None, description="业务操作流水ID")


class PosDetailCreate(BaseModel):
    """创建换机配件明细（TIT10_POS_DETAIL）。"""

    bill_id: str = Field(..., max_length=8, description="单据编号")
    sm_id: int | None = Field(None, description="SM表ID")
    noflg: str | None = Field(None, max_length=1, description="新旧设备标记")
    device_id: str | None = Field(None, max_length=13, description="整机ID")
    item_cd: str | None = Field(None, max_length=6, description="配件类型")
    accessories_id: str | None = Field(None, max_length=13, description="配件编号")
    status: str | None = Field(None, max_length=1, description="状态")


class NoCloseTrackCreate(BaseModel):
    """创建未关单跟踪（TIT29）。"""

    maintenance_id: str = Field(..., max_length=8, description="维护单号")
    idnum: int | None = Field(None, description="编号")
    dispos_dept: str | None = Field(None, max_length=20, description="处理部门")
    cause_main: str | None = Field(None, max_length=20, description="原因大类")
    cause_detail: str | None = Field(None, max_length=20, description="原因小类")
    cause_memo: str | None = Field(None, max_length=200, description="原因说明")
    description: str | None = Field(None, max_length=250, description="详情")
    feedback: str | None = Field(None, max_length=200, description="部门反馈")


class RepairInfoCreate(BaseModel):
    """创建报修信息（TIT05）。"""

    rep_type: str = Field(..., max_length=2, description="类型（01客户/02配件）")
    obj_cd: str = Field(..., max_length=8, description="对象编号")


class TimepointAreaCreate(BaseModel):
    """创建时间点级别（TIT01）。"""

    levels: str = Field(..., max_length=2, description="响应等级")
    explain: str | None = Field(None, max_length=20, description="说明")
    timepoint: str | None = Field(None, description="时间点")
    before_tm: float | None = Field(None, description="时间点前（小时）")
    after_tm: float | None = Field(None, description="时间点后（小时）")


class TimepointAreaUpdate(BaseModel):
    """更新时间点级别。"""

    explain: str | None = Field(None, max_length=20)
    before_tm: float | None = Field(None)
    after_tm: float | None = Field(None)


class OnChooseDtCreate(BaseModel):
    """创建开通选择明细（TIT19）。"""

    bill_id: str = Field(..., max_length=8, description="单据编号")
    business_id: int | None = Field(None, description="设备操作流水")
    oldflg: str | None = Field(None, max_length=1, description="新旧设备标记")
    device_id: str | None = Field(None, max_length=13, description="整机ID")
    item_cd: str | None = Field(None, max_length=6, description="配件类型")
    accessories_id: str | None = Field(None, max_length=13, description="配件编号")
    chooseflg: str | None = Field(None, max_length=1, description="选取标记")
