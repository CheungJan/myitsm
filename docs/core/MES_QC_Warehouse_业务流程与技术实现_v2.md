---
类型: 技术文档
阅读状态: 已完成
tags: 技术文档, MES, QC, 仓库, 业务流程, 4主线2子流程
更新日期: 2026-06-11
创建时间: 2026-06-08
---

# MES/QC/仓库联动 — 业务流程与技术实现 v2.1

> 结构：4种主线模式 + 2类子流程处理 + IQC/IPQC/FQC三类质检边界
> 适用：开发、测试、运维、业务人员

### 文档版本说明

| 章节 | 来源 | 状态 |
|------|------|------|
| 1. 业务流程层次结构 | **v2 新增** | ✅ |
| 1.3 工单状态机 (PICKING/QC_PENDING) | **v2 新增** | ✅ |
| 1.4 三种QC类型 (IQC/IPQC/FQC) | **v2 新增** | ✅ |
| 2. 主线流程详解 (模式A/B/C/D) | v1 重构 | ✅ 更新 |
| 2.5 生产工单状态机表 | **v2 新增** | ✅ |
| 2.6 三类QC边界说明 | **v2 新增** | ✅ |
| 3. 子流程详解 | v1 重构 | ✅ 更新 |
| 4. 数据流与技术实现 | v1 重构 | ✅ 更新 |
| 5. 操作指南 | **v2 新增** | ✅ |
| 6. 验证方法 | v1 重构 | ✅ 更新 |
| 7. 附录 | v1 重构 | ✅ 更新 |
| 8. 修复记录 | **v2 新增** | ✅ |
| 9. 异常处理与边界情况 | v1 迁移 | ✅ 已评审更新 |
| 10. 数据一致性保障 | v1 迁移 | ✅ 已评审更新 |
| 11. 性能优化 | v1 迁移 | ✅ 已评审更新 |
| 12. 扩展性设计 | v1 迁移 | ✅ 已评审更新 |
| 13. 质检录入模块设计 | **v2 新增** | ✅ |
| 14. FQC不良处理与补料 | **v2.1 新增** | ✅ |

> v1 迁移章节：来自 `MES_QC_Warehouse_Technical_Document.md`，已按当前代码实际逻辑评审修正。若发现问题，先核对上述来源标记，判断是迁移内容过时还是新增内容有误。

---

## 1. 业务流程层次结构

### 1.1 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    生产质检仓库联动体系                        │
├─────────────────────────────────────────────────────────────┤
│  第一层：主线流程（4种生产质检模式）                          │
│  ├─ 模式A：独立质检（采购→质检→入库，非生产触发）            │
│  ├─ 模式B：生产领料-EID（工单→OV=8→生产→FQC→IV=8，先贴标） │
│  ├─ 模式C：生产领料-批次（工单→OV=8→生产→FQC→贴标入库）    │
│  └─ 模式D：旧机翻新（翻新工单→旧机出库→翻新→新机入库）       │
├─────────────────────────────────────────────────────────────┤
│  第二层：子流程（嵌入主线）                                   │
│  ├─ 子流程5：质检结果分流（QC审核时自动触发）                 │
│  │   ├─ 链路A（采购质检）                                     │
│  │   │   ├─ GA/GB/GC合格 → IV=11质检入库             │
│  │   │   ├─ BF报废 → OV=7报废出库                 │
│  │   │   ├─ BH返修 → OV=9返修出库                    │
│  │   │   └─ TH退换 → OV=6退换出库                │
│  │   ├─ 链路B（工单生产FQC）                                  │
│  │   │   ├─ GA/GB/GC合格 → IV=8生产入库                        │
│  │   │   ├─ 工单状态 QC_PENDING → COMPLETED                     │
│  │   │   └─ BH返修/BF报废/TH退换 → 对应异常出库                   │
│  │   │                                                       │
│  └─ 子流程6：生产退换/补领/IPQC（模式B/C/D生产/翻新中发现问题时触发）│
│      ├─ 发现坏件 → 即时退换（OV=6退货 + 新领料，不进入最终质检）   │
│      ├─ 物料不足 → 补领出库OV=8（TMS04累加）                   │
│      └─ 返修完成 → 返修入库IV=9（EID sflg='3'）                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模式选择决策树

```
是否有MES工单？
    ├── 否 → 模式A：独立质检流程（采购入库质检）
    └── 是 → 工单类型？
            ├── RENOVATION（翻新）→ 模式D：旧机翻新
            └── PRODUCTION（生产）→ 物料类型？
                    ├── EID模式（已贴标/已IQC合格配件）→ 模式B
                    └── 批次模式（BOM导入/耗材/免IQC物料）→ 模式C
```

---


### 1.3 工单状态机

```
DRAFT → RELEASED → PICKING → IN_PROGRESS → QC_PENDING → COMPLETED
          │             │              │              │
          │             │              │              └─ FQC GA/GB/GC通过
          │             │              └─ 手动完工
          │             └─ OV=8审核
          └─ 自动生成OV=8草稿

PICKING  = 领料中，OV=8草稿已生成，等待仓库审核出库
IN_PROGRESS = 生产中，允许过程检(IPQC)和异常处理
QC_PENDING = 待最终检，整机完工等待FQC
COMPLETED = FQC通过，终态
```

