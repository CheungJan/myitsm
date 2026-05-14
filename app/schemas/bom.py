"""BOM 管理模块请求/响应 Schema。"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class BomCreateRequest(BaseModel):
    """创建 BOM。"""

    bomcd: str = Field(..., max_length=6, description="BOM编码（整机物料编码）")
    bomnm: str = Field(..., max_length=50, description="BOM名称")

    @field_validator("bomcd")
    @classmethod
    def bomcd_must_be_6_chars(cls, v: str) -> str:
        if len(v.strip()) != 6:
            raise ValueError("BOM编码必须为6位")
        return v.strip().upper()


class BomUpdateRequest(BaseModel):
    """更新 BOM。"""

    bomnm: str | None = Field(None, max_length=50, description="BOM名称")
    useflg: str | None = Field(None, max_length=1, description="有效标志")


class BomDtCreateRequest(BaseModel):
    """添加 BOM 明细。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    bomqty: Decimal = Field(..., description="BOM数量")
    itemtyp: str = Field("0", max_length=1, description="物料类型(0=外设,1=核心)")


class BomDtUpdateRequest(BaseModel):
    """更新 BOM 明细。"""

    bomqty: Decimal | None = Field(None, description="BOM数量")
    itemtyp: str | None = Field(None, max_length=1, description="物料类型")
