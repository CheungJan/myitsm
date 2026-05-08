# myitsm 前端开发方案（Vue 3 + Element Plus）

> **Status**: 待确认 | **融合**: frontend-vue-development skill + 项目整体实施计划 §5 + 愿景全覆盖

**Goal**: 从零搭建 Vue 3 + Element Plus 管理后台，覆盖全部 35 个子模块，205 个 API 端点。按"地基→业务主链→配套增强→打磨上线"四阶段推进，F2 结束即可端到端跑通核心业务流。

**Tech Stack**: Vue 3.4+ | Vite | Element Plus | Pinia | Vue Router 4 | Axios | SCSS | TypeScript

---

## 核心业务流 vs 前端阶段映射

```
基础数据(型号/BOM/EID)              ──→ F1 地基
    ↓
预计划 → 话务台(客户确认)           ──→ F2 业务主链
    ↓
资产决策:
  ├─ 有库存 → 仓库出库              ──→ F2
  ├─ 有配件 → MES生产               ──→ F3
  └─ 无库存 → 采购 → 质检 → 入库    ──→ F2
    ↓
实施执行 → 设备流转                ──→ F2 (ITSM)
    ↓
ITSM运维(维护/保养/翻新/变更/回收)  ──→ F2
    ↓
配套: 押金/资产/考核/IoT/报表       ──→ F3
```

---

## 目录结构

```
frontend/
├── index.html / package.json / vite.config.ts / tsconfig.json
├── src/
│   ├── main.ts / App.vue
│   ├── router/index.ts             # 路由 + beforeEach 守卫
│   ├── stores/
│   │   ├── auth.ts                 # JWT + 用户信息 + 权限列表
│   │   ├── app.ts                  # 侧边栏折叠 + 语言
│   │   └── tabs.ts                 # 多标签页状态
│   ├── api/
│   │   ├── request.ts              # Axios（JWT 注入 + 统一拦截 + 401跳转）
│   │   ├── auth.ts / system.ts     # 地基
│   │   ├── itsm.ts / warehouse.ts  # 业务主链
│   │   ├── procurement.ts / sales.ts / qc.ts
│   │   ├── deposit.ts / billing.ts / finance.ts / portal.ts
│   │   ├── mes.ts / iot.ts / sla.ts / attendance.ts
│   │   └── transaction.ts / report.ts
│   ├── layouts/MainLayout.vue      # 侧边栏 + 标签页 + 顶栏 + 内容区
│   ├── views/                      # 按阶段分目录
│   │   ├── login/
│   │   ├── system/                 # F1: 用户/部门/角色/菜单
│   │   ├── master/                 # F1: 客户/资产/EID/物料BOM
│   │   ├── itsm/                   # F2: 10类工单
│   │   ├── warehouse/              # F2: 仓库/出入库/盘点/设备回收
│   │   ├── procurement/            # F2: 采购
│   │   ├── sales/                  # F2: 预计划/销售/话务台
│   │   ├── qc/                     # F2: 质检
│   │   ├── deposit/                # F3: 押金
│   │   ├── billing/                # F3: 结算
│   │   ├── finance/                # F3: 财务
│   │   ├── portal/                 # F3: 门户
│   │   ├── sla/                    # F3: SLA
│   │   ├── notification/           # F3: 通知
│   │   ├── mes/                    # F3: MES
│   │   ├── iot/                    # F3: IoT
│   │   ├── attendance/             # F3: 考勤
│   │   ├── inventory/              # F3: 预警/价格
│   │   └── reports/                # F3: 报表
│   ├── components/
│   │   ├── AppMenu.vue             # 动态菜单（权限过滤）
│   │   ├── AppTabs.vue             # 多标签页导航
│   │   ├── PageHeader.vue          # 面包屑
│   │   ├── StatusTransition.vue    # ITSM 状态流转（可复用）
│   │   ├── GlobalSearch.vue        # 全局搜索 (Ctrl+K)
│   │   └── common/                 # TablePage / FormDialog / AuditButton / ExportButton
│   ├── directives/permission.ts    # v-permission 按钮级权限
│   └── styles/variables.scss / global.scss
```

