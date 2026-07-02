---
类型: 技术文档
阅读状态: 已完成
tags: 技术文档, MES, QC, 仓库, 联动流程
更新日期: 2026-06-07
创建时间: 2026-06-07
---

# MES/QC/仓库联动技术文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | MES/QC/仓库联动技术文档 |
| 版本 | v1.0 |
| 创建日期 | 2026-06-07 |
| 适用系统 | myitsm |
| 相关模块 | MES(生产)、QC(质检)、Warehouse(仓库) |

---

## 1. 系统架构概览

### 1.1 模块关系图

```
┌─────────────────────────────────────────────────────────────┐
│                         业务流程联动                          │
└─────────────────────────────────────────────────────────────┘

    ┌──────────┐         ┌──────────┐         ┌──────────┐
    │   MES    │ ──────→ │   QC     │ ──────→ │ Warehouse│
    │  生产工单 │         │  质检结果  │         │  出入库   │
    └──────────┘         └──────────┘         └──────────┘
         │                      │                      │
         ▼                      ▼                      ▼
    ┌──────────┐         ┌──────────┐         ┌──────────┐
    │TMS01工单 │         │TQC10结果 │         │TWH11库存 │
    │TMS04消耗 │         │TQC11明细 │         │TWH12流水 │
    │TMS03工序 │         │          │         │TWH10单据 │
    └──────────┘         └──────────┘         └──────────┘
```

### 1.2 核心数据表

| 模块 | 主表 | 子表/明细 | 说明 |
|------|------|----------|------|
| **MES** | TMS01_WORK_ORDER | TMS03_WORK_PROCESS | 工单+工序 |
| | | TMS04_MATERIAL_CONSUME | 物料消耗 |
| **QC** | TQC10_RESULT | TQC11_RESULT_DT | 质检结果+明细 |
| | | TQC12_RESULT_EID | 质检设备明细 |
| **Warehouse** | TWH10_INBILL | TWH11_INDETAIL | 入库单+明细 |
| | TWH10_OUTBILL | TWH11_OUTDETAIL | 出库单+明细 |
| | TWH12_STOCKDT | - | 库存流水 |

---

## 2. 业务流程详解

### 2.1 生产→质检→入库 正向流程

```
┌────────────────────────────────────────────────────────────────┐
│  阶段1: 生产工单 (MES)                                           │
├────────────────────────────────────────────────────────────────┤
│  DRAFT → RELEASED → IN_PROGRESS → COMPLETED                    │
│   ↓         ↓           ↓            ↓                         │
│  创建      下达       生产中       完工                          │
│                              ↓                                  │
│                         自动生成 OV=8                          │
│                         (生产出库草稿)                          │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  阶段2: 仓库出库 (Warehouse OV=8)                              │
├────────────────────────────────────────────────────────────────┤
│  OV=8 生产出库审核 → 扣减库存 → 写入 TMS04                     │
│                                                         ↓      │
│                                                  生成 IV=8     │
│                                                  (生产入库)    │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  阶段3: 质检 (QC)                                              │
├────────────────────────────────────────────────────────────────┤
│  来源: IV=8 入库单 → TQC10_RESULT                              │
│                                                         ↓      │
│  质检类型分流:                                                  │
│  ├─ C1(合格) → 自动贴标 + 自动入库                             │
│  ├─ YH(易耗品报废) → OV=7 报废出库                             │
│  ├─ PJ/C2(配件/降级) → BH件返修 OV=9                           │
│  └─ 其他 → 人工处理                                            │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 质检审核联动详细逻辑

```python
# qc_service.py:54-154
class QcService:
    def audit(qcbillid, auditor):
        # 1. 审核前捕获坏件 EID
        bh_eids_pre = []
        for row in eid_rows:
            if EID.qcflg == "BH":  # 坏件
                bh_eids_pre.append({"itemcd": row.itemcd, "eid": row.eid})
        
        # 2. 按质检类型分流处理
        if optyp == "C1":  # 成品合格
            for row in eid_rows:
                EID.update(qcflg="GA")  # 合格
                Label.update(useflg="0")  # 自动激活标签
            StockInService.create(invtyp="8")  # 自动生成入库
            
        elif optyp == "YH":  # 易耗品报废
            for row in eid_rows:
                EID.update(sflg="2", qcflg="BF")  # 报废
            StockOutService.create(invtyp="7")  # OV=7 报废出库
            
        elif optyp in ("PJ", "C2"):  # 配件/降级
            for row in eid_rows:
                EID.update(qcflg="DJ")  # 待检
            if bh_eids_pre:
                StockOutService.create(invtyp="9")  # OV=9 返修出库
