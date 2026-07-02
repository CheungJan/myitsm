---
类型: 设计文档
阅读状态: 未开始
tags: [预计划, EID, 设备绑定, 销售出库, 安装单, 专项设计]
更新日期: 2026-06-30
创建时间: 2026-06-30
---

# 预计划设备来源与 EID 绑定专项设计

> 本文档专项记录"预计划设备来源→商用仓库→对应设备选择"功能的设计决策、已完成后端工作、待完成前端工作，以及销售实施全链路（预计划→领货→配送→安装→EID 绑定）的规划与现状分析。

## 一、背景与问题

### 1.1 问题起源

预计划新增页面"设备来源→商用仓库→对应设备选择"功能存在以下待澄清问题：

1. 设备选择下拉是否需要显示 `asset_type` 字典名称
2. `itemtyp` 与 `asset_type` 的关联关系
3. 计划机型查询成品为什么查 `TWH11_DETAIL` 而不是 `TMM43_EID`
4. 库存数字是统计 `itemcd` 所在仓库还是固定仓库编号
5. 可用设备查询过滤条件是硬编码还是参数配置

### 1.2 实际业务流程

```
预计划创建 (销售部门)
    ↓
话务核实 (话务台)
    ↓
分派实施部门 (plan_status='02'→'04')
    ↓
实施部门制定送货计划
    ↓
仓库领货 (领货单/OV=1 销售出库草稿)
    ↓
装车配送 (货运车辆)
    ↓
工程师上门安装 (ITSM 安装单)
    ↓
安装完成 → 预计划状态更新为完成
```

**关键节点**：
- **领货单**：实施部门根据计划数量和机型从仓库领取设备，对应系统 `OV=1` 销售出库单
- **配送**：一批门店的设备装在一辆货运车上，按路线配送
- **安装**：工程师上门时从领货设备的 EID 中勾选并绑定给门店

## 二、五个问题的结论

### Q1：设备选择下拉显示 asset_type 字典名称

**结论**：必须显示。

- 当前 EID 查询返回 `asset_type` 是原始码值（01/02/03/04），用户无法理解
- 前端已有 `AT` 字典（`tmm31_syscodes.code_typ='AT'`），直接用 `codeMaps.AT` 渲染
- `EidList.vue` 已改，设备选择组件同理

### Q2：itemtyp 与 asset_type 的关联

**结论**：正交的两个维度，不是映射关系。

| 维度 | itemtyp（物料类型） | asset_type（资产生命周期） |
|------|---------------------|--------------------------|
| 定义 | 物料的质量/来源属性 | 设备的生命周期阶段 |
| 字典 | QC 码表（GA/BH/BF/DJ...） | AT 码表（01/02/03/04） |
| 粒度 | 生产质检维度 | 资产状态维度 |

**现实组合**：
- `itemtyp=GA, asset_type=01` → 合格新机 ✅
- `itemtyp=GA, asset_type=03` → 合格翻新机 ✅
- `itemtyp=BH, asset_type=02` → 待返修旧机 ✅
- `itemtyp=BF, asset_type=04` → 已报废 ✅

**结论**：不能从 `itemtyp` 推导 `asset_type`，也不能反过来。两者独立存在。

**当前系统采用**：`itemtyp`（质检状态 QC）= `GA/GB/GC`，`asset_type`（资产类型 AT）= `01/02/03`。

### Q3：为什么查 TWH11 而不是 TMM43_EID？

**结论**：两个表回答不同的问题，都需要，但场景不同。

| 维度 | TWH11_DETAIL（全仓库库存余量） | TMM43_EID（设备库存） |
|------|-------------------------------|----------------------|
| 定位 | 仓库模块第 11 张表，全仓库库存余量统一台账（`whcd` 列区分仓库） | 设备主表，逐台设备身份与状态 |
| 粒度 | itemcd + whcd + itemtyp | 逐台 EID |
| 回答 | "成品库有 5 台 4Q2006" | "具体是 EID A/B/C/D/E" |
| 适用 | 库存余额、齐套校验 | 设备选择、EID 追溯 |
| 有 EID？ | ❌ 只有数量 | ✅ 每行一个 EID |

**说明**：`TWH11_DETAIL` 不是"11 号仓库"或"来料仓库"，是仓库事务模块（TWH = Transaction Warehouse）的第 11 张表——**全仓库库存余量表**。同一张表通过 `whcd` 列区分 41 个不同仓库（01 新品库、03 成品库、04 生产配件库、05-33 工程师库、MH 翻新仓等）。

**当前 `check_stock` 查 TWH11 只能回答"够不够"**，但预计划的"设备来源→商用仓库→设备选择"需要用户挑具体的 EID。这个场景应该查 `TMM43_EID`，加上 `whcd + asset_type + sflg` 过滤。

### Q4：库存数字是汇总所有仓库还是固定仓库？

**结论**：应按仓库类型（`whtyp`）过滤，默认成品库（`whtyp='03'`）。

**仓库分类**（WT 字典）：

| whtyp | 含义 | 是否商用可用 |
|-------|------|------------|
| 01 | 新品库 | 否（来料/配件） |
| 02 | 维护库 | 否 |
| 03 | 成品库（whcd=03） | ✅ 商用可用设备 |
| 04 | 生产配件库 | 否 |
| EN | 工程师库（whcd=05-33） | 否（已借出） |
| MH | 翻新仓 | 否（翻新中） |
| L0 | 待报废库 | 否 |

**当前代码问题**：`system_repository.py:846` 硬编码 `whcd == "03"`，应改为按 `whtyp` 过滤。

#### 补充澄清：TWH11 如何查成品不同状态的数量？

**TWH11_DETAIL 本身就有 `itemtyp` 字段**（GC/DJ 等 QC 状态码），不需要关联 TMM43_EID。`itemtyp` 就是质检状态，不同状态分别汇总即可。

```sql
-- TWH11 查 4Q4007 各仓库各状态数量
SELECT s.whcd, w.whnm, s.itemtyp, SUM(s.itemqty) AS qty
FROM twh11_detail s LEFT JOIN twh01_warehouse w ON s.whcd=w.whcd
WHERE s.itemcd='4Q4007' AND s.useflg='1' AND s.itemqty>0
GROUP BY s.whcd, w.whnm, s.itemtyp
```

结果：

| whcd | whnm | itemtyp | qty |
|------|------|---------|-----|
| 03 | 成品库 | GC | 5 |
| L7 | 待报废库（维护）2 | DJ | 22 |
| S2 | 临时库2 | DJ | 2 |

#### 改成 TMM43_EID 方式需要固定仓库吗？

**不需要固定 `whcd`**，可以通过关联 `twh01_warehouse` 按 `whtyp` 过滤：

```sql
-- TMM43_EID 查 4Q4007 成品库（whtyp=03）各状态数量
SELECT e.whcd, w.whnm, e.asset_type, e.itemtyp, e.qcflg, COUNT(*) AS cnt
FROM tmm43_eid e LEFT JOIN twh01_warehouse w ON e.whcd=w.whcd
WHERE e.itemcd='4Q4007' AND e.useflg='1' AND e.sflg='8'
  AND w.whtyp='03'  -- 按仓库类型过滤，不固定 whcd
GROUP BY e.whcd, w.whnm, e.asset_type, e.itemtyp, e.qcflg
```

结果：

| whcd | whnm | asset_type | itemtyp | qcflg | cnt |
|------|------|------------|---------|-------|-----|
| 03 | 成品库 | 01 | GC | GC | 5 |

#### TMM43_EID 的 itemtyp 和 qcflg 关系

从数据看，`TMM43_EID.itemtyp` 和 `TMM43_EID.qcflg` **存的是同一个值**（GC/GC、DJ/DJ），两者都来自 QC 字典。`itemtyp` 是物料类型，`qcflg` 是质检标志，但在实际数据中两者一致。

**TWH11 的 itemtyp = TMM43_EID 的 itemtyp = TMM43_EID 的 qcflg**（同源）。

#### 两种方式对比

| 维度 | TWH11 查数量 | TMM43_EID 查数量 |
|------|-------------|-----------------|
| 仓库过滤 | `whcd='03'`（固定编号）或关联 wh01 按 whtyp | 关联 wh01 按 `whtyp='03'`（不固定编号） |
| 状态维度 | `itemtyp`（GC/DJ 等） | `itemtyp` + `asset_type` + `qcflg`（更丰富） |
| 返回 | 数量 | 逐台 EID（可 count 汇总） |
| 性能 | 快（聚合表） | 稍慢（逐台 count） |

**结论**：
1. TWH11 本身有 `itemtyp`，查不同状态数量不需要关联 TMM43
2. 改成 TMM43_EID 方式**不需要固定仓库编号**，通过 `whtyp` 过滤即可
3. TMM43_EID 比 TWH11 多了 `asset_type` 维度，可以按新机/旧机/翻新机分别统计
4. `itemtyp` 和 `qcflg` 在 TMM43_EID 中同源，查数量时用哪个分组都可以

### Q5：过滤条件是固定值还是参数配置？

**结论**：部分参数化。

| 条件 | 当前 | 建议 |
|------|------|------|
| 仓库范围 | 无限制 | 参数：默认 `whtyp='03'`（成品库） |
| asset_type | 无 | 参数：默认 `['01','02','03']`（新机+旧机+翻新机） |
| sflg | 无 | 固定：`'8'`（在库） |
| itemtyp | 无 | 参数：默认 `['GA','GB','GC']`（合格+让步+降级） |
| useflg | 硬编码 `'1'` | 保持不变 |

**理由**：
- 旧机只要可用也可租赁或临时给客户使用 → `asset_type` 默认包含 `02`
- 确保是合格可用的 → `itemtyp` 默认包含 `GA/GB/GC`，排除 `BF`（报废）、`BH`（返修）、`DJ`（待检）、`QA`（质检中）
- `sflg='8'`（在库）是业务规则硬编码合理
- 仓库范围、`asset_type` 应参数化（不同业务场景不同偏好）

## 三、TWH11 与 TMM43_EID 联动关系

### 3.1 TWH11 不是单纯来料仓库

**澄清**：TWH11_DETAIL 不是"11 号仓库"，是仓库模块的第 11 张表——**全仓库库存余量表**。

```
TWH01_warehouse     → 仓库定义（01=新品库, 03=成品库, ...）
TWH11_detail        → 库存余量（全仓库，whcd 列区分哪个仓）
TWH12_detaildt      → 库存变动流水
TWH13_in            → 入库单头
TWH14_checkindt     → 入库明细（带 eid！）
TWH15_out           → 出库单头
TWH16_outdteid      → 出库明细（带 eid！）
```

**数据实证**：同一张 TWH11 表里有 41 个不同 whcd：

```
whcd=01 新品库     751件   ← 来料/配件
whcd=02 维护库     783件
whcd=03 成品库      82件   ← 生产组装后的整机！
whcd=04 生产配件库 621件   ← 生产线上的配件
whcd=05~33 工程师库 ...    ← 外借设备
```

