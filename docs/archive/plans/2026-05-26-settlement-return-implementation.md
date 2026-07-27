# 采购结算单与退货功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成采购结算单（TPC14+DT）和采购退货（TPC16/TPC17）的完整 CRUD + Audit 功能，支持五种付款方式（COD/PIA/DEP/MON/INS）。

**Architecture:** 多对多结算（一张结算单可包含多个订单行，一个订单行可被多次结算），通过 TPC14_DT 明细表实现。结算单 1:1 可选关联来源订单（月结时置空）。退货与订单行关联，校验退货量 ≤ 入库量 - 已退量。

**Tech Stack:** Flask + SQLAlchemy + PostgreSQL + Alembic / Vue 3 + Element Plus + TypeScript / Pydantic v2

**Design Doc:** `docs/采购结算单与退货功能设计方案.md`

---

## File Structure

```
Create:
  migrations/versions/xxxx_settlement_return_enhance.py   # 数据库迁移

Modify:
  app/models/procurement.py          # +PurchaseBillDt, 修改 PurchaseBill/ReturnPurchaseBill/ReturnPurchaseBillDt
  app/schemas/procurement.py         # +结算明细Schema, 修改 PurchaseBillCreate/ReturnPurchaseBillCreate
  app/repositories/procurement_repository.py  # +PurchaseBillDtRepository, 扩展 PurchaseBillRepository/ReturnPurchaseRepository
  app/services/procurement_service.py         # 扩展 PurchaseBillService/ReturnPurchaseService
  app/api/procurement.py             # +结算/退货的 update/audit/void, +settleable-items/returnable-items
  frontend/src/api/procurement.ts    # +新 API 函数
  frontend/src/views/procurement/PurchaseBillList.vue     # 增强列表+新建+审核
  frontend/src/views/procurement/ReturnPurchaseList.vue   # 增强列表+新建+审核
  frontend/src/router/index.ts       # 如果需要路由调整
```

---

### Task 1: 数据库迁移

**Files:**
- Create: `migrations/versions/xxxx_settlement_return_enhance.py`

- [ ] **Step 1: 查看当前最新迁移版本号**

Run: `ls -t migrations/versions/*.py | head -1 && grep "revision\|down_revision" $(ls -t migrations/versions/*.py | head -1)`

- [ ] **Step 2: 创建迁移文件**

Run: `uv run flask db revision --autogenerate -m "settlement_return_enhance"`
然后重命名生成的文件，替换内容如下：

```python
"""enhance settlement and return modules

Revision ID: <auto>
Revises: <auto>
Create Date: <auto>
"""
from alembic import op
import sqlalchemy as sa

revision = "<auto>"
down_revision = "<auto>"


def upgrade():
    # 1. TPC13 唯一约束（TPC14_DT 外键前置条件）
    op.execute("""
        ALTER TABLE tpc13_registerdt
        ADD CONSTRAINT uq_registerdt_bill_line UNIQUE(rgstbillid, lineno)
    """)

    # 2. TPC14 重命名 + 补字段
    op.execute("ALTER TABLE tpc14_pcbill RENAME COLUMN custcd TO suppliercd")
    op.add_column("tpc14_pcbill", sa.Column("ref_rgstbillid", sa.String(8), nullable=True))
    op.add_column("tpc14_pcbill", sa.Column("pay_type", sa.String(3), server_default="COD"))
    op.add_column("tpc14_pcbill", sa.Column("invoice_no", sa.String(50), nullable=True))
    op.add_column("tpc14_pcbill", sa.Column("invoice_date", sa.Date, nullable=True))
    op.add_column("tpc14_pcbill", sa.Column("total_settle_amt", sa.Numeric(16, 4), server_default="0"))
    op.add_column("tpc14_pcbill", sa.Column("auditflg", sa.String(1), server_default="0"))
    op.add_column("tpc14_pcbill", sa.Column("auditman", sa.String(6), nullable=True))
    op.add_column("tpc14_pcbill", sa.Column("auditdate", sa.DateTime, nullable=True))

    # 3. TPC14_DT 新建
    op.create_table(
        "tpc14_pcbilldt",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("pcbillid", sa.String(8), sa.ForeignKey("tpc14_pcbill.pcbillid", ondelete="CASCADE"), nullable=False),
        sa.Column("lineno", sa.Integer, nullable=False),
        sa.Column("ref_rgstbillid", sa.String(8), nullable=False),
        sa.Column("ref_rgstlineno", sa.Integer, nullable=False),
        sa.Column("itemcd", sa.String(6), nullable=False),
        sa.Column("order_qty", sa.Numeric(12, 2), server_default="0"),
        sa.Column("received_qty", sa.Numeric(12, 2), server_default="0"),
        sa.Column("already_settled", sa.Numeric(12, 2), server_default="0"),
        sa.Column("settle_qty", sa.Numeric(12, 2), nullable=False),
        sa.Column("settle_price", sa.Numeric(16, 4), nullable=False),
        sa.Column("settle_amt", sa.Numeric(16, 4), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ("ref_rgstbillid", "ref_rgstlineno"),
            ("tpc13_registerdt", "rgstbillid", "lineno"),
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("pcbillid", "lineno"),
    )
    op.create_index("idx_sdt_pcbillid", "tpc14_pcbilldt", ["pcbillid"])
    op.create_index("idx_sdt_order", "tpc14_pcbilldt", ["ref_rgstbillid", "ref_rgstlineno"])
    op.create_index("idx_sdt_itemcd", "tpc14_pcbilldt", ["itemcd"])

    # 4. TPC16 重命名 + 补字段
    op.execute("ALTER TABLE tpc16_rpcbill RENAME COLUMN custcd TO suppliercd")
    op.add_column("tpc16_rpcbill", sa.Column("return_reason", sa.String(20), nullable=True))

    # 5. TPC17 补字段
    op.add_column("tpc17_rpcbilldt", sa.Column("return_price", sa.Numeric(16, 4), nullable=True))
    op.add_column("tpc17_rpcbilldt", sa.Column("return_amt", sa.Numeric(16, 4), nullable=True))
    op.add_column("tpc17_rpcbilldt", sa.Column("line_reason", sa.String(100), nullable=True))


def downgrade():
    op.drop_column("tpc17_rpcbilldt", "line_reason")
    op.drop_column("tpc17_rpcbilldt", "return_amt")
    op.drop_column("tpc17_rpcbilldt", "return_price")
    op.drop_column("tpc16_rpcbill", "return_reason")
    op.execute("ALTER TABLE tpc16_rpcbill RENAME COLUMN suppliercd TO custcd")
    op.drop_table("tpc14_pcbilldt")
    op.drop_column("tpc14_pcbill", "auditdate")
    op.drop_column("tpc14_pcbill", "auditman")
    op.drop_column("tpc14_pcbill", "auditflg")
    op.drop_column("tpc14_pcbill", "total_settle_amt")
    op.drop_column("tpc14_pcbill", "invoice_date")
    op.drop_column("tpc14_pcbill", "invoice_no")
    op.drop_column("tpc14_pcbill", "pay_type")
    op.drop_column("tpc14_pcbill", "ref_rgstbillid")
    op.execute("ALTER TABLE tpc14_pcbill RENAME COLUMN suppliercd TO custcd")
    op.execute("ALTER TABLE tpc13_registerdt DROP CONSTRAINT IF EXISTS uq_registerdt_bill_line")
```

- [ ] **Step 3: 检查 tpc13_registerdt 无重复数据（安全校验）**

Run: `psql -U cheungjan -d myitsm -c "SELECT rgstbillid, lineno, COUNT(*) FROM tpc13_registerdt GROUP BY rgstbillid, lineno HAVING COUNT(*) > 1"`

Expected: (0 rows) — 已确认无重复

- [ ] **Step 4: 执行迁移**

Run: `uv run flask db upgrade`

Expected: INFO Running upgrade ... -> <revision>, settlement_return_enhance

- [ ] **Step 5: 验证迁移结果**

Run:
```bash
psql -U cheungjan -d myitsm -c "\d tpc14_pcbill" && \
psql -U cheungjan -d myitsm -c "\d tpc14_pcbilldt" && \
psql -U cheungjan -d myitsm -c "\d tpc16_rpcbill" && \
psql -U cheungjan -d myitsm -c "\d tpc17_rpcbilldt"
```

确认所有新字段和约束已创建。

- [ ] **Step 6: 回滚测试**

Run: `uv run flask db downgrade -1 && uv run flask db upgrade`

Expected: 回滚成功 + 重新升级成功，无报错。

- [ ] **Step 7: Commit**

```bash
git add migrations/versions/xxxx_settlement_return_enhance.py
git commit -m "feat(procurement): TPC14/16/17迁移 — 结算明细表+字段补全+重命名"
```

---

### Task 2: 更新 ORM 模型

**Files:**
- Modify: `app/models/procurement.py:149-221`
- Modify: `app/models/__init__.py:120-131`

- [ ] **Step 1: 更新 PurchaseBill 模型 + 新增 PurchaseBillDt**

修改 `app/models/procurement.py` 第149-167行：