### 1.4 三种QC类型

| 类型 | 名称 | 发生阶段 | refbillid | 影响工单状态 | 现状 |
|------|------|---------|-----------|:--:|:--:|
| IQC | 来料质检 | OV=5质检出库后 | OT... | 不影响工单 | 已验收 |
| IPQC | 过程检 | IN_PROGRESS | WO.../工序ID | 不改主状态 | 已实现 |
| FQC | 最终检 | QC_PENDING | WO... | GA/GB/GC→COMPLETED；BH/BF/TH→回退IN_PROGRESS | 已实现 |

**FQC 不良处理（v2.1新增）**：若 FQC 判定为 BH/BF/TH，不良品不进入生产入库（IV=8），而是先入 IV=11 暂存仓（L1/LS），审核后自动 OV=7/9/6 出库。工单从 QC_PENDING 回退到 IN_PROGRESS（回退生产状态），同时自动生成补料 OV=8 关联该工单，待补料后重新提交 FQC。


## 2. 主线流程详解

### 2.1 模式A：独立质检（采购→质检→入库）

**适用场景**：来料质检，非生产触发

**业务流程**：

```
采购订单
    │
    ▼
IV=1 采购入库（DJ待检状态）
    │
    ├──→ OV=5 质检出库（选采购入库单）
    │          │
    │          ▼
    │    QC质检判定（来源=质检出库）
    │          │
    │          ├──→ GA/GB/GC合格 → IV=11 质检入库（仅合格物料）
    │          ├──→ BF报废 → OV=7 报废出库
    │          ├──→ BH返修 → OV=9 返修出库
    │          └──→ TH退换 → OV=6 退换出库
    │
    └──→ 标签管理 → 激活EID（GA/DJ）→ TMM43_EID
```

**关键单据**：IV=1→OV=5→QC→IV=11

**技术实现**：
- `StockInService.create(invtyp='1')` 创建采购入库
- `StockOutService.create(invtyp='5')` 创建质检出库
- `QcService.create(source_type='qc_out')` 录入质检（来源=质检出库OV=5）
- `LabelService.activate()` 激活标签

---

### 2.2 模式B：生产领料-EID（先贴标后生产）

**适用场景**：配件已贴标或已通过IQC，生产领用后按EID追溯。

**业务流程**：

```
MES工单（PRODUCTION）
    │
    ▼
DRAFT → RELEASED（下达）
    │
    ▼
自动生成 OV=8 生产出库草稿 → 工单进入 PICKING
    │
    ▼
OV=8 生产出库审核（选EID，关联工单）
    │  ├─ 审核 → EID sflg='7'（生产中），whcd=NULL
    │  ├─ 写入 TMS04 物料消耗
    │  └─ 工单 PICKING → IN_PROGRESS
    │
    ▼
组装生产
    │
    ├── 过程检 IPQC（可多次发生，不改变工单主状态）
    ├── 过程发现坏件 → 即时退换/返修/报废/补领（不进入最终质检）
    │
    ▼
手动完工 → 工单 IN_PROGRESS → QC_PENDING
    │
    ▼
FQC最终质检（来源=生产工单）
    │
    └── FQC审核GA/GB/GC合格 → IV=8 生产入库 + 工单COMPLETED
           ├─ 标签激活 → EID sflg='1', qcflg='GA/GB/GC'
           └─ 工单 QC_PENDING → COMPLETED
```

**关键特征**：
- EID已存在，出库时选择已有EID
- 出库审核自动写TMS04
- 生产过程中允许IPQC，过程异常即时退换/返修/报废/补领，不改变工单主状态
- 手动完工只进入QC_PENDING，不直接COMPLETED
- FQC GA/GB/GC合格生成IV=8入库 + 工单COMPLETED

---

### 2.3 模式C：生产领料-批次（后贴标模式）

**适用场景**：BOM导入批次物料、耗材、免IQC原材料，生产完成后贴标或形成成品批次。

**业务流程**：

```
MES工单（PRODUCTION）
    │
    ▼
DRAFT → RELEASED（下达）
    │
    ▼
自动生成 OV=8 生产出库草稿 → 工单进入 PICKING
    │
    ▼
OV=8 生产出库审核（BOM导入，批次模式，无EID）
    │  ├─ 审核 → TWH11扣库存 → TMS04写入
    │  └─ 工单 PICKING → IN_PROGRESS
    │
    ▼
组装生产
    │
    ├── 过程检 IPQC（可多次发生，不改变工单主状态）
    │
    ▼
手动完工 → 工单 IN_PROGRESS → QC_PENDING
    │
    ▼
FQC最终质检（GA/GB/BH/BF/TH/GC）
    │
    ├──→ GA/GB/GC合格 → 标签激活/生成新EID → IV=8生产入库
    ├──→ BH返修       → OV=9返修
    ├──→ BF报废       → OV=7报废
    └──→ TH退换       → OV=6退换
```