### 3.2 整机如何进 TWH11

```
配件采购入库 (invtyp=1)
  → TWH11 whcd=04 (生产配件库) qty+N
  → TWH14 入库明细 (无 eid，是来料)

生产领料出库 (invtyp=8 生产出库)
  → TWH11 whcd=04 qty-N
  → TWH16 出库明细 (带 eid)
  → TMM43_EID.whcd = None (生产中 sflg=7)

成品入库审核 (invtyp=8)
  → TWH11 whcd=03 (成品库) qty+N    ← 整机进了成品库！
  → TWH14 入库明细 (带 eid)          ← 具体哪台设备
  → TMM43_EID.whcd = 03 (在库 sflg=8)
```

### 3.3 三表联动关系

```
入库单审核 (warehouse_service.py:513-549)
    │
    ├─① StockDetailRepository.update_balance()  → TWH11_DETAIL   qty+1
    ├─② StockDetailRepository.add_movement()    → TWH12_DETAILDT 写变动记录
    └─③ if detail.eid → 更新 TMM43_EID         → whcd/sflg/qcflg 同步

出库单审核 (warehouse_service.py:1160-1210)
    │
    ├─① StockDetailRepository.update_balance()  → TWH11_DETAIL   qty-1
    ├─② StockDetailRepository.add_movement()    → TWH12_DETAILDT 写变动记录
    └─③ if detail.eid → 更新 TMM43_EID         → whcd=None (离库)
```

**完整的成品设备信息**：

```
TWH11_DETAIL (库存余量)          TMM43_EID (设备身份)
┌──────────────────────┐        ┌──────────────────────────┐
│ whcd=03 (成品库)      │        │ eid=2013010801980         │
│ itemcd=4Q2006         │  ←→   │ itemcd=4Q2006             │
│ itemtyp=GA            │        │ whcd=03                   │
│ itemqty=5             │        │ asset_type=01 (新机)      │
└──────────────────────┘        │ sflg=8 (在库)             │
        ↑ 数量                  │ itemtyp=GA                │
        ↑                       └──────────────────────────┘
        ↑                               ↑ 身份
        ↑                               ↑
  "成品库有5台4Q2006"             "具体是哪5台、各自什么状态"
```

两者通过 `(itemcd, whcd)` 联动，但不是冗余——它们回答不同层次的问题：

| 维度 | TWH11 | TMM43_EID |
|------|-------|-----------|
| 粒度 | itemcd + whcd + itemtyp | 逐台 EID |
| 作用 | 库存余额、数量校验 | 设备身份、追溯、选择 |
| 查询 | "成品库有多少台？" | "成品库有哪些设备？" |

**结论**：预计划设备选择应该查 `TMM43_EID`，过滤 `whcd` 在成品库范围。`TWH11` 只告诉你数量够了，不告诉你可以选哪些具体设备。两个表都需要，但场景不同：

- `check_stock` → TWH11（还够不够？）
- `list_available_eids` → TMM43_EID（具体选哪台？）← 本次新增

## 四、已完成后端工作

### 4.1 新增 `PlanStockService.list_available_eids()`

**文件**：`app/services/plan_stock_service.py:89-187`

**功能**：查询机型可用设备列表（TMM43_EID 设备维度，供预计划设备选择）。

**签名**：

```python
@staticmethod
def list_available_eids(
    model_cd: str,              # 机型编码
    whtyp: str | None = "03",   # 仓库类型，默认成品库
    asset_types: list[str] | None = None,  # 默认 ['01','02','03'] 新机+旧机+翻新机
    itemtyp: list[str] | None = None,      # 默认 ['GA','GB','GC'] 合格+让步+降级
    page: int = 1,
    per_page: int = 50,
) -> dict[str, Any]
```

**返回字段**：

```json
{
  "model_cd": "4Q4007",
  "item_cd": "4Q4007",
  "total": 5,
  "items": [
    {
      "eid": "20171031D0194",
      "itemcd": "4Q4007",
      "whcd": "03",
      "whnm": "成品库",
      "asset_type": "01",
      "asset_type_nm": "新机",
      "itemtyp": "GC",
      "itemtyp_nm": "降级品",
      "sflg": "8",
      "qcflg": "GC"
    }
  ]
}
```

**固定过滤**（业务规则硬编码合理）：
- `useflg='1'`（有效记录）
- `sflg='8'`（在库状态）

**参数化过滤**（不同场景可调整）：
- `whtyp` 仓库类型（默认成品库 03）
- `asset_types` 资产类型（默认新机+旧机+翻新机）
- `itemtyp` 物料类型（默认合格+让步+降级，排除报废/返修/待检/质检中）

**字典查询**：
- `AT` 字典（资产类型名称）：`tmm31_syscodes.code_typ='AT'`
- `QC` 字典（物料类型名称）：`tmm31_syscodes.code_typ='QC'`

### 4.2 新增 API 端点

**文件**：`app/api/sales.py:100-132`

**端点**：

```
GET /api/v1/plans/available-eids
  ?model_cd=4Q4007
  &whtyp=03              (可选，默认 03 成品库；空=不限)
  &asset_types=01,02,03  (可选，默认 01+02+03；空=不限)
  &itemtyp=GA,GB,GC      (可选，默认 GA+GB+GC；空=不限)
  &page=1&per_page=50
```

**返回**：同 4.1 的返回结构，包裹在统一响应格式 `{code, message, data}` 中。

### 4.3 数据验证

**4Q4007 成品库查询结果**（默认参数）：

```
5 台设备，全部 asset_type=01（新机）、itemtyp=GC（降级品）
```

| eid | itemcd | whcd | whnm | asset_type | itemtyp | sflg |
|-----|--------|------|------|------------|---------|------|
| 20171031D0194 | 4Q4007 | 03 | 成品库 | 01 | GC | 8 |
| 20171122D0232 | 4Q4007 | 03 | 成品库 | 01 | GC | 8 |
| 20180104D0387 | 4Q4007 | 03 | 成品库 | 01 | GC | 8 |
| 20180108D0426 | 4Q4007 | 03 | 成品库 | 01 | GC | 8 |
| 20180108D0437 | 4Q4007 | 03 | 成品库 | 01 | GC | 8 |

**编译验证**：`uv run python -m py_compile app/services/plan_stock_service.py app/api/sales.py` 通过。

> ⚠️ **数据验证说明（评审问题 5）**：当前 4Q4007 成品库只有 5 台设备且全部是 GC（降级品），样本单一。建议补充以下测试：
> - 查询其他机型（如 4Q2006）确认不同机型的设备分布
> - 查询其他仓库类型（`whtyp='01'` 原材料库、`'02'` 半成品库）确认仓库过滤生效
> - 当前测试样本不足以验证 `asset_types` 多值过滤的完整性
>
> ❌ **不建议**：不加 `itemtyp` 过滤查询。`itemtyp` 值域包含 `BF=报废`、`BH=返修`、`TH=退换`、`DJ=待检`、`QA=质检中`，不加过滤会把不合格需要报废/返修的成品也算入可选范围，违反业务规则。默认 `['GA','GB','GC']`（合格+让步+降级）是正确口径，测试时应保持这个过滤，只是需要验证多值过滤在数据库有 GA/GB 设备时能正确返回。

### 4.4 P0-P4 已完成工作汇总（2026-07-01 更新）

| 阶段 | 内容 | 代码位置 | 状态 |
|------|------|---------|------|
| **P0** | `implement()` 状态码 `02`→`04`（分派中→实施中），对齐 PB `usp_plan_imple` | `app/services/sales_service.py:574` | ✅ 已完成 |
| **P1** | `is_outflag` 注释对齐"是否已发计划" | `app/models/sales.py` | ✅ 已完成 |
| **P2** | `create_outbound()` 支持 `eids` 参数，写 `StockOutDetailEid` 明细 | `app/services/sales_service.py:835` | ✅ 已完成 |
| **P3** | MO 关单写 `tmm43_eid_track` type='C'（客户分配） | `app/services/itsm_service.py:225-296` `_write_eid_track_on_close()` | ✅ 已完成 |
| **P4** | MO 关单写 `tmm35_cust_pos_rl`（设备绑定到门店）+ 回写 `plan_status='01'` | `app/services/itsm_service.py:297-378` `_link_equipment_to_store()` + `_write_back_plan_status()` | ✅ 已完成 |
| **P5** | `complete()` 写 `tmm43_eid_track` type='u'（状态变更） | `app/services/sales_service.py:619-664` `_write_eid_track_on_complete()` | ✅ 已完成 |
| **基础设施** | `SystemRepository.create_eid_track()` 封装写入逻辑 | `app/repositories/system_repository.py:1134-1190` | ✅ 已完成 |
| **EID 创建联动** | EID 创建时写入 `itemtyp=qcflg`（资产类型与质检结果同步） | `app/api/inventory.py:321,380` + `app/services/qc_service.py:247` | ✅ 已完成 |
| **P6 字段扩展** | `EidTrack.refid`/`n_refid` 从 `varchar(8)` 扩展为 `varchar(20)`，容纳 10 位 `planno` | `app/models/master.py:446,453` + 迁移 `b181717d589f` | ✅ 已完成 |
| **P7 出库字段修正** | `create_outbound` 构造 `details_eid` 字段名 `qty`→`outqty`，对齐 `StockOutDetailEid` 模型 | `app/services/sales_service.py:898` | ✅ 已完成 |
| **ETK 码表** | `tmm31_syscodes` 插入 C/R/T/A 四条码（C=客户分配/R=回收/T=客户转移/A=属性变更） | 数据库 `tmm31_syscodes` `code_typ='ETK'` | ✅ 已存在 |
| **E2E 测试** | P0-P5 全链路联调测试（路径 A: MO 关单 / 路径 B: complete） | `tests/test_sales_api.py::TestPlanEndToEnd` | ✅ 已完成 |
| **11a 事件监听** | SQLAlchemy `after_insert/after_update/after_delete` 监听 `Eid` 模型，自动写 `tmm43_eid_track` type='i/u/d'（对齐 PB `TRIG_I/U/D_TMM43_TRACK`） | `app/extensions/eid_listeners.py` + `app/__init__.py:48` | ✅ 已完成 |
| **11b BG 子类型** | plantyp=10 DeviceChangeService BG 子类型关单写 type='T'（客户转移）+ rl 转移（旧失效/新建）+ 回写 plan_status='01'；CK/BQ 只回写 | `app/services/itsm_service.py:488-628` | ✅ 已完成 |

**说明**：
- P0-P5 命名沿用行动项表格的编号，对应关系见 §8 行动项表格
- P3/P4/P5 的写入逻辑仅覆盖 `MaintenanceOpenService`（plantyp=00），其他 plantyp 待补齐（见行动项 11）
- `EidTrack` 模型已扩展 12 个资产追踪字段（`install_date`/`n_install_date`/`cust_cd`/`n_cust_cd`/`asset_type`/`n_asset_type`/`recyclable`/`n_recyclable`/`recycle_status`/`n_recycle_status`/`asset_owner`/`n_asset_owner`），见 `app/models/master.py:468-479`