```python
class PurchaseBill(BaseModel):
    """采购结算单（TPC14_PCBILL）。"""

    __tablename__ = "tpc14_pcbill"

    pcbillid = db.Column(db.String(8), primary_key=True, comment="结算单号")
    ref_rgstbillid = db.Column(db.String(8), comment="来源采购订单（月结置空）")
    suppliercd = db.Column(db.String(8), comment="供应商编码")
    pctyp = db.Column(db.String(2), comment="采购类型")
    pay_type = db.Column(db.String(3), default="COD", comment="付款方式")
    invoice_no = db.Column(db.String(50), comment="发票号码")
    invoice_date = db.Column(db.Date, comment="发票日期")
    pcdate = db.Column(db.DateTime, comment="结算日期")
    total_settle_amt = db.Column(db.Numeric(16, 4), default=0, comment="结算总额")
    whcd = db.Column(db.String(2), comment="入库仓库")
    invoiceflg = db.Column(db.String(1), comment="发票标志")
    ptimes = db.Column(db.Integer, comment="打印次数")
    opercd = db.Column(db.String(6), comment="操作员")
    memo = db.Column(db.String(255), comment="备注")
    gendate = db.Column(db.DateTime, comment="创建日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")

    details = db.relationship("PurchaseBillDt", back_populates="bill", lazy="dynamic")


class PurchaseBillDt(BaseModel):
    """采购结算明细（TPC14_PCBILLDT）。"""

    __tablename__ = "tpc14_pcbilldt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pcbillid = db.Column(
        db.String(8),
        db.ForeignKey("tpc14_pcbill.pcbillid", ondelete="CASCADE"),
        nullable=False,
        comment="结算单号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    ref_rgstbillid = db.Column(db.String(8), nullable=False, comment="来源采购订单号")
    ref_rgstlineno = db.Column(db.Integer, nullable=False, comment="来源订单行号")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    order_qty = db.Column(db.Numeric(12, 2), default=0, comment="订购数量(快照)")
    received_qty = db.Column(db.Numeric(12, 2), default=0, comment="已入库数量(快照)")
    already_settled = db.Column(db.Numeric(12, 2), default=0, comment="该行已结算累计(不含本次)")
    settle_qty = db.Column(db.Numeric(12, 2), nullable=False, comment="本次结算数量")
    settle_price = db.Column(db.Numeric(16, 4), nullable=False, comment="结算单价")
    settle_amt = db.Column(db.Numeric(16, 4), nullable=False, comment="结算金额")

    bill = db.relationship("PurchaseBill", back_populates="details")
```

- [ ] **Step 2: 更新 ReturnPurchaseBill 模型**

修改 `app/models/procurement.py` 第174-195行，将 `custcd` 改为 `suppliercd`，新增 `return_reason`：

```python
class ReturnPurchaseBill(BaseModel):
    """采购退货单（TPC16_RPCBILL）。"""

    __tablename__ = "tpc16_rpcbill"

    pcbillid = db.Column(db.String(8), primary_key=True, comment="退货单号")
    suppliercd = db.Column(db.String(8), comment="供应商编码")
    pcdate = db.Column(db.DateTime, comment="退货日期")
    pcamt = db.Column(db.Integer, comment="退货金额")
    whcd = db.Column(db.String(2), comment="仓库编码")
    invoiceflg = db.Column(db.String(2), comment="发票标志")
    ptimes = db.Column(db.Integer, comment="打印次数")
    opercd = db.Column(db.String(6), comment="操作员")
    memo = db.Column(db.String(255), comment="备注")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    gendate = db.Column(db.DateTime, comment="创建日期")
    ref_rgstbillid = db.Column(db.String(8), comment="来源采购订单号")
    return_reason = db.Column(db.String(20), comment="退货原因")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")

    details = db.relationship("ReturnPurchaseBillDt", back_populates="bill", lazy="dynamic")
```

- [ ] **Step 3: 更新 ReturnPurchaseBillDt 模型**

修改 `app/models/procurement.py` 第198-220行，新增三个字段：

```python
class ReturnPurchaseBillDt(BaseModel):
    """采购退货明细（TPC17_RPCBILLDT）。"""

    __tablename__ = "tpc17_rpcbilldt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pcbillid = db.Column(
        db.String(8),
        db.ForeignKey("tpc16_rpcbill.pcbillid"),
        nullable=False,
        comment="退货单号",
    )
    lineno = db.Column(db.Integer, nullable=False, comment="行号")
    itemtyp = db.Column(db.String(2), comment="物料类型")
    itemcd = db.Column(db.String(6), nullable=False, comment="物料编码")
    eid = db.Column(db.String(13), comment="设备EID")
    seid = db.Column(db.String(30), comment="序列号")
    rpcqty = db.Column(db.Integer, default=0, comment="退货数量")
    return_price = db.Column(db.Numeric(16, 4), comment="退货单价")
    return_amt = db.Column(db.Numeric(16, 4), comment="退货金额")
    invoiceqty = db.Column(db.Integer, default=0, comment="发票数量")
    units = db.Column(db.String(4), comment="单位")
    ref_rgstlineno = db.Column(db.Integer, comment="来源订单行号")
    line_reason = db.Column(db.String(100), comment="行级退货原因说明")

    bill = db.relationship("ReturnPurchaseBill", back_populates="details")
```

- [ ] **Step 4: 更新 models/__init__.py**

修改 `app/models/__init__.py` 的 procurement 导入段（约第120-131行）：

```python
from app.models.procurement import (
    PurchaseBill,
    PurchaseBillDt,
    PurchaseCheckInDt,
    PurchasePlan,
    PurchasePlanDt,
    PurchasePlanStatus,
    PurchaseRegister,
    PurchaseRegisterDt,
    ReturnPurchaseBill,
    ReturnPurchaseBillDt,
    SupplierAppraisal,
    SupplierAppraisalDt,
)
```

并在 `__all__` 中添加 `"PurchaseBillDt"`：

```python
# 在 __all__ 的采购管理段中添加
"PurchaseBill",
"PurchaseBillDt",
```

- [ ] **Step 5: 验证模型可导入**

Run: `python3 -c "from app.models.procurement import PurchaseBill, PurchaseBillDt, ReturnPurchaseBill, ReturnPurchaseBillDt; print('OK')"`

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add app/models/procurement.py app/models/__init__.py
git commit -m "feat(procurement): 更新TPC14/TPC16/TPC17模型，新增PurchaseBillDt"
```

---

### Task 3: 更新 Pydantic Schema

**Files:**
- Modify: `app/schemas/procurement.py`

- [ ] **Step 1: 重写 PurchaseBillCreate + 新增相关 Schema**

替换 `app/schemas/procurement.py` 中第46-54行的 `PurchaseBillCreate`：

```python
class PurchaseBillCreate(BaseModel):
    """创建采购结算单。"""

    suppliercd: str = Field(..., max_length=8, description="供应商编码")
    pay_type: str = Field("COD", max_length=3, description="付款方式 COD/PIA/DEP/MON/INS")
    invoice_no: str | None = Field(None, max_length=50, description="发票号码")
    invoice_date: date | None = Field(None, description="发票日期")
    pcdate: date | None = Field(None, description="结算日期")
    whcd: str | None = Field(None, max_length=2, description="入库仓库")
    memo: str | None = Field(None, max_length=255, description="备注")
    details: list["PurchaseBillDetailCreate"] = Field(..., min_length=1, description="结算明细")


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
    whcd: str | None = Field(None, max_length=2)
    memo: str | None = Field(None, max_length=255)
    details: list["PurchaseBillDetailCreate"] | None = Field(None, description="结算明细（全量替换）")
```

- [ ] **Step 2: 更新 ReturnPurchaseBillCreate + 新增相关 Schema**

替换 `app/schemas/procurement.py` 中第73-93行的退货 Schema：

```python
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
```

- [ ] **Step 3: 验证 Schema 导入**

Run: `python3 -c "from app.schemas.procurement import PurchaseBillCreate, PurchaseBillDetailCreate, PurchaseBillUpdate, ReturnPurchaseBillCreate, ReturnPurchaseBillDetailCreate, ReturnPurchaseBillUpdate; print('OK')"`

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add app/schemas/procurement.py
git commit -m "feat(procurement): 更新结算/退货 Schema — 新增明细+编辑Schema"
```

---

### Task 4: 扩展 Repository 层

**Files:**
- Modify: `app/repositories/procurement_repository.py`

- [ ] **Step 1: 替换 _gen_id() 使用 _gen_master_id()**

修改 `app/repositories/procurement_repository.py` 中 `PurchaseBillRepository.create` (第577-586行) 和 `ReturnPurchaseRepository.create` (第611-620行) 的 ID 生成方式：

`PurchaseBillRepository.create`:
```python
    @staticmethod
    def create(data: dict[str, Any], creator: str) -> PurchaseBill:
        now = datetime.now(UTC)
        record = PurchaseBill(
            pcbillid=_gen_master_id("SB", "采购结算单号"),
            opercd=creator,
            gendate=now,
            **data,
        )
        db.session.add(record)
        return record
```

`ReturnPurchaseRepository.create`:
```python
    @staticmethod
    def create(data: dict[str, Any], creator: str) -> ReturnPurchaseBill:
        now = datetime.now(UTC)
        record = ReturnPurchaseBill(
            pcbillid=_gen_master_id("RT", "采购退货单号"),
            opercd=creator,
            gendate=now,
            **data,
        )
        db.session.add(record)
        return record
```

- [ ] **Step 2: 扩展 PurchaseBillRepository — add update, get_details, list_details**

在 `PurchaseBillRepository` 类中新增方法：

