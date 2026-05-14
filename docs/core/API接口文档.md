# API 接口文档

**版本**: v1.2  
**基础路径**: `/api/v1`  
**更新日期**: 2026-05-08（新增资产盘点+POS变更端点）

---

## 一、全局约定

### 1.1 认证方式

除 `/api/v1/health` 和 `/api/v1/login` 外，所有接口均需 JWT 认证。

```
Authorization: Bearer <token>
```

通过 `POST /api/v1/login` 获取 token。

### 1.2 统一响应结构

```json
{
  "code": 200,
  "message": "操作成功",
  "data": { ... },
  "request_id": "uuid-string"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 业务状态码（200=成功，400=参数错误，401=未认证，404=不存在，500=服务错误） |
| message | string | 提示信息 |
| data | any | 响应数据（列表/对象/null） |
| request_id | string | 请求追踪 ID（UUID） |

### 1.3 通用查询参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| page | int | 页码 | 1 |
| per_page | int | 每页条数 | 20 |

### 1.4 通用错误码

| HTTP 状态码 | 含义 | 场景 |
|-------------|------|------|
| 400 | 参数错误 | 请求体校验失败 |
| 401 | 未认证 | 缺少/无效/过期 Token |
| 403 | 无权限 | 角色权限不足 |
| 404 | 资源不存在 | ID 查询未命中 |
| 500 | 服务器错误 | 未捕获异常 |

---

## 二、接口详情

### 2.0 基础服务

#### 健康检查 `health`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/health` | 健康检查 | 否 |

#### 认证与会话 `auth`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/login` | 用户登录 | 否 |
| GET | `/api/v1/session` | 获取当前会话信息 | 是 |

**POST /api/v1/login 请求体**：
```json
{
  "user_id": "U001",
  "password": "secret"
}
```

**响应 data**：
```json
{
  "token": "eyJ...",
  "user_code": "U001",
  "user_name": "张三"
}
```

---

### 2.1 系统管理 `system`

路由前缀：`/api/v1`

#### 用户/部门/组/权限

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/users` | 用户列表 | `status`,`user_cd`,`user_nm`,`dept_cd` |
| GET/POST | `/users` / `/users/<cd>` | 用户CRUD | - |
| GET | `/departments` | 部门列表 | - |
| GET/POST/PUT/DELETE | `/departments` / `/departments/<cd>` | 部门CRUD | - |
| GET/POST/PUT/DELETE | `/groups` / `/groups/<cd>` | 用户组CRUD | - |
| GET/POST | `/groups/<cd>/members` | 组成员管理 | - |
| GET/PUT | `/groups/<cd>/rights` | 组权限管理 | - |
| GET | `/users/<cd>/permissions` | 用户有效权限 | - |
| GET | `/menus` | 菜单树 | - |
| GET | `/menus/perm-tree` | 权限树(动态) | - |

#### 物料分类 & 物料

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/itemclasses/tree` | 分类树(CTE递归) | - |
| GET/POST | `/itemclasses` | 分类列表/新增 | - |
| PUT/DELETE | `/itemclasses/<cd>` | 分类编辑/删除 | - |
| GET | `/items` | 物料列表(分页) | `page`,`per_page`,`class_cd`,`recursive`,`search` |
| POST/PUT/DELETE | `/items` / `/items/<cd>` | 物料CRUD | - |

#### 客户分类 & 客户

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/custclasses/tree` | 分类树 | - |
| GET/POST | `/custclasses` | 分类列表/新增 | - |
| PUT/DELETE | `/custclasses/<cd>` | 分类编辑/删除 | - |
| GET | `/customers` | 客户列表(分页) | `page`,`per_page`,`class_cd`,`search` |
| POST/PUT/DELETE | `/customers` / `/customers/<cd>` | 客户CRUD | - |

#### EID 设备管理

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/eid/tree` | 物料分类树(含EID数量) | - |
| GET | `/eid` | EID列表(分页) | `page`,`per_page`,`class_cd`,`search` |
| POST | `/eid` | 新增EID | - |
| PUT/DELETE | `/eid/<itemcd>/<eid>` | 编辑/删除EID | - |
| GET | `/eid/<itemcd>/<eid>/tracks` | 变更历史(含自动纠正) | - |