## 五、前端工作（已完成）

### 5.1 PlanList.vue 改造（已完成）

**文件**：`frontend/src/views/sales/PlanList.vue`

**已改造点**：

1. **商用仓库场景加"对应设备"下拉**（方案 A 预绑定，已完成）
   - 在 `pos_from=00` 且 `plantyp in ('00','20')` 时，选机型后显示"对应设备"可选下拉
   - 调用 `/sales/plans/available-eids?model_cd=xxx` 加载设备列表
   - 下拉显示 `eid + whnm + asset_type_nm + itemtyp_nm`
   - 选中后写入 `form.posid`，不选则方案 B 发货时绑定
   - `onModelSelect` 选机型后自动加载可用 EID 并清空已选 `posid`

2. **旧设备下拉显示 asset_type 名称**（已完成）
   - `mainAssets` 加载时带 `asset_type` 字段
   - 下拉 `label` 改为 `mainAssetLabel(eid)`：`eid（资产类型名称）`
   - 使用 `useDict('AT')` 的 `atLabel` 渲染

3. **方案 B 出库 EID 选择对话框**（已完成）
   - `doOutbound` 在 `posid` 未选时弹出 EID 选择对话框
   - 仓库人勾选要出库的设备 EID，调 `createOutbound(planno, whcd, eids)` 传 EID 列表
   - 后端 `create_outbound` 根据 `eids` 构造 `StockOutDetailEid` 明细

4. **机型下拉库存数字来源**
   - 当前 `modelOptions` 的 `stock_qty` 仍来自 `get_pos_models`（查 TWH11）
   - 方案 A 对应设备下拉已显示具体可用 EID 列表，可视为 TMM43_EID 维度的补充

### 5.2 销售出库页（方案 B，已完成）

**文件**：`frontend/src/views/sales/PlanList.vue` 的 `doOutbound` 流程

- 方案 B 的 EID 选择集成在预计划页的出库操作中，未单独改 `StockOutList.vue`
- `api/sales.ts` 的 `createOutbound` 新增 `eids` 参数

### 5.3 安装单页改造（已完成）

**文件**：`frontend/src/views/itsm/MaintenanceOpenList.vue`

- 列表加门店、主设备EID列
- 详情对话框 `@open` 时调 `fetchMaintenanceOpenDetail` 加载单条
- 详情中加 equipments 子表（TIT14_EQUIPMENT_OPEN）：设备 EID/送货单号/是否完成/是否换机/换机EID/来源磁卡号/来源POS
- 后端 `MaintenanceOpenService.get` 已附带 `equipments` 子表数据

## 六、EID 绑定模式讨论

### 6.1 你的场景本质

**批量开通场景**：一批门店要装设备，设备从成品库批量出库→装车→按路线配送→到店安装。

如果预计划阶段就绑定 EID，意味着还没发货就知道"这台设备去哪个店"。

### 6.2 两种模式对比

| 维度 | A. 预计划绑定 EID | B. 预计划只定机型，发货时才绑 EID |
|------|------------------|-------------------------------|
| 绑定时机 | 预计划创建时 | 销售出库/发货时 |
| 门店-设备关系 | 提前确定 | 发货现场确定 |
| 货运装载 | 必须按门店清单装车 | 按机型混装，到现场再分配 |
| 临时调换 | 要改预计划 | 现场直接换，系统自动绑 |
| 安装效率 | 到店直接装（已知道是哪台） | 到店扫码绑 EID 再装 |
| 系统自动化 | 出库单自动生成、自动触发安装单 | 出库时才生成绑定关系 |
| 错发风险 | 装错车就麻烦 | 现场扫码绑定，错发当场发现 |
| 库存占用 | 绑定后 EID 被占用 | 只锁机型数量，EID 不占用 |

### 6.3 行业做法

**1. 通信/POS 机行业（你的场景）**：普遍采用 **B 模式（发货时绑定）**

原因：
- 设备同质化高（4Q4007 都是同样的机器，EID 只是序列号）
- 批量配送，司机按路线送货，不可能为每台设备单独标"这是哪家店的"
- 到店后工程师扫码激活，系统此时才建立 EID↔门店绑定
- 例外：**大客户专机**（如某连锁指定设备批次）才用 A 模式

**2. 医疗设备/大型工业设备**：用 **A 模式（预绑定）**

原因：
- 设备单价高、定制化强
- 一台一订单，不存在批量混装问题
- 发货前要验收，EID 提前确定便于追踪

**3. 手机/消费电子**：**B 模式**，但渠道商有"预分配池"

- 仓库里 1000 台手机不绑门店
- 发货时从池子里取，扫码绑订单
- 系统只锁"可用池数量"，不锁具体 EID

### 6.4 推荐方案：B 模式 + 可选 A 模式

**默认 B 模式**（推荐）：
- 预计划只选机型 + 数量
- 库存校验用 `check_stock`（TWH11 数量维度）
- 锁定"机型可用数量"，不锁具体 EID
- 销售出库时才选 EID（调用 `list_available_eids`），扫码绑定
- 安装单自动从出库单的 EID 明细生成

**A 模式作为可选**（大客户专机场景）：
- 预计划可选"指定设备"（调 `list_available_eids` 选 EID）
- 绑定后 EID 状态改为"已预占"（新增 sflg 值或用 refid 关联预计划号）
- 其他计划不能再选这台
- 适合：某客户指定要某批次、某 EID 段的设备

### 6.5 技术实现差异

```
B 模式（默认）:
  预计划 → pos_item=机型, pos_qty=N, posid=null
  库存校验 → check_stock(机型) → TWH11 数量
  销售出库 → 选 N 台 EID → 写 TWH16 出库明细 → 绑定

A 模式（可选）:
  预计划 → pos_item=机型, posid=EID1 (指定设备)
  库存校验 → list_available_eids(机型) → TMM43_EID 具体设备
  销售出库 → 自动带出已绑 EID → 直接出库
```

### 6.6 方案 A/B 完整链路设计（2026-06-30 补充）

**用户需求确认**：商用仓库对应计划机型支持方案 A 和方案 B，两种方案的出库单创建方式和设备绑定时机不同。

#### 方案 A：预绑定 EID（大客户专机场景）

```
预计划创建
  ├─ 选机型 + 选具体 EID（调 list_available_eids）
  ├─ posid = EID1（预绑定）
  └─ EID 状态改为"已预占"（sflg 或 refid 关联预计划号）
    ↓
implement() 实施确认
  ├─ 生成 ITSM 单据（device_id = posid = EID1）
  └─ 自动创建销售出库单 OV=1（refbillid = planno，明细带 EID1）
    ↓
仓库审核出库
  ├─ 出库单已有 EID1 明细，直接审核
  └─ EID 状态：sflg='8'（在库）→ whcd=None（离库）
    ↓
ITSM 单据关单（安装完成）
  ├─ 写 tmm35_cust_pos_rl（设备绑定到门店，cust_cd + eid + posupddate）
  ├─ 写 tmm43_eid_track type='C'（客户分配，refid=planno）
  └─ 出库单的 refbillid 已是 planno，无需回写
```

**方案 A 特点**：
- 预计划阶段就锁定具体 EID，其他计划不能选这台
- `implement()` 自动创建出库单，不需要人工创建
- 出库单创建时 `refbillid=planno` 已关联预计划号
- 出库单明细 `StockOutDetailEid` 已带 EID1

#### 方案 B：发货时绑定（默认场景，批量配送）

```
预计划创建
  ├─ 选机型 + 数量（不选具体 EID）
  └─ posid = null，只锁"机型可用数量"（TWH11 数量维度）
    ↓
implement() 实施确认
  ├─ 生成 ITSM 单据（device_id = null，安装时才绑）
  └─ ❌ 不自动创建出库单（需要人工创建）
    ↓
仓库人工创建销售出库单 OV=1
  ├─ 仓库实施部领机时调 create_outbound()
  ├─ 出库单 refbillid = planno（关联预计划号）
  ├─ 仓库人选 N 台 EID（调 list_available_eids 扫码绑定）
  └─ 写 StockOutDetailEid（出库明细带 EID）
    ↓
仓库审核出库
  ├─ 扣库存 + EID 状态：sflg='8'（在库）→ whcd=None（离库）
  └─ 出库单 refbillid 已是 planno
    ↓
ITSM 单据关单（安装完成）
  ├─ 从出库单明细取 EID → 写 tmm35_cust_pos_rl（设备绑定到门店）
  ├─ 写 tmm43_eid_track type='C'（客户分配，refid=planno）
  └─ 出库单的 refbillid 已是 planno，无需回写
```

**方案 B 特点**：
- 预计划阶段不锁具体 EID，只锁机型数量
- `implement()` 不自动创建出库单，由仓库人工创建
- 仓库人创建出库单时扫码选 EID，这是真正建立 EID↔门店关系的地方
- 出库单创建时 `refbillid=planno` 已关联预计划号

#### 关键澄清：出库单的预计划号不需要回写

**用户问**："等实施单据完成后对应设备也就绑定到门店并关联这个预计划号对应回写销售出库单据里的预计划号?"

**答**：不需要回写。**出库单在创建时就已经带预计划号**：
- 方案 A：`implement()` 自动创建出库单时，`refbillid=planno`（`sales_service.py:830`）
- 方案 B：仓库人工调 `create_outbound()` 创建出库单时，`refbillid=planno`（`sales_service.py:830`）

**实施单据完成后真正发生的是**：
1. **设备绑定到门店**——写 `tmm35_cust_pos_rl`（cust_cd + eid + posupddate），这是新数据，不是回写出库单
2. **设备变更轨迹**——写 `tmm43_eid_track` type='C'（refid=planno），记录"这台设备在什么时候分配给了哪个客户"
3. **出库单本身不需要回写**——它的 `refbillid` 从创建时就是 `planno`，一直是关联的

#### 当前代码的缺口（方案 A/B 都需要补）

| 缺口 | 方案 A | 方案 B | 当前代码 |
|------|--------|--------|----------|
| 预计划选 EID（posid） | ✅ 需要 | ❌ 不需要 | `posid` 字段已有，`list_available_eids` API 已有 |
| EID 预占状态 | ✅ 需要 | ❌ 不需要 | ❌ 缺失（无 sflg 预占值或 refid 关联） |
| `implement()` 自动创建出库单 | ✅ 需要 | ❌ 不需要 | ❌ 缺失（当前 `implement()` 不创建出库单） |
| 人工 `create_outbound()` | ❌ 不需要 | ✅ 需要 | ✅ 已有（`sales_service.py:784`） |
| 出库单明细带 EID | ✅ 自动带 | ✅ 仓库人选 | ✅ 已完成（P2：`create_outbound` 传 `eids` 写 `StockOutDetailEid`） |
| 出库审核更新 EID 状态 | ✅ 需要 | ✅ 需要 | ✅ 已有（`warehouse_service.py` audit 逻辑） |
| ITSM 单据关单写 `tmm35_cust_pos_rl` | ✅ 需要 | ✅ 需要 | ✅ 已完成（P4：`itsm_service.py:297-378` `_link_equipment_to_store`，仅 plantyp=00） |
| ITSM 单据关单写 `tmm43_eid_track` type='C' | ✅ 需要 | ✅ 需要 | ✅ 已完成（P3：`itsm_service.py:225-296` `_write_eid_track_on_close`，仅 plantyp=00） |