```python
    @staticmethod
    def update(record: PurchaseBill, data: dict[str, Any]) -> PurchaseBill:
        skip = {"pcbillid", "details", "opercd", "gendate", "auditflg", "auditman", "auditdate"}
        for k, v in data.items():
            if k in skip:
                continue
            setattr(record, k, v)
        return record

    @staticmethod
    def add_detail(pcbillid: str, lineno: int, data: dict[str, Any]) -> PurchaseBillDt:
        record = PurchaseBillDt(pcbillid=pcbillid, lineno=lineno, **data)
        db.session.add(record)
        return record

    @staticmethod
    def clear_details(pcbillid: str) -> None:
        db.session.query(PurchaseBillDt).filter(
            PurchaseBillDt.pcbillid == pcbillid
        ).delete()

    @staticmethod
    def list_details(pcbillid: str) -> list[PurchaseBillDt]:
        return db.session.query(PurchaseBillDt).filter(
            PurchaseBillDt.pcbillid == pcbillid
        ).order_by(PurchaseBillDt.lineno).all()

    @staticmethod
    def get_settled_total(ref_rgstbillid: str, ref_rgstlineno: int, exclude_pcbillid: str | None = None) -> float:
        """获取某订单行已结算累计（排除指定结算单）。"""
        from sqlalchemy import func
        q = db.session.query(func.coalesce(func.sum(PurchaseBillDt.settle_qty), 0)).filter(
            PurchaseBillDt.ref_rgstbillid == ref_rgstbillid,
            PurchaseBillDt.ref_rgstlineno == ref_rgstlineno,
        ).join(PurchaseBill, PurchaseBill.pcbillid == PurchaseBillDt.pcbillid).filter(
            PurchaseBill.useflg != "9"
        )
        if exclude_pcbillid:
            q = q.filter(PurchaseBillDt.pcbillid != exclude_pcbillid)
        return float(q.scalar() or 0)

    # get_returned_total 已移到 ReturnPurchaseRepository
```

- [ ] **Step 3: 扩展 PurchaseBillRepository.list_by_filters — 增加筛选条件**

替换 `list_by_filters` 方法：

```python
    @staticmethod
    def list_by_filters(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        pay_type: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PurchaseBill], int]:
        query = db.session.query(PurchaseBill).filter(PurchaseBill.useflg != "9")
        if suppliercd:
            query = query.filter(PurchaseBill.suppliercd == suppliercd)
        if auditflg:
            query = query.filter(PurchaseBill.auditflg == auditflg)
        if pay_type:
            query = query.filter(PurchaseBill.pay_type == pay_type)
        if start_date:
            query = query.filter(PurchaseBill.gendate >= start_date)
        if end_date:
            query = query.filter(PurchaseBill.gendate <= end_date)
        query = query.order_by(desc(PurchaseBill.gendate))
        total: int = query.count()
        items: list[PurchaseBill] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total
```

- [ ] **Step 4: 扩展 ReturnPurchaseRepository — add update**

在 `ReturnPurchaseRepository` 类中新增（放到 `add_detail` 方法之后）：

```python
    @staticmethod
    def update(record: ReturnPurchaseBill, data: dict[str, Any]) -> ReturnPurchaseBill:
        skip = {"pcbillid", "details", "opercd", "gendate", "auditflg", "auditman", "auditdate"}
        for k, v in data.items():
            if k in skip:
                continue
            setattr(record, k, v)
        return record

    @staticmethod
    def clear_details(pcbillid: str) -> None:
        db.session.query(ReturnPurchaseBillDt).filter(
            ReturnPurchaseBillDt.pcbillid == pcbillid
        ).delete()

    @staticmethod
    def list_details(pcbillid: str) -> list[ReturnPurchaseBillDt]:
        return db.session.query(ReturnPurchaseBillDt).filter(
            ReturnPurchaseBillDt.pcbillid == pcbillid
        ).order_by(ReturnPurchaseBillDt.lineno).all()

    @staticmethod
    def get_returned_total(ref_rgstbillid: str, ref_rgstlineno: int) -> float:
        """获取某订单行已退货累计。"""
        from sqlalchemy import func
        return float(
            db.session.query(func.coalesce(func.sum(ReturnPurchaseBillDt.rpcqty), 0)).filter(
                ReturnPurchaseBillDt.ref_rgstlineno == ref_rgstlineno,
            ).join(ReturnPurchaseBill, ReturnPurchaseBill.pcbillid == ReturnPurchaseBillDt.pcbillid).filter(
                ReturnPurchaseBill.ref_rgstbillid == ref_rgstbillid,
                ReturnPurchaseBill.useflg != "9",
            ).scalar() or 0
        )
```

- [ ] **Step 5: 扩展 ReturnPurchaseRepository.list_by_filters — 增加筛选条件**

替换 `list_by_filters`：

```python
    @staticmethod
    def list_by_filters(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ReturnPurchaseBill], int]:
        query = db.session.query(ReturnPurchaseBill).filter(ReturnPurchaseBill.useflg != "9")
        if suppliercd:
            query = query.filter(ReturnPurchaseBill.suppliercd == suppliercd)
        if auditflg:
            query = query.filter(ReturnPurchaseBill.auditflg == auditflg)
        if start_date:
            query = query.filter(ReturnPurchaseBill.gendate >= start_date)
        if end_date:
            query = query.filter(ReturnPurchaseBill.gendate <= end_date)
        query = query.order_by(desc(ReturnPurchaseBill.gendate))
        total: int = query.count()
        items: list[ReturnPurchaseBill] = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total
```

- [ ] **Step 6: 验证**

Run: `python3 -c "from app.repositories.procurement_repository import PurchaseBillRepository, ReturnPurchaseRepository; print('OK')"`

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add app/repositories/procurement_repository.py
git commit -m "feat(procurement): 扩展Repository — 结算/退货update+明细+筛选+IdMaster取号"
```

---

### Task 5: 扩展 Service 层

**Files:**
- Modify: `app/services/procurement_service.py`

- [ ] **Step 1: 重写 PurchaseBillService**

替换 `app/services/procurement_service.py` 第515-546行的 `PurchaseBillService`：

```python
class PurchaseBillService:
    """采购结算单服务 (TPC14 + TPC14_DT)。"""

    @staticmethod
    def get(pcbillid: str) -> dict[str, Any] | None:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return None
        result = record.to_dict()
        details = [d.to_dict() for d in PurchaseBillRepository.list_details(pcbillid)]
        for d in details:
            d.pop("bill", None)
        result["details"] = details
        return result

    @staticmethod
    def list_records(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        pay_type: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = PurchaseBillRepository.list_by_filters(
            suppliercd=suppliercd, auditflg=auditflg, pay_type=pay_type,
            start_date=start_date, end_date=end_date, page=page, per_page=per_page,
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total, "page": page, "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        details = data.pop("details", [])
        # 校验+计算结算金额
        total_amt = 0.0
        validated_details = []
        for d in details:
            ref_bill = d["ref_rgstbillid"]
            ref_line = d["ref_rgstlineno"]
            settle_qty = float(d["settle_qty"])
            settle_price = float(d["settle_price"])

            # 查订单行数据（PurchaseRegisterDt 主键是 id，不是 (rgstbillid, lineno)）
            order_dt = (
                db.session.query(PurchaseRegisterDt)
                .filter(
                    PurchaseRegisterDt.rgstbillid == ref_bill,
                    PurchaseRegisterDt.lineno == ref_line,
                )
                .first()
            )
            if order_dt is None:
                raise ValueError(f"订单行 {ref_bill}:{ref_line} 不存在")

            order_qty = float(order_dt.rgsqty or 0)
            received_qty = float(order_dt.inqty or 0)

            # 查已结算累计
            already = PurchaseBillRepository.get_settled_total(ref_bill, ref_line)

            # 按付款方式确定结算上限
            pay_type = data.get("pay_type", "COD")
            if pay_type in ("COD", "MON"):
                max_settle = received_qty - already
            else:
                max_settle = order_qty - already

            if settle_qty > max_settle:
                raise ValueError(
                    f"订单 {ref_bill} 行 {ref_line} 结算数量({settle_qty})"
                    f"超过可结算余量({max_settle})"
                )

            settle_amt = settle_qty * settle_price
            total_amt += settle_amt
            validated_details.append({
                **d,
                "order_qty": order_qty,
                "received_qty": received_qty,
                "already_settled": already,
                "settle_amt": settle_amt,
            })

        data["total_settle_amt"] = total_amt
        data["auditflg"] = "0"
        record = PurchaseBillRepository.create(data, creator)
        for i, d in enumerate(validated_details, start=1):
            PurchaseBillRepository.add_detail(record.pcbillid, i, d)
        db.session.commit()
        return PurchaseBillService.get(record.pcbillid)  # type: ignore[return-value]

    @staticmethod
    def update(pcbillid: str, data: dict[str, Any]) -> dict[str, object]:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "结算单不存在"}
        if record.auditflg != "0":
            return {"success": False, "error": "仅未审核单据可编辑"}

        details = data.pop("details", None)
        if details is not None:
            total_amt = 0.0
            validated_details = []
            for d in details:
                ref_bill = d["ref_rgstbillid"]
                ref_line = d["ref_rgstlineno"]
                settle_qty = float(d["settle_qty"])
                settle_price = float(d["settle_price"])

                order_dt = (
                    db.session.query(PurchaseRegisterDt)
                    .filter(
                        PurchaseRegisterDt.rgstbillid == ref_bill,
                        PurchaseRegisterDt.lineno == ref_line,
                    )
                    .first()
                )
                if order_dt is None:
                    raise ValueError(f"订单行 {ref_bill}:{ref_line} 不存在")

                order_qty = float(order_dt.rgsqty or 0)
                received_qty = float(order_dt.inqty or 0)
                already = PurchaseBillRepository.get_settled_total(ref_bill, ref_line, pcbillid)

                pay_type = data.get("pay_type", record.pay_type or "COD")
                max_settle = (received_qty if pay_type in ("COD", "MON") else order_qty) - already
                if settle_qty > max_settle:
                    raise ValueError(
                        f"订单 {ref_bill} 行 {ref_line} 结算数量({settle_qty})"
                        f"超过可结算余量({max_settle})"
                    )

                settle_amt = settle_qty * settle_price
                total_amt += settle_amt
                validated_details.append({
                    **d, "order_qty": order_qty, "received_qty": received_qty,
                    "already_settled": already, "settle_amt": settle_amt,
                })

            data["total_settle_amt"] = total_amt
            PurchaseBillRepository.clear_details(pcbillid)
            for i, d in enumerate(validated_details, start=1):
                PurchaseBillRepository.add_detail(pcbillid, i, d)

        PurchaseBillRepository.update(record, data)
        record.auditflg = "0"
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def audit(pcbillid: str, auditor: str, auditflg: str) -> dict[str, object]:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "结算单不存在"}
        if record.useflg == "9":
            return {"success": False, "error": "已作废单据不可审核"}
        if record.auditflg not in ("0", "1"):
            return {"success": False, "error": "不可重复审核"}
        record.auditflg = auditflg
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def void(pcbillid: str) -> dict[str, object]:
        record = PurchaseBillRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "结算单不存在"}
        if record.auditflg == "2":
            return {"success": False, "error": "已审核通过的结算单不能作废"}
        record.useflg = "9"
        record.auditflg = "9"  # 同时设审核状态为作废，防止通过 audit() 误审
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def get_settleable_items(rgstbillid: str) -> list[dict[str, Any]]:
        """查询订单的可结算商品行。"""
        order = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if order is None:
            raise ValueError("订单不存在")
        items = []
        for dt in order.details:  # type: ignore[attr-defined]
            d = dt.to_dict()
            order_qty = float(dt.rgsqty or 0)
            received_qty = float(dt.inqty or 0)
            settled = PurchaseBillRepository.get_settled_total(rgstbillid, dt.lineno)
            returned = ReturnPurchaseRepository.get_returned_total(rgstbillid, dt.lineno)
            d["order_qty"] = order_qty
            d["received_qty"] = received_qty
            d["already_settled"] = settled
            d["already_returned"] = returned
            d["settleable_qty_cod"] = max(0, received_qty - settled)
            d["settleable_qty_pia"] = max(0, order_qty - settled)
            items.append(d)
        return items
