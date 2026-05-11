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

## 模块清单（与系统功能对比分析交叉核对）

> 按 `系统功能对比分析与扩展规划.md` 逐条核对，确保愿景全覆盖无遗漏。

### F1 地基 — 13 子模块

| # | 模块 | 子功能 | API蓝图 | 端点 | 页面 | 原PB模块 | 覆盖度 |
|---|------|--------|---------|------|------|---------|--------|
| 1 | 登录认证 | 登录/会话/退出 | auth | 2 | 登录页 | — | ✅ 已重构 |
| 2 | 权限控制 | 菜单级+按钮级 | system | 2 | 菜单树配置 | app_system.pbl | ✅ 已重构 |
| 3 | 用户管理 | 列表/详情/编辑 | system | 4 | 2页 | app_system.pbl | 完整 |
| 4 | 部门管理 | 列表/树形 | system | 1 | 1页 | app_system.pbl | 完整 |
| 5 | 用户组管理 | 列表/分配 | system | 2 | 1页 | app_system.pbl | 完整 |
| 6 | 系统参数 | 分组表单+登录接入 | system | 3 | 1页 | app_system.pbl | ✅ allowmultilogon已生效 |
| 7 | 系统字典 | 类型树+码值CRUD | system | 5 | 1页 | *(tit03合并新增)* | 完整 |
| 8 | 物料/BOM | 物料清单+BOM结构树 | reports (BOM) | 1 | 2页 | base_cust.pbl | 完整 |
| 9 | 客户主数据 | 列表/详情/分类树 | system | 2 | 2页 | base_cust.pbl | 完整 |
| 10 | EID 管理 | SN码+变更追踪 | — | — | 2页 | base_cust.pbl | 完整 |
| 11 | 资产台账 | 设备-客户关联+asset_type | — | — | 1页 | base_cust.pbl | 完整 |
| 12 | 资产属性扩展 | 扩展属性管理 | — | — | 1页 | base_cust.pbl | 完整 |
| 12 | 仓库主数据 | CRUD | warehouse | 4 | 1页 | wh.pbl | 完整 |
| | | | | **20** | **17页** | | |

### F2 业务主链 — 34 子模块