**结论**：
- 方案 A 和方案 B 的分歧点只在"出库单创建方式"和"EID 绑定时机"
- 两种方案最终都需要在 ITSM 单据关单时写 `tmm35_cust_pos_rl`（设备绑定到门店）和 `tmm43_eid_track` type='C'——✅ 已完成（仅 plantyp=00，其他 plantyp 见行动项 11）
- **当前剩余缺口**：EID 预占状态、`implement()` 自动创建出库单（均为方案 A 专属，方案 B 不需要）

## 七、销售实施全链路现状分析

### 7.1 PB 源码实际状态流转（权威基线）

**PB 源码位置**：`PBsrc/sale.pbl/u_plan_befor.sru`（预计划前置）、`u_plan_imple.sru`（实施安排）、`u_serve_imple.sru`（话务实施）

**⚠️ 关键发现：`plan_cust` 表有两个状态字段，PB 代码混用**

PB 代码中 `plan_status` 和 `status` 是两个独立字段，但不同按钮检查的字段不同，导致状态码含义混乱：

| 字段 | 用途 | 值域（从代码推断） |
|------|------|-------------------|
| `status` | 主状态（整体流转） | 00/02/04/03/05/09 |
| `plan_status` | 计划状态（呼出/实施安排） | 00/01/03/04/05 |
| `serve_status` | 呼出状态 | 01=呼出中, 02=呼出完成 |

**状态码定义**（PB 代码两处注释存在矛盾，以按钮逻辑为准）：

| 状态码 | `status` 字段含义 | `plan_status` 字段含义 | 来源 |
|--------|-------------------|------------------------|------|
| 00 | 计划中 | 计划中 | 创建初始值 |
| 01 | 计划完成 | 呼出中 | `u_plan_befor:488` 检查 `plan_status='01'` → "还在呼出中" |
| 02 | 实施中 | - | `u_plan_befor:535` 计划确认按钮 `status='02'` |
| 03 | 实施完成 | 实施安排中 | `u_plan_imple:1750` 检查 `status='03'` → "实施已完成"；`u_plan_befor:494` 检查 `plan_status='03'` → "已在实施安排中" |
| 04 | 分派中/实施中 | 实施完成 | `u_plan_imple:491` 实施确认 `status='04'`；`u_plan_befor:500` 检查 `plan_status='04'` → "已实施完成" |
| 05 | 配置已确认 | 配置已确认 | `u_plan_imple:460` 检查 `status='05'`；`u_plan_befor:506` 检查 `plan_status='05'` |
| 08 | 计划退回 | - | `u_plan_imple:550` 计划退回 `status='00'` |
| 09 | 计划作废 | - | `u_plan_befor:689` 计划作废 `status='09'` |

**实际流转**（从按钮逻辑推断，以 `status` 字段为主）：

```
00 计划中 (创建，status='00')
  ↓ 请求呼出 (u_plan_befor.oe_dobutton3)
  ↓ 生成 PLAN_SERVE 呼出单，serve_status='01'
01 呼出中 (serve_status='01')
  ↓ 呼出完成 (serve_status='02')
  ↓ 计划确认 (u_plan_befor.oe_dobutton1)  ← status='02'
02 实施中 (status='02')
  ↓ 同步时间 (u_plan_imple 同步按钮)  ← 前置 status='02'，只写 send_date/train_date/imple_date，不改 status
  ↓ 实施确认 (u_plan_imple.oe_dobutton1)  ← status='04'，调 USP_PLAN_IMPLE 生成 ITSM 单据
04 分派中/实施中 (status='04')
  ↓ 04→03 转换机制不明（可能由 USP_PLAN_IMPLE 存储过程内部完成，源码未导出）
03 实施完成 (status='03')
  ↓ 配置确认
05 配置已确认 (status='05')
```

> ⚠️ **同步按钮的真实逻辑**（`u_plan_imple.sru:1735-1761` 实测）：
> - 拒绝 `status='09'`（已作废）
> - 拒绝 `status='01'`（计划已完成）
> - 拒绝 `status='04'`（在实施中）
> - 拒绝 `status='03'`（实施已完成）
> - **唯一可执行同步的状态是 `status='02'`（实施中）**
> - 同步只写 `send_date/train_date/imple_date` 三个日期字段，**不改 `status`**

**关键字段**（`d_plan_imple_list.srd:117-126`）：

| 字段 | 列标题 | 含义 |
|------|--------|------|
| `imple_date` | 实施日期 | 实施完成日期 |
| `send_date` | 送机时间 | 设备送达门店时间 |
| `train_date` | 培训时间 | 客户培训时间 |
| `imple_result` | 实施结果 | `00=成功, 01=失败` |
| `is_outflag` | 是否已发计划 | 是否已发送给实施部门（非"是否已出库"） |

**关键结论**：
1. **PB 代码有 `status` 和 `plan_status` 两个字段，含义不同且混用**——这是 PB 代码的固有混乱，重构时必须统一
2. **实施完成是 `status='03'`，不是 `04`**——`04` 是"分派中/实施中"（生成 ITSM 单据后）
3. **"同步时间"按钮只设置日期，不改 `status`**——前置条件是 `status='02'`（实施中），`status='04'` 时会被拒绝；`status` 从 `04` 到 `03` 的转换机制不明，可能由 `USP_PLAN_IMPLE` 存储过程内部完成（源码未导出）
4. **`is_outflag` = "是否已发计划"**，不是"是否已出库"
5. **PB 没有"领货单"概念**——销售出库 OV=1 在 `wh.pbl` 里是独立录入界面，不与预计划直接关联

### 7.1.1 PB 三步流转 vs 重构两步合并（关键差异）

**PB 代码的实际业务流程**（从 `tmm43_eid_track` 时序约定推断，见 `docs/core/客户主数据字段规范.md:299-304`）：

```
02 实施中 (status='02')
  ↓ 同步时间 (u_plan_imple 同步按钮，前置 status='02')
  ↓ 只写 send_date/train_date/imple_date，不改 status
  ↓ 实施确认 (u_plan_imple.oe_dobutton1)  ← status='04'，调 USP_PLAN_IMPLE 生成 ITSM 单据
04 分派中/实施中 (status='04')
  ↓ 04→03 转换机制不明（可能由 USP_PLAN_IMPLE 存储过程内部完成，源码未导出）
03 实施完成 (status='03')
  ↓ 写 tmm43_eid_track type='C'（客户分配），refid=planno，change_date=imple_date
  ↓ 配置尚未生效，需要配置人员在系统里进行"数据接收(业务回馈)"
05 配置已确认 (status='05'，配置人员执行"数据接收/业务回馈"功能)
  ↓ 写 tmm43_eid_track type='u'（状态变更），refid=出库单号，change_date=确认时间
  ↓ 配置在门店生效
01 计划完成 (status='01'，配置生效，门店可用)
```

> ⚠️ **PB 流程的顺序说明**：
> - 同步按钮在 `status='02'`（实施中）时执行，只写三个日期字段
> - 实施确认按钮在同步之后执行，设置 `status='04'` 并调 `USP_PLAN_IMPLE`
> - `04→03` 的转换机制不明，可能由 `USP_PLAN_IMPLE` 存储过程内部完成（源码未导出）
> - `03→05→01` 是配置确认的三步流转

**PB 代码的缺陷**：
- `03 实施完成` → `05 配置已确认` → `01 计划完成` 是三步人工流转
- 配置人员需要手动在系统里执行"数据接收(业务回馈)"功能
- PB 老系统人工后置确认导致 `tmm43_eid_track` 记录顺序颠倒（先写 u 后写 C）

**重构版本的优化**（`sales_service.py:587-619` `complete()` 方法）：

```
04 实施中（ITSM 单据关单）
  ↓ complete() 自动完成配置生效
01 计划完成（配置生效 + 门店可用）
```

**重构版本合并了 PB 的 `05 配置已确认` 和 `01 计划完成` 为一步**，理由：
1. PB 代码的"配置确认"步骤本质是人工后置确认，导致 `tmm43_eid_track` 记录顺序颠倒
2. `docs/core/客户主数据字段规范.md:304` 明确规定"PB 老系统人工后置确认导致顺序颠倒，新系统不允许"
3. 重构版本通过 `complete()` 方法自动完成配置生效，消除了人工确认环节
4. ITSM 单据关单时自动写入 `tmm43_eid_track` type='C' 和 type='u'，保证时序正确

**结论：重构版本的"实施完成即计划完成"是合理优化**：
- ✅ 消除了 PB 的人工后置确认环节（配置人员不再需要手动执行"数据接收"）
- ✅ 保证了 `tmm43_eid_track` 记录时序正确（先 C 后 u）
- ✅ 状态码从 PB 的三步（03→05→01）简化为两步（04→01）
- ⚠️ 但需要注意：`complete()` 方法内部应该同时完成"配置生效"和"计划完成"两个动作，不能只改状态码

> ✅ **交叉引用（评审问题 3）已落地（2026-07-01 更新）**：`complete()` 的配置生效 + `tmm43_eid_track` 写入已完整落地——P5 补充了 type='u' 写入（`sales_service.py:619-664`）。plantyp=00 的 type='C' 由 `MaintenanceOpenService.transition(to_status='5')` 写入（P3）。

**`complete()` 方法应包含的动作**（对照 PB 三步）：
1. ✅ 状态码 `04` → `01`（计划完成）—— `sales_service.py:609`
2. ✅ 客户 PENDING → ACTIVE（配置生效）—— `sales_service.py:613`
3. ✅ 写 `tmm43_eid_track` type='u'（状态变更）—— `sales_service.py:619-664` `_write_eid_track_on_complete()`（P5 已完成）；type='C' 由 ITSM 关单时写入（P3 已完成）
4. ✅ 客户无效化联动（`_apply_cust_useflg_invalidation`）

**建议**：✅ 已完成。其他 plantyp 待补齐（见行动项 11）。

### 7.1.2 检查结果：`tmm43_eid_track` 写入逻辑（2026-07-01 更新，仅 plantyp=00 已落地）

**检查方法**：全项目搜索 `EidTrack` 模型的写入调用（`db.session.add(EidTrack(...))` / `EidTrack.create` / `INSERT INTO tmm43_eid_track`）

**检查结论**（2026-07-01 更新）：