**关键特征**：
- 出库时为批次模式，按BOM导入物料清单
- 质检通过后生成新EID
- FQC GA/GB/GC合格生成IV=8入库 + 工单COMPLETED
- 批次物料可来自未经过IQC但允许直接生产使用的新品库原材料或耗材

---

### 2.4 模式D：旧机翻新（翻新工单流程）

**适用场景**：旧设备翻新，新旧EID溯源

**业务流程**：

```
MES工单（RENOVATION）
    │
    ▼
OV=10 翻新出库（选旧EID，关联工单）
    │  ├─ 审核 → EID sflg='7'（翻新中）
    │  └─ 写入 TMS04
    │
    ▼
拆解/换件（如需补件 → OV=8关联同工单）
    │
    ▼
标签激活新EID
    │
    ▼
IV=6 翻新入库 → 审核
    ├─ 旧EID：sflg='8', qcflg='BF'
    └─ 新EID：ref_eid=旧EID（溯源）
    │
    ▼
手动完工 → 工单状态 QC_PENDING
    │
    ▼
FQC 最终检（refbillid=WO...）
    │  ├─ GA/GB/GC → IV=8生产入库 + 工单COMPLETED
    │  └─ BH/BF/TH → OV=6/7/9异常出库
```

**关键特征**：
- 独立出库类型OV=10，入库类型IV=6
- 新旧EID通过`ref_eid`建立溯源关系
- 旧机最终状态为报废，新机为可用

---

### 2.5 生产工单状态机（模式B/C）

生产工单主状态只表达工单生命周期，不把每次过程检都展开为主状态。生产中发现的过程异常通过 IPQC 与异常出库/补领处理；整机或成品完成后进入 FQC 等待最终检。

```
DRAFT ──下达→ RELEASED ──自动OV=8→ PICKING ──OV=8审核→ IN_PROGRESS ──手动完工→ QC_PENDING ──FQC通过→ COMPLETED
  │              │               │                  │           │              │
  ├──FQC不良────┴───────────────┴──────────────────┴──←─FQC不合格(BH/BF/TH)───┘
  │              │               │                  │                         │
  └──取消────────┴───────────────┴──────────────────┴─────────────────────────┴──→ CANCELLED
```

| 状态 | 含义 | 触发 | 可操作 |
|------|------|------|--------|
| DRAFT | 草稿 | 新建工单 | 下达/取消 |
| RELEASED | 已下达 | 手动下达 | 系统自动生成OV=8草稿后进入PICKING |
| PICKING | 领料中 | OV=8草稿已生成 | OV=8审核通过后自动IN_PROGRESS/取消 |
| IN_PROGRESS | 生产中 | OV=8审核通过 | 允许IPQC、补领、退换、返修、报废；手动完工进入QC_PENDING |
| QC_PENDING | 待最终检 | 手动完工 | FQC审核GA/GB/GC→COMPLETED；FQC不合格(BH/BF/TH)→回退IN_PROGRESS补料 |
| COMPLETED | 已完工 | FQC通过 | 终态 |
| CANCELLED | 已取消 | 中间态取消 | 终态 |

---

### 2.6 三类QC边界（IQC/IPQC/FQC）

| 类型 | 名称 | 发生阶段 | refbillid | 状态影响 | 当前状态 |
|------|------|----------|-----------|----------|----------|
| IQC | 来料检 | OV=5质检出库后 | OT... | 不影响工单 | 已实现/已验收 |
| IPQC | 过程检 | IN_PROGRESS生产中 | WO...或工序ID | 不改变工单主状态 | 已实现 |
| FQC | 最终检 | QC_PENDING待最终检 | WO... | GA/GB/GC触发QC_PENDING→COMPLETED | 已实现 |

**IPQC 适用模式**：
- 模式B/C/D 都适用——只要工单进入 `IN_PROGRESS` 状态，即可触发 IPQC
- 模式D（翻新）：拆解/换件过程中发现配件有缺陷，通过 IPQC 退换/返修/报废，不改变工单状态
- 模式A（独立质检）：不涉及工单，无 IPQC

**边界说明**：
- IQC面向采购来料，合格后进入IV=11质检入库，可供后续生产领用。
- IPQC面向生产过程和工序异常（含翻新过程），处理坏件、报废、返修、退换、补领，不直接推进工单完工。
  - **实现方式**：复用现有 QC 审核逻辑，refbillid=WO... 且工单状态=IN_PROGRESS 时判定为 IPQC
  - **前端实现**：QC 录入页面选择"生产工单"来源后，系统按工单状态自动区分：QC_PENDING → FQC 树形布局（成品+BOM配件），IN_PROGRESS → IPQC 扁平布局（物料列表）
  - **核心区别**：
    - IPQC 不推动工单状态（IN_PROGRESS 不动）
    - IPQC 合格（GA/GB/GC）不入库，只标记 EID 状态
    - IPQC 异常（BH/BF/TH）生成异常出库单（OV=6/7/9）
  - **不需要新增数据模型**：通过 refbillid 前缀和工单状态区分 IQC/IPQC/FQC
