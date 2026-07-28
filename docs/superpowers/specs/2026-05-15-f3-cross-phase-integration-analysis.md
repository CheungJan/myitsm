# F3 跨阶段联动分析

> **创建**: 2026-05-15 | **目的**: 逐模块识别 F3 与 F1/F2 的联动需求，列出具体字段级改动

---

## 总览

F3 40 个页面中有 **12 个场景** 需要对 F1/F2 已有页面或后端进行联动修改。按优先级分为三级：

| 级别 | 含义 | 数量 |
|------|------|------|
| P0 阻塞 | F3 页面依赖此改动，不做无法工作 | 4 |
| P1 重要 | 业务流程闭环必需 | 5 |
| P2 增强 | 锦上添花，可后续迭代 | 3 |

---

## P0 阻塞级联动（F3 实施前必须完成）

### L1: 预计划表单缺少押金/租赁/机型字段

**影响**: F3.3 押金模块无法与预计划联动

**当前状态:**

| 层 | 现状 |
|----|------|
| DB `plan_cust` | `deposit` (Numeric), `is_rent` (String(1)), `yun_type` (String(2)), `pos_item` (String(6)) — **全部有值** |
| `PlanCustCreate` Schema | 仅 9 字段，**缺失** `deposit`, `yun_type`, `custcard`, `classcd`, `pos_item` 等；`is_rent` 仅在 Create 有 |
| `PlanCustUpdate` Schema | 仅 7 字段（全是状态类），**缺失** `deposit`, `is_rent`, `yun_type` |
| PlanList.vue 表格 | 11 列，**无** 押金/租赁/机型/运营类型 列 |
| PlanList.vue 表单 | 10 字段，**无** deposit/is_rent/yun_type/pos_item 输入 |

**需要的改动:**

```
后端:
  app/schemas/sales.py:
    PlanCustCreate +: is_rent, deposit, yun_type, pos_item, custcard, custrnm
    PlanCustUpdate +: is_rent, deposit, yun_type, pos_item

前端:
  frontend/src/views/sales/PlanList.vue:
    表格 +: is_rent (是否租赁 tag), deposit (押金金额), pos_item (机型)
    表单 +: is_rent (el-switch 或 el-radio), deposit (el-input-number),
            pos_item (el-select 关联物料), yun_type (el-select)
```

**工作量**: 后端 0.5h + 前端 1h = 1.5h

---

### L2: 保养计划/保养工单 API 缺失

**影响**: F3.3 MaintenancePlanList + MaintenanceList 两个页面无数据源

**当前状态:**

| 层 | 现状 |
|----|------|
| DB 模型 | `MaintenancePlan` (TIT17_PLAN) + `Maintenance` (TIT17) — **模型存在** |
| API 端点 | **不存在** — itsm blueprint 未暴露这两个模型 |
| Pydantic Schema | **不存在** |
| Service | **不存在** |

**需要的改动:**

```
后端（新增）:
  app/schemas/itsm.py +: MaintenancePlanCreate, MaintenancePlanUpdate, MaintenanceCreate
  app/services/itsm_service.py +: list_plans, create_plan, update_plan, list_maintenance
  app/api/itsm.py +:
    GET/POST /maintenance-plans
    GET/PUT /maintenance-plans/<id>
    GET /maintenance (TIT17 保养工单列表)

前端:
  新建 frontend/src/api/itsm.ts +: fetchMaintenancePlans, fetchMaintenance (TIT17)
  新建 frontend/src/views/itsm/MaintenancePlanList.vue
  新建 frontend/src/views/itsm/MaintenanceList.vue (TIT17)
```

**工作量**: 后端 2h + 前端 1h = 3h

---

### L3: DepositIO API 缺失

**影响**: F3.3 DepositIOList 页面无数据源

**当前状态:**

| 层 | 现状 |
|----|------|
| DB 模型 | `DepositIO` — **模型存在** |
| API 端点 | **不存在** |
| Pydantic Schema | **不存在** |

**需要的改动:**

```
后端（新增）:
  app/schemas/deposit.py +: DepositIOCreate
  app/services/deposit_service.py +: list_io, create_io
  app/api/deposit.py +: GET /deposits/io, POST /deposits/io

前端:
  新建 frontend/src/views/deposit/DepositIOList.vue
```

**工作量**: 后端 1h + 前端 0.5h = 1.5h

---

### L4: TransferAccount API 缺失

**影响**: F3.5 TransferAccountList 页面无数据源