| 位置 | 用途 | 是否写入 `tmm43_eid_track` |
|------|------|---------------------------|
| `app/services/sales_service.py:619-664` `complete()` `_write_eid_track_on_complete()` | 预计划完成 | ✅ 已写入 type='u'（P5） |
| `app/services/itsm_service.py:225-296` `MaintenanceOpenService.transition()` `_write_eid_track_on_close()` | 开通单关单 | ✅ 已写入 type='C'（P3） |
| `app/services/itsm_service.py` `MaintenanceRenovateService.transition()` | 翻新单关单 | ✅ 已写入 type='R'+'C'（11c） |
| `app/services/itsm_service.py` `DeviceChangeService.transition()` | 磁卡号变更单关单 | ✅ 已写入 type='T'（11b，仅 BG 子类型） |
| `app/services/itsm_service.py` `RecycleTaskService.transition()` | 回收任务关单 | ✅ 已写入 type='R'（11d） |
| `app/services/itsm_service.py` `StoreCloseService.transition()` | 门店关闭关单 | ✅ 已写入 type='R' 批量（11e） |
| `app/services/warehouse_service.py` `StockOutService.audit()` | 销售出库审核 | ❌ 未写入（EID 状态变更由审核逻辑直接 update `tmm43_eid`，重构版无触发器所以不写 i/u/d，见行动项 11a） |
| `app/services/system_service.py:642-649` | 仅查询 `EidTrack` 用于翻新匹配 | ❌ 只读不写 |
| `app/repositories/system_repository.py:1134-1190` `create_eid_track()` | 写入封装 | ✅ 写入工具方法（P3/P5 调用） |
| `app/repositories/report_repository.py:191-196` | 仅查询 EID 变更追溯 | ❌ 只读不写 |
| `scripts/scrap_orphan_devices.py:43` | 孤儿设备报废脚本 | ✅ 原生 SQL 写入（一次性脚本，非业务代码） |

**核心结论**（2026-07-01 更新）：

**业务代码已实现 `tmm43_eid_track` 写入，但仅覆盖 `MaintenanceOpenService`（plantyp=00 新机开通）**：
- ✅ `MaintenanceOpenService.transition(to_status='5')` 写 type='C'（客户分配）—— `itsm_service.py:225-296`
- ✅ `PlanCustService.complete()` 写 type='u'（状态变更）—— `sales_service.py:619-664`
- ✅ `SystemRepository.create_eid_track()` 封装写入逻辑—— `system_repository.py:1134-1190`
- ✅ 其他 plantyp（10/20/30/40）的 `transition()` 已写 type='T/R/C'（11b-e 完成）
- ✅ DB 操作层 i/u/d 已用 SQLAlchemy 事件监听补齐（11a 完成）

**历史结论已过时**：此前"业务代码完全没有写入 `tmm43_eid_track` 的逻辑"的结论（2026-06-30）已被 P3/P5 落地推翻。`scripts/scrap_orphan_devices.py` 不再是唯一写入点。

**影响**（2026-07-01 更新）：
1. **`docs/core/客户主数据字段规范.md:299-304` 规定的时序约定（先 C 后 u）**——plantyp=00 已落地，其他 plantyp 待补齐
2. **设备变更追溯能力**——plantyp=00 已具备，其他 plantyp 缺失
3. **翻新单匹配逻辑**——`system_service.py:642-649` 依赖 `EidTrack` type='C' 记录匹配翻新单，plantyp=00 关单后会写 C 记录，翻新单（plantyp=20）自身待补齐 type='R'+'C'
4. **EID 变更追溯报表数据**——plantyp=00 产生的变更可查，其他 plantyp 产生的变更查不到

**需要补充的写入点**（按 PB `tmm43_eid_track` 时序约定）：

| 业务节点 | 写入类型 | refid | change_date | 应写入位置 |
|---------|---------|-------|-------------|-----------|
| 预计划执行完成（ITSM 单据关单） | `C`（客户分配） | planno | imple_date | `itsm_service.py` 各 `transition()` to_status='5' 时 |
| 配置人员确认（重构版 `complete()`） | `u`（状态变更） | 出库单号 | 确认时间 | `sales_service.py:complete()` |

**建议改动**（2026-07-01 更新）：
1. ✅ `itsm_service.py` `MaintenanceOpenService.transition(to_status='5')` 已补充 `EidTrack` type='C' 写入（P3）
2. ✅ `sales_service.py:complete()` 已补充 `EidTrack` type='u' 写入（P5）
3. ✅ `SystemRepository.create_eid_track()` 已封装写入逻辑
4. ✅ 其他 plantyp（10/20/30/40）的 `transition()` 已补充 type='T/R/C' 写入（11b-e 完成）
5. ✅ DB 操作层 i/u/d 已用 SQLAlchemy 事件监听补齐（11a 完成）
6. 写入字段应包含：`type`/`change_date`/`itemcd`/`eid`/`opercd`/`sflg`/`refid`/`qcflg`/`whcd`/`n_sflg`/`n_refid`/`n_qcflg`/`n_whcd` 等变更前后状态

> ✅ **验证点（评审问题 4）已澄清（2026-07-01 从生产 Oracle 导出）**：
>
> **PB 系统的 `tmm43_eid_track` 写入机制**：
> - **完全由 `TMM43_EID` 表上的三个触发器自动写入**，不是存储过程显式写
>   - `TRIG_I_TMM43_TRACK`：INSERT 时写 type='i'（记录新值）
>   - `TRIG_U_TMM43_TRACK`：UPDATE 时写 type='u'（记录旧/新 sflg/refid/qcflg/whcd/prddate/itemtyp/new_old/remark/manuf_seq/old_degree）
>   - `TRIG_D_TMM43_TRACK`：DELETE 时写 type='d'（记录旧值）
> - **PB 系统的 type 字段只有 `i/u/d` 三种**，**没有 `C` 类型**
> - `usp_plan_imple` / `usp_trans_in_confrim` / `usp_plan_confrim` 都**不显式写 `tmm43_eid_track`**
> - 任何存储过程对 `tmm43_eid` 的 `update sflg='1'/'2'/'8'` 都会**间接触发**写 type='u' 记录
>
> **`tmm35_cust_pos_rl` 与 `plan_cust.status` 的写入机制**：
> - **`usp_plan_confrim`**（被 `usp_trans_in_confrim` 对所有 plantyp 调用）**显式处理**：
>   - plantyp='00'（新机开通）：L116-126 insert 新 rl；L145-174 按 POS_FROM 分支处理新旧客户 rl
>   - plantyp='10'（磁卡号变更，含 CK/BG/BQ 三子类型）：L221-243 update 旧 rl useflg=0 + insert/update 新 rl（仅 BG 设备变更子类型涉及 rl 转移）
>   - plantyp='20'（旧机翻新）：L301-356 insert/update rl；L403-405 旧机 rl useflg=0
>   - plantyp='30'/'GB'（门店关闭）：L414-438 只更新 tmm22，不处理 rl
>   - type='3'（维护单整机换）：L591-593 旧机 rl useflg=0
>   - **所有 plantyp**：L449 `update plan_cust set status='01'`（完成）；L462 `update plan_cust set status='09'`（拒绝）
> - `TRIG_U_PLAN_STATUS` 触发器只在 `plan_cust.status='01'` 时写 `PLAN_F_TIME` 审计表，不写其他内容
>
> **结论**：
> 1. **DB 操作层 i/u/d**：PB 由触发器自动写；重构版需用 SQLAlchemy `after_insert/after_update/after_delete` 事件监听 `Eid` 模型模拟
> 2. **业务语义层 C/R/T/A**：PB **没有**，是重构版优化（见 `docs/core/实施单资产同步开发规范.md`），解决 PB 的 T+1 延迟、人工审核、时间不一致问题
> 3. **`tmm35_cust_pos_rl` + `plan_cust.status` 回写**：PB 由 `usp_plan_confrim` 对所有 plantyp 处理；重构版需在各 plantyp service 关单时按分支逻辑实现

### 7.2 当前重构代码的流程

**文件**：`app/services/sales_service.py`、`app/services/warehouse_service.py`

```
预计划创建 (PlanCustService.create)
  plan_status='00'（计划中）  ← sales_service.py:394
    ↓
话务核实 (PlanServeService.create)  ← sales_service.py:887-890
  ❌ 不修改预计划 plan_status（预计划保持 '00'）
  只创建呼出单 PLAN_SERVE，PlanServe.status='00'（待呼出）
  呼出完成后 PlanServeService.transition → PlanServe.status='01'（已呼出）
  ← ⚠️ 与 PB 不符：PB 话务核实后 serve_status='01'（呼出中），预计划 status 不变
    ↓
分派实施 (PlanCustService.dispatch)
  plan_status='02'（分派中）  ← ⚠️ 与 PB 不符，PB 是 status='02' 实施中
    ↓
实施确认 (PlanCustService.implement)  ← sales_service.py:482-585
  按 plantyp 生成下游 ITSM 单据：
    - plantyp='00' → MaintenanceOpenService（TIT13 新机开通单）
    - plantyp='10' → DeviceChangeService（TIT16 磁卡号变更单，含 CK/BG/BQ 三子类型）
    - plantyp='20' → MaintenanceRenovateService（TIT15 翻新单）
    - plantyp='30' → RecycleTaskService（TIT20 回收单）
    - plantyp='40' → StoreCloseService（门店关闭单）
  plan_status='04'（实施中）  ← sales_service.py:574  ✅ P0 已修复（对齐 PB status='04' 分派中/实施中）
    ↓
生成销售出库草稿 (PlanCustService.create_outbound)  ← sales_service.py:784-846
  前置条件：plan_status='04'（实施中）  ← sales_service.py:800  ✅ P0 已修复（与 implement() 输出一致）
  创建 OV=1 销售出库草稿（refbillid=planno）
    ↓
仓库审核出库 (StockOutService.audit)  ← warehouse_service.py:1074-1413
  扣库存 + 更新 EID 状态（whcd=None 离库）
```

> ⚠️ **评审问题 2 验证结论**：§7.2 原文说"话务核实后 `plan_status='01'`（计划完成）"是**错误的**。代码验证（`sales_service.py:887-890`）显示 `PlanServeService.create()` 只创建呼出单记录，**不修改预计划的 `plan_status`**。预计划创建后 `plan_status` 保持 `'00'`，只有 `PlanServe.status`（呼出单自身状态）从 `'00'`→`'01'`。`plan_status='01'`（计划完成）只在 `complete()` 方法（`sales_service.py:609`）中设置。

### 7.3 当前流程与 PB 的差异（问题清单）

**问题 1：状态流转顺序与 PB 不符（含阻断性 Bug）**

| 步骤 | PB 实际 | 当前重构 | 差异 |
|------|---------|----------|------|
| 话务核实后 | `serve_status='01'`（呼出中），`status` 不变 | `plan_status` 保持 `'00'`，`PlanServe.status='01'` | 字段错（PB 改 serve_status 不改 status，重构改 PlanServe.status 不改 plan_status，行为一致但字段名不同） |
| 计划确认后 | `status='02'`（实施中） | `plan_status='02'`（分派中） | 含义错，02 是实施中不是分派中 |
| 实施确认后 | `status='04'`（分派中/实施中） | `plan_status='04'`（实施中） | ✅ P0 已修复，含义对齐 |
| 同步后 | `status='02'`（实施中），只写日期不改状态 | 无对应步骤 | 缺少"同步"步骤（前置 02，只写 send_date/train_date/imple_date） |
| 04→03 转换 | 机制不明（可能 USP_PLAN_IMPLE 内部完成） | 无对应机制 | 待确认 |
| 配置确认后 | `status='05'`（配置已确认） | 无对应步骤 | 缺少"配置确认"步骤 |