```

### 2.3 出入库单据类型映射

| 单据类型 | 代码 | 触发场景 | 自动生成 |
|----------|------|----------|----------|
| **入库单 (IV)** | | | |
| 采购入库 | IV=1 | 采购订单到货 | - |
| 销售退货 | IV=2 | 客户退货 | 关联 OV=1 |
| 调拨入库 | IV=4 | 调拨出库审核 | 关联 OV=3 |
| 返修入库 | IV=9 | 返修完成 | 关联 OV=9 |
| 生产入库 | IV=8 | QC C1 合格 | 关联 QC |
| **出库单 (OV)** | | | |
| 销售出库 | OV=1 | 销售发货 | - |
| 服务领用 | OV=2 | 工程师领料 | - |
| 调拨出库 | OV=3 | 仓库间调拨 | - |
| 借出出库 | OV=4 | 借给客户 | - |
| 质检出库 | OV=5 | 质检取样 | - |
| 翻新出库 | OV=10 | 旧机翻新 | - |
| 生产出库 | OV=8 | 工单领料 | 关联 WO |
| 返修出库 | OV=9 | 坏件返修 | 关联 QC |
| 报废出库 | OV=7 | 质检报废 | 关联 QC |

---

## 3. 数据流详细设计

### 3.1 生产工单→物料消耗 数据流

```
MES: WorkOrderService.create()
    ↓
生成 WO+日期+序号 (WO20240607-001)
    ↓
MES: WorkOrderService.transition(wo_id, "COMPLETED")
    ↓
检查是否存在 OV=8/OV=10
    ├─ 存在 → 跳过
    └─ 不存在 → _create_production_outbound_draft()
        ↓
        查询 TMS04 实际消耗 → 生成 OV=8 明细
        或查询 BOM 展开 → 生成 OV=8 明细
        ↓
StockOutService.create(invtyp="8")
    ↓
Warehouse: 审核 OV=8
    ↓
    ├─ 扣减库存 (TWH11)
    ├─ 写入 TMS04 (实际消耗)
    └─ 生成 IV=8 草稿
```

### 3.2 EID 状态流转图

```
┌──────────┐    OV=4借出     ┌──────────┐
│  sflg=1  │ ──────────────→ │  sflg=6  │
│  在库可用 │                 │  借出中  │
└──────────┘                 └──────────┘
     │                            │
     │ OV=8/OV=10               │ IV=5归还
     │ 生产/翻新领料             │
     ▼                            ▼
┌──────────┐                 ┌──────────┐
│  sflg=7  │                 │  sflg=2  │
│  生产/翻新│                 │  待检   │
└──────────┘                 └──────────┘
     │                            │
     │ QC C1合格                  │ QC质检
     │                            │
     ▼                            ▼
┌──────────┐    OV=9返修      ┌──────────┐
│  sflg=1  │ ←──────────────  │  sflg=3  │
│  qcflg=GA│                  │  qcflg=DJ│
│  合格在库 │                  │  待检   │
└──────────┘                  └──────────┘
     │                            │
     │ OV=7报废                   │ OV=9返修审核
     │                            │
     ▼                            ▼
