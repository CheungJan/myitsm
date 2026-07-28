---
类型: 技术设计文档
阅读状态: 待评审
tags:
  - 供应商管理
  - 商品关联
  - 价格维护
  - CRUD
更新日期: 2026-05-24
创建日期: 2026-05-24
作者: CJ
版本: v1.0
---

# 供应商商品关联与价格维护功能设计规格

## 一、设计目标

在供应商详情中一站式管理"该供应商能供应哪些商品"以及"各商品的报价"，为采购订单拆单/并单中的供应商推荐提供数据基础。

当前状态：物料侧已有 `/items/<cd>/suppliers` CRUD（操作同一张 `tmm24_custitems` 表），供应商侧完全缺失。

## 二、API 端点

### 2.1 供应商-商品关联

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/suppliers/<supp_cd>/items` | 查询该供应商供应的商品列表（含物料名称、单位） |
| POST | `/suppliers/<supp_cd>/items` | 新增供应商品关联 |
| PUT | `/suppliers/<supp_cd>/items/<item_cd>` | 修改关联（周期参数、默认标志） |
| DELETE | `/suppliers/<supp_cd>/items/<item_cd>` | 删除商品关联 |

### 2.2 供应商价格

`tip02_supplier_price` 主键为自增 `id`（同一供应商+商品可有多个时间段报价）。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/suppliers/<supp_cd>/prices` | 查询报价，支持 `?item_cd=xxx&current_only=true` |
| POST | `/suppliers/<supp_cd>/prices` | 新增报价（需校验商品已关联） |
| PUT | `/suppliers/<supp_cd>/prices/<int:id>` | 修改报价（按主键 id） |
| DELETE | `/suppliers/<supp_cd>/prices/<int:id>` | 删除报价（按主键 id） |

**GET 查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `item_cd` | string | 按物料筛选 |
| `current_only` | bool | 仅返回当前有效报价（`effective_date <= today <= expire_date`） |

**GET 返回字段**（含 JOIN 补充信息）：`id`, `itemcd`, `item_nm`, `supp_cd`, `min_qty`, `itemprice`, `effective_date`, `expire_date`, `is_current`。

## 三、业务规则

### 3.1 默认供应商

一个物料只能有一个默认供应商（`tmm24_custitems.dfltflg = 'Y'`）。设置新默认时，需将该物料其他供应商的 `dfltflg` 改为 `'N'`。事务中完成。

### 3.2 周期参数

`tmm24_custitems` 中的三个周期字段：

| 字段 | 说明 | 单位 |
|------|------|------|
| delivercycle | 配送周期 | 天 |
| servicecycle | 服务周期 | 天 |
| guaranteeperiod | 保修期 | 天 |

### 3.3 价格时效

`tip02_supplier_price` 中的时间控制：

- `effective_date` + `expire_date` 控制报价有效期
- `is_current` 标记是否当前有效报价
- `min_qty` 最小起订量

### 3.4 删除约束

删除供应商-商品关联前检查：
- 该关联是否有对应的采购订单（通过 `tpc20_requisition_order_link` + `tpc12_register` 关联查询）
- 有 → `409 Conflict`
- 无 → 允许删除

### 3.5 价格新增前置条件

```python
# POST /suppliers/<supp_cd>/prices 时后端检查
exists = db.session.query(CustItems).filter(
    CustItems.custcd == supp_cd,
    CustItems.itemcd == itemcd
).first()
if not exists:
    return error_response("该供应商未关联此商品，请先维护供应商品关系", 400)
```

必须先有 `tmm24_custitems` 关联记录，才能录入 `tip02_supplier_price` 报价。

### 3.6 GET 返回字段优化

| 接口 | 补充返回字段 | 来源 |
|------|-------------|------|
| `GET /suppliers/<cd>/items` | `item_nm`, `item_unit`, `class_nm` | JOIN `tmm01_items` |
| `GET /suppliers/<cd>/prices` | `item_nm` | JOIN `tmm01_items` |