---

## 阶段 F1：地基（5-6 周）

> 目标：登录可用，权限就绪，基础数据全部就位。F1 结束即可独立演示系统管理 + 基础数据 CRUD。

### F1.1 脚手架 + 布局 + 登录（1 周）

```bash
npm create vite@latest frontend -- --template vue-ts
npm install element-plus pinia vue-router axios
npm install -D sass @types/node
```

- `api/request.ts`：Axios 封装（JWT 注入 → 401 跳转 → `{code,message,data}` 拦截）
- `stores/auth.ts`：token + userInfo + permissions
- `layouts/MainLayout.vue`：侧边栏(AppMenu) + 标签页(AppTabs) + 面包屑 + 顶栏(用户/退出)
- `router/index.ts`：`beforeEach` 守卫（无 token → login，已登录 → home）
- `views/login/`：用户名密码 → `POST /login` → 存 token → 跳转

### F1.2 权限控制（与 F1.1 并行）

- **菜单级**：`GET /menus` 获取菜单树 → `AppMenu` 递归渲染，无权限节点不展示
- **按钮级**：`v-permission` 指令，无权限按钮自动移除

### F1.3 系统管理（1 周）

| 页面 | 路由 | API |
|------|------|-----|
| 用户管理 | `/system/users` | `/users` CRUD |
| 部门管理 | `/system/departments` | `/departments` 树形 |
| 用户组管理 | `/system/groups` | `/groups` |
| 菜单/权限配置 | `/system/menus` | `/menus` 权限编辑 |
| 系统参数 | `/system/params` | `/sysparms` |

### F1.4 基础数据 — 客户/资产/EID/物料（1.5 周）

> 对应业务流起点：创建型号 → BOM → EID → 客户。后续所有操作依赖此层。

| 页面 | 路由 | 数据表 | 说明 |
|------|------|--------|------|
| 物料/BOM | `/master/items` | TMM11/12 + TMM41/42 | 型号分类 + BOM结构树 |
| 客户主数据 | `/master/customers` | TMM22 + TMM21 | 客户列表+分类 |
| EID 管理 | `/master/eid` | TMM43 + TMM43_TRACK | 设备SN码+变更追踪 |
| 资产台账 | `/master/assets` | TMM35 + TMM62 | 设备-客户关联+asset_type |
| 仓库主数据 | `/master/warehouses` | TWH01 | 仓库基础信息 |

---

## 阶段 F2：业务主链（5-6 周）

> 目标：端到端走通"预计划→资产决策→实施→ITSM运维"全流程。F2 结束系统即可上线试运行。

### F2.1 销售管理（预计划 → 话务台，1 周）

> 业务流起点：市场部创建预计划 → 话务台呼出确认客户信息

| 页面 | 路由 | API |
|------|------|-----|
| 预计划 | `/sales/plans` | `/sales/plans` CRUD |
| 话务台 | `/sales/calls` | — 呼出管理 |
| 销售单据 | `/sales/bills` | `/sales/bills` + 审核 |
| 延期管理 | `/sales/extends` | `/sales/extends` |

### F2.2 仓储管理 — 库存决策（1 周）

> 资产决策核心：查库存 → 有成品则出库；无成品则触发 MES/采购

| 页面 | 路由 | 说明 |
|------|------|------|
| 入库单 | `/warehouse/stock-in` | 8种入库类型，创建(含明细)+审核 |
| 出库单 | `/warehouse/stock-out` | 8种出库类型 |
| 库存查询 | `/warehouse/stock` | 实时库存+筛选 |
| 盘盈盘亏 | `/warehouse/overlost` | 差异处理 |
| 设备回收确认 | `/warehouse/pos-change` | 仓库接收 ITSM 回收单返回的设备，确认入库/调换/报废 (twh21/22) ✅ |
| 资产盘点 | `/warehouse/asset-check` | 设备级盘点 ✅ |