- FQC面向整机或成品最终放行，只有GA/GB/GC通过后，工单才从QC_PENDING进入COMPLETED。
  - **FQC 只判定成品整机（工单 item_cd），不重复判定已 IQC 通过的子件物料**
  - **前端实现**：QC 录入页面选择"生产工单"来源时，QC_PENDING 工单展示树形结构（成品+BOM配件），系统自动按工单状态进入 FQC 处理逻辑
  - 生产过程中发现配件坏了，通过 IPQC（过程检）处理，不走 FQC 流程
- **FQC 不良处理（v2.1 新增）**：FQC 判定为 BH/BF/TH 时，不良品先入 IV=11 暂存仓（L1/LS），审核后自动 OV 出库；工单从 QC_PENDING 回退到 IN_PROGRESS；自动生成补料 OV=8 关联该工单
- 当前暂不新增`qc_type`字段，先通过`refbillid`前缀和工单状态区分：`OT...`表示IQC来源质检出库，`WO...`表示生产工单来源；IPQC 和 FQC 都用 `WO...`，通过工单状态区分（IN_PROGRESS=IPQC，QC_PENDING=FQC）。

---

## 3. 子流程详解

### 3.1 子流程5：质检结果分流（QC审核自动触发）

**审核按 qcstatus 分流**：

```python
QcService.audit(qcstatus)
├── GA/GB/GC(合格/让步/降级) → EID qcflg=GA/GB/GC + 标签激活 → IV=11质检入库
├── BH(返修)   → EID qcflg='BH' → OV=9返修出库
├── BF(报废)   → EID sflg='2',qcflg='BF' → OV=7报废出库
├── TH(退换)   → EID qcflg='TH' → OV=6退换出库（耗材退供应商）
└── DJ(待检)   → EID qcflg='DJ' → 无仓库动作
```

**质检判定选项（按物料类型）**：

| 物料类型 | 可见判定 |
|----------|----------|
| 配件 | GA/GB/BH/BF/TH |
| 耗材 | GA/BF/TH |
| 成品 | GA/GB/BH/BF/TH/GC |

**仓库动作对照表**：

| qcstatus | IQC/OV=5来源 | FQC/WO来源 | 异常动作 |
|----------|--------------|------------|----------|
| GA/GB/GC | IV=11质检入库 | IV=8生产入库+工单COMPLETED | — |
| BH | OV=9返修出库 | OV=9返修出库 | 返修 |
| BF | OV=7报废出库 | OV=7报废出库 | 报废 |
| TH | OV=6退换出库 | OV=6退换出库 | 退换 |
| DJ | 无仓库动作 | 停留QC_PENDING | 待判 |
| BH/BF/TH(FQC) | — | IV=11暂存→OV出库；工单QC_PENDING→IN_PROGRESS；补料OV=8 | FQC不良回退 |
| BH/BF/TH(IPQC) | — | IV=11暂存→OV出库；补料OV=8；工单保持IN_PROGRESS | IPQC异常处理 |

---

### 3.2 子流程6：生产退换/补领（异常处理）

#### 坏件退货流程

```
生产过程中发现坏件
    │
    ▼
创建 OV=9 返修出库（关联原工单）
    │
    ▼
审核OV=9
    ├─ EID状态：sflg='5'（返修中）
    └─ 自动生成 IV=9 返修入库草稿
    │
    ▼
返修完成 → IV=9 入库
    └─ EID状态：sflg='3'（待检）
```

#### 缺料补领流程

```
生产过程中物料不足
    │
    ▼
创建 OV=8 生产出库（关联原工单）
    │
    ▼
审核OV=8 → TMS04 累加去重
    ├─ 同物料多次出库：actual_qty累加
    └─ 避免重复写入
```

---

## 4. 数据流与技术实现

### 4.1 EID生命周期状态流转

```
标签生成 → 激活(GA/DJ) → 入库(whcd=仓, sflg='8')
    │
    ├── 生产领用 OV=8   → whcd=NULL, sflg='7'(生产中)
    ├── 返修出库 OV=9   → whcd=NULL, sflg='5'(返修中)
    ├── 翻新出库 OV=10  → whcd=NULL, sflg='7'(翻新中)
    ├── 报废出库 OV=7   → whcd=NULL, sflg='2', qcflg='BF'
    │
    ├── IPQC/FQC不良BH → whcd=NULL, sflg='3'(待检), qcflg='BH'
    │   └── IV=11暂存LS → whcd='LS', sflg='3'(待检), qcflg='BH'
    │       └── OV=9返修出库 → whcd=NULL, sflg='5'(返修中), qcflg='BH'
    ├── 返修入库 IV=9   → whcd=仓, sflg='3', qcflg='DJ'
    ├── 生产入库 IV=8   → whcd=仓, sflg='1', qcflg='GA'
    └── 翻新入库 IV=6   → whcd=仓, sflg='8', ref_eid=旧EID
```