> ✅ **阻断性 Bug 已修复（P0，2026-07-01 确认）**：`implement()` 现在设置 `plan_status="04"`（`sales_service.py:574`），与 `complete()` 和 `create_outbound()` 的前置条件一致，链路已打通：
> - `implement()` 设置 `plan_status="04"`（`sales_service.py:574`）
> - `complete()` 要求 `plan_status="04"`（`sales_service.py:602-606`）✅ 通
> - `create_outbound()` 要求 `plan_status="04"`（`sales_service.py:800-804`）✅ 通
>
> 历史描述（已过时）：`implement()` 原设置 `plan_status="03"`，导致 `complete()`/`create_outbound()` 前置检查失败，需手动调 `transition(planno, "04")` 才能继续。P0 修复后此问题不再存在。

**问题 2：缺少"同步"步骤**

PB 代码 `u_plan_imple.sru:1735-1761` 有"同步时间"按钮：
- 前置条件：`status='02'`（实施中），`status='04'`/`'03'`/`'01'`/`'09'` 都会被拒绝
- 只设置 `send_date`（送机时间）、`train_date`（培训时间）、`imple_date`（实施日期）
- **不改 `status`**

当前重构代码没有这个步骤，`implement()` 直接从 `02` 跳到 `04`，跳过了同步（写日期）步骤。

**问题 3：`is_outflag` 含义误解**

当前重构代码 `create_outbound` 把 `is_outflag='1'` 当作"已出库"标志（`sales_service.py:839`）。

PB 代码里 `is_outflag` 是"是否已发计划"（`d_plan_imple_list.srd:126` 列标题），不是"是否已出库"。

**问题 4：领货单与销售出库的关系**

PB 代码：销售出库 OV=1 在 `wh.pbl/u_wh_saleout.sru` 是独立录入界面，`is_invtyp='8'`（实际是其他出库），不与预计划直接关联。

当前重构：`create_outbound` 直接创建 OV=1 销售出库草稿，`refbillid=planno` 关联预计划。

**差异分析**：PB 系统里预计划和销售出库是两个独立模块，通过人工关联；重构后改为系统自动关联，这是优化但需注意状态码要对齐。

**问题 5：安装单的 EID 绑定**

当前代码：`implement()` 生成 ITSM 单据时，`_build_downstream_payload` 传 `device_id=record.posid`，但 `posid` 在预计划阶段可能为空（B 模式）。

PB 代码：`USP_PLAN_IMPLE` 存储过程生成 ITSM 单据（源码未导出，逻辑不可见），但从 `of_agein_imple` 看，它会先检查是否已有实施单，不重复生成。

实际业务：安装时工程师从领货设备的 EID 中勾选并绑定给门店。

### 7.4 当前 ITSM 单据的设备字段

**TIT13 新机开通单**（`app/models/itsm.py:320-351`）：
- `device_id`：整机编号（EID）
- `equipments`：设备附表（TIT14），含 `device_id`、`delivery_id`（送货单号）

**TIT14 设备附表**（`app/models/itsm.py:354-369`）：
- `device_id`：整机 ID（EID）
- `delivery_id`：送货单号
- `is_finish`：是否完成
- `is_change`：是否换机
- `change_eid`：换机设备号

**现状**：模型已支持一台开通单关联多个设备（`equipments` 关系），但当前 `_build_downstream_payload` 只传了一个 `device_id`，没有传 `equipments` 列表。

### 7.5 状态码对齐方案（建议）

**建议采用 PB 的状态码定义**，保持与老系统一致，便于数据迁移和用户习惯：

| 状态码 | 含义 | 对应动作 | 当前重构动作 |
|--------|------|----------|------------|
| 00 | 计划中 | 创建 | `create` ✅ |
| 01 | 呼出中 | 请求呼出（生成 PLAN_SERVE） | `PlanServeService.create` |
| 02 | 实施中 | 计划确认（呼出完成后）+ 同步（写送机/培训日期） | 需新增"计划确认"+"同步"动作 |
| 04 | 分派中/实施中 | 实施确认（生成 ITSM 单据） | `implement` ← 需改状态码 |
| 03 | 实施完成 | 04→03 转换机制不明（可能由 USP_PLAN_IMPLE 内部完成） | 待确认 |
| 05 | 配置已确认 | 配置确认 | 需新增"配置确认"动作 |
| 08 | 计划退回 | 计划退回 | 需新增"计划退回"动作 |
| 09 | 计划作废 | 计划作废 | `void` ← 需改状态码 |

**改动点**（按 PB 源码修正）：
1. `implement()` 把 `plan_status='03'` 改为 `plan_status='04'`
2. 新增 `sync()` 方法：**前置 `plan_status='02'`，只写 `send_date/train_date/imple_date`，不改状态**（对齐 PB 同步按钮逻辑）
3. `04→03` 转换机制待确认：可能由 `USP_PLAN_IMPLE` 存储过程内部完成（源码未导出），重构版需在 `implement()` 内部或 ITSM 单据关单时处理
4. 新增 `confirm_config()` 方法，状态 `03`→`05`（配置确认）
5. 新增 `rollback()` 方法，状态回退到 `00`
6. `create_outbound` 前置条件改为 `plan_status='04'`（分派中）或 `03`（实施完成）
7. `is_outflag` 字段含义改回"是否已发计划"，出库标志用其他字段


### 7.6 方案对比：简化版 vs PB 对齐版

上节 §7.5 描述了"完全对齐 PB"的方案。但考虑到重构版已经做了简化，实际可选两条路线：

#### 方案 A：最小修复（推荐优先执行）

**思路**：保持重构版的简化流程，只修 Bug，不增加步骤。

| 状态码 | 含义 | 动作 |
|--------|------|------|
| 00 | 计划中 | `create()` |
| 02 | 分派中 | `transition(00→02)`，呼出完成 |
| 04 | 实施中 | `implement()` ← 从 03 改为 04 |
| 01 | 计划完成 | `complete()` 或 `transition(04→01)` |
| 09 | 计划作废 | `void()` |

**流转**：
```
00 计划中 → 02 分派中 → 04 实施中 → 01 计划完成
                   ↓
                   └──→ 同步(可选，只写日期，不改状态)
```

**只需改 1 行代码**：
```python
# sales_service.py:573
- record.plan_status = "03"
+ record.plan_status = "04"
```

> 💡 **隐性收益**：方案 A 修 `implement()→04` 后，`create_outbound()`（前置 `plan_status='04'`，`sales_service.py:800`）也通了——同一个 Bug 修复同时打通了 `complete()` 和 `create_outbound()` 两条下游链路。

| 维度 | 评价 |
|------|------|
| 改动量 | ⭐ 极小（1 行） |
| 风险 | ⭐ 低（不引入新状态） |
| PB 兼容 | ⚠️ 状态码含义不同（01=计划完成 vs PB 01=呼出中） |
| 用户体验 | ✅ 步骤少，操作简单 |
| 数据迁移 | ⚠️ PB 老数据 status='01' 呼出中 与新 01=完成 冲突 |

#### 方案 B：完全对齐 PB

**思路**：恢复 PB 的完整状态码和多步流转，保持与老系统一致。

> ⚠️ **状态码 01 的冲突说明**：PB 中 `status` 和 `plan_status` 是两个不同字段，`status='01'`=计划完成，`plan_status='01'`=呼出中。方案 B 如果继续用重构版的单字段 `plan_status`，01 就会出现两次（呼出中 vs 计划完成），语义冲突。**解决方案**：要么恢复双字段（`status` + `plan_status`），要么用不同码值区分（如呼出中用 `10`）。

| 状态码 | 含义 | 动作 |
|--------|------|------|
| 00 | 计划中 | `create()` |
| 01 | 呼出中（`plan_status` 字段） | `PlanServeService.create()` |
| 02 | 实施中 | 计划确认（呼出完成后）+ 同步 |
| 04 | 分派中 | `implement()`（生成 ITSM 单据） |
| 03 | 实施完成 | ITSM 单据关单回写 |
| 05 | 配置已确认 | `confirm_config()` |
| 01 | 计划完成（`status` 字段，与上 01 不同字段） | 配置生效后自动完成 |
| 08 | 计划退回 | `rollback()` |
| 09 | 计划作废 | `void()` |

**流转**（完整 PB 三步）：
```
00 计划中 → 01 呼出中 → 02 实施中 → 04 分派中 → 03 实施完成 → 05 配置确认 → 01 计划完成
                    ↑ 请求呼出    ↑ 计划确认   ↑ implement  ↑ ITSM关单   ↑ 配置确认
                                  ↑ 同步(可选，只写日期，不改status)
```
> 注：01 出现两次对应不同字段——`plan_status='01'`（呼出中）和 `status='01'`（计划完成），见上方冲突说明。

**改动量**：
- `implement()` 改设 `status='04'`
- 新增 `sync()`（前置 02，只写日期）
- 新增 `confirm_config()`（03→05）
- 新增 `rollback()`（任意→00）
- ITSM 各 `transition(to_status='5')` 回写预计划 04→03
- `complete()` 适配：05→01
- 前端状态标签对齐新码值

| 维度 | 评价 |
|------|------|
| 改动量 | ⚠️ 大（6+ 文件，多个新方法） |
| 风险 | ⚠️ 中（涉及 ITSM 回写链路） |
| PB 兼容 | ✅ 完全一致，数据迁移无冲突 |
| 用户体验 | ⚠️ 步骤多（呼出→确认→实施→同步→配置确认） |
| 维护成本 | ⚠️ 高（状态码多，流转复杂） |

#### 建议策略：A 先行 + B 按需

1. **立即执行方案 A**：修复 `implement()` 状态码 Bug，让 `complete()` 和 `create_outbound()` 可正常调用
2. **观察业务需求**：如果用户反馈需要"呼出中"、"配置确认"等中间状态，再按方案 B 扩展
3. **数据迁移时再评估**：如果 PB 老数据的状态码含义冲突严重（如 01 呼出中 vs 01 完成），届时升级到方案 B

| 对比维度 | 方案 A（推荐先执行） | 方案 B（按需扩展） |
|---------|-------------------|-------------------|
| 适用场景 | 当前重构版快速修复 | 长期与 PB 完全兼容 |
| 状态码数量 | 5 个 | 8 个 |
| 用户操作步骤 | 3 步 | 5 步 |
| 代码改动 | 1 行 | ~200 行 |
| 时间 | 5 分钟 | 1-2 天 |

### 7.7 应该怎么规划