| # | 模块 | 子功能 | API蓝图 | 端点 | 页面 | 原PB模块 | 覆盖度 |
|---|------|--------|---------|------|------|---------|--------|
| | **销售管理** | | | | | | |
| 13 | 预计划 | 列表/详情/创建/编辑 | sales | 4 | 2页 | sale.pbl | 完整 |
| 14 | 话务台 | 客户呼出管理 | — | — | 1页 | sale.pbl | 完整 |
| 15 | 销售单据 | 列表+审核 | sales | 4 | 1页 | sale.pbl | 🔗 soinvaliddays |
| 16 | 延期管理 | 列表+创建(含明细) | sales | 4 | 1页 | sale.pbl | 🔗 soinvaliddays |
| | **仓储管理** | | | | | | |
| 17 | 入库管理 | 8种入库+明细+审核 | warehouse | 4 | 2页 | wh.pbl | 🔗 costtype, centralwarehouse |
| 18 | 出库管理 | 8种出库+明细+审核 | warehouse | 4 | 2页 | wh.pbl | 完整 |
| 19 | 库存查询 | 实时库存+筛选 | warehouse | 1 | 1页 | wh.pbl | 完整 |
| 20 | 盘盈盘亏 | 差异处理+明细 | warehouse | — | 2页 | wh.pbl | 完整 |
| 21 | 资产盘点 | 列表+创建(含明细)+审核 | warehouse | 5 | 2页 | wh.pbl | ✅ 补全 |
| 22 | 设备回收确认 | 仓库接收ITSM回收设备 | warehouse | 4 | 2页 | wh.pbl | ✅ 补全 |
| | **采购管理** | | | | | | |
| 23 | 供应商主数据 | 分类+基础信息 | procurement | 2 | 1页 | base_cust.pbl | 完整 |
| 24 | 采购计划 | 计划+明细+审核 | procurement | 4 | 2页 | purchase.pbl | 完整 |
| 25 | 采购登记 | 到货登记+审批 | procurement | 4 | 2页 | purchase.pbl | 完整 |
| 26 | 采购单据 | 正式采购单 | procurement | 2 | 1页 | purchase.pbl | 完整 |
| 27 | 退货管理 | 采购退货 | procurement | — | 1页 | purchase.pbl | 完整 |
| 28 | 供应商评价 | 考评+明细 | procurement | 4 | 2页 | purchase.pbl | 完整 |
| | **质检管理** | | | | | | |
| 29 | 质检结果 | 列表+创建+审核 | — | — | 2页 | qc.pbl | 完整 |
| 30 | 质检明细 | 检项明细(内嵌详情) | — | — | — | qc.pbl | 完整 |
| 31 | 质检设备关联 | 按SN码关联 | — | — | — | qc.pbl | 完整 |
| | **ITSM 工单** | | | | | | |
| 32 | 日常维护单 | 列表+详情+创建+流转 | itsm | 6 | 3页 | itsm.pbl | 完整 |
| 33 | 新机开通 | 同上 | itsm | 5 | 3页 | itsm.pbl | 完整 |
| 34 | 旧机翻新 | 同上 | itsm | 5 | 3页 | itsm.pbl | 完整 |
| 35 | 设备变更(CK/BQ/BG) | 同上+磁卡号历史 | itsm | 5 | 3页 | itsm02.pbl | 完整 |
| 36 | 门店关闭 | 同上 | itsm | 5 | 3页 | itsm02.pbl | 完整 |
| 37 | 回收任务(P0-1) | 同上+明细管理 | itsm | 6 | 3页 | 重构新增 | 完整 |
| 38 | 日常保养 | 同上+计划+设备明细 | itsm | 5 | 3页 | itsm02.pbl | 完整 |
| 39 | 免费更换 | 同上+设备附表 | itsm | 5 | 3页 | itsm02.pbl | 完整 |
| 40 | 未关单跟踪 | 列表+详情 | itsm | 2 | 1页 | itsm02.pbl | 完整 |
| 41 | 上门服务 | 列表+创建(公用附表) | itsm | 2 | — | itsm.pbl | 完整 |
| 42 | 客户回访 | 同上 | itsm | 2 | — | itsm.pbl | 完整 |
| 43 | 配件更新 | 同上 | itsm | 2 | — | itsm02.pbl | 完整 |
| 44 | 关单管理 | 同上 | itsm | 2 | — | itsm02.pbl | 完整 |
| 45 | 分派管理 | 同上 | itsm | 2 | — | itsm02.pbl | 完整 |
| 46 | 收费记录 | 同上 | itsm | 1 | — | — | 部分 |
| | | | | **96** | **49页** | | |

### F3 配套增强 — 21 子模块