**当前状态:**

| 层 | 现状 |
|----|------|
| DB 模型 | `TransferAccount` (TTX01_TXKMG) — **模型存在** |
| API 端点 | **不存在** |

**需要的改动:**

```
后端: 新增 CRUD Schema + Service + API 端点
前端: 新建 TransferAccountList.vue
```

**工作量**: 后端 1.5h + 前端 0.5h = 2h

---

## P1 重要级联动（业务流程闭环）

### L5: 话务台转派增强（报修→工单→SLA→通知链）

**影响**: F3.1 CallConsole 需实现完整的报修受理→转派→关单流程

**当前状态:**

| 文件 | 现状 |
|------|------|
| `CallConsole.vue` | 占位页面，只有标题文字 |
| 后端转派 API | `POST /itsm/maintenance-daily/<id>/transition` — **已存在** |
| 后端 SLA 绑定 | `POST /sla/tickets/attach` — **已存在** |
| 后端通知发送 | `POST /notification/notifications/<id>/send` — **已存在** |

**需要的改动:**

```
前端重写 CallConsole.vue:
  - 客户电话查询 → 调 fetchMaintenanceDaily({phone: xxx})
  - 工单列表（复用 useListPage）
  - 转派操作: POST /itsm/maintenance-daily/<id>/transition {to_status, remark}
  - SLA 绑定: 创建工单后 POST /sla/tickets/attach
  - 通知推送: 状态变更后 POST /notification/notifications/<id>/send
  - 关单确认: transition to_status=3
```

**工作量**: 前端 3h

---

### L6: 维修工单状态流转打通

**影响**: F3.1 MaintenanceList 详情弹窗缺少状态操作按钮

**当前状态:**

| 层 | 现状 |
|----|------|
| MaintenanceList.vue 详情 | 只读 el-descriptions，**无** 状态流转操作 |
| 后端 transition API | 5 个工单类型都有 `/transition` 端点 ✅ |
| SLA ticket API | `POST /sla/tickets/response`, `/resolve` — **已存在** |

**需要的改动:**

```
frontend/src/views/itsm/MaintenanceList.vue:
  详情弹窗 +: 状态流转按钮组
    - "分派" → transition {to_status:"1", remark:"分派给xxx"}
    - "开始维修" → transition {to_status:"2"} + POST sla/response
    - "关单" → transition {to_status:"3"} + POST sla/resolve

新增组件（可选，F3.6 提取）:
  frontend/src/components/common/StatusTransition.vue
```

**工作量**: 前端 2h

---

### L7: 合同→发票→预计划关联链

**影响**: F3.2 合同模块需要与 F2 预计划的 `is_contract` 字段联动

**当前状态:**

| 层 | 现状 |
|----|------|
| PlanCust.is_contract | DB 有值，前端 PlanList 显示"是/否" tag |
| Contract.htbh | 合同编号，Invoice.htbh 外键关联 ✅ |
| 预计划关联合同 | PlanCust 无 `htbh` 字段，无法直接关联 |

**需要的改动:**

```
前端:
  ContractList.vue: 详情中显示关联的预计划列表（通过客户编码匹配）
  PlanList.vue: 详情中显示关联的合同信息（通过客户编码匹配）

注: 数据库层面 PlanCust 无 htbh 外键，短期通过 custcd 间接关联即可
```

**工作量**: 前端 2h

---

### L8: 应收应付与合同/账单/发票关联

**影响**: F3.2 财务模块需要在详情中展示关联的上游单据

**当前状态:**

| 模型 | 关联字段 |
|------|---------|
| Receivable | `bill_id`, `fpbh` (发票编号), `htbh` (合同编号) — **都有** ✅ |
| Payable | `po_id` (采购单号) — **有** ✅ |
| Payment | `ref_id` (关联应收/应付编号) — **有** ✅ |

**前端改动:**

```
ReceivableList.vue: 详情 +: 关联账单、发票、合同的可点击链接
PayableList.vue: 详情 +: 关联采购单的可点击链接
PaymentList.vue: 详情 +: 关联应收/应付编号
```

**工作量**: 前端 1.5h

---

### L9: MES 生产与仓储库存联动

**影响**: F3.5 MES 工单物料消耗需扣减库存

**当前状态:**

| 模型 | 关联字段 |
|------|---------|
| WorkOrder | `warehouse_cd` — **有** ✅ |
| MaterialConsume | `warehouse_cd`, `item_cd` — **有** ✅ |

