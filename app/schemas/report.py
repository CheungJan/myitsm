"""报表查询请求 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class InventorySnapshotQuery(BaseModel):
    """库存快照查询参数。"""

    whcd: str | None = Field(default=None, description="仓库编码")
    itemtyp: str | None = Field(default=None, description="物料类型")
    itemcd: str | None = Field(default=None, description="物料编码")
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")


class MovementLogQuery(BaseModel):
    """库存流水查询参数。"""

    whcd: str | None = Field(default=None, description="仓库编码")
    itemcd: str | None = Field(default=None, description="物料编码")
    start_date: str | None = Field(default=None, description="开始日期")
    end_date: str | None = Field(default=None, description="结束日期")
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")


class EidLifecycleQuery(BaseModel):
    """EID 生命周期查询参数。"""

    eid: str | None = Field(default=None, description="设备唯一标识（模糊搜索）")
    itemcd: str | None = Field(default=None, description="物料编码")
    custcd: str | None = Field(default=None, description="客户编码")
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")


class SalesReportQuery(BaseModel):
    """销售报表查询参数。"""

    start_date: str | None = Field(default=None, description="开始日期")
    end_date: str | None = Field(default=None, description="结束日期")


class BOMTreeQuery(BaseModel):
    """BOM 结构树查询参数。"""

    itemcd: str | None = Field(default=None, description="主物料编码")
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")