### 4.2 核心API清单

| 模块 | 端点 | 功能 | 触发联动 |
|------|------|------|----------|
| MES | `/mes/work-orders/<id>/transition` | 工单流转 | RELEASED→生成OV=8草稿并进入PICKING；IN_PROGRESS→QC_PENDING |
| QC | `/qc/results/<id>/audit` | QC审核 | IQC: GA/GB/GC→IV=11；FQC: GA/GB/GC→IV=8+COMPLETED；IPQC: GA/GB/GC不入库、BH/BF/TH→异常出库 |
| WH | `/warehouse/stock-out/<id>/audit` | 出库审核 | OV=8→TMS04+工单PICKING→IN_PROGRESS |
| WH | `/warehouse/stock-in/<id>/audit` | 入库审核 | IV=6→溯源ref_eid |
| INV | `/inventory/labels/activate` | 标签激活 | 生成TMM43_EID |

### 4.3 关键代码路径

**工单下达触发领料出库**：
```python
# mes_service.py
WorkOrderService.transition(status='RELEASED')
    → _create_production_outbound_draft(wo_id)
    → invtyp = '10' if wo.wo_type=='RENOVATION' else '8'
    → status='PICKING'
```

**工单完工进入最终检**：
```python
# mes_service.py
WorkOrderService.transition(status='QC_PENDING')
    → actual_end = today
    → 等待FQC审核通过后由QC服务推动COMPLETED
```

**QC审核自动动作**：
```python
# qc_service.py
QcService.audit(qcbillid)
    1. 读取TQC10/TQC11明细
    2. 按refbillid判断来源：OT...=IQC(质检出库)，WO...=FQC/IPQC(生产工单)
       └─ 工单QC_PENDING→FQC；工单IN_PROGRESS→IPQC
    3. GA/GB/GC：IQC生成IV=11质检入库；FQC生成IV=8生产入库+推动工单COMPLETED
    4. BH/BF/TH：统一先IV=11入暂存仓(L1/LS)，审核后自动OV=7/9/6出库
       ├─ IPQC+不良：自动补料OV=8（关联同工单，TMS04累加）
       └─ FQC+不良：工单QC_PENDING→IN_PROGRESS + 自动补料OV=8
    5. EID更新：BH→sflg='3'(待检) qcflg='BH'；BF→sflg='2' qcflg='BF'
    6. 激活标签（GA/GB/GC时TMM40_LABEL.useflg='0'）
```

---

## 5. 操作指南

### 5.1 模式A：独立质检

1. **采购入库**：入库单管理 → 新建 → IV=1 → 填DJ物料 → 审核
2. **质检出库**：出库单管理 → 新建 → OV=5 → 选采购入库单 → 审核
3. **质检录入**：质检管理 → 录入 → 来源=质检出库
4. **质检审核**：录入质检，逐行选择判定（GA/GB/GC/BH/BF/TH）
5. **质检入库**：QC审核GA/GB/GC后生成IV=11，再由仓库审核入库

### 5.2 模式B/C：生产工单

1. **创建工单**：工单管理 → 新建 → 填物料编码/数量 → 保存
2. **下达工单**：工单 → 下达（RELEASED → 自动OV=8 → PICKING）
3. **生产领料**：系统自动生成OV=8草稿，工单进入PICKING
4. **出库审核**：审核OV=8，写入TMS04，工单自动进入IN_PROGRESS
5. **生产过程**：允许IPQC、补领、退换、返修、报废，不改变主状态
6. **手动完工**：工单IN_PROGRESS → QC_PENDING
7. **最终质检**：质检管理 → 录入 → 来源=生产工单
8. **质检审核**：FQC GA/GB/GC触发IV=8生产入库，并推动工单COMPLETED

**删除限制**：
- 工单仅DRAFT可删除
- 工序仅PENDING可删除

### 5.3 模式D：旧机翻新

1. **创建翻新工单**：工单 → wo_type=RENOVATION → 填旧EID
2. **翻新出库**：系统自动生成OV=10 → 审核
3. **翻新处理**：拆解/换件（如需补件→OV=8关联同工单）
4. **生成新标**：标签管理 → 批量生成
5. **翻新入库**：入库单 → 选OV=10来源 → 填新EID → 审核

---

## 6. 验证方法

### 6.1 数据链路验证SQL

```sql
-- 出库单
SELECT outbillid, invtyp, whcd, auditflg, refbillid 
FROM twh15_out WHERE outbillid = '<单号>';

-- 关联入库单
SELECT inbillid, invtyp, refbillid, whcd 
FROM twh13_in WHERE refbillid = '<出库单号>';

-- EID状态
SELECT eid, sflg, qcflg, whcd FROM tmm43_eid 
WHERE eid IN (SELECT eid FROM twh16_outdteid WHERE outbillid = '<单号>');

-- TMS04消耗
SELECT wo_id, itemcd, plan_qty, actual_qty 
FROM tms04_material_consume WHERE wo_id = '<工单号>';
```