┌──────────┐                 ┌──────────┐
│  sflg=2  │                 │  sflg=5  │
│  qcflg=BF│                 │  返修中  │
│  已报废  │                 └──────────┘
└──────────┘
```

### 3.3 质检结果与库存联动矩阵

| QC类型 | EID状态变化 | 自动生成单据 | 标签激活 | 备注 |
|--------|------------|-------------|----------|------|
| **C1 合格** | qcflg: ''→'GA' | IV=8 入库单 | ✅ 激活 | 全流程自动 |
| **YH 易耗品** | sflg: ''→'2', qcflg: ''→'BF' | OV=7 报废出库 | ❌ | 直接报废 |
| **PJ 配件** | qcflg: ''→'DJ' | OV=9 返修出库(仅BH) | ❌ | 坏件返修 |
| **C2 降级** | qcflg: ''→'DJ' | OV=9 返修出库(仅BH) | ❌ | 同配件处理 |

---

## 4. API 接口清单

### 4.1 MES 模块 API

| 端点 | 方法 | 功能 | 联动触发 |
|------|------|------|----------|
| `/mes/work-orders` | GET/POST | 工单列表/创建 | - |
| `/mes/work-orders/<id>` | GET/PUT/DELETE | 工单详情/更新/删除 | - |
| `/mes/work-orders/<id>/transition` | POST | 状态流转 | COMPLETED→生成OV=8 |
| `/mes/processes` | GET/POST | 工序定义 | - |
| `/mes/work-processes` | GET/POST/PUT/DELETE | 工单工序 | - |
| `/mes/materials` | GET/POST | 物料消耗 | OV=8审核→写入TMS04 |

### 4.2 QC 模块 API

| 端点 | 方法 | 功能 | 联动触发 |
|------|------|------|----------|
| `/qc/results` | GET/POST | 质检结果列表/创建 | - |
| `/qc/results/<id>` | GET | 质检详情 | - |
| `/qc/results/<id>/audit` | POST | **质检审核** | 自动生成入库/出库 |

### 4.3 Warehouse 模块 API

| 端点 | 方法 | 功能 | 联动触发 |
|------|------|------|----------|
| `/warehouse/stock-in` | GET/POST | 入库单列表/创建 | - |
| `/warehouse/stock-in/<id>/audit` | POST | 入库审核 | 生成关联出库 |
| `/warehouse/stock-out` | GET/POST | 出库单列表/创建 | - |
| `/warehouse/stock-out/<id>/audit` | POST | 出库审核 | 生成关联入库 |
| `/warehouse/stock` | GET | **库存查询** | - |
| `/warehouse/stock-movement` | GET | 库存流水 | - |

---

## 5. 核心业务代码路径

### 5.1 关键服务文件

| 文件路径 | 功能 | 核心方法 |
|----------|------|----------|
| `app/services/mes_service.py` | MES业务逻辑 | WorkOrderService.transition() |
| `app/services/qc_service.py` | QC业务逻辑 | QcService.audit() |
| `app/services/warehouse_service.py` | 仓库业务逻辑 | StockInService.audit(), StockOutService.audit() |
| `app/repositories/mes_repository.py` | MES数据访问 | - |
| `app/repositories/qc_repository.py` | QC数据访问 | - |
| `app/repositories/warehouse_repository.py` | 仓库数据访问 | - |

### 5.2 联动触发点

```
触发点1: MES工单完工
文件: app/services/mes_service.py:132
方法: WorkOrderService.transition() → target="COMPLETED"
动作: _create_production_outbound_draft() → StockOutService.create(invtyp="8")

触发点2: QC C1合格审核
文件: app/services/qc_service.py:97-125
方法: QcService.audit() → optyp="C1"
动作: 
  - EID.update(qcflg="GA")
  - Label.update(useflg="0")
  - StockInService.create(invtyp="8")

触发点3: QC YH报废审核
文件: app/services/qc_service.py:85-90, 142-146
方法: QcService.audit() → optyp="YH"
动作: 
  - EID.update(sflg="2", qcflg="BF")
  - StockOutService.create(invtyp="7")

触发点4: QC PJ/C2返修审核
文件: app/services/qc_service.py:74-82, 147-151
方法: QcService.audit() → optyp in ("PJ", "C2")
动作: 
  - 审核前捕获BH EID (bh_eids_pre)
  - EID.update(qcflg="DJ")
  - StockOutService.create(invtyp="9", details_eid=bh_eids_pre)

