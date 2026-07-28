"""事务查询请求/响应 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AllBillQuery(BaseModel):
    """全模块单据查询参数。"""

    bill_type: str | None = Field(default=None, description="单据类型")
    store_id: str | None = Field(default=None, description="门店ID")
    status: str | None = Field(default=None, description="状态")
    start_date: str | None = Field(default=None, description="开始日期")
    end_date: str | None = Field(default=None, description="结束日期")
    keyword: str | None = Field(default=None, description="关键词（单号模糊搜索）")
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")


class ErrorCorrectionCreate(BaseModel):
    """错账冲销请求。"""

    table_name: str = Field(
        ...,
        description="表名（stock_in / stock_out）",
        pattern=r"^(stock_in|stock_out)$",
    )
    record_id: str = Field(..., min_length=1, description="单据ID")


class StockSummaryQuery(BaseModel):
    """进销存汇总查询参数。"""

    whcd: str | None = Field(default=None, description="仓库编码")
    itemtyp: str | None = Field(default=None, description="物料类型")
    start_date: str | None = Field(default=None, description="开始日期（YYYY-MM-DD）")
    end_date: str | None = Field(default=None, description="结束日期（YYYY-MM-DD）")
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")