## 四、前端设计

### 4.1 交互流程

1. 供应商列表点击行 → 打开 Dialog（宽度 750px）
2. Tab 默认显示"基本信息"
3. 切换到"供应商品"Tab → 触发 `GET /suppliers/<cd>/items`
4. 切换到"价格报价"Tab → 触发 `GET /suppliers/<cd>/prices`

数据按 Tab 懒加载，避免打开弹窗时一次性请求所有数据。

### 4.2 供应商详情弹窗布局

SupplierList.vue 详情 Dialog 改为 **Tab 布局**：

| Tab | 内容 |
|-----|------|
| 基本信息 | 现有 el-descriptions（编码、名称、分类、联系人、电话、地址） |
| 供应商品 | 表格 + 新增/编辑/删除，显示 itemcd、itemnm、dfltflg、delivercycle、servicecycle、guaranteeperiod |
| 价格报价 | 表格 + 新增/编辑/删除，显示 itemcd、itemnm、min_qty、itemprice、effective_date、expire_date |

### 4.3 供应商品 Tab

```
┌─────────────────────────────────────────────────┐
│  物料编码 │ 名称  │ 默认 │ 配送周期│服务周期│保修期│操作│
│  PWR-001  │ 电源  │  ★  │ 7天    │ 30天  │ 365天│[编][删]│
│  PWR-002  │ 备用电│     │ 5天    │ 30天  │ 365天│[编][删]│
│                              [+ 新增供应商品]   │
└─────────────────────────────────────────────────┘
```

- **新增**：弹出下拉选择物料（搜索 + 树形），填写周期参数
- **编辑**：修改周期参数和默认标志
- **删除**：约束检查 → 确认 → 删除

### 4.4 价格报价 Tab

```
┌─────────────────────────────────────────────────┐
│  物料编码 │ 名称  │ 最小起订│ 单价  │ 生效  │ 失效  │操作│
│  PWR-001  │ 电源  │ 10     │ 150.00│2024-01│2024-12│[编][删]│
│                              [+ 新增报价]       │
└─────────────────────────────────────────────────┘
```

- **新增**：下拉选择已关联商品（仅显示供应商品 Tab 中已有的物料），填写价格信息
- **编辑**：修改价格、起订量、有效期
- **删除**：直接删除（tip02 价格记录无强业务约束）

### 4.5 数据一致性

两端操作同一张 `tmm24_custitems` 表：
- 供应商侧 `POST /suppliers/<cd>/items` ≡ 物料侧 `POST /items/<cd>/suppliers`
- 供应商侧删除 = 物料侧也看不到该关联

后端统一走同一个 Repository 方法，确保事务一致。

## 五、后端文件变更

| 文件 | 变更 |
|------|------|
| `app/api/system.py` | 新增 8 个路由（items 4 + prices 4） |
| `app/services/system_service.py` | 新增 supplier items CRUD + prices CRUD + 删除约束检查 |
| `app/repositories/system_repository.py` | 新增 supplier_items 查询（JOIN tmm01_items）、prices 查询、默认供应商切换 |
| `app/schemas/system.py` | 新增 `SupplierItemCreate`、`SupplierItemUpdate`、`SupplierPriceCreate`、`SupplierPriceUpdate` |

## 六、测试用例

- 供应商侧新增商品关联 → 成功 → 物料侧 ItemList 供应商 tab 同步可见
- 设置默认供应商 → 该物料其他供应商 dfltflg 自动变为 N
- 删除有关联采购订单的商品关联 → 409
- 新增价格 → 成功（仅限已关联商品）
- 过期报价不显示在采购订单供应商推荐中

## 七、实施工期

| 任务 | 工期 |
|------|------|
| 后端：supplier items CRUD + 价格 CRUD | 1 天 |
| 前端：详情弹窗 Tab 改造 | 1 天 |
| 联调 | 0.5 天 |
| **合计** | **2.5 天** |
