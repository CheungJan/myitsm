# 仓库模块补全实施方案

本方案针对 `2026-05-27-warehouse-module-plan.md` 中已识别的缺口，给出具体代码改动清单，供评审确认后再开始编码。

---

## 现状核查结论（2026-05-27 实测）

| # | 功能点 | 实际状态 | 说明 |
|---|--------|---------|------|
| 1 | 库存同步 `update_balance` | ✅ 已实现 | 入库/出库审核时均调用 |
| 2 | 盘盈盘亏 API | ✅ 已实现 | `/overlost` 完整 |
| 3 | **采购入库审核 → 更新 TPC13.inqty** | ❌ 缺失 | `StockInService.audit` 只更新 TWH11/12，未写回 TPC13 |
| 4 | **退货出库 API (invtyp=6)** | ❌ 缺失 | TWH15 出库单无退货出库入口；退货单审核后无联动 |
| 5 | TWH15 出库单 `refbillid` 字段 | ❌ 缺失 | 数据库 `twh15_out` 无 `refbillid` 列，无法关联来源单据 |
| 6 | TWH14 冗余关联字段 | ❌ 缺失 | 无 `ref_rgstbillid` / `ref_rgstlineno`；追溯需 JOIN TWH13 |
| 7 | 采购订单审核 → 自动生成入库草稿 | ❌ 未实现 | 当前人工手动创建入库单 |

---

## P0 — 必须实现（业务闭环）

### P0-1：`StockInService.audit` 写回 TPC13.inqty

**改动位置**：`app/services/warehouse_service.py` → `StockInService.audit`

**逻辑**：
```
审核通过 + invtyp = '1'（采购入库）时：
  遍历 TWH14 明细（detail.reflineno = 订单行号）
  通过 TWH13.refbillid 取采购订单号
  UPDATE tpc13_registerdt
    SET inqty = inqty + detail.inqty
    WHERE rgstbillid = TWH13.refbillid AND lineno = detail.reflineno
```

**影响范围**：仅在 `invtyp='1'` 时执行，其他入库类型不触发。

---

### P0-2：TWH15 增加 `refbillid` 字段

**问题**：`twh15_out` 表没有 `refbillid`，退货出库无法关联来源退货单号。

**需要**：
1. Alembic 迁移：`ALTER TABLE twh15_out ADD COLUMN refbillid VARCHAR(10)`
2. `StockOut` 模型 (`app/models/warehouse.py`) 增加 `refbillid` 字段
3. `StockOutRepository.create` 传入 `refbillid`
4. `StockOutSchema` 增加 `refbillid` 字段

---

### P0-3：退货出库 API + 采购退货审核联动

**A. 退货出库手动创建**（仓库侧主动操作）

已有 `POST /api/v1/warehouse/stock-out`，只需在前端支持 `invtyp=6` 时输入退货单号作为 `refbillid`，后端无需新增端点，补 `refbillid` 字段后即可使用。

**B. 退货审核自动生成出库草稿**（P0 核心联动）

**改动位置**：`app/services/procurement_service.py` → `ReturnPurchaseService.audit`

```
审核通过（auditflg='2'）后：
  读取 TPC16 退货单（refbillid=退货订单号, whcd, details）
  调用 StockOutService.create({
    invtyp = '6',
    whcd = 退货单的 whcd,
    refbillid = pcbillid（退货单号）,
    suppcd = 退货单的 suppliercd,
    details_prd = [{itemcd, outqty=rpcqty, reflineno}]
  })
  → 生成草稿出库单（auditflg='0'），等待仓库确认后再审核
```

**注意**：只生成草稿，不自动审核，避免库存被自动扣减而仓库未实际出货。

---

## P1 — 增强（追溯能力）

### P1-1：TWH14 增加 `ref_rgstbillid` + `ref_rgstlineno`

**目的**：让入库明细自身携带来源订单信息，免去每次追溯都要 JOIN TWH13。

**改动**：
1. Alembic 迁移：`ALTER TABLE twh14_checkindt ADD COLUMN ref_rgstbillid VARCHAR(10), ADD COLUMN ref_rgstlineno SMALLINT`
2. `StockInDetail` 模型增加两个字段
3. `StockInRepository.add_detail` 在 `invtyp='1'` 时从 TWH13.refbillid 填充这两个字段

---

### P1-2：采购订单审核 → 自动生成入库草稿

**改动位置**：`app/services/procurement_service.py` → `PurchaseRegisterService.audit`

```
审核通过后：
  调用 StockInService.create({
    invtyp = '1',
    refbillid = rgstbillid,
    suppcd = 订单的 suppliercd,
    whcd = 订单的 whcd（若有，否则空），
    details = TPC13 明细 → [{itemcd, inqty=rgsqty, reflineno=lineno}]
  })
  → 生成草稿入库单（auditflg='0'）
```

---

## P2 — 暂不实现

- 质检联动（待质检模块开发）
- 批次管理（TWH14.batchno 字段已存在，前端功能待做）
- 库存预警（需独立触发机制）

---

## 迁移脚本清单

| 迁移 | DDL | 依赖 |
|------|-----|------|
| M1 | `ALTER TABLE twh15_out ADD COLUMN refbillid VARCHAR(10)` | P0-2 前必须执行 |
| M2 | `ALTER TABLE twh14_checkindt ADD COLUMN ref_rgstbillid VARCHAR(10), ADD COLUMN ref_rgstlineno SMALLINT` | P1-1 |

---

## 实施顺序

```
M1 迁移 → P0-2 模型/Schema → P0-3 审核联动
    ↓
P0-1 inqty 写回
    ↓
M2 迁移 → P1-1 冗余字段
    ↓
P1-2 自动草稿
```

---

## 待确认问题

1. **P0-3 退货出库草稿的 whcd**：退货单 `TPC16` 的 `whcd` 是退货发货仓库（物品当前所在仓），请确认这个字段含义是否正确？
2. **P0-1 inqty 类型**：`TPC13.inqty` 为 `Numeric(12,0)`，`TWH14.inqty` 为 `Integer`，累加时需类型对齐，确认用 `int()` 转换即可？
3. **P1-2 自动草稿的 whcd**：采购订单 `TPC12` 无固定 `whcd`（由仓库操作员选择），自动生成草稿时 whcd 留空还是有默认值？
