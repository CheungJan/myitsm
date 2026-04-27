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


class MaintenanceDailyUpdate(BaseModel):
    """更新日常维护单。"""

    fault_type: str | None = Field(None, max_length=8)
    servrity: str | None = Field(None, max_length=1)
    emergency_level: str | None = Field(None, max_length=1)
    priority: str | None = Field(None, max_length=1)
    short_description: str | None = Field(None, max_length=80)
    detail_description: str | None = Field(None, max_length=200)
    device_id: str | None = Field(None, max_length=13)
    memo: str | None = Field(None, max_length=200)


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
    maintenance_type: str = Field(..., max_length=2, description="维护类型")
    accpectd_group: str | None = Field(None, max_length=2, description="分派组")
    accpectder: str | None = Field(None, max_length=6, description="分派人")


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
    d2d_descripiton: str | None = Field(None, max_length=200, description="处理过程描述")
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
    c_type: str | None = Field(None, max_length=1, description="操作类型（1维修/2购买）")


# ---------------------------------------------------------------------------
# 关单 (TIT27)
# ---------------------------------------------------------------------------


class CloseBillCreate(BaseModel):
    """创建关单记录。"""

    maintenance_id: str = Field(..., max_length=8, description="任务单ID")
    close_type: str | None = Field(None, max_length=2, description="关单类型")
    description: str | None = Field(None, max_length=200, description="描述")
    is_old: str | None = Field(None, max_length=1, description="是否补关单")


# ---------------------------------------------------------------------------
# 设备变更 (TIT16)
# ---------------------------------------------------------------------------


class DeviceChangeCreate(BaseModel):
    """创建设备变更单。"""

    store_id: str = Field(..., max_length=8, description="门店ID")
    change_type: str = Field(..., max_length=8, description="变更类型（CK/BQ/BG）")
    device_id: str | None = Field(None, max_length=13, description="整机ID")
    new_contactor: str | None = Field(None, max_length=10, description="变更后联系人")
    new_tel: str | None = Field(None, max_length=60, description="变更后电话")
    new_address: str | None = Field(None, max_length=200, description="变更后地址")
    new_store_card: str | None = Field(None, max_length=20, description="变更后门店磁卡号")
    new_store_id: str | None = Field(None, max_length=8, description="变更后门店ID")
    is_store_inside_change: str | None = Field(None, max_length=1, description="是否店内移机")
    short_description: str | None = Field(None, max_length=80, description="简述")
    detail_description: str | None = Field(None, max_length=200, description="详细描述")


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
    """维护单列表查询参数。"""

    status: str | None = Field(None, max_length=2, description="状态码过滤")
    store_id: str | None = Field(None, max_length=8, description="门店ID过滤")
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页条数")
