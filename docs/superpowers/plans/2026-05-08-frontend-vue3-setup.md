# myitsm 前端开发方案（Vue 3 + Element Plus）

> **Status**: 待确认 | **融合**: frontend-vue-development skill + 项目整体实施计划 §5

**Goal**: 从零搭建 Vue 3 + Element Plus 管理后台，覆盖 20 个 API 蓝图 205 个端点，含登录认证、系统管理、ITSM 工单、仓储、采购、销售、合同、财务、报表等 18 个业务模块。

**Tech Stack**: Vue 3.4+ | Vite | Element Plus | Pinia | Vue Router 4 | Axios | SCSS | TypeScript

---

## 目录结构

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── router/
│   │   └── index.ts               # 路由配置 + 守卫
│   ├── stores/
│   │   ├── auth.ts                # 认证状态（Pinia）
│   │   ├── app.ts                 # 全局（侧边栏+标签页）
│   │   └── tabs.ts                # 多标签页状态
│   ├── api/
│   │   ├── request.ts             # Axios 封装（JWT+错误拦截）
│   │   └── *.ts                   # 按蓝图拆分（auth/system/itsm/warehouse/...）
│   ├── layouts/
│   │   └── MainLayout.vue         # 主布局（侧边栏+标签页+顶栏+内容区）
│   ├── views/                     # 按模块分目录
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── system/                # 用户/部门/角色/菜单
│   │   ├── itsm/                  # 7类ITSM工单
│   │   ├── warehouse/             # 仓库/出入库/盘点/POS变更
│   │   ├── procurement/           # 采购
│   │   ├── sales/                 # 销售
│   │   ├── contract/              # 合同+发票
│   │   ├── deposit/               # 押金
│   │   ├── billing/               # 结算
│   │   ├── finance/               # 财务
│   │   ├── portal/                # 门户
│   │   ├── attendance/            # 考勤
│   │   ├── inventory/             # 预警+价格
│   │   ├── sla/                   # SLA
│   │   ├── notification/          # 通知
│   │   ├── mes/                   # MES
│   │   ├── iot/                   # IoT
│   │   ├── transactions/          # 事务查询
│   │   └── reports/               # 报表
│   ├── components/
│   │   ├── AppMenu.vue            # 动态菜单（权限过滤）
│   │   ├── AppTabs.vue            # 多标签页导航
│   │   ├── PageHeader.vue         # 页面标题+面包屑
│   │   ├── StatusTransition.vue   # ITSM 状态流转（可复用）
│   │   ├── GlobalSearch.vue       # 全局搜索
│   │   └── common/                # 通用组件（表格/表单/搜索/导出）
│   ├── directives/
│   │   └── permission.ts          # v-permission 按钮级权限指令
│   └── styles/
│       ├── variables.scss
│       └── global.scss
```

---

## 阶段 F1：核心框架 + P0 页面（4-6 周）

### F1.1 项目脚手架（1 周）

```bash
npm create vite@latest frontend -- --template vue-ts
cd frontend
npm install element-plus pinia vue-router axios
npm install -D sass @types/node
```

### F1.2 布局框架（与 F1.1 并行）

**主布局**（侧边栏 + 标签页 + 面包屑 + 顶栏）：

```
┌─────────────────────────────────────┐
│ 🏷 日常维护 / 新机开通 / 设备变更    │ ← 标签页导航 (AppTabs)
├──────────┬──────────────────────────┤
│ 📋 工单   │  ┌───────────────────┐  │
│  - 日常   │  │  面包屑: 首页>ITSM │  │
│  - 开通   │  ├───────────────────┤  │
│  - 翻新   │  │                   │  │
│ 📦 仓储   │  │   <router-view>   │  │
│ 💰 采购   │  │                   │  │
│ ...       │  │                   │  │
└──────────┴──────────────────────────┘
```

### F1.3 登录认证 + 路由守卫

- 登录页 → `POST /login` → token 存入 Pinia + localStorage
- `router.beforeEach` 守卫：无 token → 跳转 `/login`
- Axios 响应拦截：401 → 自动退出 + 跳转登录

```typescript
// router/index.ts
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.path !== '/login' && !authStore.token) {
    next('/login')
  } else if (to.path === '/login' && authStore.token) {
    next('/')  // 已登录 → 首页
  } else {
    next()
  }
})
```

### F1.4 权限控制

**菜单级**：从后端 `GET /menus` 获取用户菜单树，`AppMenu` 递归渲染且有权限的节点。

**按钮级**：自定义 `v-permission` 指令，比对用户权限列表。

```typescript
// directives/permission.ts
app.directive('permission', {
  mounted(el, binding) {
    const { value } = binding  // 如 'user:create'
    const permissions = useAuthStore().permissions
    if (!permissions.includes(value)) {
      el.parentNode?.removeChild(el)
    }
  }
})
```

### F1.5 系统管理页面（8 端点）

| 页面 | 路由 | Element Plus 组件 |
|------|------|-------------------|
| 用户列表 | `/system/users` | el-table + el-pagination + el-input 搜索 |
| 用户编辑 | `/system/users/:id` | el-form + el-dialog |
| 部门管理 | `/system/departments` | el-tree + el-table |
| 用户组管理 | `/system/groups` | el-table + el-tag |
| 菜单/权限 | `/system/menus` | el-tree（编辑权限） |
| 系统参数 | `/system/params` | el-table |

### F1.6 ITSM 工单页面（36 端点）

**复用模式**：所有 ITSM 工单共享 `StatusTransition` + 通用列表/详情/创建模式。

| 工单类型 | 路由 | 说明 |
|---------|------|------|
| 日常维护单 | `/itsm/maintenance-daily` | 核心工单，含配件明细 (TIT10) |
| 新机开通 | `/itsm/maintenance-open` | 设备安装开通 (TIT13) |
| 旧机翻新 | `/itsm/maintenance-renovate` | 旧机→新机映射 (TIT15) |
| 设备变更 | `/itsm/device-change` | CK/BQ/BG 三种类型，磁卡号变更自动保存历史 (TIT16) |
| 门店关闭 | `/itsm/store-close` | 门店关闭流程 (TIT18) |
| 回收任务 | `/itsm/recycle-task` | P0-1新增，取机回收独立化 (TIT20) |
| 日常保养 | `/itsm/maintenance` | 保养计划+执行+设备明细 (TIT17) |
| 免费更换 | `/itsm/free-replace` | 免费更换维护单+设备附表 (TIT28) |
| 未关单跟踪 | `/itsm/unclose-track` | 超时未关单监控 (TIT29) |
| 公用附表 | 内嵌于详情页 | 上门服务(TIT23)/回访(TIT24)/配件更新(TIT25)/关单(TIT27)/分派(TIT21)/收费(TIT26) |

### F1.7 仓储管理页面（23 端点）

| 页面 | 路由 | 说明 |
|------|------|------|
| 仓库管理 | `/warehouse/warehouses` | CRUD |
| 入库单 | `/warehouse/stock-in` | 8种入库类型，列表+创建（含明细）+审核 |
| 出库单 | `/warehouse/stock-out` | 8种出库类型，同上 |
| 库存查询 | `/warehouse/stock` | 库存明细表格+多条件筛选 |
| 盘盈盘亏 | `/warehouse/overlost` | 盘点差异处理 (TWH17/18) |
| 资产盘点 | `/warehouse/asset-check` | 设备级资产盘点，列表+创建+审核 ✅ |
| POS设备变更 | `/warehouse/pos-change` | 1新增/2替换/3删除/4查询，列表+创建 ✅ |

### F1.8 客户/资产管理（6 子模块）

数据来源于 `base_cust.pbl`，是 ITSM 和仓储的核心基础数据。

| 页面 | 路由 | API | 说明 |
|------|------|-----|------|
| 客户主数据 | `/master/customers` | system.py (`/users` 蓝图) | 客户列表+搜索+详情+编辑，含生命周期状态 (TMM22) |
| 客户分类 | `/master/cust-class` | — | 分类树 (TMM21) |
| 资产台账 | `/master/assets` | — | 设备-客户关联，含 asset_type/recycle_status (TMM35) |
| EID 管理 | `/master/eid` | — | 设备 SN 码管理+变更追踪 (TMM43+TMM43_TRACK) |
| 资产属性 | `/master/asset-attrib` | — | 资产扩展属性 (TMM62) |
| 物料/BOM | `/master/items` | reports.py (BOM树) | 物料清单+BOM结构树 (TMM12+TMM41/42) |

> EID（设备唯一标识）体系是连接仓储→资产→ITSM→IoT 的关键纽带。

### F1.9 质检管理（3 子模块）

| 页面 | 路由 | 说明 |
|------|------|------|
| 质检结果 | `/qc/results` | 质检主记录列表+创建+审核 (TQC10) |
| 质检明细 | 内嵌详情页 | 检项明细 (TQC11_RESULTDT) |
| 质检设备 | 内嵌详情页 | 按 SN 码关联质检设备 (TQC11_RESULTEID) |

---

## 阶段 F2：P1 业务页面 + 通用组件（4-5 周）

### F2.1 采购管理（13 端点）

采购计划 → 登记审批 → 采购单据 → 退货 → 供应商评价。含审核流程。

### F2.2 销售管理（11 端点）

预计划 → 销售单据 → 延期管理 + 话务台呼出。含审核流程。

### F2.3 合同 + 发票（8 端点）

合同 CRUD + 发票 CRUD，合同-发票关联展示。

### F2.4 押金管理（9 端点）

押金主记录 + 变更明细 + 设备型号押金标准。

### F2.5 结算管理（12 端点，Tier-2 G4）

结算规则 → 账单（含明细） → 结算批次。

### F2.6 财务管理（15 端点，Tier-2 G5）

会计科目 + 应收 + 应付 + 收付款 + 设备折旧。

### F2.7 客户门户（9 端点，Tier-2 G9）

门户用户 + 自助报修 + 服务评价。

### F2.8 调拨流转 + 考核评价

| 页面 | 路由 | API | 说明 |
|------|------|-----|------|
| 调拨流转 | `/transactions/transfers` | transactions.py | 跨仓调拨 (trans.pbl) |
| 考核评价 | `/system/appraisals` | — | 供应商/人员考核 (TMM45) |

### F2.9 通用组件沉淀

本阶段从重复模式中提取：

| 组件 | 用途 | 覆盖模块 |
|------|------|---------|
| `TablePage` | 列表页壳（搜索栏+表格+分页） | 所有模块 |
| `FormDialog` | 创建/编辑弹窗（表单+校验） | 所有模块 |
| `AuditButton` | 审核按钮（确认弹窗+调用audit接口） | 采购/销售/仓储 |
| `ExportButton` | 导出按钮（调用后端导出接口） | 报表/列表页 |
| `SearchBar` | 多条件搜索栏（el-form inline） | 所有列表页 |

---

## 阶段 F3：P2 辅助页面 + 报表（3-4 周）

### F3.1 库存预警/价格管理（8 端点）

预警规则 CRUD + 价格规则 + 调价记录。

### F3.2 考勤管理（3 端点）

按月查询考勤记录 + 考勤汇总。

### F3.3 SLA 管理（8 端点）

SLA 定义 + 工单监控（绑定/响应/解决） + 达标率统计。

### F3.4 通知管理（7 端点）

通知模板 CRUD + 通知记录 + 发送。

### F3.5 MES（10 端点，Tier-3）

生产工单 + 工序定义 + 工单工序 + 物料消耗。

### F3.6 IoT（10 端点，Tier-3）

设备接入 + 数据采集 + 报警规则 + 报警记录。

### F3.7 事务查询 + 报表（12 端点）

- **事务查询**: 全模块单据联合查询 + 错账更正 + 进销存汇总
- **报表**: 库存/EID/销售/BOM 图表 + 数据导出（推荐 ECharts）

### F3.8 全局搜索 + 消息通知

- **全局搜索**: 顶部搜索框 `Ctrl+K` 唤起，搜索工单/客户/设备
- **消息通知**: 顶栏通知铃铛，拉取未读通知，点击查看详情

---

## 阶段 F4：优化与联调（2-3 周）

### F4.1 性能优化

- **路由懒加载**: `() => import('@/views/itsm/MaintenanceList.vue')`
- **虚拟滚动**: 大表（>1000行）用 `el-table-v2`
- **Pinia 持久化**: 标签页/侧边栏状态 localStorage

### F4.2 前后端联调

- 逐模块对接真实 API
- Mock 数据 → 真实接口切换
- 异常场景测试（超时/500/401）

### F4.3 UI/UX 打磨

- 统一间距/字号/颜色变量
- 表单校验提示语优化
- 空状态 / 加载态 / 错误态 覆盖

### F4.4 多浏览器兼容

- Chrome / Edge / Safari 最新两个版本
- Element Plus 默认支持

### F4.5 部署配置

```nginx
# Nginx 反向代理
location /api/v1 {
    proxy_pass http://127.0.0.1:5000;    # Flask 后端
}
location / {
    root /var/www/myitsm-frontend/dist;   # Vue 静态文件
    try_files $uri $uri/ /index.html;     # SPA history mode
}
```

---

## 技术约定

### 代码风格（与 frontend-vue-development skill 一致）

- 4 空格缩进，无分号
- 组件 kebab-case 命名
- Props 完整 type+default，数组/对象用工厂函数
- 禁止 v-html（防 XSS）
- Scoped 样式

### 项目特有

- API 响应 `{ code, message, data }`，`code === 200` 表示成功
- JWT `Authorization: Bearer <token>`
- Element Plus 中文语言包

### 命名约定

| 类型 | 模式 | 示例 |
|------|------|------|
| 组件文件 | kebab-case.vue | `maintenance-list.vue` |
| API 方法 | 动词+名词 | `fetchUsers()`, `createMaintenance()` |
| 事件处理 | handle* | `handleSubmit()`, `handleDelete()` |
| 初始化 | init* | `initTableData()` |
| 路由路径 | 模块前缀 | `/itsm/maintenance-daily` |

---

## 预估时间

| 阶段 | 内容 | 时间 |
|------|------|------|
| **F1** | 脚手架+布局+登录+权限+系统管理+ITSM(10类)+仓储(7)+客户资产(6)+质检(3) | 6 周 |
| **F2** | 采购(6)+销售(4)+合同+押金+结算+财务+门户+调拨+考核+通用组件 | 5 周 |
| **F3** | 预警+考勤+SLA+通知+MES+IoT+报表+全局搜索 | 3 周 |
| **F4** | 性能+联调+UI打磨+兼容+部署 | 2 周 |
| **合计** | 覆盖 **35 个子模块**（原 PB 25 个 + Tier-1/2/3 新增 10 个） | **16 周** |

> **移动端适配 (G10)** 不在本期范围——后端 API 已就绪，待小程序/PWA 前端独立项目启动。

---