#### 资产台账

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/assets` | 资产台账列表(分页) | `page`,`per_page`,`class_cd`,`search`,`asset_type`,`asset_owner`,`useflg`,`location`,`whcd`,`sflg`,`cust_cd`,`item_class` |
| GET | `/assets/bom` | BOM配件明细(含门店退回状态) | `eid` |
| PUT | `/assets/<id>` | 更新资产属性 | - |

> **`plan_refid` 取值逻辑**（EID列表）：优先查 `tit15_maintenance_renovate.new_device_id` → 其次查 C 记录（`change_date >= gendate`）。详见表 `tit15_maintenance_renovate`。  
> **BOM 配件归属**：通过 `tmm44_pos_r_eid` → 父设备 `CustPosRl` 链路解析客户，按页批量后解析。  
> **`location` 筛选**：`customer` 含直接分配+BOM配件(父设备有客户)；`warehouse` 仅无客户且非BOM配件。

#### 码表查询

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/syscodes` | 按类型查编码 | `code_typ`(BT/YB/ZF/ES/QS/PS/SS/CS/SRC等) |
| GET | `/areas` | 区域列表 | - |
| GET | `/commodes` | 通讯方式列表 | - |
| GET | `/countries` | 国家列表 | - |
| GET | `/provinces` | 省份列表 | - |
| GET | `/cities` | 城市列表 | `prvn_cd` |
| GET | `/towns` | 区县列表 | `city_cd` |
| GET | `/warehouses` | 仓库列表 | - |

#### 系统参数

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/sysparms` | 系统参数列表 |
| GET | `/sysparms/<parm_cd>` | 指定系统参数 |
| PUT | `/sysparms/<parm_cd>` | 更新系统参数 |

---

### 2.2 ITSM 核心业务 `itsm`

路由前缀：`/api/v1/itsm`

#### 日常维护单 (MD)

| 方法 | 路径 | 说明 | 查询/请求参数 |
|------|------|------|-------------|
| GET | `/maintenance-daily` | 列表 | `status`, `store_id`, `page`, `per_page` |
| GET | `/maintenance-daily/<maintenance_id>` | 详情 | - |
| POST | `/maintenance-daily` | 创建 | Body: `MaintenanceDailyCreate` |
| PUT | `/maintenance-daily/<maintenance_id>` | 更新 | Body: `MaintenanceDailyUpdate` |
| POST | `/maintenance-daily/<maintenance_id>/transition` | 状态流转 | Body: `{"to_status": "...", "remark": "..."}` |

#### 新机开通 (MO)

| 方法 | 路径 | 说明 | 查询/请求参数 |
|------|------|------|-------------|
| GET | `/maintenance-open` | 列表 | `status`, `store_id`, `page`, `per_page` |
| GET | `/maintenance-open/<opening_id>` | 详情 | - |
| POST | `/maintenance-open` | 创建 | Body: `MaintenanceOpenCreate` |
| POST | `/maintenance-open/<opening_id>/transition` | 状态流转 | Body: `StatusTransition` |

#### 旧机翻新 (MR)

| 方法 | 路径 | 说明 | 查询/请求参数 |
|------|------|------|-------------|
| GET | `/maintenance-renovate` | 列表 | `status`, `store_id`, `page`, `per_page` |
| GET | `/maintenance-renovate/<renew_id>` | 详情 | - |
| POST | `/maintenance-renovate` | 创建 | Body: `MaintenanceRenovateCreate` |
| POST | `/maintenance-renovate/<renew_id>/transition` | 状态流转 | Body: `StatusTransition` |

#### 设备变更 (BG)

| 方法 | 路径 | 说明 | 查询/请求参数 |
|------|------|------|-------------|
| GET | `/device-change` | 列表 | `status`, `store_id`, `change_type`, `page`, `per_page` |
| GET | `/device-change/<change_id>` | 详情 | - |
| POST | `/device-change` | 创建 | Body: `DeviceChangeCreate` |
| POST | `/device-change/<change_id>/transition` | 状态流转 | Body: `StatusTransition` |

> `change_type` 枚举：CK=改磁卡号, BQ=信息变更, BG=设备变更。CK 类型流转完成后自动保存磁卡号历史到 `TMM22_CUSTOMERS_HISTORY`。

#### 门店关闭 (GB)

| 方法 | 路径 | 说明 | 查询/请求参数 |
|------|------|------|-------------|
| GET | `/store-close` | 列表 | `status`, `store_id`, `page`, `per_page` |
| GET | `/store-close/<close_id>` | 详情 | - |
| POST | `/store-close` | 创建 | Body: `StoreCloseCreate` |
| POST | `/store-close/<close_id>/transition` | 状态流转 | Body: `StatusTransition` |

#### 回收任务 (TIT20, P0-1/优化4.2)

| 方法 | 路径 | 说明 | 查询/请求参数 |
|------|------|------|-------------|
| GET | `/recycle-task` | 列表 | `task_status`, `cust_cd`, `page`, `per_page` |
| GET | `/recycle-task/<recycle_id>` | 详情 | - |
| POST | `/recycle-task` | 创建 | Body: `RecycleTaskCreate` |
| POST | `/recycle-task/<recycle_id>/transition` | 状态流转 | Body: `StatusTransition` |
| GET | `/recycle-task/<recycle_id>/details` | 明细列表 | - |
| POST | `/recycle-task/<recycle_id>/details` | 添加明细 | Body: `RecycleTaskDtlCreate` |

#### 公用附表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/d2d/<maintenance_id>` | 上门服务记录列表 |
| POST | `/d2d` | 创建上门服务记录 |
| GET | `/rv/<maintenance_id>` | 回访记录列表 |
| POST | `/rv` | 创建回访记录 |
| GET | `/accessories/<maintenance_id>` | 配件更新记录列表 |
| POST | `/accessories` | 创建配件更新记录 |
| GET | `/close-bill/<maintenance_id>` | 关单记录列表 |
| POST | `/close-bill` | 创建关单记录 |
| GET | `/dispatch/<maintenance_id>` | 分派记录列表 |
| POST | `/dispatch` | 创建分派记录 |