### F2.3 采购管理（1 周）

> 无库存时触发采购。也可独立提前做采购计划（设备采购有周期，不等生产订单）。

| 页面 | 路由 | 说明 |
|------|------|------|
| 供应商主数据 | `/procurement/suppliers` | 供应商分类+基础信息 (TMM18/19) |
| 采购计划 | `/procurement/plans` | 计划+明细+状态+审核 (TPC01/02/03) |
| 采购登记 | `/procurement/registers` | 到货登记+审批 (TPC12/13) |
| 采购单据 | `/procurement/bills` | 正式采购单 (TPC14) |
| 退货管理 | `/procurement/returns` | 采购退货 (TPC16/17) |
| 供应商评价 | `/procurement/appraisals` | 考评+明细 (TPC20/21) |

### F2.4 质检管理（0.5 周）

> 采购到货 → 质检 → 合格入库。内部线：采购 → **质检** → 入库。

| 页面 | 路由 | 说明 |
|------|------|------|
| 质检结果 | `/qc/results` | 质检主记录列表+创建+审核 (TQC10) |
| 质检明细 | `/qc/results/:id` | 检项明细，嵌入详情页 (TQC11_RESULTDT) |
| 设备关联 | 同上 | 按 SN 码关联质检设备 (TQC11_RESULTEID) |

> QC 是独立模块（PB 中 `qc.pbl`），与采购分离设计。

### F2.5 ITSM 工单 — 实施 + 运维（2 周）

> 实施执行 + 设备流转 + ITSM 运维。**最核心模块**。

| 工单类型 | 路由 | 说明 |
|---------|------|------|
| 日常维护单 | `/itsm/maintenance-daily` | 核心工单，含配件明细 (TIT10) |
| 新机开通 | `/itsm/maintenance-open` | 设备安装开通 (TIT13) |
| 旧机翻新 | `/itsm/maintenance-renovate` | 旧机→新机映射 (TIT15) |
| 设备变更 | `/itsm/device-change` | CK/BQ/BG，磁卡号变更存历史 (TIT16) |
| 门店关闭 | `/itsm/store-close` | 门店关闭 (TIT18) |
| 回收任务 | `/itsm/recycle-task` | P0-1 取机回收 (TIT20) |
| 日常保养 | `/itsm/maintenance` | 保养计划+执行 (TIT17) |
| 免费更换 | `/itsm/free-replace` | 免费更换 (TIT28) |
| 未关单跟踪 | `/itsm/unclose-track` | 超时监控 (TIT29) |
| 公用附表 | 嵌入详情页 | 上门/回访/配件/关单/分派/收费 |

**复用组件**: `StatusTransition` — 状态流转弹窗（所有工单共享）

---

## 阶段 F3：配套增强（4-5 周）

> 目标：补全配套模块，覆盖押金/资产/财务/考核/IoT/报表等增强功能。

### F3.1 押金 + 资产（1 周）

| 页面 | 路由 | 说明 |
|------|------|------|
| 押金主记录 | `/deposit/deposits` | 客户押金余额+明细 |
| 押金型号标准 | `/deposit/models` | 按型号定义押金/租金 |
| 资产属性 | `/master/asset-attrib` | 扩展属性管理 |

### F3.2 合同 + 发票 + 结算 + 财务（1.5 周）

| 模块 | 路由 | 说明 |
|------|------|------|
| 合同管理 | `/contract/contracts` | 合同 CRUD |
| 发票管理 | `/contract/invoices` | 发票 CRUD + 合同关联 |
| 结算规则 | `/billing/rules` | 租金/费用规则 |
| 账单管理 | `/billing/bills` | 账单生成+明细+批次 |
| 会计科目 | `/finance/accounts` | 科目管理 |
| 应收/应付 | `/finance/receivables` `/finance/payables` | 客户/供应商对账 |
| 收付款 | `/finance/payments` | 收付款记录 |
| 设备折旧 | `/finance/depreciations` | 折旧管理 |

