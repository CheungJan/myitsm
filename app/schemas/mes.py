"""生产制造MES模块请求/响应 Schema（Tier-3 G7）。"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 生产工单
# ---------------------------------------------------------------------------


class WorkOrderCreate(BaseModel):
    """创建生产工单。"""

    wo_id: str = Field(..., max_length=20, description="工单编号")
    item_cd: str = Field(..., max_length=20, description="产品编码")
    plan_qty: int = Field(..., description="计划数量")
    plan_start: date | None = Field(None, description="计划开始日期")
    plan_end: date | None = Field(None, description="计划完成日期")
    priority: str | None = Field("NORMAL", max_length=10, description="优先级")
    warehouse_cd: str | None = Field(None, max_length=20, description="目标仓库")
    remark: str | None = Field(None, max_length=200, description="备注")


class WorkOrderUpdate(BaseModel):
    """更新生产工单。"""

    actual_qty: int | None = Field(None, description="实际完成数量")
    actual_start: date | None = Field(None, description="实际开始日期")
    actual_end: date | None = Field(None, description="实际完成日期")
    status: str | None = Field(None, max_length=10, description="状态")
    priority: str | None = Field(None, max_length=10, description="优先级")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 工序定义
# ---------------------------------------------------------------------------


class ProcessDefCreate(BaseModel):
    """创建工序定义。"""

    process_cd: str = Field(..., max_length=20, description="工序编码")
    process_nm: str = Field(..., max_length=100, description="工序名称")
    process_type: str | None = Field(None, max_length=10, description="工序类型")
    std_hours: Decimal | None = Field(None, description="标准工时")
    sort_no: int | None = Field(0, description="排序号")
    remark: str | None = Field(None, max_length=200, description="备注")


class ProcessDefUpdate(BaseModel):
    """更新工序定义。"""

    process_nm: str | None = Field(None, max_length=100, description="工序名称")
    process_type: str | None = Field(None, max_length=10, description="工序类型")
    std_hours: Decimal | None = Field(None, description="标准工时")
    sort_no: int | None = Field(None, description="排序号")
    useflg: str | None = Field(None, max_length=1, description="有效标志")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 工单工序
# ---------------------------------------------------------------------------


class WorkProcessCreate(BaseModel):
    """创建工单工序。"""

    wo_id: str = Field(..., max_length=20, description="工单编号")
    process_cd: str = Field(..., max_length=20, description="工序编码")
    seq_no: int = Field(..., description="工序序号")
    plan_qty: int | None = Field(None, description="计划数量")
    remark: str | None = Field(None, max_length=200, description="备注")


class WorkProcessUpdate(BaseModel):
    """更新工单工序。"""

    actual_qty: int | None = Field(None, description="完成数量")
    defect_qty: int | None = Field(None, description="不良品数量")
    status: str | None = Field(None, max_length=10, description="状态")
    worker_cd: str | None = Field(None, max_length=20, description="操作工")
    remark: str | None = Field(None, max_length=200, description="备注")


# ---------------------------------------------------------------------------
# 物料消耗
# ---------------------------------------------------------------------------


class MaterialConsumeCreate(BaseModel):
    """创建物料消耗记录。"""

    wo_id: str = Field(..., max_length=20, description="工单编号")
    process_cd: str | None = Field(None, max_length=20, description="工序编码")
    item_cd: str = Field(..., max_length=20, description="物料编码")
    plan_qty: Decimal | None = Field(None, description="计划用量")
    actual_qty: Decimal | None = Field(None, description="实际用量")
    unit: str | None = Field(None, max_length=10, description="单位")
    warehouse_cd: str | None = Field(None, max_length=20, description="领料仓库")
    consume_date: date | None = Field(None, description="领料日期")
    remark: str | None = Field(None, max_length=200, description="备注")