触发点5: 仓库出库审核自动生成入库
文件: app/services/warehouse_service.py:850-980
方法: StockOutService.audit()
动作:
  OV=3调拨 → 生成 IV=4
  OV=9返修 → 生成 IV=9
  OV=1销售 → 生成 IV=2
```

---

## 6. 异常处理与边界情况

### 6.1 幂等性设计

| 场景 | 处理方式 | 实现 |
|------|----------|------|
| 重复生成OV=8 | 去重检查 | mes_service.py:135-141 检查已存在OV=8/OV=10 |
| 重复审核 | 状态检查 | qc_service.py:65-66 auditflg=="1"拒绝 |
| 重复入库 | 唯一索引 | 数据库层TWH10.inbillid唯一 |

### 6.2 错误处理

| 错误类型 | 处理方式 | 返回信息 |
|----------|----------|----------|
| 工单不存在 | 提前返回 | `{"success": False, "error": "工单不存在"}` |
| 状态不允许流转 | 状态机校验 | `{"success": False, "error": "不允许从X流转到Y"}` |
| 库存不足 | 事务回滚 | `raise ValueError("库存不足")` |
| 标签不存在 | 静默跳过 | `if label: label.useflg = "0"` |

---

## 7. 数据一致性保障

### 7.1 事务边界

```python
# 所有联动操作在同一个事务中
from app.extensions import db

def audit():
    try:
        # 1. 更新QC状态
        QcRepository.audit(qc, auditor)
        
        # 2. 更新EID状态
        db.session.query(EidModel).filter(...).update(...)
        
        # 3. 激活标签
        label.useflg = "0"
        
        # 4. 创建入库单
        StockInService.create(..., _commit=False)
        
        # 统一提交
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
```

### 7.2 补偿机制

| 场景 | 补偿策略 |
|------|----------|
| 自动生成单据失败 | 记录日志，不影响主流程状态 |
| 标签激活失败 | 独立事务，失败不阻断审核 |
| 库存更新失败 | 整体回滚，保持数据一致性 |

---

## 8. 性能优化

### 8.1 批量操作

```python
# EID状态批量更新（避免N+1）
db.session.query(EidModel).filter(
    EidModel.eid.in_([r.eid for r in eid_rows])
).update({"qcflg": "GA"}, synchronize_session=False)
```

### 8.2 查询优化

| 优化点 | 实现 | 效果 |
|--------|------|------|
| 仓库名称缓存 | _enrich_warehouse_names() | 批量查询，减少N+1 |
| 物料名称缓存 | _enrich_item_names() | 批量查询IN语句 |
| 分页查询 | 所有list接口 | 避免大数据量查询 |

---

## 9. 扩展性设计

### 9.1 新增质检类型

如需新增QC类型，只需在 `qc_service.py:audit()` 添加分支：

```python
elif optyp == "NEW_TYPE":
    # 自定义EID状态更新
    # 自定义仓库联动逻辑
    pass