#### 状态流转说明

所有主表共享 `MaintenanceState` 状态机，`to_status` 枚举值：

```
NEW → ASSIGNED → IN_PROGRESS → COMPLETED → CLOSED
                 IN_PROGRESS → SUSPENDED → IN_PROGRESS (挂起/恢复)
```

**StatusTransition 请求体**：
```json
{
  "to_status": "ASSIGNED",
  "remark": "已派单给工程师张三"
}
```

---

### 2.3 仓储管理 `warehouse`

路由前缀：`/api/v1/warehouse`

#### 仓库主数据

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/warehouses` | 仓库列表 |
| GET | `/warehouses/<whcd>` | 仓库详情 |
| POST | `/warehouses` | 创建仓库 |
| PUT | `/warehouses/<whcd>` | 更新仓库 |

#### 入库单

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/stock-in` | 入库单列表 | `whcd`, `invtyp`, `auditflg`, `page`, `per_page` |
| GET | `/stock-in/<inbillid>` | 入库单详情 | - |
| POST | `/stock-in` | 创建入库单（含明细） | Body + `details[]` |
| POST | `/stock-in/<inbillid>/audit` | 审核入库单（审核后更新库存） | - |

#### 出库单

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/stock-out` | 出库单列表 | `whcd`, `invtyp`, `auditflg`, `page`, `per_page` |
| GET | `/stock-out/<outbillid>` | 出库单详情 | - |
| POST | `/stock-out` | 创建出库单（含明细） | Body + `details_eid[]`, `details_prd[]` |
| POST | `/stock-out/<outbillid>/audit` | 审核出库单（审核后扣减库存） | - |

> `invtyp` 区分16种出入库类型（采购入库、销售出库、调拨、退货等）。

#### 库存查询

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/stock` | 库存明细列表/指定物品余额 | `whcd`, `itemcd`, `page`, `per_page` |

#### 资产盘点 ✅ 新增（2026-05-08）

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/asset-check` | 盘点单列表 | `page`, `per_page` |
| GET | `/asset-check/<opbillid>` | 盘点单详情（含明细） | - |
| POST | `/asset-check` | 创建盘点单（含明细） | Body + `details[]` |
| PUT | `/asset-check/<opbillid>` | 更新盘点单 | Body |
| POST | `/asset-check/<opbillid>/audit` | 审核盘点单 | - |

#### POS设备变更 ✅ 新增（2026-05-08）

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/pos-change` | 变更记录列表 | `page`, `per_page` |
| GET | `/pos-change/<pk>` | 变更记录详情（含明细） | - |
| POST | `/pos-change` | 创建设备变更（含明细） | Body + `details[]` |
| PUT | `/pos-change/<pk>` | 更新设备变更 | Body |

