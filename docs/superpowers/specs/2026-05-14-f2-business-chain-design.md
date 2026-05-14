# F2 业务主链前端开发设计

> **Status**: 待实施 | **创建**: 2026-05-14 | **分支**: `feature/f2-business-chain`

**Goal**: 在 F1 地基上完成预计划→仓储→采购→ITSM 四个模块的前端页面，打通核心业务流。

**Tech Stack**: Vue 3 + Element Plus + TypeScript + Vite（同 F1）

---

## 1. 推进方式

单人开发，按依赖链递进，边铺页面边提取可复用模式。

```
第1步：预计划（1-2天）        → plan_cust 列表/创建/详情
第2步：仓储（2天）            → 入库/出库/库存/盘点
第3步：采购+质检（2天）        → 采购+验收+质检结果
第4步：ITSM 高频工单（3天）    → 维修/开通/翻新/变更
第5步：ITSM 剩余工单（2天）    → 回收/保养/关店/关单/附表
第6步：补全（2天）            → 详情/审核/批量/状态流转
```

## 2. 模块蓝图与 API 对应

### 2.1 预计划（`/plans`）

| API | 页面 |
|-----|------|
| `GET /plan-cust` | 预计划列表（分页+搜索） |
| `POST /plan-cust` | 新建预计划 |
| `GET /plan-cust/<id>` | 预计划详情 |
| `PUT /plan-cust/<id>` | 编辑/审核预计划 |

### 2.2 仓储（`/warehouse`）

| API | 页面 |
|-----|------|
| `GET /stock-in` | 入库单列表 |
| `POST /stock-in` | 新建入库单 |
| `GET /stock-out` | 出库单列表 |
| `POST /stock-out` | 新建出库单 |
| `GET /inventory` | 库存查询/盘点 |
| `GET /overlost` | 盘亏列表 |

### 2.3 采购+质检（`/procurement`、`/quality`）

| API | 页面 |
|-----|------|
| `GET /purchase-plans` | 采购计划列表 |
| `GET /purchase-registers` | 采购登记列表 |
| `GET /purchase-bills` | 采购单据列表 |
| `GET /check-in` | 采购验收列表 |
| `GET /quality-results` | 质检结果列表 |

### 2.4 ITSM 工单（`/itsm`，10 类）

| 工单类型 | 表 | API 前缀 |
|---------|-----|---------|
| 日常维修 | tit10_maintenanceday | `/maintenance` |
| 新机开通 | tit13_maintenance_open | `/maintenance/open` |
| 旧机翻新 | tit15_maintenance_renovate | `/maintenance/renovate` |
| 设备变更 | tit16_device_change | `/device-change` |
| 日常保养 | tit17_maintenance | `/maintenance/daily` |
| 门店关闭 | tit18_store_close | `/store-close` |
| 回收任务 | tit20_recycle_task | `/recycle-task` |
| 免费更换 | tit28_free_replace | `/free-replace` |
| 未关单跟踪 | tit29_noclose_track | `/noclose-track` |
| 附表/配件 | tit10_pos_detail / tit11 / tit14 / tit19 | 各主表子路由 |

## 3. 页面组件模式

参考 F1 已建立的模式，F2 延续：

```
列表页结构：
├── 搜索栏（el-input + el-select 多条件）
├── 操作栏（新建按钮 + 批量操作）
├── el-table（分页 + 排序 + 状态标签）
└── 详情 Drawer/Dialog（只读 + 关联表）

表单页结构：
├── el-form（分组 + 折叠面板）
├── 明细表格（行内编辑 + 物料选择器）
└── 提交/保存/审核按钮
```

复用 F1 已有的 `AppPagination`，以及 Element Plus 的 `el-table`/`el-form` 模式。

## 4. 路由结构

```
/master/plans          → PlanList.vue
/master/plans/:id      → PlanDetail.vue (drawer)
/warehouse/stock-in    → StockInList.vue
/warehouse/stock-out   → StockOutList.vue
/warehouse/inventory   → InventoryList.vue
/procurement/plans     → PurchasePlanList.vue
/procurement/register  → PurchaseRegisterList.vue
/procurement/bills     → PurchaseBillList.vue
/procurement/check-in  → CheckInList.vue
/quality/results       → QualityResultList.vue
/itsm/maintenance      → MaintenanceList.vue (维修)
/itsm/open             → OpenList.vue (开通)
/itsm/renovate         → RenovateList.vue (翻新)
/itsm/device-change    → DeviceChangeList.vue (变更)
/itsm/daily            → DailyList.vue (保养)
/itsm/store-close      → StoreCloseList.vue (关店)
/itsm/recycle          → RecycleTaskList.vue (回收)
/itsm/free-replace     → FreeReplaceList.vue (更换)
/itsm/noclose          → NoCloseTrackList.vue (未关单)
```

## 5. 可复用模式提取时机

| 时机 | 模式 | 来源 |
|------|------|------|
| 第2个列表页 | 通用搜索+表格+分页 combo | 预计划 → 入库单 |
| 第2个表单页 | 主表+明细表双表单模式 | 入库单 → 采购单 |
| 第3个工单 | 工单状态流转组件 | 维修 → 开通 → 翻新 |

不做提前抽象，在第2-3次相同场景时才提取。

---

## 6. 验收标准

- [ ] 预计划：创建预计划 → 选择客户 → 填写物料明细 → 生成预计划单号
- [ ] 仓储：入库/出库单 CRUD + 库存查询 + 盘亏列表
- [ ] 采购：采购计划→登记→单据→验收 完整链路
- [ ] ITSM 维修工单：创建→分派→维修→关单 全流程
- [ ] 所有列表页支持搜索/筛选/分页
- [ ] TypeScript 编译通过
- [ ] 后端 API 联调通过（Mock 先行）
