---
类型: 技术设计文档
阅读状态: 待评审
tags:
  - 供应商管理
  - CRUD
  - 前端
  - 后端
更新日期: 2026-05-24
创建日期: 2026-05-24
作者: CJ
版本: v1.0
---

# 供应商主数据 CRUD 功能设计规格

## 一、设计目标

补全供应商主数据（tmm19_suppliers）的增删改查功能。Python 模型 21 个字段已齐全，当前缺失的是 API（仅 GET）和前端（只读列表）。PB 版有完整的树形分类导航 + 搜索 + CRUD。

## 二、字段分级

| 级别 | 字段 | 显示位置 | 说明 |
|------|------|---------|------|
| L1 核心 | supp_cd, supp_nm, custanm, custbrcd, class_cd, contactor, phoneno, useflg | 列表 + 表单 | 日常采购常用 |
| L2 扩展 | address, zipcd, faxno, taxno, banknm, bankaccno, pcrep | 仅表单（折叠） | 下单/开票时用 |
| L3 遗留 | scale, suppinfo, agreements, custcd, custnm, opercd, gendate, upddate | 表单底部或隐藏 | Oracle 遗留，基本不用 |

## 三、后端设计

### 3.1 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/suppliers` | 列表（已有，需增加分页和搜索参数） |
| GET | `/suppliers/<supp_cd>` | 详情（新增） |
| POST | `/suppliers` | 新增（新增） |
| PUT | `/suppliers/<supp_cd>` | 编辑（新增） |
| DELETE | `/suppliers/<supp_cd>` | 删除（新增，逻辑删除 useflg='0'） |
| GET | `/supplierclasses` | 供应商分类列表（新增） |
| POST | `/supplierclasses` | 新增分类（新增） |
| PUT | `/supplierclasses/<class_cd>` | 编辑分类（新增） |
| DELETE | `/supplierclasses/<class_cd>` | 删除分类（新增） |

### 3.2 自动编号规则

新供应商编码自动生成：查询最大 `supp_cd`（8 位数字），加 1 后左侧补零。用户也可手动输入。

### 3.3 删除约束检查

删除前检查供应商在以下表中是否存在关联数据：

| 检查表 | 检查内容 | 说明 |
|--------|---------|------|
| `tpc12_register` | `suppliercd = :supp_cd` | 采购订单引用了该供应商 |
| `tip02_supplier_price` | `supp_cd = :supp_cd` | 维护了供应商价格 |
| `tmm24_custitems` | `custcd = :supp_cd` | 维护了供应商-商品关联 |
| `tpc21_suppappraisaldt` | `supplierid = :supp_cd` | 有供应商评价记录 |

- 任一检查命中 → 返回 `409 Conflict`，提示具体原因
- 全部通过 → 执行逻辑删除（`useflg='0'`），不物理删除

这与 PB 版行为一致：有业务关联的供应商不允许删除，只能停用。

### 3.4 供应商分类 CRUD

分类表 `tmm18_supplierclass` 需独立管理：

- **新增分类**：填写 class_cd(编码)、class_nm(名称)、parent(上级编码，支持树形层级)、classtyp(分类类型)
- **编辑分类**：修改名称、上级、类型
- **删除分类**：检查是否有子节点、是否有供应商引用该分类 → 有则 409，无则允许删除

前端在分类树区域添加右键菜单或小按钮支持"新增子分类/编辑/删除"。

### 3.5 新增/修改需覆盖的字段

创建和编辑共用同一个 Schema，包含 L1+L2 全部字段。L3 字段中的 `scale`、`suppinfo`、`agreements` 表单内可选填写，`custcd`/`custnm`/`opercd`/`gendate`/`upddate` 由后端自动维护。

### 3.6 文件变更

| 文件 | 变更 |
|------|------|
| `app/api/system.py` | 新增供应商 CRUD 5 个路由 + 分类 CRUD 3 个路由 |
| `app/services/system_service.py` | 新增供应商 CRUD 方法 + 分类 CRUD 方法 + 删除约束检查 |
| `app/repositories/system_repository.py` | 新增对应 Repository 方法 + 关联数据检查查询 |
| `app/schemas/system.py` | 新增 `SupplierCreate`、`SupplierUpdate`、`SupplierClassCreate` Schema |

## 四、前端设计

### 4.1 页面布局

```
┌─────────────────────────────────────────────────────────┐
│  供应商管理                         [🔍搜索] [+新增供应商] │
├────────────┬────────────────────────────────────────────┤
│ 分类树     │ 列表（分页）                                │
│ ├─ 全部   │ 编码 │名称│简称│分类│联系人│电话│状态│操作  │
│ ├─ 原材料 │ ...                               [编辑][删]│
│ ├─ 配件   │                                              │
│ └─ 服务   │                        共 156 条  [分页组件] │
└────────────┴────────────────────────────────────────────┘
```

### 4.2 新增/编辑弹窗

使用 Element Plus Dialog，宽度 650px：
- **基本信息区**：supp_cd(自动编号/手动)、supp_nm*、custanm、custbrcd、class_cd、contactor、phoneno、useflg(开关)
- **扩展信息区**（el-collapse 折叠）：address、zipcd、faxno、taxno、banknm、bankaccno、pcrep、scale

### 4.3 搜索

顶部搜索框支持按 `supp_nm` 和 `supp_cd` 模糊搜索，后端 `GET /suppliers?keyword=xxx`。

### 4.4 分类树交互

点击分类节点筛选该分类下的供应商。分类树数据来源 `GET /suppliers/classes`。

### 4.5 文件变更

| 文件 | 变更 |
|------|------|
| `frontend/src/views/procurement/SupplierList.vue` | 重写：增加 CRUD、分类树、搜索、分页 |
| `frontend/src/api/master.ts` | 新增 `createSupplier`、`updateSupplier`、`deleteSupplier`、`fetchSupplierClasses` |

## 五、测试用例

- 新增供应商：填写必填字段 → 成功 → 列表刷新
- 编辑供应商：修改联系人/电话 → 成功
- 删除供应商（无关联）：确认 → useflg='0' → 列表不再显示
- 删除供应商（有采购订单关联）：返回 409，"该供应商存在采购订单关联，无法删除"
- 删除供应商（有商品关联）：返回 409
- 删除供应商（有价格记录）：返回 409
- 重复编码校验：输入已存在的 supp_cd → 后端返回 400
- 分类树筛选：点击"配件"节点 → 列表仅显示 class_cd 为配件的供应商
- 搜索：输入"科技" → 列出名称含"科技"的供应商
- 新增分类：填写编码/名称 → 成功 → 分类树刷新
- 删除分类（有子节点或供应商引用）：返回 409
- 删除分类（无引用）：成功

## 六、实施工期

| 任务 | 工期 |
|------|------|
| 后端：供应商 CRUD API + 删除约束检查 | 0.5 天 |
| 后端：分类 CRUD API | 0.5 天 |
| 前端：列表页改造 + 弹窗表单 + 分类树交互 | 1 天 |
| 联调 | 0.5 天 |
| **合计** | **2.5 天** |