---

### 2.4 采购管理 `procurement`

路由前缀：`/api/v1/procurement`

#### 采购计划

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/plans` | 采购计划列表 | `auditflg`, `pctyp`, `page`, `per_page` |
| GET | `/plans/<pcplanid>` | 采购计划详情 | - |
| POST | `/plans` | 创建采购计划（含明细） | Body + `details[]` |
| POST | `/plans/<pcplanid>/audit` | 审核采购计划 | - |

#### 采购登记

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/registers` | 采购登记列表 | `suppliercd`, `auditflg`, `page`, `per_page` |
| GET | `/registers/<rgstbillid>` | 采购登记详情 | - |
| POST | `/registers` | 创建采购登记（含明细） | Body + `details[]` |
| POST | `/registers/<rgstbillid>/audit` | 审核采购登记 | - |

#### 采购单据

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/bills` | 采购单据列表 | `whcd`, `page`, `per_page` |
| GET | `/bills/<pcbillid>` | 采购单据详情 | - |
| POST | `/bills` | 创建采购单据 | Body: `PurchaseBillCreate` |

#### 供应商评价

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/supplier-appraisals` | 供应商评价列表 | `auditflg`, `page`, `per_page` |
| GET | `/supplier-appraisals/<appid>` | 供应商评价详情 | - |
| POST | `/supplier-appraisals` | 创建供应商评价（含明细） | Body + `details[]` |

#### 质检管理

路由前缀：`/api/v1/qc`

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/qc` | 质检结果列表（分页） | `page`,`per_page`,`search` |
| GET | `/qc/<qcbillid>` | 质检详情（含按产品明细+按EID明细） | - |

---

### 2.5 销售管理 `sales`

路由前缀：`/api/v1/sales`

#### 预计划

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/plans` | 预计划列表 | `plantyp`, `plan_status`, `custcd`, `page`, `per_page` |
| GET | `/plans/<planno>` | 预计划详情 | - |
| POST | `/plans` | 创建预计划 | Body: `PlanCustCreate` |
| PUT | `/plans/<planno>` | 更新预计划 | Body: `PlanCustUpdate` |

#### 销售单据

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/bills` | 销售单据列表 | `sltyp`, `custcd`, `auditflg`, `page`, `per_page` |
| GET | `/bills/<slbillid>` | 销售单据详情 | - |
| POST | `/bills` | 创建销售单据 | Body: `SalesBillCreate` |
| POST | `/bills/<slbillid>/audit` | 审核销售单据 | - |

#### 延期

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/extends` | 延期列表 | `custcd`, `auditflg`, `page`, `per_page` |
| GET | `/extends/<opbillid>` | 延期详情 | - |
| POST | `/extends` | 创建延期（含明细） | Body + `details[]` |

---

### 2.6 SLA 服务级别管理 `sla`

路由前缀：`/api/v1/sla`

#### SLA 定义

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/definitions` | SLA定义列表 |
| GET | `/definitions/<sla_id>` | SLA定义详情 |
| POST | `/definitions` | 创建SLA定义 |
| PUT | `/definitions/<sla_id>` | 更新SLA定义 |

#### SLA 工单监控

| 方法 | 路径 | 说明 | 请求参数 |
|------|------|------|---------|
| GET | `/tickets` | SLA工单监控列表 | `sla_status`, `sla_id`, `page`, `per_page` |
| POST | `/tickets/attach` | 为工单绑定SLA | `maintenance_id`, `maintenance_type`, `priority` |
| POST | `/tickets/response` | 记录首次响应 | `maintenance_id`, `maintenance_type` |
| POST | `/tickets/resolve` | 记录解决并关闭SLA监控 | `maintenance_id`, `maintenance_type` |

#### 达标率统计

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/stats` | SLA达标率统计 | `sla_id`（可选） |

---

### 2.7 考勤管理 `attendance`

路由前缀：`/api/v1/attendance`

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/attendance` | 按月查询考勤记录 | `amonth`（必填）, `operid`, `page`, `per_page` |
| POST | `/attendance` | 创建考勤记录 | Body: `AttendanceCreate` |
| GET | `/attendance/summary` | 按月查询考勤汇总 | `amonth`（必填） |

---

### 2.8 库存预警与价格管理 `inventory`

路由前缀：`/api/v1/inventory`

#### 库存预警

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/inventory-limits` | 库存预警列表 |
| GET | `/inventory-limits/<itemcd>` | 库存预警详情 |
| POST | `/inventory-limits` | 创建库存预警 |
| PUT | `/inventory-limits/<itemcd>` | 更新库存预警 |