| # | 模块 | 子功能 | API蓝图 | 端点 | 页面 | 原PB模块 | 覆盖度 |
|---|------|--------|---------|------|------|---------|--------|
| | **押金管理** | | | | | | |
| 47 | 押金主记录 | 列表/详情/创建/编辑 | deposit | 4 | 1页 | new_deposit.pbl | 完整 |
| 48 | 押金变更明细 | 按客户查询+创建 | deposit | 2 | 1页 | new_deposit.pbl | 完整 |
| 49 | 押金出入记录 | 流水查询 | deposit | 1 | 1页 | new_deposit.pbl | 完整 |
| 50 | 押金清单 | 详细清单 | deposit | — | 1页 | new_deposit.pbl | 完整 |
| 51 | 型号押金标准 | CRUD | deposit | 3 | 1页 | new_deposit.pbl | 完整 |
| | **合同/发票** | | | | | | |
| 52 | 合同管理 | CRUD | contract | 4 | 1页 | — | 基础→完善 |
| 53 | 发票管理 | CRUD+合同关联 | contract | 4 | 1页 | — | 基础→完善 |
| | **结算/财务 (Tier-2)** | | | | | | |
| 54 | 结算规则 | CRUD | billing | 4 | 1页 | — | ✅ Tier-2 |
| 55 | 账单管理 | 生成+明细+批次 | billing | 8 | 2页 | — | ✅ Tier-2 |
| 56 | 会计科目 | CRUD | finance | 4 | 1页 | — | ✅ Tier-2 |
| 57 | 应收管理 | CRUD | finance | 4 | 1页 | — | ✅ Tier-2 |
| 58 | 应付管理 | CRUD | finance | 4 | 1页 | — | ✅ Tier-2 |
| 59 | 收付款 | 列表+创建 | finance | 2 | 1页 | — | ✅ Tier-2 |
| 60 | 设备折旧 | CRUD | finance | 4 | 1页 | — | ✅ Tier-2 |
| | **门户 (Tier-2)** | | | | | | |
| 61 | 门户用户 | CRUD | portal | 4 | 1页 | — | ✅ Tier-2 |
| 62 | 自助报修 | 列表+创建+编辑 | portal | 3 | 2页 | — | ✅ Tier-2 |
| 63 | 服务评价 | 列表+创建 | portal | 2 | 1页 | — | ✅ Tier-2 |
| | **SLA / 通知 (Tier-1)** | | | | | | |
| 64 | SLA 定义 | CRUD | sla | 4 | 1页 | — | ✅ Tier-1 |
| 65 | SLA 工单监控 | 绑定+响应+解决 | sla | 4 | 1页 | — | ✅ Tier-1 |
| 66 | 通知模板 | CRUD | notification | 4 | 1页 | — | ✅ Tier-1 |
| 67 | 通知记录 | 列表+发送 | notification | 3 | 1页 | — | ✅ Tier-1 |
| | **其他** | | | | | | |
| 68 | 考勤管理 | 按月查询+汇总 | attendance | 3 | 2页 | kq.pbl | 完整 |
| 69 | 考核评价 | 供应商/人员考核 | — | — | 1页 | appraisal.pbl | 完整 |
| 70 | 库存预警 | CRUD | inventory | 4 | 1页 | — | ✅ 已重构 |
| 71 | 价格规则 | CRUD+调价 | inventory | 4 | 2页 | price.pbl | 完整 |
| 72 | 调拨流转 | 跨仓调拨 | transactions | 1 | 1页 | trans.pbl | ✅ 已重构 |
| | **Tier-3** | | | | | | |
| 73 | MES 生产工单 | 工单+工序+物料 | mes | 10 | 3页 | — | ✅ Tier-3 |
| 74 | IoT 设备接入 | 连接+数据+报警 | iot | 10 | 3页 | — | ✅ Tier-3 |
| 75 | 事务查询 | 全模块查询+错账+进销存 | transactions | 3 | 2页 | — | ✅ 阶段6 |
| 76 | 报表 | 库存/EID/销售/BOM图表+导出 | reports | 8 | 4页 | report.pbl | ✅ 阶段6 |
| | | | | **102** | **41页** | | |

### 汇总

| 阶段 | 模块数 | 子功能数 | 页面数 | API端点 |
|------|--------|---------|--------|---------|
| F1 地基 | 5 | 13 | 18 | 21 |
| F2 业务主链 | 5 | 34 | 49 | 96 |
| F3 配套增强 | 10 | 21 | 41 | 102 |
| F4 打磨上线 | — | — | — | — |
| **合计** | **20** | **67** | **107** | **218** |

> **覆盖核对**: 原 PB 25 模块 + Tier-1 新增 4 + Tier-2 新增 3 + Tier-3 新增 2 + 阶段6 新增 2 = **36 模块全部覆盖**（移动端 G10 独立立项除外）。
> **API 端点**: 后端 205 + 本方案预估新增 Schema 相关端点和页面路由 = ~218 引用。

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

### 系统参数集成约定