> ⚠️ **评审问题 1 修正**：原 §7.7 阶段 2 混用了方案 A 和方案 B 的项，与 §7.6 "A 先行"建议不一致。现拆为两条路线，各自列出阶段规划。

#### 路线 A：最小修复（推荐先执行，对齐 §7.6 方案 A）

**阶段 A1：现状梳理（本次文档，已完成）**
- 澄清 TWH11 vs TMM43_EID 职责
- 落地 `list_available_eids` 后端 API
- 明确 EID 绑定模式（B 模式默认 + A 模式可选）
- 对齐 PB 状态码定义

**阶段 A2：阻断性 Bug 修复（立即，5 分钟）**
- `implement()` 状态从 `03` 改为 `04`（`sales_service.py:573`，1 行改动）
- 验证 `complete()` 和 `create_outbound()` 两条下游链路是否打通
- `is_outflag` 含义改回"是否已发计划"（可选，低优先级）

**阶段 A3：销售出库 EID 绑定**
- `PlanCustService.create_outbound` 创建 OV=1 时，支持传入 EID 列表
- 仓库审核出库时，TWH16 出库明细写 EID
- EID 状态更新：`sflg='8'`（在库）→ `whcd=None`（离库）

**阶段 A4：安装单从出库单生成**
- 销售出库审核通过后，自动生成或更新 ITSM 安装单
- 安装单的 `equipments` 列表从出库单的 EID 明细带出
- 工程师上门安装时，从 `equipments` 中勾选设备绑定给门店

**阶段 A5：安装完成回写 + 审计轨迹补齐**
- 安装单状态变为"完成"时，回写预计划 `plan_status='01'`（计划完成，方案 A 无 03 状态）
- EID 绑定关系写入 `tmm35_cust_pos_rl`（客户-设备关系表）
- `complete()` 方法补充 `tmm43_eid_track` type='C' + type='u' 写入（见 §7.1.2）

**阶段 A6：前端改造（已完成）**
- 预计划页面加"对应设备"可选绑定（A 模式）✅
- 销售出库页面加 EID 选择（B 模式）✅（集成在预计划页 `doOutbound` 流程）
- 安装单页面加设备勾选绑定 ✅（`MaintenanceOpenList.vue` 详情显示 equipments 子表）

#### 路线 B：完全对齐 PB（按需扩展，对齐 §7.6 方案 B）

> 仅在业务反馈需要"呼出中"、"配置确认"中间状态，或 PB 老数据迁移冲突严重时启动。

**阶段 B1：恢复双字段或区分码值**
- 解决 01 冲突：恢复 `status` + `plan_status` 双字段，或呼出中改用 `10` 等新码值
- 前端状态标签对齐新码值

**阶段 B2：多步状态流转**
- `implement()` 改设 `status='04'`
- 新增 `sync()`（前置 02，只写日期，不改状态）
- 确认 `04→03` 转换机制（查 USP_PLAN_IMPLE 存储过程或在 ITSM 单据关单时回写）
- 新增 `confirm_config()`（03→05）
- 新增 `rollback()`（任意→00）
- ITSM 各 `transition(to_status='5')` 回写预计划 04→03
- `complete()` 适配：05→01

**阶段 B3~B6**：同路线 A 的 A3~A6，但回写状态码改为 `03`（实施完成）而非 `01`

### 7.8 关键决策点

**决策 1：预计划是否支持 A 模式（预绑定 EID）？**
- 推荐：支持但可选，默认不绑
- 实现：`form.posid` 可选填，填了就是 A 模式，不填就是 B 模式

**决策 2：销售出库时是否强制绑 EID？**
- 推荐：是，这是真正建立 EID↔门店关系的地方
- 实现：出库明细必须选 EID（整机物料）

**决策 3：安装单的设备从哪里来？**
- 推荐：从销售出库单的 EID 明细自动带出
- 实现：出库审核通过后，自动同步到安装单的 `equipments` 列表

**决策 4：安装时是否允许换机？**
- 推荐：允许，通过 `is_change='1'` + `change_eid` 记录
- 实现：安装单页面支持"换机"操作，旧 EID 回库，新 EID 绑定

## 八、下一步行动项

| # | 任务 | 优先级 | 状态 | 负责人 |
|---|------|--------|------|--------|
| 1 | 后端 `list_available_eids` API | 高 | ✅ 已完成 | - |
| 2 | 状态码对齐 PB（implement 改 04，新增 sync/confirm_config/rollback） | 高 | ✅ 已完成（P0：implement→04） | - |
| 3 | `is_outflag` 含义改回"是否已发计划" | 高 | ✅ 已完成（P1：注释对齐） | - |
| 4 | 前端 PlanList.vue 商用仓库设备选择下拉 | 中 | ✅ 已完成（P5：方案 A 对应设备下拉） | - |
| 5 | 前端 PlanList.vue 旧设备下拉显示 asset_type 名称 | 中 | ✅ 已完成（P5：mainAssetLabel） | - |
| 6 | 销售出库 OV=1 支持 EID 列表传入 | 高 | ✅ 已完成（P2：create_outbound 传 eids） | - |
| 7 | 销售出库审核后自动同步 EID 到安装单 | 高 | ✅ 已完成（P2：出库单带 eids，安装单从明细取 EID） | - |
| 8 | 安装单设备勾选绑定 UI | 中 | ✅ 已完成（P5：equipments 子表显示） | - |
| 9 | 安装完成回写预计划状态 + EID 绑定关系 | 高 | ✅ 已完成（P3/P4：EidTrack+CustPosRl+回写） | - |
| 10 | 端到端测试验证 | 高 | ✅ 已完成（plantyp=00/20/30/40 全链路 E2E） | `tests/test_sales_api.py::TestPlanEndToEnd` |
| 11 | 其他 plantyp EidTrack/CustPosRl/回写补齐 | 中 | 📋 待规划 | - |

### 行动项 11 说明：其他 plantyp EidTrack/CustPosRl/回写补齐

**现状**：仅 `MaintenanceOpenService`（plantyp=00 新机开通）实现了关单时的三重奏：
- 写 `tmm43_eid_track` type='C'（设备分配轨迹）
- 写 `tmm35_cust_pos_rl`（设备绑定到门店）
- 回写预计划 `plan_status='01'`（计划完成）

#### 两层追踪体系（2026-07-01 澄清）

`tmm43_eid_track` 在重构版中承担**两层职责**，与 PB 有本质差异：

| 层级 | type 值 | 来源 | 目的 | PB 有无 | 重构版现状 |
|------|---------|------|------|---------|-----------|
| **DB 操作层** | `i/u/d` | PB 触发器自动写 / 重构版应用 SQLAlchemy 事件监听 | 记录 `tmm43_eid` 任何 INSERT/UPDATE/DELETE | ✅ PB 有（触发器） | ❌ 重构版缺失（无事件监听） |
| **业务语义层** | `C/R/T/A` | 服务层显式调用 | 记录业务事件（关单/回收/转移/属性变更） | ❌ PB 无 | ⚠️ 仅 plantyp=00 实现 type='C' |

**关键结论**：
- PB 的 `i/u/d` 由 `TRIG_I/U/D_TMM43_TRACK` 触发器自动写，**存储过程从不显式写 `tmm43_eid_track`**
- 重构版的 `C/R/T/A` 是**业务优化**（见 `docs/core/实施单资产同步开发规范.md`），解决 PB 的 T+1 延迟、人工审核、时间不一致问题
- **两层都需要**，不是二选一

#### 未覆盖的 plantyp

| Service | plantyp | EidTrack 'C' | CustPosRl | 回写计划 | 说明 |
|---------|---------|--------------|-----------|----------|------|
| MaintenanceOpenService | 00 | ✅ | ✅ | ✅ | 新机开通（已完成） |
| DeviceChangeService | 10 | ✅（仅 BG 子类型写 'T' 客户转移；CK/BQ 不涉及设备不写） | ✅（BG 子类型） | ✅ | 磁卡号变更（CK/BG/BQ 三子类型，11b 已完成） |
| MaintenanceRenovateService | 20 | ✅（旧机写 'R' 回收 + 新机写 'C' 分配） | ✅（旧机失效/新机新建） | ✅ | 旧机翻新（11c 已完成） |
| RecycleTaskService | 30 | ✅（写 'R' 回收） | ✅（失效） | ✅ | 设备取回（11d 已完成） |
| StoreCloseService | 40 | ✅（写 'R' 回收，批量） | ✅（全失效） | ✅ | 门店关门（11e 已完成） |

评估：合理的分阶段交付——plantyp=00 是最高频场景，其他类型按需扩展。

#### 补齐要点（按 plantyp 差异化 + 对照 PB `usp_plan_confrim` 分支）

**业务语义层 type 映射**（重构版优化，PB 无对应）：
- **plantyp=00（新机开通）**：type='C'（客户分配）—— ✅ 已实现
- **plantyp=10（磁卡号变更，含 CK/BG/BQ 三子类型）**：
  - CK=仅磁卡号变更（不涉及设备，不写 EidTrack）
  - BG=磁卡号+设备变更（写 type='T' 客户转移，A 客户→B 客户）—— 对照 `usp_plan_confrim` L221-243
  - BQ=信息变更（不涉及设备，不写 EidTrack）
  - 详见 `docs/myitsm/客户状态与磁卡号变更优化设计.md`
- **plantyp=20（旧机翻新）**：旧机 type='R'（回收）+ 新机 type='C'（分配）—— 对照 L301-356, L403-405
- **plantyp=30（设备取回）**：type='R'（回收）—— 对照 type='3' 分支 L591-593
- **plantyp=40（门店关门）**：type='R'（回收，批量）—— 对照 L414-438（PB 只更新 tmm22，重构版补充 rl 失效）

**DB 操作层 i/u/d 补齐**（PB 等价）：
- 在 `Eid` 模型上挂 SQLAlchemy `after_insert/after_update/after_delete` 事件监听
- 自动写 type='i/u/d' 记录，字段对照 `TRIG_I/U/D_TMM43_TRACK`：
  - `i`：`:new.itemcd/:new.eid/:new.opercd/:new.gendate/:new.useflg/:new.etyp/:new.sflg/:new.refid/:new.qcflg/:new.whcd/:new.prddate/:new.itemtyp/:new.new_old`
  - `u`：旧值 + 新值（`sflg/refid/qcflg/whcd/prddate/itemtyp/new_old/remark/manuf_seq/old_degree`）
  - `d`：`:old.*` 全旧值

**`tmm35_cust_pos_rl` + `plan_cust.status` 回写**（PB 等价）：
- 所有 plantyp 关单回写 `plan_cust.status='01'`，拒绝回写 `'09'`
- rl 处理按 `usp_plan_confrim` 各 plantyp 分支逻辑实现

#### 待办清单

