# F3 配套增强模块前端设计

> **Status**: 待实施 | **创建**: 2026-05-15 | **分支**: `feature/f3-enhanced-modules`

**Goal**: 在 F2 业务主链完成后，按业务流程链补全配套模块，打通"报修→处理→SLA监控→通知→合同→财务"完整闭环。

**Tech Stack**: Vue 3 + Element Plus + TypeScript + Vite（同 F1/F2）

---

## 1. 推进顺序（按业务流程链）

```
F2 终点（ITSM 工单完成）
  ↓
F3.1 门户+SLA+通知（1.5周） — 报修→处理→监控→反馈 闭环
  ↓
F3.2 合同+发票+结算+财务（1.5周） — 业务→财务 最后一公里
  ↓
F3.3 押金+资产属性（1周）
  ↓
F3.4 考勤+预警/价格（0.5周）
  ↓
F3.5 MES+IoT+调拨+报表（1.5周）
  ↓
F3.6 全局搜索+通用组件（收尾）
```

## 2. 后端 API 就绪情况

全部 12 个蓝图已实现，F3 零后端工作量：

| 蓝图 | 端点 | 说明 |
|------|------|------|
| portal | 10 | 门户用户/自助报修/服务评价 |
| sla | 9 | SLA定义/工单监控 |
| notification | 7 | 通知模板/发送记录 |
| contract | 8 | 合同管理 |
| billing | 12 | 结算规则/账单 |
| finance | 18 | 科目/应收/应付/收付款/折旧 |
| deposit | 9 | 押金管理 |
| attendance | 3 | 考勤 |
| inventory | 9 | 预警/价格 |
| mes | 12 | 生产工单/工序 |
| iot | 11 | 设备接入/数据/报警 |
| reports | 8 | 库存/EID/销售/BOM报表 |

## 3. 模块蓝图与页面

### F3.1 客户门户 + SLA + 通知（~9页）

| 页面 | 路由 | API |
|------|------|-----|
| PortalUserList | `/portal/users` | portal |
| RepairRequestList（自助报修） | `/portal/repairs` | portal |
| ServiceRatingList | `/portal/ratings` | portal |
| SlaDefinitionList | `/sla/definitions` | sla |
| SlaTicketList（SLA监控） | `/sla/tickets` | sla |
| NotificationTemplateList | `/notification/templates` | notification |
| NotificationList | `/notification/notifications` | notification |

> **话务台增强**（F2已有 CallConsole.vue 占位）：报修接收 + 转派给不同部门（技术部/实施部）+ 关单确认。调用 F2 已有 `/itsm/maintenance-daily/<id>/transition` 分派 API。

### F3.2 合同 + 发票 + 结算 + 财务（~9页）

| 页面 | 路由 | API |
|------|------|-----|
| ContractList | `/contract/contracts` | contract |
| InvoiceList | `/contract/invoices` | contract |
| BillingRuleList | `/billing/rules` | billing |
| BillList（账单管理） | `/billing/bills` | billing |
| AccountList（会计科目） | `/finance/accounts` | finance |
| ReceivableList（应收） | `/finance/receivables` | finance |
| PayableList（应付） | `/finance/payables` | finance |
| PaymentList（收付款） | `/finance/payments` | finance |
| DepreciationList（折旧） | `/finance/depreciations` | finance |

### F3.3 保养计划 + 押金 + 资产属性（~7页）

| 页面 | 路由 | API |
|------|------|-----|
| MaintenancePlanList（保养计划 CRUD） | `/itsm/maintenance-plans` | itsm |
| MaintenanceList（保养工单） | `/itsm/maintenance` | itsm |
| DepositList | `/deposit/deposits` | deposit |
| DepositDetailList | `/deposit/details` | deposit |
| DepositIOList | `/deposit/io` | deposit |
| AssetAttribList（资产属性扩展） | `/master/asset-attrib` | system |

### F3.4 考勤 + 预警/价格（~5页）

| 页面 | 路由 | API |
|------|------|-----|
| AttendanceList | `/attendance/records` | attendance |
| AttendanceCountList | `/attendance/summary` | attendance |
| InventoryLimitList | `/inventory/limits` | inventory |
| PriceList | `/inventory/prices` | inventory |
| AdjustPriceList（调价记录） | `/inventory/adjust-prices` | inventory |

### F3.5 MES + IoT + 调拨 + 报表（~10页）

| 页面 | 路由 | API |
|------|------|-----|
| WorkOrderList | `/mes/work-orders` | mes |
| ProcessDefList | `/mes/processes` | mes |
| WorkProcessList | `/mes/work-processes` | mes |
| MaterialConsumeList | `/mes/materials` | mes |
| DeviceConnList | `/iot/connections` | iot |
| DeviceDataList | `/iot/data` | iot |
| AlertRuleList | `/iot/alert-rules` | iot |
| AlertLogList | `/iot/alerts` | iot |
| TransferAccountList | `/system/transfers` | system |
| ReportCenter | `/reports/center` | reports |

### F3.6 全局搜索 + 通用组件

| 功能 | 说明 |
|------|------|
| 全局搜索 | Ctrl+K 唤起，搜索客户/工单/物料/EID |
| 通用组件提取 | AuditButton, StatusTransition, 列表/表单模式 |

## 4. 复用 F2 基础

- `useListPage<T>()` composable — 列表页零重复
- `useDetailDrawer<T>()` composable — 详情弹窗统一
- 单行模板格式 — 避免 Vite 编译问题
- 管理员自动权限 — 加菜单即可

## 5. 验收标准

- [ ] 所有页面列表+分页+搜索可用
- [ ] 核心页面含详情弹窗
- [ ] TypeScript 编译通过
- [ ] 菜单/路由/权限完整
- [ ] 管理员自动全部权限