#### 价格规则

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/prices` | 价格规则列表 |
| POST | `/prices` | 创建价格规则 |
| PUT | `/prices/<itemcd>/<busityp>` | 更新价格规则 |

#### 调价

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/adjust-prices/<pabillid>` | 调价记录列表 |
| POST | `/adjust-prices` | 创建调价记录 |

---

### 2.9 押金管理 `deposit`

路由前缀：`/api/v1/deposit`

#### 押金主记录

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/deposits` | 押金列表 | `page`, `per_page` |
| GET | `/deposits/<custcd>` | 押金详情 | - |
| POST | `/deposits` | 创建押金记录 | Body: `DepositCreate` |
| PUT | `/deposits/<custcd>` | 更新押金记录 | Body: `DepositUpdate` |

#### 押金变更明细

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/deposits/<custcd>/details` | 押金变更明细列表 | `page`, `per_page` |
| POST | `/deposits/details` | 创建押金变更明细 | Body: `DepositDetailCreate` |

#### 设备型号押金标准

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/deposit-models` | 设备型号押金标准列表 |
| POST | `/deposit-models` | 创建设备型号押金标准 |
| PUT | `/deposit-models/<model_cd>` | 更新设备型号押金标准 |

---

### 2.10 合同与发票管理 `contract`

路由前缀：`/api/v1/contract`

#### 合同管理

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/contracts` | 合同列表 | `classcd`, `busityp`, `page`, `per_page` |
| GET | `/contracts/<htbh>` | 合同详情 | - |
| POST | `/contracts` | 创建合同 | Body: `ContractCreate` |
| PUT | `/contracts/<htbh>` | 更新合同 | Body: `ContractUpdate` |

#### 发票管理

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/invoices` | 发票列表 | `htbh`, `classcd`, `page`, `per_page` |
| GET | `/invoices/<fpbh>` | 发票详情 | - |
| POST | `/invoices` | 创建发票 | Body: `InvoiceCreate` |
| PUT | `/invoices/<fpbh>` | 更新发票 | Body: `InvoiceUpdate` |

---

### 2.11 通知系统 `notification`

路由前缀：`/api/v1/notification`

#### 通知模板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/notification-templates` | 通知模板列表 |
| GET | `/notification-templates/<template_id>` | 通知模板详情 |
| POST | `/notification-templates` | 创建通知模板 |
| PUT | `/notification-templates/<template_id>` | 更新通知模板 |

#### 通知记录

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/notifications` | 通知记录列表 | `channel`, `send_status`, `ref_type`, `page`, `per_page` |
| POST | `/notifications` | 创建通知记录 | Body: `NotificationCreate` |
| POST | `/notifications/<notification_id>/send` | 发送通知 | - |

---

### 2.12 租金/费用结算 `billing`（Tier-2 G4）

路由前缀：`/api/v1/billing`

#### 结算规则

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/rules` | 结算规则列表 | `page`, `per_page` |
| GET | `/rules/<rule_id>` | 结算规则详情 | - |
| POST | `/rules` | 创建结算规则 | Body: `BillingRuleCreate` |
| PUT | `/rules/<rule_id>` | 更新结算规则 | Body: `BillingRuleUpdate` |

#### 账单

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/bills` | 账单列表 | `custcd`, `status`, `page`, `per_page` |
| GET | `/bills/<bill_id>` | 账单详情（含明细） | - |
| POST | `/bills` | 创建账单（含明细） | Body: `BillCreate` + `details[]` |
| PUT | `/bills/<bill_id>` | 更新账单 | Body: `BillUpdate` |

#### 结算批次

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/batches` | 结算批次列表 | `page`, `per_page` |
| GET | `/batches/<batch_id>` | 结算批次详情 | - |
| POST | `/batches` | 创建结算批次 | Body: `BillingBatchCreate` |
| PUT | `/batches/<batch_id>` | 更新结算批次 | Body: `BillingBatchUpdate` |

---

### 2.13 财务应收应付 `finance`（Tier-2 G5）

路由前缀：`/api/v1/finance`

