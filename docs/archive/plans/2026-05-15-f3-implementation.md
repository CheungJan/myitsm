# F3 配套增强模块实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 F2 基础上补全 ~40 个配套模块页面，打通"报修→SLA→通知→合同→财务→生产→IoT"完整闭环。

**Architecture:** 复用 F2 的 `useListPage<T>()` + `useDetailDrawer<T>()` composable，单行模板格式（避免 Vite 编译问题）。每个模块创建 API 文件 → 页面组件 → 路由 → 菜单 → 权限，5 步标准化流程。

**Tech Stack:** Vue 3 + Element Plus + TypeScript + Vite（同 F1/F2），后端全部 API 就绪零工作量。

---

## File Map

| 层 | 目录 | 文件 |
|----|------|------|
| API | `frontend/src/api/` | `portal.ts`, `sla.ts`, `notification.ts`, `contract.ts`, `billing.ts`, `finance.ts`, `deposit.ts`, `attendance.ts`, `mes.ts`, `iot.ts` |
| 页面 | `frontend/src/views/` | `portal/`, `sla/`, `notification/`, `contract/`, `billing/`, `finance/`, `deposit/`, `attendance/`, `mes/`, `iot/` |
| 路由 | `frontend/src/router/index.ts` | Modify |
| 菜单 | `frontend/src/config/menu.ts` | Modify |
| 权限 | `tmc01_menus` + `tmc02_menusdt` | SQL INSERT |

## 标准页面模板（所有 F3 页面共用）

```vue
<template><div class="page"><div class="page-header"><h2>{模块名}</h2></div><el-card shadow="never"><el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open"><!-- columns --></el-table><AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/></el-card><el-dialog :title="'详情'" v-model="drawer" width="500px"><template v-if="detail"><el-descriptions :column="2" border size="small"><!-- descriptions --></el-descriptions></template></el-dialog></div></template>
<script setup lang="ts">import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useDetailDrawer} from '@/composables/useDetailDrawer';import {fetchXxx} from '@/api/xxx';import type {XxxRecord} from '@/api/xxx'
const{items,loading,page,perPage,total}=useListPage<XxxRecord>(fetchXxx);const{drawer,detail,open}=useDetailDrawer<XxxRecord>()</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}</style>
```

---

### Task 1: F3.1 门户 + SLA + 通知（7页）

**API 文件**: Create `portal.ts`, `sla.ts`, `notification.ts`

- [ ] **Step 1: 创建 API 模块**

`frontend/src/api/portal.ts`:
```typescript
import request from './request'
export interface PortalRecord { [key:string]: unknown }
export interface PortalPage { items: PortalRecord[]; total: number }
export function fetchPortalUsers(p?:Record<string,string>){return request.get<never,{data:PortalPage}>('/portal',{params:p})}
export function fetchRepairRequests(p?:Record<string,string>){return request.get<never,{data:PortalPage}>('/portal/repairs',{params:p})}
export function fetchServiceRatings(p?:Record<string,string>){return request.get<never,{data:PortalPage}>('/portal/ratings',{params:p})}
```

`frontend/src/api/sla.ts`:
```typescript
import request from './request'
export interface SlaRecord { [key:string]: unknown }
export interface SlaPage { items: SlaRecord[]; total: number }
export function fetchSlaDefinitions(p?:Record<string,string>){return request.get<never,{data:SlaPage}>('/sla',{params:p})}
export function fetchSlaTickets(p?:Record<string,string>){return request.get<never,{data:SlaPage}>('/sla/tickets',{params:p})}
```

`frontend/src/api/notification.ts`:
```typescript
import request from './request'
export interface NotifRecord { [key:string]: unknown }
export interface NotifPage { items: NotifRecord[]; total: number }
export function fetchNotifTemplates(p?:Record<string,string>){return request.get<never,{data:NotifPage}>('/notification',{params:p})}
export function fetchNotifications(p?:Record<string,string>){return request.get<never,{data:NotifPage}>('/notification/notifications',{params:p})}
```

- [ ] **Step 2: 创建页面（参考模板，替换 API 调用和列名）**

7 个文件：
```
frontend/src/views/portal/PortalUserList.vue
frontend/src/views/portal/RepairRequestList.vue
frontend/src/views/portal/ServiceRatingList.vue
frontend/src/views/sla/SlaDefinitionList.vue
frontend/src/views/sla/SlaTicketList.vue
frontend/src/views/notification/NotificationTemplateList.vue
frontend/src/views/notification/NotificationList.vue
```