### 6.2 QC审核验证

```sql
-- 标签激活
SELECT labelid, useflg FROM tmm40_label WHERE labelid = '<EID>';

-- IV=6溯源
SELECT eid, ref_eid FROM tmm43_eid WHERE ref_eid IS NOT NULL;
```

---

## 7. 附录

### 7.1 状态码对照表

**EID状态（sflg）**：0=新品, 1=已使用, 2=报废, 3=待检, 5=返修中, 7=生产中/翻新中, 8=在库, S=销售出库

**质检标志（qcflg）**：GA/GB/GC=合格, DJ=待检, BH=坏件, BF=报废

### 7.2 单据类型

**入库（IV）**：1=采购, 2=销售退货, 4=调拨, 6=翻新, 8=生产, 9=返修, 11=质检

**出库（OV）**：1=销售, 2=借出, 3=调拨, 5=质检, 7=报废, 8=生产, 9=返修, 10=翻新

---

## 9. 异常处理与边界情况

### 9.1 幂等性

| 场景 | 处理 | 位置 |
|------|------|------|
| 重复生成OV=8/OV=10 | 检查已存在关联出库单，存在则跳过 | `mes_service.py:_create_production_outbound_draft` |
| 重复审核QC | auditflg=='1' 拒绝 | `qc_service.py:audit` |
| OV=5重复生成IV=11 | 不再自动生成，QC审核时才按合格物料生成 | `qc_service.py:audit` |
| 草稿更新 | 同来源+同类型已有草稿时更新而非新建 | `StockInService.create`, `StockOutService.create` |

### 9.2 错误处理

| 错误 | 处理 | 返回 |
|------|------|------|
| 工单不存在 | 提前返回 | `{"success": False, "error": "工单不存在"}` |
| 状态不允许流转 | 状态机校验 | `{"success": False, "error": "不允许从X流转到Y"}` |
| 库存不足 | 事务回滚 | `raise ValueError("库存不足")` |
| 标签不存在 | 静默跳过 | `if label: ...` |
| OV=8生成失败 | 不阻断工单下达，返回False | `mes_service.py:transition` |

### 9.3 质检审核异常处理

QC审核按qcstatus分流后，各分支异常不互相影响：
- GA/GB/GC入库失败 → 仅该单据失败，不影响QC主状态
- BH/BF/TH出库失败 → 仅该单据失败
- EID/标签更新失败 → 整体回滚（db.session未提交）

---

## 10. 数据一致性保障

### 10.1 仓库联动的事务模型

QC审核中，EID状态更新+标签激活+仓库单据生成在同一事务中，任一步失败整体回滚：

```python
# qc_service.py - audit()
QcRepository.audit(qc, auditor)      # 标记已审（commit）
# 以下在独立事务中
try:
    # EID状态更新
    db.session.query(EidModel).filter(...).update(...)
    # 标签激活
    label.useflg = "0"
    # 仓库单据
    StockInService.create(...)        # 内部commit
    StockOutService.create(...)       # 内部commit
except:
    db.session.rollback()
    raise
```

注：当前审核先 commit QC 状态，再执行仓库动作。若仓库动作失败，QC 已标记已审但无下游单据。后续可优化为两阶段提交。

### 10.2 补偿策略

| 场景 | 策略 |
|------|------|
| OV=8自动生成失败 | RELEASED状态保留，用户可手动取消，不阻断流程 |
| 标签激活失败 | Label PK不匹配时静默跳过，不影响审核 |
| 出入库单据生成失败 | 当前已commit QC状态后单独创建，失败无回滚 |

---

## 11. 性能优化

### 11.1 批量查询

```python
# EID状态批量更新
db.session.query(EidModel).filter(
    EidModel.eid.in_([r.eid for r in eid_rows])
).update({"qcflg": "GA"}, synchronize_session=False)
```

### 11.2 名称缓存

| 缓存 | 函数 | 方式 |
|------|------|------|
| 仓库名称 | `_enrich_warehouse_names()` | 批量IN查询 |
| 物料名称 | `_enrich_item_names()` | 批量IN查询+class_cd/is_bom |
| 供应商名称 | `_enrich_supplier_names()` | 批量IN查询 |

### 11.3 分页与数量限制

| 限制 | 值 | 位置 |
|------|----|------|
| 列表分页上限 | 100条/页 | 全局 Middleware |
| OV=5可用列表 | LIMIT 200 | `find_ov5_for_qc` |
| 可用标签预览 | LIMIT 200 | `fetchAvailableLabels` |

---

## 12. 扩展性设计

### 12.1 新增质检状态

在 `tmm31_syscodes` 表新增 `code_typ='QC'` 的记录即可：

```sql
INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, created_at, updated_at)
VALUES ('QC', 'XX', '新状态名', '1', 9, NOW(), NOW());
```

然后在 `qc_service.py:audit()` 中按 qcstatus 添加分流分支：