模块表中标注 🔗 的表示开发时需读取 `tmc71_sysparm` 对应参数。集成方式：

```python
from app.models.system import SysParm
sp = db.session.get(SysParm, "SYSPARM")
value = getattr(sp, "param_name", default_value)
```

| 参数 | 应接入模块 | 说明 |
|------|-----------|------|
| `costtype` | 仓储入库/出库、财务结算 | 成本核算方式 |
| `centralwarehouse` | 仓储调拨 | 中心仓库编码 |
| `poinvaliddays` | 采购计划 | 超期天数 |
| `soinvaliddays` | 销售单据 | 超期天数 |
| `shopbilltype` | 门店/销售 | 单据类型差异 |
| `allowmultilogon` | 登录认证 | 多点登录开关，已接入 |
| **F4 打磨上线** | 性能+联调+UI+兼容+Nginx部署 | 2 周 |
| **合计** | 35 子模块 | **17 周** |

> **F2 结束即可试运行**：预计划→库存决策→采购/质检→ITSM 全链路已通。
> **移动端 (G10)** 不在本期范围，后端 API 已就绪，独立立项。

---

## F1 实施进度记录（截至 2026-05-10）

> 实施过程中根据实际数据和 PB 源码分析做了大量调整，以下记录与原计划的偏差。

### 已完成模块

| 模块 | 状态 | 关键调整 |
|------|------|----------|
| 登录/权限 | ✅ | JWT + 动态权限树（数据库 Menu+MenuDetail 表） |
| 用户管理 | ✅ | 部门下拉/状态标签/权限组显示/CRUD |
| 部门管理 | ✅ | CRUD + 状态管理 |
| 用户组管理 | ✅ | CRUD + 成员管理 + 权限设置（动态展开树） |
| 系统字典 | ✅ | tit03→tmm31合并后新增，左类型树(SY) + 右码值CRUD + 排序 |
| 物料管理 | ✅ | 左分类树（el-tree CTE递归）+ 右表格 + 搜索/分类互斥逻辑 |
| 客户管理 | ✅ | 左分类树 + 右表格 + 详情/编辑全字段弹窗 + 6个关联字段下拉 |

### 架构调整

| 原计划 | 实际 | 原因 |
|--------|------|------|
| 权限前端配置写死 | 权限从数据库 Menu+MenuDetail 动态读取 | 用户反馈后续扩展需要动态 |
| 物料扁平列表 | 树状结构 + CTE 递归查询 | PB 三级分类设计 |
| 客户扁平列表 | 树状结构 + 48字段全展示 | PB 源表字段完整性 |
| `Record<string,string>` | 严格 TypeScript interface | 类型安全 |
| 前端本地码表映射 | 后端 `_resolve_customer_refs()` 解析 `_nm` 字段 | 码表维护后无需改前端 |

### 数据修复

| 问题 | 修复 |
|------|------|
| 物料分类 parent_cd 全空 | 从 ortopbitsmdb 同步 186 条父子关系 |
| 缺失行政区域表 | 迁移 tmm02-05 四表（3,440条）+ 客户表加四列 + 地址/分类名匹配回填 |
| 客户状态/来源全空 | syscodes 加 CS/SRC 码表 + 预计划关联识别（6,927条 PREPLAN） |
| 预计划单号缺失 | 磁卡号关联 plan_cust 回填，取最近完成计划 |
| 删除父类无保护 | 子类/客户数检查，ValueError 拦截 |

### 约定规则（详见 `docs/core/客户主数据字段规范.md`）

- 客户生命周期: customer_status=`CS`, source_type=`SRC`, 新建默认 ACTIVE/MANUAL
- 设备统计: pos_count 实时 COUNT，不可手工编辑
- 行政区域: 默认中国+上海，按分类名/地址匹配区县
- POS 软件配置: 预计划阶段→生产指令单，运营阶段→设备监控
- 码表统一 tmm31_syscodes（code_typ 区分），不新建独立码表
- 后端 `*_nm` 字段统一解析，前端直接显示

---

## 下一步