```

- [ ] **Step 2: 重写 ReturnPurchaseService**

替换 `app/services/procurement_service.py` 第548-588行的 `ReturnPurchaseService`：

```python
class ReturnPurchaseService:
    """采购退货服务 (TPC16/TPC17)。"""

    @staticmethod
    def get(pcbillid: str) -> dict[str, Any] | None:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return None
        result = record.to_dict()
        details = [d.to_dict() for d in ReturnPurchaseRepository.list_details(pcbillid)]
        for d in details:
            d.pop("bill", None)
        result["details"] = details
        return result

    @staticmethod
    def list_records(
        suppliercd: str | None = None,
        auditflg: str | None = None,
        start_date: dt | None = None,
        end_date: dt | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        items, total = ReturnPurchaseRepository.list_by_filters(
            suppliercd=suppliercd, auditflg=auditflg,
            start_date=start_date, end_date=end_date, page=page, per_page=per_page,
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total, "page": page, "per_page": per_page,
        }

    @staticmethod
    def create(data: dict[str, Any], creator: str) -> dict[str, Any]:
        details = data.pop("details", [])
        ref_rgstbillid = data.get("ref_rgstbillid", "")
        # 校验退货数量
        total_amt = 0
        for d in details:
            rpcqty = int(d.get("rpcqty", 0))
            ref_line = int(d.get("ref_rgstlineno", 0))
            if rpcqty <= 0:
                raise ValueError(f"行 {ref_line} 退货数量必须大于0")

            # 查订单行入库量（主键是 id，用 rgstbillid + lineno 查询）
            order_dt = (
                db.session.query(PurchaseRegisterDt)
                .filter(
                    PurchaseRegisterDt.rgstbillid == ref_rgstbillid,
                    PurchaseRegisterDt.lineno == ref_line,
                )
                .first()
            )
            if order_dt is None:
                raise ValueError(f"订单行 {ref_rgstbillid}:{ref_line} 不存在")
            received_qty = int(order_dt.inqty or 0)
            if received_qty <= 0:
                raise ValueError(f"订单行 {ref_rgstbillid}:{ref_line} 尚未入库，无法退货")

            # 查已退货累计
            already_returned = ReturnPurchaseRepository.get_returned_total(ref_rgstbillid, ref_line)
            max_return = received_qty - int(already_returned)
            if rpcqty > max_return:
                raise ValueError(
                    f"行 {ref_line} 退货数量({rpcqty})超过可退余量({max_return})"
                )

            return_price = float(d.get("return_price") or 0)
            return_amt = rpcqty * return_price
            total_amt += int(return_amt)
            d["return_amt"] = return_amt

        data["pcamt"] = total_amt
        data["auditflg"] = "0"
        record = ReturnPurchaseRepository.create(data, creator)
        for idx, detail_data in enumerate(details, start=1):
            ReturnPurchaseRepository.add_detail(record.pcbillid, idx, detail_data)
        db.session.commit()
        return ReturnPurchaseService.get(record.pcbillid)  # type: ignore[return-value]

    @staticmethod
    def update(pcbillid: str, data: dict[str, Any]) -> dict[str, object]:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "退货单不存在"}
        if record.auditflg != "0":
            return {"success": False, "error": "仅未审核单据可编辑"}

        details = data.pop("details", None)
        if details is not None:
            ref_rgstbillid = record.ref_rgstbillid or ""
            total_amt = 0
            for d in details:
                rpcqty = int(d.get("rpcqty", 0))
                ref_line = int(d.get("ref_rgstlineno", 0))
                if rpcqty <= 0:
                    raise ValueError(f"行 {ref_line} 退货数量必须大于0")
                order_dt = (
                    db.session.query(PurchaseRegisterDt)
                    .filter(
                        PurchaseRegisterDt.rgstbillid == ref_rgstbillid,
                        PurchaseRegisterDt.lineno == ref_line,
                    )
                    .first()
                )
                received_qty = int(order_dt.inqty or 0) if order_dt else 0
                already_returned = ReturnPurchaseRepository.get_returned_total(ref_rgstbillid, ref_line)
                max_return = received_qty - int(already_returned)
                if rpcqty > max_return:
                    raise ValueError(f"行 {ref_line} 退货数量({rpcqty})超过可退余量({max_return})")
                return_price = float(d.get("return_price") or 0)
                return_amt = rpcqty * return_price
                total_amt += int(return_amt)
                d["return_amt"] = return_amt
            data["pcamt"] = total_amt
            ReturnPurchaseRepository.clear_details(pcbillid)
            for idx, d in enumerate(details, start=1):
                ReturnPurchaseRepository.add_detail(pcbillid, idx, d)

        ReturnPurchaseRepository.update(record, data)
        record.auditflg = "0"
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def audit(pcbillid: str, auditor: str, auditflg: str) -> dict[str, object]:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "退货单不存在"}
        if record.useflg == "9":
            return {"success": False, "error": "已作废单据不可审核"}
        if record.auditflg not in ("0", "1"):
            return {"success": False, "error": "不可重复审核"}
        record.auditflg = auditflg
        record.auditman = auditor
        record.auditdate = datetime.now(UTC)
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def void(pcbillid: str) -> dict[str, object]:
        record = ReturnPurchaseRepository.get_by_id(pcbillid)
        if record is None:
            return {"success": False, "error": "退货单不存在"}
        if record.auditflg == "2":
            return {"success": False, "error": "已审核通过的退货单不能作废"}
        record.useflg = "9"
        record.auditflg = "9"  # 同时设审核状态为作废，防止通过 audit() 误审
        db.session.commit()
        return {"success": True, "pcbillid": pcbillid}

    @staticmethod
    def get_returnable_items(rgstbillid: str) -> list[dict[str, Any]]:
        """查询订单的可退货商品行。"""
        order = PurchaseRegisterRepository.get_by_id(rgstbillid)
        if order is None:
            raise ValueError("订单不存在")
        items = []
        for dt in order.details:  # type: ignore[attr-defined]
            d = dt.to_dict()
            received_qty = int(dt.inqty or 0)
            if received_qty <= 0:
                continue  # 未入库的不显示
            returned = ReturnPurchaseRepository.get_returned_total(rgstbillid, dt.lineno)
            d["received_qty"] = received_qty
            d["already_returned"] = int(returned)
            d["returnable_qty"] = max(0, received_qty - int(returned))
            items.append(d)
        return items