```python
elif qcstatus == "XX":
    # 自定义EID更新 + 仓库动作
    pass
```

### 12.2 新增出入库联动类型

参考 OV=5→QC→IV=11/OV=7/OV=9 模式，三处改动：
1. `StockOutService.audit()` - 审核时生成下游单据
2. `QcService.audit()` - QC审核时按判定生成仓库单据
3. 前端 `StockOutList.vue` / `QcInput.vue` - 来源选择和联动展示

---

## 8. 最新修复记录（2026-06-08）

### 8.1 质检出库选择器逻辑修复

**问题**：已审核的采购入库单（IN开头）在质检出库（OV=5）选择器中不显示

**原因**：原查询 `find_qc_out_pending_orders` 只检查入库单是否已审核，未检查该入库单物料是否还有未完全质检出库的剩余

**实际数据情况**：
```
IN061858, IN061859, IN061861, IN061862 已审核入库（invtyp='1', auditflg='2', whcd='01'）
入库明细：BS4001, BS40L1, PTY500 等物料已入库
无质检出库记录（OV=5 refbillid 为空）
```

**数据背景**：
- PC开头单据：PB老系统历史数据（采购来料直接入库PC单号）
- IN开头单据：新系统统一入库单号（如IN061858）
- 两类单据共存于选择器，需按创建时间倒序排列

**修复后SQL**（warehouse_repository.py:915-973）：
```sql
WITH in_summary AS (
    -- 计算每个入库单的总入库数量
    SELECT inbillid, COALESCE(SUM(inqty), 0) AS total_in_qty
    FROM twh14_checkindt
    GROUP BY inbillid
),
out_summary AS (
    -- 计算每个入库单已被质检出库的总数量（EID+批次）
    SELECT o.refbillid AS inbillid, COALESCE(SUM(e.outqty), 0) AS total_out_qty
    FROM twh15_out o
    JOIN twh16_outdteid e ON o.outbillid = e.outbillid
    WHERE o.invtyp = '5' AND o.auditflg = '2'
    GROUP BY o.refbillid
    UNION ALL
    SELECT o.refbillid AS inbillid, COALESCE(SUM(p.outqty), 0) AS total_out_qty
    FROM twh15_out o
    JOIN twh16_outdtprd p ON o.outbillid = p.outbillid
    WHERE o.invtyp = '5' AND o.auditflg = '2'
    GROUP BY o.refbillid
),
out_agg AS (
    -- 合并EID和批次出库数量
    SELECT inbillid, SUM(total_out_qty) AS total_out_qty
    FROM out_summary
    GROUP BY inbillid
),
pending_orders AS (
    -- 找出还有剩余数量的入库单
    SELECT i.inbillid
    FROM in_summary i
    LEFT JOIN out_agg o ON i.inbillid = o.inbillid
    WHERE i.total_in_qty > COALESCE(o.total_out_qty, 0)
)
-- 主查询：获取入库单详情（按生成时间倒序，新单据优先）
SELECT i.inbillid, i.whcd, i.indate, i.refbillid
FROM twh13_in i
JOIN pending_orders p ON i.inbillid = p.inbillid
WHERE i.invtyp = '1' AND i.auditflg = '2'
ORDER BY i.gendate DESC, i.inbillid DESC
LIMIT 300
```

**注意**：如需排除已结案明细，需确保数据库表`twh14_checkindt`有`closed_flg`字段，否则会出现"column does not exist"错误。当前版本暂未使用该过滤。

**新增接口**（2026-06-08）：

| 端点 | 功能 | 用途 |
|------|------|------|
| `GET /stock-out/qc-pending-lines/<inbillid>` | 查询采购入库单物料明细 | OV=5质检出库选择入库单后加载物料 |

**Bug修复记录**：
- `ImportError: Item模型路径修正`：`app.models.inventory` → `app.models.master`（Item在master.py中定义）
- `采购订单排序修正`：`ORDER BY rgstbillid` → `ORDER BY rgstdate DESC, rgstbillid DESC`（最新单据显示在最上面）

**前端改动**：
1. 选择采购入库单后自动带出仓库（与入库单一致）
2. 加载该入库单的物料明细（替代整个仓库库存）
3. 物料列表显示入库单中的批次/EID信息
4. 库存列表显示仓库列（批次模式和EID模式都显示 `whcd` 标签）
5. 出库明细表格显示**来源入库单号列**（质检出库模式下），方便追溯物料来源

**质检出库两种模式说明**：

| 模式 | 操作方式 | 适用场景 |
|------|----------|----------|
| **采购单模式**（当前实现） | 选择采购入库单 → 自动带出仓库和物料 | 需要追溯采购来源、分批入库到不同仓库 |
| **仓库模式**（简单模式） | 直接选择仓库 → 加载该仓库所有待检物料 | 快速出库、不关心具体采购单 |

**多仓库入库处理**：
- 同一采购单（PR开头）可能分批入库到不同仓库（如部分入01新品库、部分入02库）
- 系统生成不同入库单号（IN开头），分别记录各自的仓库
- 质检出库时选择具体入库单，自动带出对应仓库和物料
- 前端显示格式：`IN061862 ← PR001574 (01仓 待检)`

