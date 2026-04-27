"""合同与发票管理模块请求/响应 Schema。"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ContractCreate(BaseModel):
    """创建合同。"""

    htbh: str | None = Field(None, max_length=20, description="合同编号")
    years: str | None = Field(None, max_length=4, description="年份")
    classcd: str | None = Field(None, max_length=6, description="区域")
    busityp: str | None = Field(None, max_length=2, description="合同属性")
    feetyp: str | None = Field(None, max_length=2, description="费用类型")
    qdis: str | None = Field(None, max_length=1, description="签订与否")
    qddate: date | None = Field(None, description="签订日期")
    htbgr: str | None = Field(None, max_length=20, description="合同保管人")
    remark: str | None = Field(None, max_length=200, description="备注")
    yxqfrom: date | None = Field(None, description="有效期起始")
    yxqto: date | None = Field(None, description="有效期截止")
    htamount: Decimal | None = Field(None, description="合同金额")


class ContractUpdate(BaseModel):
    """更新合同。"""

    busityp: str | None = Field(None, max_length=2, description="合同属性")
    feetyp: str | None = Field(None, max_length=2, description="费用类型")
    qdis: str | None = Field(None, max_length=1, description="签订与否")
    qddate: date | None = Field(None, description="签订日期")
    htbgr: str | None = Field(None, max_length=20, description="合同保管人")
    remark: str | None = Field(None, max_length=200, description="备注")
    yxqfrom: date | None = Field(None, description="有效期起始")
    yxqto: date | None = Field(None, description="有效期截止")
    htamount: Decimal | None = Field(None, description="合同金额")


class InvoiceCreate(BaseModel):
    """创建发票。"""

    fpbh: str | None = Field(None, max_length=30, description="发票编号")
    years: str | None = Field(None, max_length=4, description="年份")
    classcd: str | None = Field(None, max_length=6, description="区域")
    busityp: str | None = Field(None, max_length=2, description="合同属性")
    feetyp: str | None = Field(None, max_length=2, description="费用类型")
    htbh: str | None = Field(None, max_length=20, description="合同编号")
    htq: str | None = Field(None, max_length=2, description="合同期")
    qsr: str | None = Field(None, max_length=10, description="签收人")
    lsh: str | None = Field(None, max_length=30, description="流水号")
    kpdate: date | None = Field(None, description="开票日期")
    kpamount: Decimal | None = Field(None, description="开票金额")
    hkdate: date | None = Field(None, description="回款日期")
    hkamount: Decimal | None = Field(None, description="回款金额")
    sptype: str | None = Field(None, max_length=6, description="送票方式")
    spr: str | None = Field(None, max_length=6, description="送票人")
    htqdis: str | None = Field(None, max_length=1, description="合同签订与否")
    htamount: Decimal | None = Field(None, description="合同金额")
    remark: str | None = Field(None, max_length=200, description="备注")


class InvoiceUpdate(BaseModel):
    """更新发票。"""

    htbh: str | None = Field(None, max_length=20, description="合同编号")
    kpdate: date | None = Field(None, description="开票日期")
    kpamount: Decimal | None = Field(None, description="开票金额")
    hkdate: date | None = Field(None, description="回款日期")
    hkamount: Decimal | None = Field(None, description="回款金额")
    sptype: str | None = Field(None, max_length=6, description="送票方式")
    spr: str | None = Field(None, max_length=6, description="送票人")
    remark: str | None = Field(None, max_length=200, description="备注")