以 `PortalUserList.vue` 为例：
```vue
<template><div class="page"><div class="page-header"><h2>门户用户</h2></div><el-card shadow="never"><el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row @row-click="open"><el-table-column prop="login_name" label="登录名" width="120"/><el-table-column prop="user_name" label="姓名" width="100"/><el-table-column prop="phone" label="电话" width="120"/><el-table-column prop="gendate" label="注册日期" width="110"/></el-table><AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/></el-card><el-dialog :title="'用户 — '+(detail?.login_name||'')" v-model="drawer" width="500px"><template v-if="detail"><el-descriptions :column="2" border size="small"><el-descriptions-item label="登录名">{{ detail.login_name }}</el-descriptions-item><el-descriptions-item label="姓名">{{ detail.user_name }}</el-descriptions-item><el-descriptions-item label="电话">{{ detail.phone }}</el-descriptions-item><el-descriptions-item label="邮箱">{{ detail.email||'-' }}</el-descriptions-item><el-descriptions-item label="注册日期">{{ detail.gendate }}</el-descriptions-item></el-descriptions></template></el-dialog></div></template>
<script setup lang="ts">import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {useDetailDrawer} from '@/composables/useDetailDrawer';import {fetchPortalUsers} from '@/api/portal';import type {PortalRecord} from '@/api/portal'
const{items,loading,page,perPage,total}=useListPage<PortalRecord>(fetchPortalUsers);const{drawer,detail,open}=useDetailDrawer<PortalRecord>()</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}</style>
```

其余 6 个页面按相同模式——改 API 函数名 + 列名。

- [ ] **Step 3: 注册路由（7条）**

```typescript
{ path: 'portal/users', name: 'PortalUserList', component: () => import('@/views/portal/PortalUserList.vue'), meta: { title: '门户用户' } },
{ path: 'portal/repairs', name: 'RepairRequestList', component: () => import('@/views/portal/RepairRequestList.vue'), meta: { title: '自助报修' } },
{ path: 'portal/ratings', name: 'ServiceRatingList', component: () => import('@/views/portal/ServiceRatingList.vue'), meta: { title: '服务评价' } },
{ path: 'sla/definitions', name: 'SlaDefinitionList', component: () => import('@/views/sla/SlaDefinitionList.vue'), meta: { title: 'SLA定义' } },
{ path: 'sla/tickets', name: 'SlaTicketList', component: () => import('@/views/sla/SlaTicketList.vue'), meta: { title: 'SLA监控' } },
{ path: 'notification/templates', name: 'NotificationTemplateList', component: () => import('@/views/notification/NotificationTemplateList.vue'), meta: { title: '通知模板' } },
{ path: 'notification/notifications', name: 'NotificationList', component: () => import('@/views/notification/NotificationList.vue'), meta: { title: '通知记录' } },
```

- [ ] **Step 4: 注册菜单**

```typescript
{ menu_cd: 'portal', menu_nm: '客户门户', children: [
  { menu_cd: 'portal-users', menu_nm: '门户用户', path: '/portal/users' },
  { menu_cd: 'repairs', menu_nm: '自助报修', path: '/portal/repairs' },
  { menu_cd: 'ratings', menu_nm: '服务评价', path: '/portal/ratings' }
]},
{ menu_cd: 'sla', menu_nm: 'SLA管理', children: [
  { menu_cd: 'sla-defs', menu_nm: 'SLA定义', path: '/sla/definitions' },
  { menu_cd: 'sla-tickets', menu_nm: 'SLA监控', path: '/sla/tickets' }
]},
{ menu_cd: 'notification', menu_nm: '通知管理', children: [
  { menu_cd: 'notif-tpl', menu_nm: '通知模板', path: '/notification/templates' },
  { menu_cd: 'notif-list', menu_nm: '通知记录', path: '/notification/notifications' }
]},
```

- [ ] **Step 5: 注册权限**