**前端显示优化**（StockOutList.vue:189）：
```vue
<el-option v-for="o in qcPendingOrders" 
    :key="o.inbillid" 
    :label="`${o.inbillid}${o.refbillid ? ' ← '+o.refbillid : ''} (${o.whcd||''}仓 待检)`" 
    :value="o.inbillid"/>
```
显示格式：`IN061858 ← PR001572 (01仓 待检)`

**业务逻辑**：
- 入库审核后物料进入仓库（如新品库），状态DJ
- 质检出库（OV=5）必须关联原采购入库单
- 系统检查该入库单下还有未质检的物料才显示在选择器中
- 已完全质检出库的单据不再显示

**验证SQL**：
```sql
-- 检查入库单是否存在及状态
SELECT inbillid, invtyp, auditflg, whcd, refbillid, gendate
FROM twh13_in
WHERE inbillid IN ('IN061858', 'IN061859', 'IN061861', 'IN061862');

-- 检查入库明细
SELECT inbillid, itemcd, inqty, eid
FROM twh14_checkindt
WHERE inbillid IN ('IN061858', 'IN061859', 'IN061861', 'IN061862');

-- 检查是否已有质检出库
SELECT o.outbillid, o.refbillid, o.invtyp, o.auditflg
FROM twh15_out o
WHERE o.refbillid IN ('IN061858', 'IN061859', 'IN061861', 'IN061862')
AND o.invtyp = '5';
```

---

## 13. 质检录入模块设计

### 13.1 概述

质检录入是质量管理的入口环节。OV=5（质检出库）审核后不自动生成 IV=11，待 QC 完成判定后再按结果分流生成对应出入库单据。

### 13.2 数据模型

```
TQC10_RESULT (质检结果主表)
    │  QCBILLID(主键), QCSTATUS(质检状态), REFBILLID(关联OV=5单号)
    │
    ├── TQC11_RESULTDT (按批次明细) ──→ 无EID的批次物料
    │       itemcd, itemtyp, prddate, qcqty, qcstatus
    │
    └── TQC11_RESULTEID (按设备明细) ──→ 有EID的设备物料
            itemcd, eid, manuf_seq(原厂序列号), qcqty, qcstatus
```

### 13.3 质检录入流程

```
步骤1: 选择来源单据
  └─ 来源类型: 质检出库(OV=5) / 生产工单(WO)
  └─ 选单后加载全量明细表格

步骤2: 逐行判定
  ├─ 物料属性(成品/配件/耗材) 自动识别
  ├─ 判定下拉按物料类型过滤
  ├─ 有EID行: 标签下拉或点击生成
  └─ 耗材行: EID列显示"无需标签"

步骤3: 提交 → 按判定分组生成TQC10+TQC11记录
```

### 13.4 判定选项（按物料类型）

| 物料类型 | 判定选项 | 说明 |
|----------|----------|------|
| 配件 | GA/GB/BH/BF/TH | 不含GC降级 |
| 耗材 | GA/BF/TH | 不含BH返修(无法追踪) |
| 成品 | GA/GB/BH/BF/TH/GC | 含GC降级 |

### 13.5 审核联动

OV=5 审核时不生成 IV=11。QC 审核后按判定分流：

| qcstatus | EID | 批次 | 单据 |
|----------|-----|------|------|
| GA/GB/GC | qcflg=对应值+激活标签 | IV=11入库 | IV=11 |
| BH | qcflg=BH | — | OV=9 返修出库 |
| BF | sflg=2, qcflg=BF | OV=7报废出库 | OV=7 |
| TH | qcflg=TH | OV=6退换出库 | OV=6 |
| DJ | qcflg=DJ | 无动作 | — |

### 13.6 关联链

```
OV=5 OT057427 → QC QC260608010(refbillid=OT057427)
  ├─ GA行 → IV=11(refbillid=QC260608010)
  ├─ BF行 → OV=7(refbillid=QC260608010)
  └─ BH行 → OV=9(refbillid=QC260608010)
```

### 13.8 前端页面规划

```
frontend/src/views/qc/
├── QcResultList.vue      # 质检结果列表
├── QcResultInput.vue     # 质检录入主页面
└── components/
    ├── QcSourceSelect.vue    # 来源单据选择
    ├── QcEidSelector.vue     # EID选择/生成组件
    └── QcDetailTable.vue      # 质检明细表格
```

### 13.9 注意事项

1. **IV=11语义**: IV=11是"质检入库"专用类型，区别于IV=8"生产入库"
2. **行级处理**: 质检审核必须按行处理，不能整单统一判定
3. **EID一致性**: 设备行的manuf_seq(原厂序号)和eid(新EID)都要保存
4. **标签激活**: GA/GB/GC合格时自动激活标签(TMM40_LABEL.useflg='0')
5. **溯源链**: 通过ref_inbillid可追溯原始采购入库单和供应商

---

**文档结束**