```

- [ ] **Step 3: 确保文件头部导入完整**

检查 `app/services/procurement_service.py` 顶部导入，确保有：

```python
from datetime import datetime, timezone as dt_timezone
from app.models.procurement import PurchaseBillDt, PurchaseRegisterDt, RequisitionOrderLink
```

- [ ] **Step 4: 验证服务可导入**

Run: `python3 -c "from app.services.procurement_service import PurchaseBillService, ReturnPurchaseService; print('OK')"`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add app/services/procurement_service.py
git commit -m "feat(procurement): 重写结算/退货Service — 完整CRUD+Audit+数量校验"
```

---

### Task 6: 更新 API 路由

**Files:**
- Modify: `app/api/procurement.py`

- [ ] **Step 1: 重写结算单 API**

替换 `app/api/procurement.py` 第279-310行：

```python
# ---- 采购结算单 ----

@procurement_bp.get("/settlements")
@login_required
def list_settlements():  # type: ignore[no-untyped-def]
    """采购结算单列表。"""
    return success_response(data=PurchaseBillService.list_records(
        suppliercd=request.args.get("suppliercd"),
        auditflg=request.args.get("auditflg"),
        pay_type=request.args.get("pay_type"),
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 20, type=int),
    ))


@procurement_bp.get("/settlements/<pcbillid>")
@login_required
def get_settlement(pcbillid: str):  # type: ignore[no-untyped-def]
    """采购结算单详情。"""
    data = PurchaseBillService.get(pcbillid)
    if data is None:
        return error_response(message="采购结算单不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/settlements")
@login_required
def create_settlement():  # type: ignore[no-untyped-def]
    """创建采购结算单（含明细行）。"""
    json_data = request.get_json(silent=True) or {}
    body = PurchaseBillCreate.model_validate(json_data)
    user_cd: str = g.current_user
    try:
        data = PurchaseBillService.create(body.model_dump(), user_cd)
        return success_response(data=data, message="创建成功", code=201)
    except ValueError as e:
        return error_response(message=str(e), code=400)


@procurement_bp.put("/settlements/<pcbillid>")
@login_required
def update_settlement(pcbillid: str):  # type: ignore[no-untyped-def]
    """编辑采购结算单。"""
    json_data = request.get_json(silent=True) or {}
    body = PurchaseBillUpdate.model_validate(json_data)
    try:
        result = PurchaseBillService.update(pcbillid, body.model_dump(exclude_none=True))
        if result.get("error"):
            return error_response(message=str(result["error"]), code=400)
        return success_response(data=result)
    except ValueError as e:
        return error_response(message=str(e), code=400)


@procurement_bp.post("/settlements/<pcbillid>/audit")
@login_required
def audit_settlement(pcbillid: str):  # type: ignore[no-untyped-def]
    """审核采购结算单。"""
    json_data = request.get_json(silent=True) or {}
    auditflg = json_data.get("auditflg", "2")
    user_cd: str = g.current_user
    result = PurchaseBillService.audit(pcbillid, user_cd, auditflg)
    if result.get("error"):
        return error_response(message=str(result["error"]), code=400)
    return success_response(data=result, message="审核成功")


@procurement_bp.post("/settlements/<pcbillid>/void")
@login_required
def void_settlement(pcbillid: str):  # type: ignore[no-untyped-def]
    """作废采购结算单。"""
    result = PurchaseBillService.void(pcbillid)
    if result.get("error"):
        return error_response(message=str(result["error"]), code=400)
    return success_response(data=result, message="已作废")


@procurement_bp.get("/orders/<rgstbillid>/settleable-items")
@login_required
def get_settleable_items(rgstbillid: str):  # type: ignore[no-untyped-def]
    """查询订单的可结算商品行。"""
    try:
        return success_response(data=PurchaseBillService.get_settleable_items(rgstbillid))
    except ValueError as e:
        return error_response(message=str(e), code=404)
```

- [ ] **Step 2: 重写退货 API**

替换 `app/api/procurement.py` 第313-347行：

```python
# ---- 采购退货 ----

@procurement_bp.get("/returns")
@login_required
def list_returns():  # type: ignore[no-untyped-def]
    """采购退货列表。"""
    return success_response(data=ReturnPurchaseService.list_records(
        suppliercd=request.args.get("suppliercd"),
        auditflg=request.args.get("auditflg"),
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 20, type=int),
    ))


@procurement_bp.get("/returns/<pcbillid>")
@login_required
def get_return(pcbillid: str):  # type: ignore[no-untyped-def]
    """采购退货详情。"""
    data = ReturnPurchaseService.get(pcbillid)
    if data is None:
        return error_response(message="采购退货单不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/returns")
@login_required
def create_return():  # type: ignore[no-untyped-def]
    """创建采购退货单。"""
    json_data = request.get_json(silent=True) or {}
    body = ReturnPurchaseBillCreate.model_validate(json_data)
    user_cd: str = g.current_user
    try:
        data = ReturnPurchaseService.create(body.model_dump(), user_cd)
        return success_response(data=data, message="创建成功", code=201)
    except ValueError as e:
        return error_response(message=str(e), code=400)


@procurement_bp.put("/returns/<pcbillid>")
@login_required
def update_return(pcbillid: str):  # type: ignore[no-untyped-def]
    """编辑采购退货单。"""
    json_data = request.get_json(silent=True) or {}
    body = ReturnPurchaseBillUpdate.model_validate(json_data)
    try:
        result = ReturnPurchaseService.update(pcbillid, body.model_dump(exclude_none=True))
        if result.get("error"):
            return error_response(message=str(result["error"]), code=400)
        return success_response(data=result)
    except ValueError as e:
        return error_response(message=str(e), code=400)


@procurement_bp.post("/returns/<pcbillid>/audit")
@login_required
def audit_return(pcbillid: str):  # type: ignore[no-untyped-def]
    """审核采购退货单。"""
    json_data = request.get_json(silent=True) or {}
    auditflg = json_data.get("auditflg", "2")
    user_cd: str = g.current_user
    result = ReturnPurchaseService.audit(pcbillid, user_cd, auditflg)
    if result.get("error"):
        return error_response(message=str(result["error"]), code=400)
    return success_response(data=result, message="审核成功")


@procurement_bp.post("/returns/<pcbillid>/void")
@login_required
def void_return(pcbillid: str):  # type: ignore[no-untyped-def]
    """作废采购退货单。"""
    result = ReturnPurchaseService.void(pcbillid)
    if result.get("error"):
        return error_response(message=str(result["error"]), code=400)
    return success_response(data=result, message="已作废")


@procurement_bp.get("/orders/<rgstbillid>/returnable-items")
@login_required
def get_returnable_items(rgstbillid: str):  # type: ignore[no-untyped-def]
    """查询订单的可退货商品行。"""
    try:
        return success_response(data=ReturnPurchaseService.get_returnable_items(rgstbillid))
    except ValueError as e:
        return error_response(message=str(e), code=404)
```

- [ ] **Step 3: 确保 API 文件导入正确**

检查 `app/api/procurement.py` 头部有：

```python
from app.schemas.procurement import (
    PurchaseBillCreate, PurchaseBillUpdate,
    ReturnPurchaseBillCreate, ReturnPurchaseBillDetailCreate, ReturnPurchaseBillUpdate,
    ...
)
from app.services.procurement_service import PurchaseBillService, ReturnPurchaseService
```

- [ ] **Step 4: 验证路由注册**

Run: `python3 -c "from app import create_app; app = create_app(); rules = [r.rule for r in app.url_map.iter_rules()]; print([r for r in rules if 'settle' in r or 'return' in r])"`

若 DATABASE_URL 不可用，改为：`grep -c "settlements\|returns" app/api/procurement.py`

- [ ] **Step 5: Commit**

```bash
git add app/api/procurement.py
git commit -m "feat(procurement): 结算/退货API — 完整CRUD+Audit+可结算/退货查询"
```

---

### Task 7: 更新前端 API 层 (TypeScript)

**Files:**
- Modify: `frontend/src/api/procurement.ts`

- [ ] **Step 1: 新增结算单 API 函数和类型**

在 `frontend/src/api/procurement.ts` 中替换结算单元（第33-43行）：

```typescript
// ---- 采购结算单 ----

export interface SettlementRecord {
    pcbillid: string; suppliercd: string; pay_type: string;
    invoice_no?: string; invoice_date?: string; pcdate?: string;
    total_settle_amt: number; whcd: string; invoiceflg: string;
    auditflg: string; auditman?: string; auditdate?: string;
    memo?: string; gendate: string; opercd: string;
    details?: SettlementDetail[];
    [key:string]: unknown
}
export interface SettlementDetail {
    lineno: number; ref_rgstbillid: string; ref_rgstlineno: number;
    itemcd: string; order_qty: number; received_qty: number;
    already_settled: number; settle_qty: number;
    settle_price: number; settle_amt: number;
    [key:string]: unknown
}
export interface SettlementPage { items: SettlementRecord[]; total: number }

export function fetchSettlements(p?:Record<string,string>){
    return request.get<never,{data:SettlementPage}>('/procurement/settlements',{params:p})
}
export function fetchSettlementDetail(pcbillid:string){
    return request.get<never,{data:SettlementRecord}>('/procurement/settlements/'+pcbillid)
}
export function createSettlement(body:Record<string,unknown>){
    return request.post<never,{data:SettlementRecord}>('/procurement/settlements',body)
}
export function updateSettlement(pcbillid:string, body:Record<string,unknown>){
    return request.put<never,{data:{success:boolean}}>('/procurement/settlements/'+pcbillid, body)
}
export function auditSettlement(pcbillid:string, auditflg:string='2'){
    return request.post<never,{data:{success:boolean}}>('/procurement/settlements/'+pcbillid+'/audit',{auditflg})
}
export function voidSettlement(pcbillid:string){
    return request.post<never,{data:{success:boolean}}>('/procurement/settlements/'+pcbillid+'/void')
}
export function fetchSettleableItems(rgstbillid:string){
    return request.get<never,{data:ProcRecord[]}>('/procurement/orders/'+rgstbillid+'/settleable-items')
}
```