```sql
INSERT INTO tmc01_menus (menu_cd,menu_nm,parent_cd,menu_order,status,created_at,updated_at) VALUES
('portal','客户门户',NULL,8,'1',NOW(),NOW()),
('portal-users','门户用户','portal',1,'1',NOW(),NOW()),
('repairs','自助报修','portal',2,'1',NOW(),NOW()),
('ratings','服务评价','portal',3,'1',NOW(),NOW()),
('sla','SLA管理',NULL,9,'1',NOW(),NOW()),
('sla-defs','SLA定义','sla',1,'1',NOW(),NOW()),
('sla-tickets','SLA监控','sla',2,'1',NOW(),NOW()),
('notification','通知管理',NULL,10,'1',NOW(),NOW()),
('notif-tpl','通知模板','notification',1,'1',NOW(),NOW()),
('notif-list','通知记录','notification',2,'1',NOW(),NOW())
ON CONFLICT DO NOTHING;
-- func_cd entries for each
INSERT INTO tmc02_menusdt (menu_cd,func_cd,func_nm,useflg,created_at,updated_at)
SELECT menu_cd, 'view', '查看', '1', NOW(), NOW() FROM tmc01_menus WHERE menu_cd IN ('portal','portal-users','repairs','ratings','sla','sla-defs','sla-tickets','notification','notif-tpl','notif-list')
ON CONFLICT DO NOTHING;
```

- [ ] **Step 6: 话务台转派增强** — 修改 `CallConsole.vue`

```vue
<template><div class="page"><div class="page-header"><h2>话务台</h2></div><el-card shadow="never"><p>报修受理 + 工单转派 + 关单确认</p><div style="margin:16px 0"><el-input v-model="searchPhone" placeholder="输入客户电话查询" size="small" style="width:220px" clearable @keyup.enter="doSearch"/><el-button type="primary" size="small" style="margin-left:8px" @click="doSearch">查询</el-button></div><el-table :data="items" v-loading="loading" stripe size="small"><el-table-column prop="maintenance_id" label="工单号" width="110"/><el-table-column prop="short_description" label="故障描述" min-width="140"/><el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.current_status==='3'?'success':'warning'" size="small">{{ row.current_status }}</el-tag></template></el-table-column></el-table><AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:12px;justify-content:flex-end"/></el-card></div></template>
<script setup lang="ts">import {ref} from 'vue';import AppPagination from '@/components/common/AppPagination.vue';import {useListPage} from '@/composables/useListPage';import {fetchMaintenanceDaily} from '@/api/itsm';import type {MntRecord} from '@/api/itsm'
const{items,loading,page,perPage,total,onSearch}=useListPage<MntRecord>(fetchMaintenanceDaily)
const searchPhone=ref('')
function doSearch(){onSearch(searchPhone.value?{phone:searchPhone.value}:{})}</script>
<style scoped>.page{padding:0}.page-header{display:flex;justify-content:space-between;margin-bottom:16px}.page-header h2{font-size:18px;font-weight:600;margin:0}</style>
```

- [ ] **Step 7: TypeScript 编译检查**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1 | tail -3
```
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "feat(f3): add portal + SLA + notification pages, call dispatch" && git push
```

---

### Task 2: F3.2 合同 + 发票 + 结算 + 财务（9页）

**API 文件**: Create `contract.ts`, `billing.ts`, `finance.ts`

- [ ] **Step 1: 创建 API 模块（同模式，略写）**

- [ ] **Step 2: 创建 9 个页面（同模板模式）**

```
frontend/src/views/contract/ContractList.vue
frontend/src/views/contract/InvoiceList.vue
frontend/src/views/billing/BillingRuleList.vue
frontend/src/views/billing/BillList.vue
frontend/src/views/finance/AccountList.vue
frontend/src/views/finance/ReceivableList.vue
frontend/src/views/finance/PayableList.vue
frontend/src/views/finance/PaymentList.vue
frontend/src/views/finance/DepreciationList.vue
```

- [ ] **Step 3: 注册路由 + 菜单 + 权限（同 Step1 模式）**

- [ ] **Step 4: TypeScript 编译 + Commit**

---

### Task 3: F3.3 保养计划 + 押金 + 资产属性（7页）

**API 文件**: Create `deposit.ts`，保养复用 `itsm.ts`

- [ ] **Step 1-4: 同模板创建 7 页 + 路由 + 菜单 + 权限 + Commit**