#### 会计科目

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/accounts` | 会计科目列表 | `account_type` |
| GET | `/accounts/<account_cd>` | 科目详情 | - |
| POST | `/accounts` | 创建科目 | Body: `AccountCreate` |
| PUT | `/accounts/<account_cd>` | 更新科目 | Body: `AccountUpdate` |

#### 应收

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/receivables` | 应收列表 | `custcd`, `status`, `page`, `per_page` |
| GET | `/receivables/<ar_id>` | 应收详情 | - |
| POST | `/receivables` | 创建应收 | Body: `ReceivableCreate` |
| PUT | `/receivables/<ar_id>` | 更新应收 | Body: `ReceivableUpdate` |

#### 应付

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/payables` | 应付列表 | `supp_cd`, `status`, `page`, `per_page` |
| GET | `/payables/<ap_id>` | 应付详情 | - |
| POST | `/payables` | 创建应付 | Body: `PayableCreate` |
| PUT | `/payables/<ap_id>` | 更新应付 | Body: `PayableUpdate` |

#### 收付款

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/payments` | 收付款列表 | `pay_type`, `page`, `per_page` |
| POST | `/payments` | 创建收付款 | Body: `PaymentCreate` |

#### 设备折旧

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/depreciations` | 折旧列表 | `page`, `per_page` |
| GET | `/depreciations/<eid>` | 折旧详情 | - |
| POST | `/depreciations` | 创建折旧记录 | Body: `DepreciationCreate` |
| PUT | `/depreciations/<eid>` | 更新折旧记录 | Body: `DepreciationUpdate` |

---

### 2.14 客户自助服务门户 `portal`（Tier-2 G9）

路由前缀：`/api/v1/portal`

#### 门户用户

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/users` | 门户用户列表 | `page`, `per_page` |
| GET | `/users/<portal_uid>` | 门户用户详情 | - |
| POST | `/users` | 创建门户用户 | Body: `PortalUserCreate` |
| PUT | `/users/<portal_uid>` | 更新门户用户 | Body: `PortalUserUpdate` |

#### 自助报修

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/repairs` | 报修工单列表 | `custcd`, `status`, `page`, `per_page` |
| GET | `/repairs/<request_id>` | 报修工单详情 | - |
| POST | `/repairs` | 创建报修工单 | Body: `RepairRequestCreate` |
| PUT | `/repairs/<request_id>` | 更新报修工单 | Body: `RepairRequestUpdate` |

#### 服务评价

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/ratings` | 服务评价列表 | `custcd`, `page`, `per_page` |
| POST | `/ratings` | 创建服务评价 | Body: `ServiceRatingCreate` |

---

### 2.15 生产制造 MES `mes`（Tier-3 G7）

路由前缀：`/api/v1/mes`

#### 生产工单

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/work-orders` | 工单列表 | `status`, `page`, `per_page` |
| GET | `/work-orders/<wo_id>` | 工单详情（含工序） | - |
| POST | `/work-orders` | 创建工单 | Body: `WorkOrderCreate` |
| PUT | `/work-orders/<wo_id>` | 更新工单 | Body: `WorkOrderUpdate` |

#### 工序定义

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/processes` | 工序定义列表 |
| POST | `/processes` | 创建工序定义 |
| PUT | `/processes/<process_cd>` | 更新工序定义 |

#### 工单工序

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/work-orders/<wo_id>/processes` | 工单工序列表 |
| POST | `/work-processes` | 创建工单工序 |
| PUT | `/work-processes/<wp_id>` | 更新工单工序 |

#### 物料消耗

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/work-orders/<wo_id>/materials` | 物料消耗列表 |
| POST | `/materials` | 创建物料消耗 |

---

### 2.16 IoT 数据监控 `iot`（Tier-3 G8）

路由前缀：`/api/v1/iot`

#### 设备接入

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/connections` | 设备接入列表 | `online_status`, `page`, `per_page` |
| GET | `/connections/<conn_id>` | 设备接入详情 | - |
| POST | `/connections` | 创建设备接入 | Body: `DeviceConnCreate` |
| PUT | `/connections/<conn_id>` | 更新设备接入 | Body: `DeviceConnUpdate` |

#### 设备数据

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/data/<eid>` | 设备数据查询 | `data_type`, `page`, `per_page` |
| POST | `/data` | 上报设备数据 | Body: `DeviceDataCreate` |