| # | 任务 | 优先级 | PB 等价/优化 | 状态 |
|---|------|--------|-------------|------|
| 11a | SQLAlchemy 事件监听 `Eid` 模型写 i/u/d | 高 | PB 等价 | ✅ 已完成（2026-07-01） |
| 11b | plantyp=10 DeviceChangeService（磁卡号变更 BG 子类型）写 type='T' + rl 转移 + 回写；CK/BQ 子类型只回写计划 | 中 | 优化 + PB 等价 | ✅ 已完成（2026-07-01） |
| 11c | plantyp=20 MaintenanceRenovateService 写 type='R'+'C' + rl 旧机失效/新机新建 + 回写 | 中 | 优化 + PB 等价 | ✅ 已完成（2026-07-01） |
| 11d | plantyp=30 RecycleTaskService 写 type='R' + rl 失效 + 回写 | 中 | 优化 + PB 等价 | ✅ 已完成（2026-07-01） |
| 11e | plantyp=40 StoreCloseService 写 type='R' 批量 + rl 全失效 + 回写 | 中 | 优化 + PB 等价 | ✅ 已完成（2026-07-01） |
| 11f | 资产编辑接口写 type='A'（属性变更） | 低 | 纯优化 | ✅ 已完成（2026-07-02） |
| 11g | 验证 ETK 码表（C/R/T/A 四条码是否已插入 `tmm31_syscodes`） | 低 | 纯优化 | ✅ 已完成（2026-07-01 确认） |

#### 建议执行顺序（2026-07-01 新增）

**关键依赖**：11a（i/u/d 事件监听）应先于 11b-e，因为 11b-e 写完业务语义层 C/R/T 后，对应的 `tmm43_eid` update 也会自动触发 i/u/d 记录——若 11a 先做好，11b-e 只需写业务语义层，DB 操作层自动覆盖。

**第一批：验证 + 基础设施**（建议本周完成）
1. **10** 端到端测试验证（验证 P0-P5 全链路能跑通：预计划→出库→关单→EidTrack/CustPosRl/回写）
2. **11g** ETK 码表验证（5 分钟，快速确认 C/R/T/A 四条码是否在 `tmm31_syscodes`）
3. **11a** SQLAlchemy 事件监听 `Eid` 模型写 i/u/d（基础设施，其他 plantyp 依赖）

**第二批：plantyp 补齐**（可并行，建议下周）
4. **11b** plantyp=10 磁卡号变更 BG 子类型（type='T' + rl 转移 + 回写）
5. **11c** plantyp=20 旧机翻新（旧机 type='R' + 新机 type='C' + rl 旧机失效/新机新建 + 回写）
6. **11d** plantyp=30 设备取回（type='R' + rl 失效 + 回写）
7. **11e** plantyp=40 门店关门（type='R' 批量 + rl 全失效 + 回写）

**第三批：扩展**（按需）
8. **11f** 资产编辑接口写 type='A'（属性变更，纯优化）
9. 方案 A 专属：EID 预占状态、`implement()` 自动创建出库单（如需要）

**优先级理由**：
- 11a 是基础设施，11b-e 都依赖它自动写 i/u/d
- 10 是验证 P0-P5 是否真的能跑通，应在 11a 之前或之后立即做
- 11g 是快速确认，5 分钟即可完成，应最先做
- 11b-e 可以并行，按业务频率排序：plantyp=20（3432 条）> 30（1881 条）> 10（242 条）> 40（少量）

## 九、相关文档索引

- `docs/core/预计划机型联动与采购触发技术方案.md`：预计划库存校验与采购触发技术方案
- `docs/core/预计划机型联动优化验收文档.md`：预计划机型联动优化验收记录
- `docs/core/预计划表单与机型联动优化方案.md`：预计划表单与机型联动优化方案
- `docs/core/销售管理_技术实现文档.md`：销售管理技术实现文档
- `docs/core/销售管理_预计划_实施计划.md`：销售管理预计划实施计划
- `docs/core/仓库模块操作手册.md`：仓库模块操作手册
- `docs/core/MES_QC_Warehouse_业务流程与技术实现_v2.md`：MES/QC/仓库业务流程
- `docs/core/实施单资产同步开发规范.md`：实施单资产同步开发规范
- `docs/myitsm/客户状态与磁卡号变更优化设计.md`：客户状态与磁卡号变更优化设计（plantyp=10 三子类型 CK/BG/BQ 详细设计）
- `docs/superpowers/specs/2026-05-30-warehouse-full-design.md`：仓库全设计文档（含销售实施流程）

## 十、变更记录

| 日期 | 变更内容 | 作者 |
|------|---------|------|
| 2026-06-30 | 初始创建，整合五个问题结论、TWH11/TMM43_EID 联动分析、EID 绑定模式讨论、销售实施全链路现状分析 | Cascade |
| 2026-07-01 | 从生产 Oracle 导出 `usp_trans_in_confrim`/`usp_plan_confrim`/`TRIG_I/U/D_TMM43_TRACK`/`TRIG_U_PLAN_STATUS`，澄清 PB 写入机制；修正 Action Item 11：两层追踪体系（DB 操作层 i/u/d + 业务语义层 C/R/T/A），更新各 plantyp type 映射（10→T、20→R+C、30→R、40→R） | Cascade |
| 2026-07-01 | 文档评审修复：§4.4 新增 P0-P5 已完成工作汇总；§6.6 缺口表格更新（P2/P3/P4 已完成）；§7.1.2 检查表格与结论修正（plantyp=00 已落地）；§7.1 complete() 动作第 3 点标 ✅；§8 行动项 7 标 ✅ | Cascade |
| 2026-07-01 | plantyp=10 术语修正：从"设备变更"改为"磁卡号变更（含 CK/BG/BQ 三子类型）"，对齐 PL 字典与 `sales_service.py:230` 代码；type='T' 仅适用于 BG 子类型；P0 状态码修正为 02→04；新增引用 `docs/myitsm/客户状态与磁卡号变更优化设计.md` | Cascade |
| 2026-07-01 | §8 待办清单后新增"建议执行顺序"小节：三批次（验证+基础设施 / plantyp 补齐 / 扩展），标注关键依赖（11a 先于 11b-e）和业务频率排序 | Cascade |
| 2026-07-01 | §7.2/§7.3 P0 修复标注：§7.2 流程图 implement() 状态 03→04；§7.3 问题 1 表格"实施确认后"标 ✅ P0 已修复；阻断性 Bug 说明改为"已修复"，保留历史描述 | Cascade |
| 2026-07-01 | 任务 10 + 11g 完成：新增 `tests/test_sales_api.py::TestPlanEndToEnd` 两个 E2E 测试（路径 A: MO 关单 / 路径 B: complete），发现并修复 2 个真实 Bug——(1) `EidTrack.refid`/`n_refid` 从 `varchar(8)` 扩展为 `varchar(20)`（迁移 `b181717d589f`），容纳 10 位 `planno`；(2) `sales_service.py:898` `create_outbound` 的 `details_eid` 字段名 `qty`→`outqty` 对齐 `StockOutDetailEid` 模型；§4.4 新增 P6/P7/ETK 码表/E2E 测试四行；§8 行动项 11g 标 ✅ 已完成 | Cascade |
| 2026-07-01 | 任务 11a 完成：新增 `app/extensions/eid_listeners.py`，用 SQLAlchemy `after_insert/after_update/after_delete` 事件监听 `Eid` 模型，自动写 `tmm43_eid_track` type='i/u/d' 记录（对齐 PB `TRIG_I/U/D_TMM43_TRACK`）；`after_update` 仅在追踪字段（sflg/refid/qcflg/whcd 等 17 字段）实际变更时写入，避免噪声；用 `connection.execute(insert(...))` 避免 flush 阶段 `session.add` 警告；在 `app/__init__.py:_init_extensions` 注册监听；新增 `tests/test_eid_listeners.py` 4 个测试验证 i/u/d 写入和无变更不写；§4.4 新增 11a 行，§8 行动项 11a 标 ✅ 已完成 | Cascade |
| 2026-07-01 | 任务 11b 完成：`DeviceChangeService.transition(to_status=5)` 按 change_type 分支——BG 子类型调 `_write_eid_track_on_close_bg()` 写 type='T'（cust_cd→n_cust_cd 客户转移）+ `_transfer_rl_on_close_bg()` 旧门店 rl 失效（useflg=0, asset_status=RETURNED）/新门店 rl 新建（useflg=1, asset_status=ACTIVE, created_from=DEVICE_CHANGE）；CK/BQ 子类型不写 EidTrack、不转移 rl；三种子类型都调 `_write_back_plan_status()` 回写 plan_status='01'（仅当当前='04'）；新增 `tests/test_device_change_11b.py` 3 个测试（BG/CK/BQ）；§4.4 新增 11b 行，§8 行动项 11b 标 ✅ 已完成 | Cascade |
| 2026-07-01 | 任务 11c-e 完成：`MaintenanceRenovateService.transition(to_status=5)` 写旧机 type='R' + 新机 type='C' + rl 旧机失效/新机新建 + 回写（11c）；`RecycleTaskService.transition(to_status=5)` 对每个明细 asset_id 写 type='R' + rl 失效 + 回写（11d）；`StoreCloseService.transition(to_status=5)` 通过 rl 反查门店所有活跃 EID 批量写 type='R' + rl 全失效 + 回写（11e，在原有客户状态联动基础上追加）；新增 `tests/test_maintenance_renovate_11c.py`/`test_recycle_task_11d.py`/`test_store_close_11e.py` 各 3 个测试；§7.1.2 检查表格全部标 ✅，§8 行动项 11c-e 标 ✅ 已完成，未覆盖 plantyp 表格全部标 ✅ | Cascade |
| 2026-07-02 | 质量提升项完成：(1) 抽取 11 个业务码值常量（RL_USEFLG/ASSET_STATUS/PLAN_STATUS/TRACK_TYPE/CLOSE_STATUS）替换 11a-e 所有硬编码；(2) 11c/d/e 各补 3 个失败路径测试（单据不存在/非法状态流转/边界场景），共 9 个新测试；(3) `eid_listeners.register_eid_listeners` 加 try/except + logging 告警 | Cascade |
| 2026-07-02 | 行动项 10 完成：扩展 `tests/test_sales_api.py::TestPlanEndToEnd` 新增 3 个 plantyp E2E 测试（20 翻新/30 回收/40 门店关闭），验证预计划→实施→关单全链路（EidTrack + CustPosRl + 回写）；§8 行动项 10 标 ✅ 已完成 | Cascade |
| 2026-07-02 | 任务 11f 完成：`SystemService.update_eid` 资产编辑接口写 type='A'（属性变更）轨迹——更新前取资产属性快照（asset_type/recyclable/recycle_status/asset_owner/install_date 等 15 字段），更新后比对变更，仅当实际变更时调 `create_eid_track(track_type='A')` 记录新旧值（remark 含字段级变更明细）；业务语义层 A 与 DB 操作层 u（11a 事件监听）双层覆盖；新增 `tests/test_update_eid_11f.py` 5 个测试（属性变更/无变更/不存在/双层写入）；§8 行动项 11f 标 ✅ 已完成 | Cascade |
