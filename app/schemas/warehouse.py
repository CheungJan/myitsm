"""仓储管理模块请求/响应 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class WarehouseCreate(BaseModel):
    """创建仓库。"""

    whcd: str = Field(..., max_length=2, description="仓库编码")
    whnm: str = Field(..., max_length=60, description="仓库名称")
    whtyp: str | None = Field(None, max_length=2, description="仓库类型")
    address: str | None = Field(None, max_length=60, description="地址")
    phoneno: str | None = Field(None, max_length=15, description="电话")
    leader: str | None = Field(None, max_length=6, description="负责人")


class WarehouseUpdate(BaseModel):
    """更新仓库。"""

    whnm: str | None = Field(None, max_length=60)
    address: str | None = Field(None, max_length=60)
    phoneno: str | None = Field(None, max_length=15)
    leader: str | None = Field(None, max_length=6)


class StockInCreate(BaseModel):
    """创建入库单。"""

    whcd: str = Field(..., max_length=2, description="仓库编码")
    invtyp: str = Field(..., max_length=1, description="入库类型")
    indate: str | None = Field(None, description="入库日期")
    refbillid: str | None = Field(None, max_length=8, description="关联单据号")
    suppcd: str | None = Field(None, max_length=8, description="供应商编码")
    memo: str | None = Field(None, max_length=255, description="备注")


class StockInDetailCreate(BaseModel):
    """入库明细。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    itemtyp: str | None = Field(None, max_length=2, description="物料类型")
    inqty: int = Field(..., ge=1, description="入库数量")
    batchid: str | None = Field(None, max_length=50, description="批次号")


class StockOutCreate(BaseModel):
    """创建出库单。"""

    whcd: str = Field(..., max_length=2, description="仓库编码")
    invtyp: str = Field(..., max_length=1, description="出库类型")
    outdate: str | None = Field(None, description="出库日期")
    targetwhcd: str | None = Field(None, max_length=2, description="目标仓库（调拨）")
    suppcd: str | None = Field(None, max_length=8, description="供应商（退货）")
    memo: str | None = Field(None, max_length=255, description="备注")


class StockOutDetailCreate(BaseModel):
    """出库明细。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    itemtyp: str | None = Field(None, max_length=2, description="物料类型")
    outqty: int = Field(..., ge=1, description="出库数量")
    eid: str | None = Field(None, max_length=13, description="设备EID")


class WarehouseQuery(BaseModel):
    """仓储查询参数。"""

    whcd: str | None = Field(None, max_length=2)
    invtyp: str | None = Field(None, max_length=1)
    auditflg: str | None = Field(None, max_length=1)
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class StockQuery(BaseModel):
    """库存查询参数。"""

    whcd: str | None = Field(None, max_length=2)
    itemcd: str | None = Field(None, max_length=6)
    search: str | None = Field(None, max_length=50)
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


# ---------------------------------------------------------------------------
# 调拨科目 (TTX01_TXKMG)
# ---------------------------------------------------------------------------


class TransferAccountCreate(BaseModel):
    """创建调拨科目。"""

    txkno: str = Field(..., max_length=30, description="调拨科目编号")
    commmode: str | None = Field(None, max_length=10, description="通讯方式")
    remark: str | None = Field(None, max_length=100, description="备注")
    by1: str | None = Field(None, max_length=10, description="备用字段1")
    by2: str | None = Field(None, max_length=10, description="备用字段2")


class TransferAccountUpdate(BaseModel):
    """更新调拨科目。"""

    commmode: str | None = Field(None, max_length=10)
    remark: str | None = Field(None, max_length=100)
    by1: str | None = Field(None, max_length=10)
    by2: str | None = Field(None, max_length=10)
    useflg: str | None = Field(None, max_length=1)