#### 报警规则

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/alert-rules` | 报警规则列表 |
| POST | `/alert-rules` | 创建报警规则 |
| PUT | `/alert-rules/<rule_id>` | 更新报警规则 |

#### 报警记录

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|---------|
| GET | `/alerts` | 报警记录列表 | `eid`, `status`, `page`, `per_page` |
| PUT | `/alerts/<log_id>/acknowledge` | 确认/解决报警 | Body: `AlertAcknowledge` |

---

## 三、端点统计

| 蓝图 | 前缀 | 端点数 | 阶段 |
|------|------|--------|------|
| health | /api/v1 | 1 | 阶段1 |
| auth | /api/v1 | 2 | 阶段1 |
| system | /api/v1 | 57 | 阶段1 |
| itsm | /api/v1/itsm | 36 | 阶段2 |
| warehouse | /api/v1/warehouse | 23 | 阶段3+7（资产盘点6+POS变更4） |
| procurement | /api/v1/procurement | 13 | 阶段3 |
| sales | /api/v1/sales | 11 | 阶段3 |
| sla | /api/v1/sla | 8 | 阶段3 |
| attendance | /api/v1/attendance | 3 | 阶段4 |
| inventory | /api/v1/inventory | 8 | 阶段4 |
| deposit | /api/v1/deposit | 9 | 阶段4 |
| contract | /api/v1/contract | 8 | 阶段4 |
| notification | /api/v1/notification | 7 | 阶段4 |
| billing | /api/v1/billing | 12 | 阶段5 |
| finance | /api/v1/finance | 15 | 阶段5 |
| portal | /api/v1/portal | 9 | 阶段5 |
| mes | /api/v1/mes | 10 | 阶段5 |
| iot | /api/v1/iot | 10 | 阶段5 |
| qc | /api/v1/qc | 2 | P0 补 |
| transactions | /api/v1/transactions | 4 | 阶段6 |
| reports | /api/v1/reports | 8 | 阶段6 |
| **合计** | | **207** | |

---

## 四、Schema 参考

所有请求/响应 Schema 定义在 `app/schemas/` 目录下，使用 Pydantic v2 模型。各蓝图对应的 Schema 文件：

| Schema 文件 | 对应蓝图 |
|-------------|---------|
| `auth.py` | auth（LoginRequest） |
| `itsm.py` | itsm（MaintenanceDailyCreate/Update、StatusTransition、各公用附表 Create 等） |
| `warehouse.py` | warehouse（StockInCreate、StockOutCreate、WarehouseCreate/Update、StockQuery 等） |
| `procurement.py` | procurement（PurchasePlanCreate、PurchaseRegisterCreate、PurchaseBillCreate 等） |
| `sales.py` | sales（PlanCustCreate/Update、SalesBillCreate、SalesExtendCreate 等） |
| `sla.py` | sla（SlaDefinitionCreate/Update、SlaAttachRequest、SlaResponseRequest 等） |
| `attendance.py` | attendance（AttendanceCreate） |
| `inventory.py` | inventory（InventoryLimitCreate/Update、PriceCreate/Update、AdjustPriceCreate） |
| `deposit.py` | deposit（DepositCreate/Update、DepositDetailCreate、DepositPosModelCreate/Update） |
| `contract.py` | contract（ContractCreate/Update、InvoiceCreate/Update） |
| `notification.py` | notification（NotificationCreate、NotificationTemplateCreate/Update） |
| `billing.py` | billing（BillingRuleCreate/Update、BillCreate/Update、BillingBatchCreate/Update） |
| `finance.py` | finance（AccountCreate/Update、ReceivableCreate/Update、PayableCreate/Update、PaymentCreate、DepreciationCreate/Update） |
| `portal.py` | portal（PortalUserCreate/Update、RepairRequestCreate/Update、ServiceRatingCreate） |
| `mes.py` | mes（WorkOrderCreate/Update、ProcessDefCreate/Update、WorkProcessCreate/Update、MaterialConsumeCreate） |
| `iot.py` | iot（DeviceConnCreate/Update、DeviceDataCreate、AlertRuleCreate/Update、AlertAcknowledge） |
| `transaction.py` | transactions（AllBillQuery、ErrorCorrectionCreate、StockSummaryQuery） |
| `report.py` | reports（InventorySnapshotQuery、MovementLogQuery、EidLifecycleQuery、SalesReportQuery、BOMTreeQuery） |