```

### 9.2 新增自动联动

参考 `_create_production_outbound_draft()` 模式：
1. 去重检查（避免重复生成）
2. 构建明细数据
3. 调用 StockOutService.create() 或 StockInService.create()
4. 异常捕获（失败不影响主流程）

---

## 10. 附录

### 10.1 状态码定义

| 状态码 | 含义 | 适用对象 |
|--------|------|----------|
| **工单状态** | | |
| DRAFT | 草稿 | WorkOrder |
| RELEASED | 已下达 | WorkOrder |
| IN_PROGRESS | 生产中 | WorkOrder |
| COMPLETED | 已完工 | WorkOrder |
| CANCELLED | 已取消 | WorkOrder |
| **EID状态(sflg)** | | |
| 1 | 在库可用 | EID |
| 2 | 待检/报废 | EID |
| 3 | 翻新待检 | EID |
| 5 | 返修中 | EID |
| 6 | 借出中 | EID |
| 7 | 生产/翻新中 | EID |
| **质检标志(qcflg)** | | |
| GA | 合格 | EID |
| DJ | 待检 | EID |
| BF | 报废 | EID |
| BH | 坏件 | EID |

### 10.2 单据类型编码

| 代码 | 类型 | 方向 |
|------|------|------|
| IV=1 | 采购入库 | 入库 |
| IV=2 | 销售退货 | 入库 |
| IV=4 | 调拨入库 | 入库 |
| IV=8 | 生产入库 | 入库 |
| IV=9 | 返修入库 | 入库 |
| OV=1 | 销售出库 | 出库 |
| OV=2 | 服务领用 | 出库 |
| OV=3 | 调拨出库 | 出库 |
| OV=4 | 借出出库 | 出库 |
| OV=7 | 报废出库 | 出库 |
| OV=8 | 生产出库 | 出库 |
| OV=9 | 返修出库 | 出库 |
| OV=10 | 翻新出库 | 出库 |

---

---

## 11. 最新更新（2026-06-07）

### 11.1 新增功能

| 功能 | 位置 | 说明 |
|------|------|------|
| QC C1 自动贴标 | `qc_service.py:audit` | C1审核→TMM40_LABEL.useflg='0'+gendate更新 |
| BH→OV=9 返修出库 | `qc_service.py:audit` | PJ/C2审核前捕获BH EID→自动生成OV=9草稿 |
| IV=6 ref_eid 溯源 | `warehouse_service.py:524-539` | 翻新入库新EID写ref_eid=旧EID |
| OV=8 skip_iv8 | `warehouse_service.py:1093-1118` | QC C1已存在时OV=8不重复生成IV=8 |
| TMS04 累加去重 | `StockOutService._write_material_consume` | 同物料多次出库累加actual_qty |
| 工单/工序删除 | `mes_service.py` | DRAFT/PENDING 可删 |
| 工单类型 wo_type | `tms01_work_order.wo_type` | PRODUCTION/RENOVATION |
| 标签 PB 编码规则 | `inventory.py:generate_labels` | classcd+YY+月后缀+序号 / YYYYMMDD+sign+序号 |
| 库存预警 | `StockBalance.vue` | 红色高亮+仅看预警 |
| 报表导出 .xlsx | `StockReports.vue` | 收发存/日报/库龄导出 |

### 11.2 QC 审核分流（完整版）

```
QcService.audit(optyp)
├── C1(成品合格) → qcflg='GA' + 自动IV=8 + 标签激活(TMM40.useflg='0')
├── PJ/C2(配件)  → qcflg='DJ'
│     └── 审核前qcflg=BH → 自动OV=9返修出库
├── YH(易耗品)   → sflg='2', qcflg='BF' + 自动OV=7报废出库
└── EID状态更新后 → 自动创建对应出库单(取EID当前仓库)
```

### 11.3 IV=8 双来源去重

```
OV=8审核 → 检测工单是否有QC C1审核
  ├── 有 → skip_iv8=True（QC已生成IV=8）
  └── 无 → OV=8生成IV=8（简化确认模式）
```

文档结束

### 11.4 Bug 修复记录（来自 2026-06-04 汇总）

| 问题 | 修复 |
|------|------|
| 入库日期 NULL 导致日期筛选遗漏 | `setdefault("indate"/"outdate", now)` |
| 返修入库选择器 union_all 列名丢失 | Python侧聚合 |
| EID 管理页 sflg/qcflg 显示编码 | ST→ES, QS→QC |
| OV=9 EID 状态未写入(details_eid遗漏) | 补 elif invtyp=="9" |
| _enrich_item_names 3列 dict 转换错误 | 手动构建 |
| 出库明细 prddate Schema 缺失 | StockOutDetailCreate 加字段 |
| find_lendable_orders N+1 查询 | 子查询预聚合 |
| IV=9 审核激活所有出库EID | 仅激活入库明细中有的 |
| per_page=500 超 Schema 限制 | 改回 100 |
| 采购入库 itemtyp/prddate 为空 | create+audit双路径默认值 |
| 序列冲突 | TWH11/TWH12 序列修正 |
| HG→GA 字典修正 | 6处替换 |
| 工单完工去重 | transition去重+update移除触发 |
| TMS04重复写入 | 抽取_write_material_consume |
| BH→OV=9找不坏件 | 审核前捕获bh_eids_pre |

文档结束