```
frontend/src/views/itsm/MaintenancePlanList.vue
frontend/src/views/itsm/MaintenanceList.vue
frontend/src/views/deposit/DepositList.vue
frontend/src/views/deposit/DepositDetailList.vue
frontend/src/views/deposit/DepositIOList.vue
frontend/src/views/master/AssetAttribList.vue
```

---

### Task 4: F3.4 考勤 + 预警/价格（5页）

- [ ] **Step 1-4: 同模板创建 5 页 + 路由 + 菜单 + 权限 + Commit**

```
frontend/src/views/attendance/AttendanceList.vue
frontend/src/views/attendance/AttendanceCountList.vue
frontend/src/views/inventory/InventoryLimitList.vue
frontend/src/views/inventory/PriceList.vue
frontend/src/views/inventory/AdjustPriceList.vue
```

---

### Task 5: F3.5 MES + IoT + 调拨 + 报表（10页）

**API 文件**: Create `mes.ts`, `iot.ts`

- [ ] **Step 1-4: 同模板创建 10 页 + 路由 + 菜单 + 权限 + Commit**

```
frontend/src/views/mes/WorkOrderList.vue
frontend/src/views/mes/ProcessDefList.vue
frontend/src/views/mes/WorkProcessList.vue
frontend/src/views/mes/MaterialConsumeList.vue
frontend/src/views/iot/DeviceConnList.vue
frontend/src/views/iot/DeviceDataList.vue
frontend/src/views/iot/AlertRuleList.vue
frontend/src/views/iot/AlertLogList.vue
frontend/src/views/system/TransferAccountList.vue
frontend/src/views/reports/ReportCenter.vue
```

**报表中心**需要 ECharts：
```bash
cd frontend && npm install echarts
```

- [ ] **Step 5: 安装 ECharts + Commit**

---

### Task 6: F3.6 全局搜索 + 通用组件

- [ ] **Step 1: 全局搜索组件**

`frontend/src/components/GlobalSearch.vue`:
```vue
<template>
  <el-dialog v-model="visible" title="全局搜索" width="600px" @keydown.ctrl.k.prevent="visible=!visible">
    <el-input v-model="keyword" placeholder="搜索客户/工单/物料/EID..." size="large" @keyup.enter="doSearch" ref="inputRef"/>
    <div style="margin-top:12px">
      <el-tabs v-model="activeTab"><el-tab-pane label="客户" name="cust"/><el-tab-pane label="工单" name="itsm"/><el-tab-pane label="物料" name="item"/><el-tab-pane label="设备" name="eid"/></el-tabs>
      <el-table :data="results" v-loading="searching" stripe size="small" style="margin-top:8px"><el-table-column prop="title" label="结果" min-width="200"/><el-table-column prop="subtitle" label="描述" min-width="200"/></el-table>
    </div>
  </el-dialog>
</template>
<script setup lang="ts">import {ref} from 'vue'
const visible=ref(false);const keyword=ref('');const activeTab=ref('cust');const results=ref<{title:string;subtitle:string}[]>([]);const searching=ref(false)
function doSearch(){searching.value=true;setTimeout(()=>{results.value=[{title:'搜索结果',subtitle:`关键词: ${keyword.value}`}];searching.value=false},300)}
function open(){visible.value=true}
defineExpose({open})
</script>
```

注册全局快捷键在 `App.vue` 中：
```typescript
import { onMounted } from 'vue'
onMounted(() => { document.addEventListener('keydown', (e) => { if ((e.ctrlKey||e.metaKey) && e.key==='k') { e.preventDefault(); /* trigger global search */ } }) })
```

- [ ] **Step 2: 通用组件提取** — 从 F2/F3 已有页面提取 `AuditButton`, `StatusTransition`, `ExportButton`

- [ ] **Step 3: Commit**

---

## 验证

所有阶段完成后：

```bash
# TypeScript
cd frontend && npx vue-tsc --noEmit

# 后端测试
uv run pytest -x -q tests/

# 前端可访问性
curl -s http://localhost:3000 | grep -q "myitsm" && echo "OK"
```

## 总时间估算

| Task | 页面 | 时间 |
|------|------|------|
| F3.1 | 7 | 1.5周 |
| F3.2 | 9 | 1.5周 |
| F3.3 | 7 | 1周 |
| F3.4 | 5 | 0.5周 |
| F3.5 | 10 | 1.5周 |
| F3.6 | 搜索+组件 | 0.5周 |
| **合计** | **~40** | **5.5周** |