### F3.3 客户门户 + SLA + 通知（1 周）

| 模块 | 路由 | 说明 |
|------|------|------|
| 门户用户 | `/portal/users` | 客户自助账户 |
| 自助报修 | `/portal/repairs` | 报修+查询 |
| 服务评价 | `/portal/ratings` | 客户评价 |
| SLA 定义 | `/sla/definitions` | 响应/解决时间 |
| SLA 监控 | `/sla/tickets` | 绑定+响应+解决+达标率 |
| 通知模板 | `/notification/templates` | 模板 CRUD |
| 通知记录 | `/notification/notifications` | 记录+发送 |

### F3.4 考勤 + 考核 + 预警/价格（1 周）

| 模块 | 路由 | 说明 |
|------|------|------|
| 考勤记录 | `/attendance/records` | 按月查询+汇总 |
| 考核评价 | `/system/appraisals` | 供应商/人员考核 |
| 库存预警 | `/inventory/limits` | 上下限规则 |
| 价格规则 | `/inventory/prices` | 价格+调价 |

### F3.5 MES + IoT + 调拨 + 报表（1.5 周）

| 模块 | 路由 | 说明 |
|------|------|------|
| MES 工单 | `/mes/work-orders` | 生产工单+工序+物料 |
| IoT 设备 | `/iot/connections` | 设备接入+数据+报警 |
| 调拨流转 | `/transactions/transfers` | 跨仓调拨 |
| 事务查询 | `/transactions/bills` | 全模块单据查询+错账更正+进销存 |
| 报表 | `/reports/*` | 库存/EID/销售/BOM 图表(ECharts)+导出 |

### F3.6 全局搜索 + 通用组件提取

- **全局搜索**: `Ctrl+K` 唤起，搜索工单/客户/设备
- **通用组件**: `TablePage` / `FormDialog` / `AuditButton` / `ExportButton` / `SearchBar`

---

## 阶段 F4：打磨上线（2-3 周）

| 任务 | 说明 |
|------|------|
| 性能优化 | 路由懒加载 + 虚拟滚动(el-table-v2) + Pinia 持久化 |
| 前后端联调 | 逐模块 Mock→真实 API，异常场景全覆盖 |
| UI/UX 打磨 | 统一间距/字号/颜色变量，空/加载/错误三态 |
| 多浏览器兼容 | Chrome/Edge/Safari 最新两版 |
| Nginx 部署 | SPA history mode + `/api/v1` 反向代理 Flask |

---

## 技术约定

**代码风格**（frontend-vue-development skill）：
- 4 空格缩进，无分号
- 组件 kebab-case.vue
- Props 完整 type+default，数组/对象工厂函数
- 禁止 v-html | Scoped 样式

**项目特有**：
- API 响应 `{code, message, data}`，`code===200` 成功
- JWT `Bearer <token>` | 401 → 跳转登录
- Element Plus 中文语言包

---

## 预估时间

| 阶段 | 内容 | 时间 |
|------|------|------|
| **F1 地基** | 脚手架+登录+权限+系统管理+基础数据(客户/资产/EID/物料/仓库) | 5 周 |
| **F2 业务主链** | 销售(预计划+话务台)+仓储(出入库+盘点+回收)+采购+质检+ITSM(10类工单) | 6 周 |
| **F3 配套增强** | 押金+合同/发票+结算/财务+门户/SLA/通知+考勤/考核/预警+MES/IoT+报表 | 4 周 |
| **F4 打磨上线** | 性能+联调+UI+兼容+Nginx部署 | 2 周 |
| **合计** | 35 子模块 | **17 周** |

> **F2 结束即可试运行**：预计划→库存决策→采购/质检→ITSM 全链路已通。
> **移动端 (G10)** 不在本期范围，后端 API 已就绪，独立立项。

---

## 下一步

确认方案后，从 F1.1 开始：`npm create vite` → Axios 封装 → 登录页 + 主布局。