- [ ] **Step 2: 新增退货单 API 函数**

在 `frontend/src/api/procurement.ts` 中替换退货段（第45-68行）：

```typescript
// ---- 采购退货 ----

export interface ReturnPurchaseRecord {
    pcbillid: string; suppliercd: string; whcd: string; pcamt: number;
    invoiceflg: string; memo: string; gendate: string; opercd: string;
    ref_rgstbillid?: string; return_reason?: string;
    auditflg?: string; auditman?: string; auditdate?: string;
    details?: ReturnPurchaseDetail[];
    [key:string]: unknown
}
export interface ReturnPurchaseDetail {
    itemcd: string; rpcqty: number; eid: string; units: string;
    ref_rgstlineno?: number; return_price?: number; return_amt?: number;
    line_reason?: string;
    [key:string]: unknown
}
export interface ReturnPurchasePage { items: ReturnPurchaseRecord[]; total: number }

export function fetchReturns(p?:Record<string,string>){
    return request.get<never,{data:ReturnPurchasePage}>('/procurement/returns',{params:p})
}
export function fetchReturnDetail(pcbillid:string){
    return request.get<never,{data:ReturnPurchaseRecord}>('/procurement/returns/'+pcbillid)
}
export function createReturn(body:Record<string,unknown>){
    return request.post<never,{data:ReturnPurchaseRecord}>('/procurement/returns',body)
}
export function updateReturn(pcbillid:string, body:Record<string,unknown>){
    return request.put<never,{data:{success:boolean}}>('/procurement/returns/'+pcbillid, body)
}
export function auditReturn(pcbillid:string, auditflg:string='2'){
    return request.post<never,{data:{success:boolean}}>('/procurement/returns/'+pcbillid+'/audit',{auditflg})
}
export function voidReturn(pcbillid:string){
    return request.post<never,{data:{success:boolean}}>('/procurement/returns/'+pcbillid+'/void')
}
export function fetchReturnableItems(rgstbillid:string){
    return request.get<never,{data:ProcRecord[]}>('/procurement/orders/'+rgstbillid+'/returnable-items')
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/procurement.ts
git commit -m "feat(procurement): 前端API层 — 结算/退货完整接口+类型定义"
```

---

### Task 8: 采购结算单前端页面

**Files:**
- Modify: `frontend/src/views/procurement/PurchaseBillList.vue`

- [ ] **Step 1: 重写列表页面 — 增加筛选+新建弹窗+审核**

```vue
<template>
  <div class="page">
    <div class="page-header">
      <h2>采购结算单</h2>
      <el-button type="primary" size="small" @click="openCreate">新建结算单</el-button>
    </div>
    <el-card shadow="never">
      <!-- 筛选 -->
      <div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap">
        <el-select v-model="filterSuppliercd" size="small" filterable clearable placeholder="供应商" style="width:180px" @change="load">
          <el-option v-for="s in supplierOptions" :key="s.supp_cd" :label="s.supp_nm" :value="s.supp_cd"/>
        </el-select>
        <el-select v-model="filterAuditflg" size="small" clearable placeholder="审核状态" style="width:130px" @change="load">
          <el-option label="未审核" value="0"/><el-option label="已审核" value="2"/>
        </el-select>
        <el-select v-model="filterPayType" size="small" clearable placeholder="付款方式" style="width:130px" @change="load">
          <el-option v-for="(nm,k) in payTypeMap" :key="k" :label="nm" :value="k"/>
        </el-select>
        <el-button size="small" @click="load" :icon="'Refresh'">刷新</el-button>
      </div>

      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDetail">
        <el-table-column prop="pcbillid" label="结算单号" width="110"/>
        <el-table-column label="供应商" width="120"><template #default="{row}">{{ row.suppliercd||'-' }}</template></el-table-column>
        <el-table-column label="付款方式" width="90"><template #default="{row}">{{ payTypeMap[row.pay_type]||row.pay_type||'货到付款' }}</template></el-table-column>
        <el-table-column prop="total_settle_amt" label="结算金额" width="110" align="right"><template #default="{row}">{{ row.total_settle_amt ? '¥'+Number(row.total_settle_amt).toLocaleString() : '-' }}</template></el-table-column>
        <el-table-column label="发票" width="80"><template #default="{row}"><el-tag :type="row.invoiceflg==='1'?'success':'info'" size="small">{{ row.invoiceflg==='1'?'已开':'未开' }}</el-tag></template></el-table-column>
        <el-table-column label="审核" width="80"><template #default="{row}">{{ auditMap[row.auditflg]||'未审核' }}</template></el-table-column>
        <el-table-column label="日期" width="100"><template #default="{row}">{{ row.pcdate||row.gendate||'-' }}</template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{row}">
            <el-button v-if="row.auditflg==='0'" link type="primary" size="small" @click.stop="handleAudit(row,'2')">审核</el-button>
            <el-button v-if="row.auditflg!=='2'" link type="danger" size="small" @click.stop="handleVoid(row)">作废</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer" title="结算单详情" size="650px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="结算单号">{{ detail.pcbillid }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ detail.suppliercd||'-' }}</el-descriptions-item>
          <el-descriptions-item label="付款方式">{{ payTypeMap[detail.pay_type]||detail.pay_type }}</el-descriptions-item>
          <el-descriptions-item label="发票号">{{ detail.invoice_no||'-' }}</el-descriptions-item>
          <el-descriptions-item label="结算金额">{{ detail.total_settle_amt }}</el-descriptions-item>
          <el-descriptions-item label="审核状态">{{ auditMap[detail.auditflg]||'未审核' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo||'-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">结算明细</h4>
        <el-table :data="detail.details||[]" size="small" stripe>
          <el-table-column prop="ref_rgstbillid" label="来源订单" width="100"/>
          <el-table-column prop="itemcd" label="物料" width="90"/>
          <el-table-column prop="order_qty" label="订购量" width="75"/>
          <el-table-column prop="received_qty" label="入库量" width="75"/>
          <el-table-column prop="settle_qty" label="结算量" width="75"/>
          <el-table-column prop="settle_price" label="单价" width="80"/>
          <el-table-column prop="settle_amt" label="金额" width="90"/>
        </el-table>
      </template>
    </el-drawer>

    <!-- 新建结算单弹窗 -->
    <el-dialog v-model="creating" title="新建采购结算单" width="850px" @closed="resetCreateForm">
      <el-form :model="createForm" label-width="90px" size="small">
        <el-form-item label="供应商" required>
          <el-select v-model="createForm.suppliercd" filterable placeholder="选择供应商" style="width:100%" @change="onSettleSupplierChange">
            <el-option v-for="s in supplierOptions" :key="s.supp_cd" :label="s.supp_nm" :value="s.supp_cd"/>
          </el-select>
        </el-form-item>
        <el-form-item label="付款方式">
          <el-select v-model="createForm.pay_type" style="width:200px">
            <el-option v-for="(nm,k) in payTypeMap" :key="k" :label="nm" :value="k"/>
          </el-select>
        </el-form-item>
        <el-form-item label="发票号"><el-input v-model="createForm.invoice_no" placeholder="供应商发票号码"/></el-form-item>
        <el-form-item label="发票日期"><el-date-picker v-model="createForm.invoice_date" type="date" value-format="YYYY-MM-DD" style="width:200px"/></el-form-item>
        <el-form-item label="结算日期"><el-date-picker v-model="createForm.pcdate" type="date" value-format="YYYY-MM-DD" style="width:200px"/></el-form-item>
        <el-form-item label="仓库"><el-input v-model="createForm.whcd" placeholder="入库仓库" style="width:120px"/></el-form-item>

        <el-divider content-position="left">选择结算商品行</el-divider>
        <el-alert v-if="!createForm.suppliercd" title="请先选择供应商" type="info" :closable="false" show-icon/>
        <el-table v-else :data="settleableItems" v-loading="settleableLoading" size="small" stripe max-height="300">
          <el-table-column type="selection" width="50">
            <template #default="{row}">
              <el-checkbox v-model="row._selected"/>
            </template>
          </el-table-column>
          <el-table-column prop="rgstbillid" label="订单号" width="100"/>
          <el-table-column prop="itemcd" label="物料" width="80"/>
          <el-table-column prop="itemnm" label="名称" min-width="100"/>
          <el-table-column label="订购量" width="70"><template #default="{row}">{{ row.order_qty||row.rgsqty }}</template></el-table-column>
          <el-table-column label="入库量" width="70"><template #default="{row}">{{ row.received_qty||row.inqty }}</template></el-table-column>
          <el-table-column label="已结算" width="70"><template #default="{row}">{{ row.already_settled||0 }}</template></el-table-column>
          <el-table-column label="可结算" width="80"><template #default="{row}">{{ getSettleableQty(row) }}</template></el-table-column>
          <el-table-column label="本次结算数" width="130"><template #default="{row}"><el-input-number v-model="row._sqty" :min="0" :max="getSettleableQty(row)" size="small" style="width:110px" controls-position="right" :disabled="!row._selected"/></template></el-table-column>
          <el-table-column label="结算单价" width="120"><template #default="{row}"><el-input-number v-model="row._sprice" :min="0" :precision="2" size="small" style="width:100px" controls-position="right" :disabled="!row._selected"/></template></el-table-column>
        </el-table>
        <el-form-item label="备注"><el-input v-model="createForm.memo" type="textarea" :rows="2"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="creating=false">取消</el-button>
        <el-button type="primary" @click="handleCreateSettlement" :loading="saving">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { fetchSettlements, fetchSettlementDetail, createSettlement, auditSettlement, voidSettlement, fetchSettleableItems } from '@/api/procurement'
import { fetchSupplierList } from '@/api/master'
import type { SettlementRecord, SettlementPage } from '@/api/procurement'

const payTypeMap:Record<string,string> = { COD:'货到付款', PIA:'款到发货', DEP:'预付+尾款', MON:'月结', INS:'分期付款' }
const auditMap:Record<string,string> = { '0':'未审核', '2':'已审核', '9':'已作废' }

// 列表
const items=ref<SettlementRecord[]>([]); const loading=ref(false)
const page=ref(1); const perPage=ref(20); const total=ref(0)
const filterSuppliercd=ref(''); const filterAuditflg=ref(''); const filterPayType=ref('')
const supplierOptions=ref<{supp_cd:string;supp_nm:string}[]>([])

async function load(){
  loading.value=true
  try{
    const p:Record<string,string>={page:String(page.value),per_page:String(perPage.value)}
    if(filterSuppliercd.value)p.suppliercd=filterSuppliercd.value
    if(filterAuditflg.value)p.auditflg=filterAuditflg.value
    if(filterPayType.value)p.pay_type=filterPayType.value
    const r=await fetchSettlements(p)
    items.value=(r.data as SettlementPage).items||[]
    total.value=(r.data as SettlementPage).total||0
  }catch{ElMessage.error('加载失败')}
  finally{loading.value=false}
}
async function loadSuppliers(){
  try{const r=await fetchSupplierList({per_page:'200'}); supplierOptions.value=(r.data as any)?.items||[]}
  catch{/* ignore */}
}
onMounted(()=>{loadSuppliers();load()})

// 详情
const drawer=ref(false); const detail=ref<SettlementRecord|null>(null)
async function openDetail(row:SettlementRecord){
  try{const r=await fetchSettlementDetail(row.pcbillid);detail.value=r.data as SettlementRecord;drawer.value=true}
  catch{ElMessage.error('加载详情失败')}
}

// 审核
async function handleAudit(row:SettlementRecord, auditflg:string){
  try{await auditSettlement(row.pcbillid,auditflg); ElMessage.success('审核成功'); load()}
  catch(e:any){ElMessage.error(e?.response?.data?.message||'审核失败')}
}

// 作废
async function handleVoid(row:SettlementRecord){
  try{await ElMessageBox.confirm(`确定作废结算单 ${row.pcbillid}？`,'确认'); await voidSettlement(row.pcbillid); ElMessage.success('已作废'); load()}
  catch{/* cancel */}
}

// 新建
const creating=ref(false); const saving=ref(false)
const createForm=reactive({suppliercd:'',pay_type:'COD',invoice_no:'',invoice_date:'',pcdate:'',whcd:'',memo:''})
const settleableItems=ref<any[]>([]); const settleableLoading=ref(false)

function getSettleableQty(row:any):number{
  const isCod=createForm.pay_type==='COD'||createForm.pay_type==='MON'
  const received=Number(row.received_qty||row.inqty||0)
  const ordered=Number(row.order_qty||row.rgsqty||0)
  const settled=Number(row.already_settled||0)
  return isCod ? Math.max(0,received-settled) : Math.max(0,ordered-settled)
}

async function onSettleSupplierChange(){
  settleableItems.value=[]
  if(!createForm.suppliercd)return
  settleableLoading.value=true
  try{
    // 拉该供应商所有已审核订单的可结算行
    const {fetchOrders} = await import('@/api/procurement')
    const r=await fetchOrders({suppliercd:createForm.suppliercd, auditflg:'2', per_page:'100'})
    const orders=(r.data as any)?.items||[]
    const allItems:any[]=[]
    for(const o of orders){
      try{
        const si=await fetchSettleableItems(o.rgstbillid)
        const lines=(si.data||[]) as any[]
        for(const l of lines){ l.rgstbillid=o.rgstbillid; l._selected=false; l._sqty=l.rgsqty||0; l._sprice=Number(l.rgstprice||0); allItems.push(l) }
      }catch{/* skip */}
    }
    settleableItems.value=allItems
  }catch{ElMessage.error('加载可结算商品失败')}
  finally{settleableLoading.value=false}
}

async function handleCreateSettlement(){
  const selected=settleableItems.value.filter((it:any)=>it._selected&&it._sqty>0)
  if(selected.length===0){ElMessage.warning('请至少勾选一行并填写结算数量');return}
  saving.value=true
  try{
    const details=selected.map((it:any)=>({
      ref_rgstbillid:it.rgstbillid, ref_rgstlineno:it.lineno,
      itemcd:it.itemcd, settle_qty:it._sqty, settle_price:it._sprice||0,
    }))
    await createSettlement({...createForm, details})
    ElMessage.success('创建成功'); creating.value=false; load()
  }catch(e:any){ElMessage.error(e?.response?.data?.message||'创建失败')}
  finally{saving.value=false}
}

function resetCreateForm(){
  createForm.suppliercd='';createForm.pay_type='COD';createForm.invoice_no=''
  createForm.invoice_date='';createForm.pcdate='';createForm.whcd='';createForm.memo=''
  settleableItems.value=[]
}

function openCreate(){creating.value=true}
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}</style>
```