**注**: 库存扣减逻辑是后端 Service 层的事，前端只需在物料消耗页面提供关联仓库的选择器。当前 MaterialConsumeCreate Schema 已包含 `warehouse_cd`。

**前端改动:**

```
MaterialConsumeList.vue: 列 +: warehouse_cd, 详情 +: 物料名称（JOIN item）
```

**工作量**: 前端 0.5h

---

## P2 增强级联动（可后续迭代）

### L10: IoT 设备与资产台账联动

**影响**: F3.5 DeviceConn/DeviceData 页面可展示资产信息

**当前状态:** DeviceConn.eid → 可通过 `fetchAssets({eid: xxx})` 查到资产信息

**前端改动:**

```
DeviceConnList.vue: 详情 +: 关联资产信息（客户/仓库/型号）
DeviceDataList.vue: 列 +: item_nm (JOIN eid → item)
```

**工作量**: 前端 1h

---

### L11: 全局搜索跨模块索引

**影响**: F3.6 全局搜索需检索所有 F1/F2/F3 模块

**需要的改动:**

```
前端 GlobalSearch.vue 搜索数据源:
  - 客户: GET /customers?search=xxx
  - 工单: GET /itsm/maintenance-daily?maintenance_id=xxx
  - 物料: GET /items?search=xxx
  - 设备: GET /eid?search=xxx
  - F3 新增: 合同/发票/账单/押金
```

**工作量**: 前端 2h

---

### L12: 报表中心数据聚合

**影响**: F3.5 ReportCenter 需要图表展示

**当前状态:** 后端 8 个 report 端点已存在 ✅

**前端改动:**

```
新建 ReportCenter.vue:
  - ECharts 图表（库存快照、EID 生命周期、销售状态汇总）
  - 报表导出按钮（复用 ExportButton 组件）
```

**工作量**: 前端 3h + npm install echarts

---

## 汇总

### 必须完成的 P0 后端工作（"零后端工作量"不成立）

| # | 内容 | 文件 | 工时 |
|---|------|------|------|
| L1 | PlanCustCreate/Update Schema 扩展 | `app/schemas/sales.py` | 0.5h |
| L2 | 保养计划/保养工单 API + Schema + Service | `app/schemas/itsm.py`, `app/api/itsm.py`, `app/services/itsm_service.py` | 2h |
| L3 | DepositIO API + Schema | `app/schemas/deposit.py`, `app/api/deposit.py` | 1h |
| L4 | TransferAccount API + Schema | 新建 schema + api 端点 | 1.5h |
| **合计** | | | **5h** |

### 必须完成的 P0 前端改动

| # | 内容 | 文件 | 工时 |
|---|------|------|------|
| L1 | PlanList 表单/表格扩展 | `PlanList.vue` | 1h |
| L5 | CallConsole 重写 | `CallConsole.vue` | 3h |
| L6 | MaintenanceList 状态流转 | `MaintenanceList.vue` | 2h |
| **合计** | | | **6h** |

### 建议的 F3 实施顺序调整

原计划 F3.1→F3.2→F3.3→F3.4→F3.5→F3.6，建议调整为：

```
Task 0: P0 阻塞项修复（5h 后端 + 6h 前端 = 1.5天）
  ├── L1: PlanCust Schema + PlanList 表单扩展
  ├── L2: 保养计划 API
  ├── L3: DepositIO API
  └── L4: TransferAccount API

Task 1: F3.1 门户+SLA+通知（原计划，加入 L5+L6）
Task 2: F3.2 合同+财务（原计划，加入 L7+L8）
Task 3: F3.3 押金+保养（原计划，已依赖 L1+L2+L3）
Task 4: F3.4 考勤+价格（原计划）
Task 5: F3.5 MES+IoT+报表（原计划，加入 L9+L10+L12）
Task 6: F3.6 全局搜索（原计划，加入 L11）
```

---

## 验收标准

- [ ] PlanList.vue 表单可输入 is_rent（租赁/购买）、deposit（押金金额）、pos_item（机型）
- [ ] 保养计划 CRUD API 可用（GET/POST/PUT /itsm/maintenance-plans）
- [ ] DepositIO 列表 API 可用（GET /deposits/io）
- [ ] CallConsole 可查询工单→转派→关单
- [ ] MaintenanceList 详情可执行状态流转
- [ ] 所有新 API 有对应 Pydantic Schema 校验