- [ ] **Step 2: 验证 Vue 编译**

Run: `cd frontend && npx vue-tsc --noEmit src/views/procurement/PurchaseBillList.vue 2>&1 | head -20` (如有类型错误按需调整)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/procurement/PurchaseBillList.vue
git commit -m "feat(procurement): 结算单前端 — 列表筛选+新建弹窗+审核作废"
```

---

### Task 9: 采购退货前端页面

**Files:**
- Modify: `frontend/src/views/procurement/ReturnPurchaseList.vue`

- [ ] **Step 1: 重写退货列表 — 增加筛选+新建+审核**

```vue
<template>
  <div class="page">
    <div class="page-header">
      <h2>采购退货</h2>
      <el-button type="primary" size="small" @click="openCreate">新建退货单</el-button>
    </div>
    <el-card shadow="never">
      <div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap">
        <el-select v-model="filterSuppliercd" size="small" filterable clearable placeholder="供应商" style="width:180px" @change="load">
          <el-option v-for="s in supplierOptions" :key="s.supp_cd" :label="s.supp_nm" :value="s.supp_cd"/>
        </el-select>
        <el-select v-model="filterAuditflg" size="small" clearable placeholder="审核状态" style="width:130px" @change="load">
          <el-option label="未审核" value="0"/><el-option label="已审核" value="2"/>
        </el-select>
        <el-button size="small" @click="load">刷新</el-button>
      </div>

      <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="openDetail">
        <el-table-column prop="pcbillid" label="退货单号" width="110"/>
        <el-table-column label="供应商" width="120"><template #default="{row}">{{ row.suppliercd||'-' }}</template></el-table-column>
        <el-table-column label="来源订单" width="100"><template #default="{row}">{{ row.ref_rgstbillid||'-' }}</template></el-table-column>
        <el-table-column label="退货原因" width="100"><template #default="{row}">{{ reasonMap[row.return_reason]||row.return_reason||'-' }}</template></el-table-column>
        <el-table-column prop="pcamt" label="金额" width="100" align="right"><template #default="{row}">{{ row.pcamt ? '¥'+Number(row.pcamt).toLocaleString() : '-' }}</template></el-table-column>
        <el-table-column label="审核" width="80"><template #default="{row}">{{ auditMap[row.auditflg]||'未审核' }}</template></el-table-column>
        <el-table-column label="日期" width="100"><template #default="{row}">{{ row.pcdate||row.gendate||'-' }}</template></el-table-column>
        <el-table-column prop="memo" label="备注" min-width="120" show-overflow-tooltip/>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{row}">
            <el-button v-if="row.auditflg==='0'" link type="primary" size="small" @click.stop="handleAudit(row,'2')">审核</el-button>
            <el-button v-if="row.auditflg!=='2'" link type="danger" size="small" @click.stop="handleVoid(row)">作废</el-button>
          </template>
        </el-table-column>
      </el-table>
      <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer" title="退货单详情" size="650px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="退货单号">{{ detail.pcbillid }}</el-descriptions-item>
          <el-descriptions-item label="来源订单">{{ detail.ref_rgstbillid||'-' }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ detail.suppliercd||'-' }}</el-descriptions-item>
          <el-descriptions-item label="退货原因">{{ reasonMap[detail.return_reason]||detail.return_reason||'-' }}</el-descriptions-item>
          <el-descriptions-item label="退货金额">{{ detail.pcamt }}</el-descriptions-item>
          <el-descriptions-item label="审核状态">{{ auditMap[detail.auditflg]||'未审核' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.memo||'-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">退货明细</h4>
        <el-table :data="detail.details||[]" size="small" stripe>
          <el-table-column prop="itemcd" label="物料" width="90"/>
          <el-table-column prop="rpcqty" label="退货数量" width="85"/>
          <el-table-column prop="return_price" label="退货单价" width="90"/>
          <el-table-column prop="return_amt" label="退货金额" width="90"/>
          <el-table-column prop="line_reason" label="行原因" min-width="120" show-overflow-tooltip/>
          <el-table-column prop="eid" label="EID" width="130"/>
        </el-table>
      </template>
    </el-drawer>

    <!-- 新建退货单弹窗 -->
    <el-dialog v-model="creating" title="新建采购退货单" width="850px" @closed="resetCreateForm">
      <el-form :model="createForm" label-width="90px" size="small">
        <el-form-item label="来源订单" required>
          <el-select v-model="createForm.ref_rgstbillid" filterable placeholder="选择已入库的采购订单" style="width:100%" @change="onOrderChange">
            <el-option v-for="o in orderOptions" :key="o.rgstbillid" :label="`${o.rgstbillid} (${o.suppliercd||''})`" :value="o.rgstbillid"/>
          </el-select>
        </el-form-item>
        <el-form-item label="退货原因" required>
          <el-select v-model="createForm.return_reason" style="width:200px">
            <el-option v-for="(nm,k) in reasonMap" :key="k" :label="nm" :value="k"/>
          </el-select>
        </el-form-item>
        <el-form-item label="退货日期"><el-date-picker v-model="createForm.pcdate" type="date" value-format="YYYY-MM-DD" style="width:200px"/></el-form-item>
        <el-form-item label="仓库"><el-input v-model="createForm.whcd" placeholder="退货仓库" style="width:120px"/></el-form-item>

        <el-divider content-position="left">选择退货商品行</el-divider>
        <el-alert v-if="!createForm.ref_rgstbillid" title="请先选择来源采购订单" type="info" :closable="false" show-icon/>
        <el-table v-else :data="returnableItems" v-loading="returnableLoading" size="small" stripe max-height="300">
          <el-table-column type="selection" width="50">
            <template #default="{row}"><el-checkbox v-model="row._selected"/></template>
          </el-table-column>
          <el-table-column prop="itemcd" label="物料" width="80"/>
          <el-table-column prop="itemnm" label="名称" min-width="100"/>
          <el-table-column label="已入库" width="75"><template #default="{row}">{{ row.received_qty||row.inqty||0 }}</template></el-table-column>
          <el-table-column label="已退货" width="75"><template #default="{row}">{{ row.already_returned||0 }}</template></el-table-column>
          <el-table-column label="可退" width="70"><template #default="{row}">{{ Math.max(0,(row.received_qty||row.inqty||0)-(row.already_returned||0)) }}</template></el-table-column>
          <el-table-column label="本次退货数" width="130"><template #default="{row}"><el-input-number v-model="row._rqty" :min="0" :max="Math.max(0,(row.received_qty||row.inqty||0)-(row.already_returned||0))" size="small" style="width:110px" controls-position="right" :disabled="!row._selected"/></template></el-table-column>
          <el-table-column label="退货单价" width="120"><template #default="{row}"><el-input-number v-model="row._rprice" :min="0" :precision="2" size="small" style="width:100px" controls-position="right" :disabled="!row._selected"/></template></el-table-column>
          <el-table-column label="行原因" width="160"><template #default="{row}"><el-input v-model="row._reason" size="small" placeholder="补充描述" :disabled="!row._selected"/></template></el-table-column>
        </el-table>
        <el-form-item label="备注"><el-input v-model="createForm.memo" type="textarea" :rows="2"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="creating=false">取消</el-button>
        <el-button type="primary" @click="handleCreateReturn" :loading="saving">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPagination from '@/components/common/AppPagination.vue'
import { fetchReturns, fetchReturnDetail, createReturn, auditReturn, voidReturn, fetchReturnableItems, fetchOrders } from '@/api/procurement'
import { fetchSupplierList } from '@/api/master'
import type { ReturnPurchaseRecord, ReturnPurchasePage } from '@/api/procurement'

const reasonMap:Record<string,string> = { quality:'质量问题', quantity:'数量不符', spec:'规格错误', other:'其他' }
const auditMap:Record<string,string> = { '0':'未审核', '2':'已审核', '9':'已作废' }

// 列表
const items=ref<ReturnPurchaseRecord[]>([]); const loading=ref(false)
const page=ref(1); const perPage=ref(20); const total=ref(0)
const filterSuppliercd=ref(''); const filterAuditflg=ref('')
const supplierOptions=ref<{supp_cd:string;supp_nm:string}[]>([])

async function load(){
  loading.value=true
  try{
    const p:Record<string,string>={page:String(page.value),per_page:String(perPage.value)}
    if(filterSuppliercd.value)p.suppliercd=filterSuppliercd.value
    if(filterAuditflg.value)p.auditflg=filterAuditflg.value
    const r=await fetchReturns(p)
    items.value=(r.data as ReturnPurchasePage).items||[]
    total.value=(r.data as ReturnPurchasePage).total||0
  }catch{ElMessage.error('加载失败')}
  finally{loading.value=false}
}
async function loadSuppliers(){
  try{const r=await fetchSupplierList({per_page:'200'}); supplierOptions.value=(r.data as any)?.items||[]}
  catch{/* ignore */}
}
onMounted(()=>{loadSuppliers();load()})

// 详情
const drawer=ref(false); const detail=ref<ReturnPurchaseRecord|null>(null)
async function openDetail(row:ReturnPurchaseRecord){
  try{const r=await fetchReturnDetail(row.pcbillid);detail.value=r.data as ReturnPurchaseRecord;drawer.value=true}
  catch{ElMessage.error('加载详情失败')}
}

// 审核
async function handleAudit(row:ReturnPurchaseRecord, auditflg:string){
  try{await auditReturn(row.pcbillid,auditflg); ElMessage.success('审核成功'); load()}
  catch(e:any){ElMessage.error(e?.response?.data?.message||'审核失败')}
}

// 作废
async function handleVoid(row:ReturnPurchaseRecord){
  try{await ElMessageBox.confirm(`确定作废退货单 ${row.pcbillid}？`,'确认'); await voidReturn(row.pcbillid); ElMessage.success('已作废'); load()}
  catch{/* cancel */}
}

// 新建
const creating=ref(false); const saving=ref(false)
const createForm=reactive({ref_rgstbillid:'',return_reason:'quality',pcdate:'',whcd:'',memo:''})
const returnableItems=ref<any[]>([]); const returnableLoading=ref(false)
const orderOptions=ref<any[]>([])

async function loadOrders(){
  try{
    const r=await fetchOrders({auditflg:'2',per_page:'200'})
    orderOptions.value=(r.data as any)?.items||[]
  }catch{/* ignore */}
}

async function onOrderChange(){
  returnableItems.value=[]
  if(!createForm.ref_rgstbillid)return
  returnableLoading.value=true
  try{
    const r=await fetchReturnableItems(createForm.ref_rgstbillid)
    const lines=(r.data||[]) as any[]
    for(const l of lines){
      l._selected=false; l._rqty=l.rgsqty||0; l._rprice=Number(l.rgstprice||0); l._reason=''
    }
    returnableItems.value=lines
  }catch{ElMessage.error('加载可退货商品失败')}
  finally{returnableLoading.value=false}
}

async function handleCreateReturn(){
  const selected=returnableItems.value.filter((it:any)=>it._selected&&it._rqty>0)
  if(selected.length===0){ElMessage.warning('请至少勾选一行并填写退货数量');return}
  if(!createForm.return_reason){ElMessage.warning('请选择退货原因');return}
  saving.value=true
  try{
    const details=selected.map((it:any)=>({
      itemcd:it.itemcd,ref_rgstlineno:it.lineno,rpcqty:it._rqty,
      return_price:it._rprice||0,eid:it.eid,units:it.units,
      line_reason:it._reason||undefined,
    }))
    await createReturn({...createForm,details})
    ElMessage.success('创建成功'); creating.value=false; load()
  }catch(e:any){ElMessage.error(e?.response?.data?.message||'创建失败')}
  finally{saving.value=false}
}

function resetCreateForm(){
  createForm.ref_rgstbillid='';createForm.return_reason='quality'
  createForm.pcdate='';createForm.whcd='';createForm.memo=''
  returnableItems.value=[]
}

function openCreate(){loadOrders();creating.value=true}
</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/procurement/ReturnPurchaseList.vue
git commit -m "feat(procurement): 退货前端 — 列表筛选+新建弹窗+审核作废"
```

---

### Task 10: 集成验证

- [ ] **Step 1: 启动后端验证路由**

Run: `uv run flask run --debug &` 然后 `curl -s http://localhost:5000/api/v1/procurement/settlements -H "Authorization: Bearer $(获取token)"`

- [ ] **Step 2: 前端功能验证**

Run: `cd frontend && npm run dev`
浏览器访问：结算单列表 `/procurement/settlements`、退货列表 `/procurement/returns`

- [ ] **Step 3: 运行已有测试确保无回归**

Run: `uv run pytest tests/test_procurement_api.py tests/test_procurement_batch.py -q`

- [ ] **Step 4: Commit 最后调整**

```bash
git add -A
git commit -m "chore(procurement): 集成验证+修复"
```
