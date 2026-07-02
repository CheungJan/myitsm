# 采购供应商 + 拆单并单 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 依次实现供应商主数据 CRUD → 供应商商品关联+价格 → 采购订单拆单/并单，形成完整的采购业务链

**Architecture:** 三阶段串行实施。Phase A 补全 tmm19/tmm18 的 CRUD，Phase B 补全 tmm24/tip02 的供应商侧管理入口，Phase C 增加批量订单创建 + 智能合并 + advisory lock 并发控制

**Tech Stack:** Flask + SQLAlchemy + PostgreSQL, Vue 3 + Element Plus + TypeScript

**规格文档:**
- `docs/superpowers/specs/2026-05-24-supplier-master-crud.md`
- `docs/superpowers/specs/2026-05-24-supplier-item-mapping.md`
- `docs/superpowers/specs/2026-05-24-procurement-split-merge-design.md`

---

## Phase A: 供应商主数据 CRUD

### Task A1: 供应商分类 API（后端）

**Files:**
- Modify: `app/repositories/system_repository.py` (追加方法)
- Modify: `app/services/system_service.py` (追加方法)
- Modify: `app/api/system.py` (追加路由)

- [ ] **Step 1: 在 Repository 中新增分类 CRUD 方法**

在 `app/repositories/system_repository.py` 末尾追加：

```python
# ========== SupplierClass CRUD ==========

@staticmethod
def get_supplier_classes() -> list[dict[str, Any]]:
    """获取供应商分类列表（用于树形结构）。"""
    rows = db.session.query(SupplierClass).order_by(SupplierClass.class_cd).all()
    return [r.to_dict() for r in rows]

@staticmethod
def get_supplier_class(class_cd: str):
    """获取单个供应商分类。"""
    return db.session.get(SupplierClass, class_cd)

@staticmethod
def create_supplier_class(data: dict[str, Any]) -> SupplierClass:
    """新增供应商分类。"""
    obj = SupplierClass(**data)
    db.session.add(obj)
    db.session.flush()
    return obj

@staticmethod
def update_supplier_class(obj: SupplierClass, data: dict[str, Any]) -> SupplierClass:
    """更新供应商分类。"""
    for k, v in data.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.session.flush()
    return obj

@staticmethod
def delete_supplier_class(obj: SupplierClass) -> None:
    """删除供应商分类。"""
    db.session.delete(obj)
    db.session.flush()

@staticmethod
def count_suppliers_by_class(class_cd: str) -> int:
    """统计某分类下的供应商数量。"""
    return db.session.query(Supplier).filter(Supplier.class_cd == class_cd, Supplier.useflg == "1").count()

@staticmethod
def count_child_classes(class_cd: str) -> int:
    """统计某分类下的子分类数量。"""
    return db.session.query(SupplierClass).filter(SupplierClass.parent == class_cd).count()
```

在文件顶部 import 区域追加 `SupplierClass` 和 `Supplier`：
```python
from app.models.master import (
    ...,
    SupplierClass,
    Supplier,
)
```

- [ ] **Step 2: 在 Service 中新增分类 CRUD 方法**

在 `app/services/system_service.py` 末尾追加：

```python
def get_supplier_classes(self) -> list[dict[str, Any]]:
    return self._repo.get_supplier_classes()

def create_supplier_class(self, data: dict[str, Any]) -> dict[str, Any]:
    existing = self._repo.get_supplier_class(data["class_cd"])
    if existing:
        raise ValueError(f"分类编码 {data['class_cd']} 已存在")
    return self._repo.create_supplier_class(data).to_dict()

def update_supplier_class(self, class_cd: str, data: dict[str, Any]) -> dict[str, Any]:
    obj = self._repo.get_supplier_class(class_cd)
    if not obj:
        raise ValueError(f"分类 {class_cd} 不存在")
    return self._repo.update_supplier_class(obj, data).to_dict()

def delete_supplier_class(self, class_cd: str) -> None:
    obj = self._repo.get_supplier_class(class_cd)
    if not obj:
        raise ValueError(f"分类 {class_cd} 不存在")
    child_count = self._repo.count_child_classes(class_cd)
    if child_count > 0:
        raise ValueError(f"分类 {class_cd} 下存在 {child_count} 个子分类，无法删除")
    supplier_count = self._repo.count_suppliers_by_class(class_cd)
    if supplier_count > 0:
        raise ValueError(f"分类 {class_cd} 下存在 {supplier_count} 个供应商，无法删除")
    self._repo.delete_supplier_class(obj)
```

- [ ] **Step 3: 在 API 中新增分类路由**

在 `app/api/system.py` 中追加（放在 `/suppliers` 路由附近）：

```python
@system_bp.get("/supplierclasses")
@login_required
def list_supplier_classes():  # type: ignore[no-untyped-def]
    """供应商分类列表。"""
    return success_response(data=_service.get_supplier_classes())

@system_bp.post("/supplierclasses")
@login_required
def create_supplier_class():  # type: ignore[no-untyped-def]
    """新增供应商分类。"""
    json_data = request.get_json(silent=True) or {}
    if not json_data.get("class_cd") or not json_data.get("class_nm"):
        return error_response("分类编码和名称不能为空", 400)
    try:
        return success_response(data=_service.create_supplier_class(json_data), code=201)
    except ValueError as e:
        return error_response(str(e), 400)

@system_bp.put("/supplierclasses/<class_cd>")
@login_required
def update_supplier_class(class_cd: str):  # type: ignore[no-untyped-def]
    """编辑供应商分类。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.update_supplier_class(class_cd, json_data))
    except ValueError as e:
        return error_response(str(e), 400)

@system_bp.delete("/supplierclasses/<class_cd>")
@login_required
def delete_supplier_class(class_cd: str):  # type: ignore[no-untyped-def]
    """删除供应商分类。"""
    try:
        _service.delete_supplier_class(class_cd)
        return success_response(message="删除成功")
    except ValueError as e:
        return error_response(str(e), 409)
```

- [ ] **Step 4: 运行测试验证**

```bash
uv run pytest tests/ -x -q --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add app/repositories/system_repository.py app/services/system_service.py app/api/system.py
git commit -m "feat(supplier): 供应商分类 CRUD API"
```

---

### Task A2: 供应商主数据 CRUD API（后端）

**Files:**
- Modify: `app/repositories/system_repository.py`
- Modify: `app/services/system_service.py`
- Modify: `app/api/system.py`

- [ ] **Step 1: 在 Repository 中新增供应商 CRUD 方法**

在 `app/repositories/system_repository.py` 追加：

```python
# ========== Supplier CRUD ==========

@staticmethod
def get_supplier(supp_cd: str):
    """获取单个供应商。"""
    return db.session.get(Supplier, supp_cd)

@staticmethod
def list_suppliers_paginated(keyword: str = "", class_cd: str = "", page: int = 1, per_page: int = 20):
    """分页查询供应商列表，支持搜索和分类筛选。"""
    q = db.session.query(Supplier)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(db.or_(Supplier.supp_nm.ilike(like), Supplier.supp_cd.ilike(like)))
    if class_cd:
        q = q.filter(Supplier.class_cd == class_cd)
    q = q.order_by(Supplier.supp_cd)
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    }

@staticmethod
def get_max_supp_cd() -> str | None:
    """获取当前最大供应商编码（用于自动编号）。"""
    row = db.session.query(db.func.max(Supplier.supp_cd)).filter(
        Supplier.supp_cd.regexp_match(r'^\d{8}$')
    ).scalar()
    return row

@staticmethod
def create_supplier(data: dict[str, Any]) -> Supplier:
    """新增供应商。"""
    obj = Supplier(**data)
    db.session.add(obj)
    db.session.flush()
    return obj

@staticmethod
def update_supplier(obj: Supplier, data: dict[str, Any]) -> Supplier:
    """更新供应商。"""
    readonly = {"supp_cd", "custcd", "custnm", "opercd", "gendate", "upddate"}
    for k, v in data.items():
        if hasattr(obj, k) and k not in readonly:
            setattr(obj, k, v)
    db.session.flush()
    return obj

@staticmethod
def delete_supplier(obj: Supplier) -> None:
    """逻辑删除供应商（useflg='0'）。"""
    obj.useflg = "0"
    db.session.flush()
```

在 import 中追加 `db` 的 `or_`：
```python
from app.extensions import db
import sqlalchemy as sa  # 如果尚未导入
```

- [ ] **Step 2: 在 Service 中新增供应商 CRUD 方法**

在 `app/services/system_service.py` 追加：

```python
def get_supplier(self, supp_cd: str) -> dict[str, Any] | None:
    obj = self._repo.get_supplier(supp_cd)
    return obj.to_dict() if obj else None

def list_suppliers(self, keyword: str = "", class_cd: str = "", page: int = 1, per_page: int = 20) -> dict[str, Any]:
    return self._repo.list_suppliers_paginated(keyword, class_cd, page, per_page)

def create_supplier(self, data: dict[str, Any]) -> dict[str, Any]:
    supp_cd = data.get("supp_cd", "").strip()
    if supp_cd:
        existing = self._repo.get_supplier(supp_cd)
        if existing:
            raise ValueError(f"供应商编码 {supp_cd} 已存在")
    else:
        # 自动编号：8位数字递增
        max_cd = self._repo.get_max_supp_cd()
        next_num = int(max_cd) + 1 if max_cd else 1
        supp_cd = str(next_num).zfill(8)
        data["supp_cd"] = supp_cd
    if not data.get("supp_nm"):
        raise ValueError("供应商名称不能为空")
    return self._repo.create_supplier(data).to_dict()

def update_supplier(self, supp_cd: str, data: dict[str, Any]) -> dict[str, Any]:
    obj = self._repo.get_supplier(supp_cd)
    if not obj:
        raise ValueError(f"供应商 {supp_cd} 不存在")
    return self._repo.update_supplier(obj, data).to_dict()

def delete_supplier(self, supp_cd: str) -> dict[str, Any]:
    """删除供应商，返回约束检查结果。"""
    obj = self._repo.get_supplier(supp_cd)
    if not obj:
        raise ValueError(f"供应商 {supp_cd} 不存在")
    conflicts = self._check_supplier_delete_conflicts(supp_cd)
    if conflicts:
        raise ValueError(f"该供应商存在以下关联：{'; '.join(conflicts)}，无法删除")
    self._repo.delete_supplier(obj)
    return {"supp_cd": supp_cd, "conflicts": []}

def _check_supplier_delete_conflicts(self, supp_cd: str) -> list[str]:
    """检查供应商删除约束。"""
    conflicts = []
    if self._repo.count_orders_by_supplier(supp_cd) > 0:
        conflicts.append("采购订单关联")
    if self._repo.count_prices_by_supplier(supp_cd) > 0:
        conflicts.append("供应商价格记录")
    if self._repo.count_custitems_by_supplier(supp_cd) > 0:
        conflicts.append("供应商商品关联")
    if self._repo.count_appraisals_by_supplier(supp_cd) > 0:
        conflicts.append("供应商评价记录")
    return conflicts
```

- [ ] **Step 3: 在 Repository 中新增约束检查查询方法**

在 `app/repositories/system_repository.py` 追加：

```python
@staticmethod
def count_orders_by_supplier(supp_cd: str) -> int:
    from app.models.procurement import PurchaseRegister
    return db.session.query(PurchaseRegister).filter(PurchaseRegister.suppliercd == supp_cd).count()

@staticmethod
def count_prices_by_supplier(supp_cd: str) -> int:
    from app.models.inventory import SupplierPrice
    return db.session.query(SupplierPrice).filter(SupplierPrice.supp_cd == supp_cd).count()

@staticmethod
def count_custitems_by_supplier(supp_cd: str) -> int:
    return db.session.query(CustItems).filter(CustItems.custcd == supp_cd).count()

@staticmethod
def count_appraisals_by_supplier(supp_cd: str) -> int:
    from app.models.procurement import SupplierAppraisalDt
    return db.session.query(SupplierAppraisalDt).filter(SupplierAppraisalDt.supplierid == supp_cd).count()
```

- [ ] **Step 4: 在 API 中新增/修改供应商路由**

修改 `app/api/system.py` 中现有的 `list_all_suppliers`，并新增路由：

```python
@system_bp.get("/suppliers")
@login_required
def list_suppliers():  # type: ignore[no-untyped-def]
    """供应商列表（分页 + 搜索 + 分类筛选）。"""
    keyword = request.args.get("keyword", "").strip()
    class_cd = request.args.get("class_cd", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return success_response(data=_service.list_suppliers(keyword, class_cd, page, per_page))

@system_bp.get("/suppliers/<supp_cd>")
@login_required
def get_supplier(supp_cd: str):  # type: ignore[no-untyped-def]
    """供应商详情。"""
    data = _service.get_supplier(supp_cd)
    if not data:
        return error_response("供应商不存在", 404)
    return success_response(data=data)

@system_bp.post("/suppliers")
@login_required
def create_supplier():  # type: ignore[no-untyped-def]
    """新增供应商。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.create_supplier(json_data), code=201)
    except ValueError as e:
        return error_response(str(e), 400)

@system_bp.put("/suppliers/<supp_cd>")
@login_required
def update_supplier(supp_cd: str):  # type: ignore[no-untyped-def]
    """编辑供应商。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.update_supplier(supp_cd, json_data))
    except ValueError as e:
        return error_response(str(e), 400)

@system_bp.delete("/suppliers/<supp_cd>")
@login_required
def delete_supplier(supp_cd: str):  # type: ignore[no-untyped-def]
    """删除供应商（逻辑删除）。"""
    try:
        result = _service.delete_supplier(supp_cd)
        return success_response(data=result, message="删除成功")
    except ValueError as e:
        return error_response(str(e), 409)
```

- [ ] **Step 5: 运行测试**

```bash
uv run pytest tests/ -x -q --tb=short
```

- [ ] **Step 6: Commit**

```bash
git add app/repositories/system_repository.py app/services/system_service.py app/api/system.py
git commit -m "feat(supplier): 供应商主数据 CRUD API + 删除约束检查 + 自动编号"
```

---

### Task A3: 前端 — SupplierList.vue 重写（分类树 + 搜索 + CRUD）

**Files:**
- Modify: `frontend/src/views/procurement/SupplierList.vue`
- Modify: `frontend/src/api/master.ts`

- [ ] **Step 1: 新增前端 API 函数**

在 `frontend/src/api/master.ts` 末尾追加：

```typescript
// 供应商 CRUD
export const fetchSuppliersPaginated = (params: { keyword?: string; class_cd?: string; page?: number; per_page?: number }) =>
  request.get('/suppliers', { params })

export const fetchSupplierDetail = (suppCd: string) =>
  request.get(`/suppliers/${suppCd}`)

export const createSupplier = (data: Record<string, unknown>) =>
  request.post('/suppliers', data)

export const updateSupplier = (suppCd: string, data: Record<string, unknown>) =>
  request.put(`/suppliers/${suppCd}`, data)

export const deleteSupplier = (suppCd: string) =>
  request.delete(`/suppliers/${suppCd}`)

// 供应商分类
export const fetchSupplierClasses = () =>
  request.get('/supplierclasses')

export const createSupplierClass = (data: Record<string, unknown>) =>
  request.post('/supplierclasses', data)

export const updateSupplierClass = (classCd: string, data: Record<string, unknown>) =>
  request.put(`/supplierclasses/${classCd}`, data)

export const deleteSupplierClass = (classCd: string) =>
  request.delete(`/supplierclasses/${classCd}`)
```

- [ ] **Step 2: 重写 SupplierList.vue**

将 `frontend/src/views/procurement/SupplierList.vue` 完整替换为：

```vue
<template>
  <div class="page">
    <div class="page-header">
      <h2>供应商管理</h2>
      <div style="display:flex;gap:8px;">
        <el-input v-model="searchKeyword" placeholder="搜索编码/名称" clearable style="width:200px" size="small" @keyup.enter="handleSearch" @clear="handleSearch" />
        <el-button type="primary" size="small" @click="openCreate">新增供应商</el-button>
      </div>
    </div>
    <div style="display:flex;gap:12px;">
      <!-- 分类树 -->
      <div style="width:180px;flex-shrink:0;">
        <el-card shadow="never" style="height:100%;">
          <template #header><span style="font-size:14px;font-weight:600;">供应商分类</span></template>
          <el-menu :default-active="activeClass" @select="handleClassSelect" style="border-right:none;">
            <el-menu-item index="">全部</el-menu-item>
            <el-menu-item v-for="c in classList" :key="c.class_cd" :index="c.class_cd">
              {{ c.class_nm }}
            </el-menu-item>
          </el-menu>
          <div style="padding:8px;border-top:1px solid #ebeef5;margin-top:8px;">
            <el-button link size="small" @click="openClassDialog(null)">+ 新增分类</el-button>
          </div>
        </el-card>
      </div>
      <!-- 列表 -->
      <div style="flex:1;">
        <el-card shadow="never">
          <el-table :data="items" v-loading="loading" stripe size="small" highlight-current-row>
            <el-table-column prop="supp_cd" label="编码" width="90" />
            <el-table-column prop="supp_nm" label="名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="custanm" label="简称" width="100" />
            <el-table-column label="分类" width="100">
              <template #default="{row}">{{ classMap[row.class_cd] || row.class_cd }}</template>
            </el-table-column>
            <el-table-column prop="contactor" label="联系人" width="80" />
            <el-table-column prop="phoneno" label="电话" width="110" />
            <el-table-column label="状态" width="70">
              <template #default="{row}">
                <el-tag :type="row.useflg==='0'?'info':'success'" size="small">{{ row.useflg==='0'?'停用':'启用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{row}">
                <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
                <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:12px;display:flex;justify-content:space-between;align-items:center;">
            <span style="color:#909399;font-size:13px;">共 {{ total }} 条</span>
            <el-pagination v-model:current-page="page" :page-size="perPage" :total="total" layout="prev,pager,next" small @current-change="load" />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="formTitle" v-model="formVisible" width="650px" @close="resetForm">
      <el-form ref="formRef" :model="form" label-width="100px" size="small">
        <el-divider content-position="left">基本信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="编码">
              <el-input v-model="form.supp_cd" :disabled="isEdit" :placeholder="isEdit?'':'留空自动生成'" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="名称" required>
              <el-input v-model="form.supp_nm" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="简称"><el-input v-model="form.custanm" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="简码"><el-input v-model="form.custbrcd" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="分类"><el-select v-model="form.class_cd" style="width:100%"><el-option v-for="c in classList" :key="c.class_cd" :label="c.class_nm" :value="c.class_cd" /></el-select></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态"><el-switch v-model="form.useflg" active-value="1" inactive-value="0" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联系人"><el-input v-model="form.contactor" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话"><el-input v-model="form.phoneno" /></el-form-item>
          </el-col>
        </el-row>
        <el-collapse>
          <el-collapse-item title="扩展信息">
            <el-row :gutter="16">
              <el-col :span="24"><el-form-item label="地址"><el-input v-model="form.address" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="8"><el-form-item label="邮编"><el-input v-model="form.zipcd" /></el-form-item></el-col>
              <el-col :span="8"><el-form-item label="传真"><el-input v-model="form.faxno" /></el-form-item></el-col>
              <el-col :span="8"><el-form-item label="等级"><el-input v-model="form.scale" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="24"><el-form-item label="税号"><el-input v-model="form.taxno" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="开户银行"><el-input v-model="form.banknm" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="银行账号"><el-input v-model="form.bankaccno" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="采购代表"><el-input v-model="form.pcrep" /></el-form-item></el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>
      </el-form>
      <template #footer>
        <el-button size="small" @click="formVisible=false">取消</el-button>
        <el-button type="primary" size="small" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分类管理弹窗 -->
    <el-dialog :title="classDialogTitle" v-model="classDialogVisible" width="400px">
      <el-form :model="classForm" label-width="80px" size="small">
        <el-form-item label="编码" required><el-input v-model="classForm.class_cd" :disabled="classIsEdit" /></el-form-item>
        <el-form-item label="名称" required><el-input v-model="classForm.class_nm" /></el-form-item>
        <el-form-item label="上级"><el-select v-model="classForm.parent" style="width:100%" clearable><el-option v-for="c in classList" :key="c.class_cd" :label="c.class_nm" :value="c.class_cd" /></el-select></el-form-item>
        <el-form-item label="类型"><el-input v-model="classForm.classtyp" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="classDialogVisible=false">取消</el-button>
        <el-button v-if="!classIsEdit" link type="danger" size="small" @click="handleDeleteClass">删除</el-button>
        <el-button type="primary" size="small" @click="handleSaveClass">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchSuppliersPaginated, createSupplier, updateSupplier, deleteSupplier,
  fetchSupplierClasses, createSupplierClass, updateSupplierClass, deleteSupplierClass
} from '@/api/master'

const searchKeyword = ref('')
const activeClass = ref('')
const page = ref(1)
const perPage = 20
const total = ref(0)
const items = ref<Record<string,unknown>[]>([])
const loading = ref(false)
const saving = ref(false)
const classList = ref<Record<string,unknown>[]>([])
const classMap = computed(() => {
  const m: Record<string,string> = {}
  classList.value.forEach((c: any) => { m[c.class_cd] = c.class_nm })
  return m
})

// 表单
const formVisible = ref(false)
const isEdit = ref(false)
const form = reactive<Record<string,unknown>>({
  supp_cd: '', supp_nm: '', custanm: '', custbrcd: '', class_cd: '',
  contactor: '', phoneno: '', useflg: '1',
  address: '', zipcd: '', faxno: '', taxno: '', banknm: '', bankaccno: '', pcrep: '', scale: ''
})
const formTitle = computed(() => isEdit.value ? '编辑供应商' : '新增供应商')

// 分类表单
const classDialogVisible = ref(false)
const classIsEdit = ref(false)
const classForm = reactive({ class_cd: '', class_nm: '', parent: '', classtyp: '' })
const classDialogTitle = computed(() => classIsEdit.value ? '编辑分类' : '新增分类')

async function load() {
  loading.value = true
  try {
    const res = await fetchSuppliersPaginated({ keyword: searchKeyword.value, class_cd: activeClass.value, page: page.value, per_page: perPage })
    const d = res.data as any
    items.value = d.items || []
    total.value = d.total || 0
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

async function loadClasses() {
  try { const r = await fetchSupplierClasses(); classList.value = (r.data as any[]) || [] } catch { /**/ }
}

function handleSearch() { page.value = 1; load() }
function handleClassSelect(index: string) { activeClass.value = index; page.value = 1; load() }

function resetForm() {
  Object.keys(form).forEach(k => { form[k] = '' })
  form.useflg = '1'
  isEdit.value = false
}

function openCreate() { resetForm(); formVisible.value = true }
function openEdit(row: any) {
  isEdit.value = true
  Object.keys(form).forEach(k => { if (row[k] !== undefined) form[k] = row[k] })
  formVisible.value = true
}

function openDetail(row: any) {
  // Phase B 将改造为 Tab 弹窗
  ElMessage.info('详情功能将在 Phase B 实现')
}

async function handleSave() {
  if (!form.supp_nm) { ElMessage.warning('请输入供应商名称'); return }
  saving.value = true
  try {
    const data = { ...form }
    if (isEdit.value) {
      await updateSupplier(form.supp_cd as string, data)
      ElMessage.success('修改成功')
    } else {
      await createSupplier(data)
      ElMessage.success('新增成功')
    }
    formVisible.value = false
    await load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
  finally { saving.value = false }
}

async function handleDelete(row: any) {
  try { await ElMessageBox.confirm(`确定删除供应商 ${row.supp_nm}？`, '确认删除', { type: 'warning' }) } catch { return }
  try {
    await deleteSupplier(row.supp_cd as string)
    ElMessage.success('删除成功')
    await load()
  } catch (e: any) {
    const msg = e?.response?.data?.message || '删除失败'
    ElMessage.error(msg)
  }
}

function openClassDialog(row?: any) {
  if (row) {
    classIsEdit.value = true
    classForm.class_cd = row.class_cd
    classForm.class_nm = row.class_nm
    classForm.parent = row.parent || ''
    classForm.classtyp = row.classtyp || ''
  } else {
    classIsEdit.value = false
    Object.keys(classForm).forEach(k => { (classForm as any)[k] = '' })
  }
  classDialogVisible.value = true
}

async function handleSaveClass() {
  if (!classForm.class_cd || !classForm.class_nm) { ElMessage.warning('编码和名称不能为空'); return }
  try {
    if (classIsEdit.value) {
      await updateSupplierClass(classForm.class_cd, classForm)
      ElMessage.success('修改成功')
    } else {
      await createSupplierClass(classForm)
      ElMessage.success('新增成功')
    }
    classDialogVisible.value = false
    await loadClasses()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
}

async function handleDeleteClass() {
  try { await ElMessageBox.confirm(`确定删除分类 ${classForm.class_nm}？`, '确认', { type: 'warning' }) } catch { return }
  try {
    await deleteSupplierClass(classForm.class_cd)
    ElMessage.success('删除成功')
    classDialogVisible.value = false
    await loadClasses()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

onMounted(() => { loadClasses(); load() })
</script>

<style scoped>
.page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; margin: 0; }
</style>
```

- [ ] **Step 3: 验证构建**

```bash
cd frontend && npm run build --if-present 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/procurement/SupplierList.vue frontend/src/api/master.ts
git commit -m "feat(supplier): SupplierList 重写 — 分类树 + 搜索 + CRUD 弹窗"
```

---

## Phase B: 供应商商品关联 + 价格维护

### Task B1: 供应商侧 items API（后端）

**Files:**
- Modify: `app/repositories/system_repository.py`
- Modify: `app/services/system_service.py`
- Modify: `app/api/system.py`

- [ ] **Step 1: Repository 新增 supplier items 查询方法**

在 `app/repositories/system_repository.py` 追加：

```python
# ========== Supplier Items (tmm24) ==========

@staticmethod
def get_supplier_items(supp_cd: str) -> list[dict[str, Any]]:
    """查询供应商关联的商品列表，含物料名称、单位、分类。"""
    from app.models.master import Item
    rows = (
        db.session.query(CustItems, Item.item_nm, Item.item_unit, Item.class_cd)
        .join(Item, CustItems.itemcd == Item.item_cd)
        .filter(CustItems.custcd == supp_cd)
        .all()
    )
    result = []
    for ci, item_nm, item_unit, class_cd in rows:
        d = ci.to_dict()
        d["item_nm"] = item_nm
        d["item_unit"] = item_unit
        d["class_cd"] = class_cd
        result.append(d)
    return result

@staticmethod
def get_supplier_item(supp_cd: str, item_cd: str):
    """获取单个供应商-商品关联。"""
    return db.session.query(CustItems).filter(
        CustItems.custcd == supp_cd,
        CustItems.itemcd == item_cd
    ).first()

@staticmethod
def add_supplier_item(supp_cd: str, data: dict[str, Any]) -> CustItems:
    """新增供应商-商品关联。"""
    obj = CustItems(custcd=supp_cd, itemcd=data["itemcd"], **{k: v for k, v in data.items() if k != "itemcd"})
    db.session.add(obj)
    db.session.flush()
    return obj

@staticmethod
def set_item_default_supplier(item_cd: str, cust_cd: str) -> None:
    """将该物料其他供应商的默认标志清除。"""
    db.session.query(CustItems).filter(
        CustItems.itemcd == item_cd,
        CustItems.custcd != cust_cd,
        CustItems.dfltflg == "Y"
    ).update({"dfltflg": "N"})

@staticmethod
def delete_supplier_item(obj: CustItems) -> None:
    """删除供应商-商品关联。"""
    db.session.delete(obj)
    db.session.flush()

@staticmethod
def check_supplier_item_has_orders(supp_cd: str, item_cd: str) -> bool:
    """检查供应商-商品关联是否有对应的采购订单。"""
    from app.models.procurement import PurchaseRegister, RequisitionOrderLink
    count = (
        db.session.query(RequisitionOrderLink)
        .join(PurchaseRegister, RequisitionOrderLink.rgstbillid == PurchaseRegister.rgstbillid)
        .filter(
            PurchaseRegister.suppliercd == supp_cd,
            RequisitionOrderLink.pcplanid.isnot(None)
        )
        .count()
    )
    return count > 0
```

- [ ] **Step 2: Service 新增方法**

在 `app/services/system_service.py` 追加：

```python
def get_supplier_items(self, supp_cd: str) -> list[dict[str, Any]]:
    return self._repo.get_supplier_items(supp_cd)

def add_supplier_item(self, supp_cd: str, data: dict[str, Any]) -> dict[str, Any]:
    item_cd = data.get("itemcd", "")
    if not item_cd:
        raise ValueError("物料编码不能为空")
    existing = self._repo.get_supplier_item(supp_cd, item_cd)
    if existing:
        raise ValueError(f"物料 {item_cd} 已关联")
    if data.get("dfltflg") == "Y":
        self._repo.set_item_default_supplier(item_cd, supp_cd)
    return self._repo.add_supplier_item(supp_cd, data).to_dict()

def update_supplier_item(self, supp_cd: str, item_cd: str, data: dict[str, Any]) -> dict[str, Any]:
    obj = self._repo.get_supplier_item(supp_cd, item_cd)
    if not obj:
        raise ValueError("关联不存在")
    if data.get("dfltflg") == "Y":
        self._repo.set_item_default_supplier(item_cd, supp_cd)
    updatable = {"dfltflg", "delivercycle", "servicecycle", "guaranteeperiod", "backup", "useflg"}
    for k, v in data.items():
        if k in updatable and hasattr(obj, k):
            setattr(obj, k, v)
    db.session.flush()
    return obj.to_dict()

def delete_supplier_item(self, supp_cd: str, item_cd: str) -> None:
    obj = self._repo.get_supplier_item(supp_cd, item_cd)
    if not obj:
        raise ValueError("关联不存在")
    if self._repo.check_supplier_item_has_orders(supp_cd, item_cd):
        raise ValueError("该商品关联存在采购订单，无法删除")
    self._repo.delete_supplier_item(obj)
```

- [ ] **Step 3: API 新增路由**

在 `app/api/system.py` 追加：

```python
@system_bp.get("/suppliers/<supp_cd>/items")
@login_required
def list_supplier_items(supp_cd: str):  # type: ignore[no-untyped-def]
    """查询供应商关联的商品列表。"""
    return success_response(data=_service.get_supplier_items(supp_cd))

@system_bp.post("/suppliers/<supp_cd>/items")
@login_required
def add_supplier_item(supp_cd: str):  # type: ignore[no-untyped-def]
    """为供应商新增商品关联。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.add_supplier_item(supp_cd, json_data), code=201)
    except ValueError as e:
        return error_response(str(e), 400)

@system_bp.put("/suppliers/<supp_cd>/items/<item_cd>")
@login_required
def update_supplier_item(supp_cd: str, item_cd: str):  # type: ignore[no-untyped-def]
    """修改供应商-商品关联。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.update_supplier_item(supp_cd, item_cd, json_data))
    except ValueError as e:
        return error_response(str(e), 400)

@system_bp.delete("/suppliers/<supp_cd>/items/<item_cd>")
@login_required
def delete_supplier_item(supp_cd: str, item_cd: str):  # type: ignore[no-untyped-def]
    """删除供应商-商品关联。"""
    try:
        _service.delete_supplier_item(supp_cd, item_cd)
        return success_response(message="删除成功")
    except ValueError as e:
        return error_response(str(e), 409)
```

- [ ] **Step 4: 运行测试**

```bash
uv run pytest tests/ -x -q --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add app/repositories/system_repository.py app/services/system_service.py app/api/system.py
git commit -m "feat(supplier): 供应商侧商品关联 CRUD API"
```

---

### Task B2: 供应商价格 API（后端）

**Files:**
- Modify: `app/repositories/system_repository.py`
- Modify: `app/services/system_service.py`
- Modify: `app/api/system.py`

- [ ] **Step 1: Repository 新增价格查询方法**

在 `app/repositories/system_repository.py` 追加：

```python
# ========== Supplier Prices (tip02) ==========

@staticmethod
def get_supplier_prices(supp_cd: str, item_cd: str = "", current_only: bool = False) -> list[dict[str, Any]]:
    """查询供应商报价，支持物料筛选和当前有效筛选。"""
    from app.models.inventory import SupplierPrice
    from app.models.master import Item
    from datetime import date
    q = (
        db.session.query(SupplierPrice, Item.item_nm)
        .join(Item, SupplierPrice.itemcd == Item.item_cd)
        .filter(SupplierPrice.supp_cd == supp_cd)
    )
    if item_cd:
        q = q.filter(SupplierPrice.itemcd == item_cd)
    if current_only:
        today = date.today()
        q = q.filter(SupplierPrice.effective_date <= today, SupplierPrice.expire_date >= today)
    rows = q.order_by(SupplierPrice.itemcd, SupplierPrice.effective_date).all()
    result = []
    for sp, item_nm in rows:
        d = sp.to_dict()
        d["item_nm"] = item_nm
        result.append(d)
    return result

@staticmethod
def get_supplier_price(price_id: int):
    from app.models.inventory import SupplierPrice
    return db.session.get(SupplierPrice, price_id)

@staticmethod
def create_supplier_price(data: dict[str, Any]) -> SupplierPrice:
    from app.models.inventory import SupplierPrice
    obj = SupplierPrice(**data)
    db.session.add(obj)
    db.session.flush()
    return obj

@staticmethod
def update_supplier_price(obj: SupplierPrice, data: dict[str, Any]) -> SupplierPrice:
    for k, v in data.items():
        if hasattr(obj, k) and k not in {"id", "opercd", "gendate", "upddate"}:
            setattr(obj, k, v)
    db.session.flush()
    return obj

@staticmethod
def delete_supplier_price(obj: SupplierPrice) -> None:
    db.session.delete(obj)
    db.session.flush()

@staticmethod
def check_custitems_exists(supp_cd: str, item_cd: str) -> bool:
    """检查供应商-商品关联是否存在。"""
    return db.session.query(CustItems).filter(
        CustItems.custcd == supp_cd, CustItems.itemcd == item_cd
    ).first() is not None
```

- [ ] **Step 2: Service 新增价格方法**

在 `app/services/system_service.py` 追加：

```python
def get_supplier_prices(self, supp_cd: str, item_cd: str = "", current_only: bool = False) -> list[dict[str, Any]]:
    return self._repo.get_supplier_prices(supp_cd, item_cd, current_only)

def create_supplier_price(self, supp_cd: str, data: dict[str, Any]) -> dict[str, Any]:
    item_cd = data.get("itemcd", "")
    if not item_cd:
        raise ValueError("物料编码不能为空")
    if not self._repo.check_custitems_exists(supp_cd, item_cd):
        raise ValueError("该供应商未关联此商品，请先维护供应商品关系")
    data["supp_cd"] = supp_cd
    return self._repo.create_supplier_price(data).to_dict()

def update_supplier_price(self, price_id: int, data: dict[str, Any]) -> dict[str, Any]:
    obj = self._repo.get_supplier_price(price_id)
    if not obj:
        raise ValueError("报价记录不存在")
    return self._repo.update_supplier_price(obj, data).to_dict()

def delete_supplier_price(self, price_id: int) -> None:
    obj = self._repo.get_supplier_price(price_id)
    if not obj:
        raise ValueError("报价记录不存在")
    self._repo.delete_supplier_price(obj)
```

- [ ] **Step 3: API 新增价格路由**

在 `app/api/system.py` 追加：

```python
@system_bp.get("/suppliers/<supp_cd>/prices")
@login_required
def list_supplier_prices(supp_cd: str):  # type: ignore[no-untyped-def]
    """查询供应商报价。"""
    item_cd = request.args.get("item_cd", "").strip()
    current_only = request.args.get("current_only", "false").lower() == "true"
    return success_response(data=_service.get_supplier_prices(supp_cd, item_cd, current_only))

@system_bp.post("/suppliers/<supp_cd>/prices")
@login_required
def create_supplier_price(supp_cd: str):  # type: ignore[no-untyped-def]
    """新增供应商报价。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.create_supplier_price(supp_cd, json_data), code=201)
    except ValueError as e:
        return error_response(str(e), 400)

@system_bp.put("/suppliers/<supp_cd>/prices/<int:price_id>")
@login_required
def update_supplier_price(supp_cd: str, price_id: int):  # type: ignore[no-untyped-def]
    """修改供应商报价。"""
    json_data = request.get_json(silent=True) or {}
    try:
        return success_response(data=_service.update_supplier_price(price_id, json_data))
    except ValueError as e:
        return error_response(str(e), 400)

@system_bp.delete("/suppliers/<supp_cd>/prices/<int:price_id>")
@login_required
def delete_supplier_price(supp_cd: str, price_id: int):  # type: ignore[no-untyped-def]
    """删除供应商报价。"""
    try:
        _service.delete_supplier_price(price_id)
        return success_response(message="删除成功")
    except ValueError as e:
        return error_response(str(e), 400)
```

- [ ] **Step 4: 运行测试**

```bash
uv run pytest tests/ -x -q --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add app/repositories/system_repository.py app/services/system_service.py app/api/system.py
git commit -m "feat(supplier): 供应商价格 CRUD API + 商品关联校验"
```

---

### Task B3: 前端 — 供应商详情 Tab 改造

**Files:**
- Modify: `frontend/src/views/procurement/SupplierList.vue`
- Modify: `frontend/src/api/master.ts`

- [ ] **Step 1: 新增前端 API 函数**

在 `frontend/src/api/master.ts` 追加：

```typescript
// 供应商商品关联
export const fetchSupplierItems = (suppCd: string) =>
  request.get(`/suppliers/${suppCd}/items`)

export const addSupplierItem = (suppCd: string, data: Record<string, unknown>) =>
  request.post(`/suppliers/${suppCd}/items`, data)

export const updateSupplierItem = (suppCd: string, itemCd: string, data: Record<string, unknown>) =>
  request.put(`/suppliers/${suppCd}/items/${itemCd}`, data)

export const deleteSupplierItem = (suppCd: string, itemCd: string) =>
  request.delete(`/suppliers/${suppCd}/items/${itemCd}`)

// 供应商价格
export const fetchSupplierPrices = (suppCd: string, params?: { item_cd?: string; current_only?: boolean }) =>
  request.get(`/suppliers/${suppCd}/prices`, { params })

export const createSupplierPrice = (suppCd: string, data: Record<string, unknown>) =>
  request.post(`/suppliers/${suppCd}/prices`, data)

export const updateSupplierPrice = (suppCd: string, priceId: number, data: Record<string, unknown>) =>
  request.put(`/suppliers/${suppCd}/prices/${priceId}`, data)

export const deleteSupplierPrice = (suppCd: string, priceId: number) =>
  request.delete(`/suppliers/${suppCd}/prices/${priceId}`)
```

- [ ] **Step 2: 改造 SupplierList.vue 的 openDetail 方法**

将 `openDetail` 替换为完整的 Tab 弹窗。在 `<script setup>` 中的 `openDetail` 替换为：

```typescript
// 详情 Tab 弹窗
const detailVisible = ref(false)
const detailSuppCd = ref('')
const activeTab = ref('info')
const detail = ref<Record<string,unknown>|null>(null)

// 供应商品
const suppItems = ref<Record<string,unknown>[]>([])
const suppItemsLoading = ref(false)
const itemDialogVisible = ref(false)
const itemIsEdit = ref(false)
const currentItemCd = ref('')
const itemForm = reactive({ itemcd: '', dfltflg: 'N', delivercycle: 0, servicecycle: 0, guaranteeperiod: 0 })
const allItems = ref<Record<string,unknown>[]>([])

// 价格
const suppPrices = ref<Record<string,unknown>[]>([])
const suppPricesLoading = ref(false)
const priceDialogVisible = ref(false)
const priceIsEdit = ref(false)
const currentPriceId = ref<number>(0)
const priceForm = reactive({ itemcd: '', min_qty: 0, itemprice: 0, effective_date: '', expire_date: '', is_current: true })

function openDetail(row: any) {
  detailSuppCd.value = row.supp_cd as string
  detail.value = { ...row }
  activeTab.value = 'info'
  suppItems.value = []
  suppPrices.value = []
  detailVisible.value = true
}

async function handleTabChange(tab: string) {
  if (tab === 'items' && suppItems.value.length === 0) {
    suppItemsLoading.value = true
    try { const r = await fetchSupplierItems(detailSuppCd.value); suppItems.value = (r.data as any[]) || [] } catch { ElMessage.error('加载失败') }
    finally { suppItemsLoading.value = false }
  }
  if (tab === 'prices' && suppPrices.value.length === 0) {
    suppPricesLoading.value = true
    try { const r = await fetchSupplierPrices(detailSuppCd.value); suppPrices.value = (r.data as any[]) || [] } catch { ElMessage.error('加载失败') }
    finally { suppPricesLoading.value = false }
  }
}

// 供应商品 新增/编辑
async function openAddItem() {
  itemIsEdit.value = false; currentItemCd.value = ''
  itemForm.itemcd = ''; itemForm.dfltflg = 'N'; itemForm.delivercycle = 0; itemForm.servicecycle = 0; itemForm.guaranteeperiod = 0
  itemDialogVisible.value = true
}
function openEditItem(row: any) {
  itemIsEdit.value = true; currentItemCd.value = row.itemcd as string
  itemForm.itemcd = row.itemcd; itemForm.dfltflg = row.dfltflg || 'N'
  itemForm.delivercycle = Number(row.delivercycle) || 0; itemForm.servicecycle = Number(row.servicecycle) || 0
  itemForm.guaranteeperiod = Number(row.guaranteeperiod) || 0
  itemDialogVisible.value = true
}
async function handleSaveItem() {
  if (!itemForm.itemcd) { ElMessage.warning('请选择物料'); return }
  try {
    const data = { ...itemForm }
    if (itemIsEdit.value) {
      await updateSupplierItem(detailSuppCd.value, currentItemCd.value, data)
    } else {
      data.itemcd = itemForm.itemcd
      await addSupplierItem(detailSuppCd.value, data)
    }
    itemDialogVisible.value = false
    suppItems.value = []; await handleTabChange('items')
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
}
async function handleDeleteItem(row: any) {
  try { await ElMessageBox.confirm(`确定移除商品 ${row.item_nm}？`, '确认', { type: 'warning' }) } catch { return }
  try { await deleteSupplierItem(detailSuppCd.value, row.itemcd as string); suppItems.value = suppItems.value.filter(i => i.itemcd !== row.itemcd) } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

// 价格 新增/编辑
function openAddPrice() {
  priceIsEdit.value = false; currentPriceId.value = 0
  priceForm.itemcd = ''; priceForm.min_qty = 0; priceForm.itemprice = 0; priceForm.effective_date = ''; priceForm.expire_date = ''; priceForm.is_current = true
  priceDialogVisible.value = true
}
function openEditPrice(row: any) {
  priceIsEdit.value = true; currentPriceId.value = row.id as number
  priceForm.itemcd = row.itemcd; priceForm.min_qty = Number(row.min_qty) || 0; priceForm.itemprice = Number(row.itemprice) || 0
  priceForm.effective_date = row.effective_date || ''; priceForm.expire_date = row.expire_date || ''; priceForm.is_current = !!row.is_current
  priceDialogVisible.value = true
}
async function handleSavePrice() {
  if (!priceForm.itemcd) { ElMessage.warning('请选择物料'); return }
  try {
    if (priceIsEdit.value) {
      await updateSupplierPrice(detailSuppCd.value, currentPriceId.value, { ...priceForm, itemcd: undefined })
    } else {
      await createSupplierPrice(detailSuppCd.value, { ...priceForm })
    }
    priceDialogVisible.value = false
    suppPrices.value = []; await handleTabChange('prices')
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
}
async function handleDeletePrice(row: any) {
  try { await ElMessageBox.confirm(`确定删除此报价？`, '确认', { type: 'warning' }) } catch { return }
  try { await deleteSupplierPrice(detailSuppCd.value, row.id as number); suppPrices.value = suppPrices.value.filter(p => p.id !== row.id) } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}
```

- [ ] **Step 3: 在模板中添加详情 Tab 弹窗**

在 SupplierList.vue 的 `</template>` 前追加（放在分类管理弹窗 `<el-dialog>` 之后）：

```vue
    <!-- 详情 Tab 弹窗 -->
    <el-dialog :title="'供应商 — ' + (detail?.supp_nm || '')" v-model="detailVisible" width="750px">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="基本信息" name="info">
          <el-descriptions v-if="detail" :column="2" border size="small">
            <el-descriptions-item label="编码">{{ detail.supp_cd }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ detail.supp_nm }}</el-descriptions-item>
            <el-descriptions-item label="简称">{{ detail.custanm || '-' }}</el-descriptions-item>
            <el-descriptions-item label="简码">{{ detail.custbrcd || '-' }}</el-descriptions-item>
            <el-descriptions-item label="分类">{{ classMap[detail.class_cd as string] || detail.class_cd }}</el-descriptions-item>
            <el-descriptions-item label="联系人">{{ detail.contactor || '-' }}</el-descriptions-item>
            <el-descriptions-item label="电话">{{ detail.phoneno || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态"><el-tag :type="detail.useflg==='0'?'info':'success'" size="small">{{ detail.useflg==='0'?'停用':'启用' }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="地址" :span="2">{{ detail.address || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <el-tab-pane label="供应商品" name="items">
          <div style="margin-bottom:8px;"><el-button type="primary" size="small" @click="openAddItem">+ 新增供应商品</el-button></div>
          <el-table :data="suppItems" v-loading="suppItemsLoading" size="small" stripe>
            <el-table-column prop="itemcd" label="物料编码" width="90" />
            <el-table-column prop="item_nm" label="名称" min-width="140" show-overflow-tooltip />
            <el-table-column label="默认" width="60"><template #default="{row}"><el-tag :type="row.dfltflg==='Y'?'success':'info'" size="small">{{ row.dfltflg==='Y'?'是':'否' }}</el-tag></template></el-table-column>
            <el-table-column prop="delivercycle" label="配送周期(天)" width="90" />
            <el-table-column prop="servicecycle" label="服务周期(天)" width="90" />
            <el-table-column prop="guaranteeperiod" label="保修期(天)" width="90" />
            <el-table-column label="操作" width="120"><template #default="{row}"><el-button link type="primary" size="small" @click="openEditItem(row)">编辑</el-button><el-button link type="danger" size="small" @click="handleDeleteItem(row)">删除</el-button></template></el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="价格报价" name="prices">
          <div style="margin-bottom:8px;"><el-button type="primary" size="small" @click="openAddPrice">+ 新增报价</el-button></div>
          <el-table :data="suppPrices" v-loading="suppPricesLoading" size="small" stripe>
            <el-table-column prop="itemcd" label="物料编码" width="90" />
            <el-table-column prop="item_nm" label="名称" min-width="120" show-overflow-tooltip />
            <el-table-column prop="min_qty" label="最小起订" width="80" />
            <el-table-column prop="itemprice" label="单价" width="100" />
            <el-table-column prop="effective_date" label="生效" width="100" />
            <el-table-column prop="expire_date" label="失效" width="100" />
            <el-table-column label="操作" width="120"><template #default="{row}"><el-button link type="primary" size="small" @click="openEditPrice(row)">编辑</el-button><el-button link type="danger" size="small" @click="handleDeletePrice(row)">删除</el-button></template></el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 供应商品新增/编辑弹窗 -->
    <el-dialog :title="itemIsEdit?'编辑供应商品':'新增供应商品'" v-model="itemDialogVisible" width="400px">
      <el-form :model="itemForm" label-width="80px" size="small">
        <el-form-item label="物料" required><el-select v-model="itemForm.itemcd" :disabled="itemIsEdit" style="width:100%" filterable placeholder="搜索物料编码/名称"><el-option v-for="it in allItems" :key="it.item_cd as string" :label="`${it.item_cd} ${it.item_nm}`" :value="it.item_cd" /></el-select></el-form-item>
        <el-form-item label="默认"><el-switch v-model="itemForm.dfltflg" active-value="Y" inactive-value="N" /></el-form-item>
        <el-form-item label="配送周期"><el-input-number v-model="itemForm.delivercycle" :min="0" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="服务周期"><el-input-number v-model="itemForm.servicecycle" :min="0" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="保修期"><el-input-number v-model="itemForm.guaranteeperiod" :min="0" controls-position="right" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button size="small" @click="itemDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="handleSaveItem">保存</el-button></template>
    </el-dialog>

    <!-- 价格新增/编辑弹窗 -->
    <el-dialog :title="priceIsEdit?'编辑报价':'新增报价'" v-model="priceDialogVisible" width="400px">
      <el-form :model="priceForm" label-width="80px" size="small">
        <el-form-item label="物料" required><el-select v-model="priceForm.itemcd" :disabled="priceIsEdit" style="width:100%"><el-option v-for="it in suppItems" :key="it.itemcd as string" :label="`${it.itemcd} ${it.item_nm}`" :value="it.itemcd" /></el-select></el-form-item>
        <el-form-item label="最小起订"><el-input-number v-model="priceForm.min_qty" :min="0" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="单价" required><el-input-number v-model="priceForm.itemprice" :min="0" :precision="2" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="生效日期"><el-date-picker v-model="priceForm.effective_date" type="date" style="width:100%" /></el-form-item>
        <el-form-item label="失效日期"><el-date-picker v-model="priceForm.expire_date" type="date" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button size="small" @click="priceDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="handleSavePrice">保存</el-button></template>
    </el-dialog>
```

- [ ] **Step 4: 添加物料列表加载（onMounted）**

在 `<script setup>` 的 `onMounted` 中追加：

```typescript
// 加载全部物料（供商品关联下拉选择）
import { fetchItems } from '@/api/master'
async function loadAllItems() {
  try { const r = await fetchItems({ per_page: 9999 }); allItems.value = (r.data as any)?.items || [] } catch { /**/ }
}
onMounted(() => { loadClasses(); load(); loadAllItems() })
```

- [ ] **Step 5: 验证构建**

```bash
cd frontend && npm run build --if-present 2>&1 | tail -5
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/procurement/SupplierList.vue frontend/src/api/master.ts
git commit -m "feat(supplier): 供应商详情 Tab 弹窗 — 基本信息 + 供应商品 + 价格报价"
```

---

## Phase C: 采购订单拆单/并单

### Task C1: 批量创建订单 API + advisory lock（后端）

**Files:**
- Modify: `app/services/procurement_service.py`
- Modify: `app/api/procurement.py`

- [ ] **Step 1: 在 Service 中新增 batch_create 方法**

在 `app/services/procurement_service.py` 的 `PurchaseRegisterService` 类中追加：

```python
import hashlib
import sqlalchemy as sa

@staticmethod
def _lock_requisition_line(pcplanid: str, pclineno: int) -> None:
    """获取需求行的 advisory lock，防止并发超量。"""
    key = int(hashlib.md5(f"{pcplanid}:{pclineno}".encode()).hexdigest()[:16], 16)
    db.session.execute(sa.text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})

@staticmethod
def batch_create(orders_data: list[dict[str, Any]], creator: str) -> dict[str, Any]:
    """
    批量创建采购订单（统一处理拆单和并单）。

    校验规则：
    1. 汇总所有 detail 按 (pcplanid, pclineno) 的 rgsqty
    2. 逐一获取 advisory lock
    3. 检查已关联数量 + 新增数量 ≤ auditqty
    4. 写入 tpc12 → tpc13 → TPC20
    """
    from collections import defaultdict
    from app.repositories.procurement_repository import (
        PurchasePlanRepository, PurchaseRegisterRepository, RequisitionOrderLinkRepository
    )

    if not orders_data:
        raise ValueError("orders 不能为空")
    if len(orders_data) > 10:
        raise ValueError("单次最多创建 10 个订单")

    # 1. 收集需求行 + 汇总数量
    req_line_qty: dict[tuple[str, int], float] = defaultdict(float)
    for order in orders_data:
        for d in order.get("details", []):
            ref_pid = d.get("ref_pcplanid")
            ref_lno = d.get("ref_pclineno")
            if ref_pid and ref_lno is not None:
                req_line_qty[(str(ref_pid), int(ref_lno))] += float(d.get("rgsqty", 0))

    # 2. 逐一获取 advisory lock（排序避免死锁）
    for (pid, lno) in sorted(req_line_qty.keys()):
        PurchaseRegisterService._lock_requisition_line(pid, lno)

    # 3. 校验数量
    for (pid, lno), total_qty in req_line_qty.items():
        available = PurchasePlanRepository.get_available_qty(pid, lno)
        if total_qty > available:
            raise ValueError(
                f"需求 {pid} 行 {lno} 总采购数量({total_qty})超过可用余额({available})"
            )

    # 4. 逐个创建订单
    created_orders = []
    for order_data in orders_data:
        record = PurchaseRegisterRepository.create_from_batch(order_data, creator)
        rgstbillid = record.rgstbillid

        for i, d in enumerate(order_data.get("details", []), start=1):
            PurchaseRegisterRepository.add_detail_from_batch(rgstbillid, i, d)

        link_details = []
        for i, d in enumerate(order_data.get("details", []), start=1):
            ref_pid = d.get("ref_pcplanid")
            ref_lno = d.get("ref_pclineno")
            if ref_pid and ref_lno is not None:
                link_details.append({
                    "pcplanid": str(ref_pid),
                    "pclineno": int(ref_lno),
                    "rgstbillid": rgstbillid,
                    "rgstlineno": i,
                    "linkqty": float(d.get("rgsqty", 0)),
                    "itemcd": d.get("itemcd", ""),
                })
        if link_details:
            RequisitionOrderLinkRepository.create_links(link_details)

        created_orders.append(rgstbillid)

    return {"created_orders": created_orders, "count": len(created_orders)}
```

- [ ] **Step 2: 在 Repository 中新增批量创建辅助方法**

在 `app/repositories/procurement_repository.py` 的 `PurchaseRegisterRepository` 中追加：

```python
@staticmethod
def create_from_batch(order_data: dict[str, Any], creator: str) -> PurchaseRegister:
    """从批量数据创建订单主表记录。"""
    record = PurchaseRegister(
        suppliercd=order_data.get("suppliercd", ""),
        memo=order_data.get("memo", ""),
        opercd=creator,
        gendate=db.func.now(),
        auditflg="0",
    )
    db.session.add(record)
    db.session.flush()
    return record

@staticmethod
def add_detail_from_batch(rgstbillid: str, lineno: int, detail: dict[str, Any]) -> PurchaseRegisterDt:
    """从批量数据创建订单明细。"""
    from app.models.procurement import PurchaseRegisterDt
    dt = PurchaseRegisterDt(
        rgstbillid=rgstbillid,
        lineno=lineno,
        itemcd=detail.get("itemcd", ""),
        rgsqty=float(detail.get("rgsqty", 0)),
        units=detail.get("units", "PCS"),
        unitprice=float(detail.get("unitprice", 0)) if detail.get("unitprice") else None,
        ref_pcplanid=detail.get("ref_pcplanid"),
        ref_pclineno=detail.get("ref_pclineno"),
    )
    db.session.add(dt)
    db.session.flush()
    return dt
```

在文件顶部 import 区域确认有 `PurchaseRegister` 和 `PurchaseRegisterDt` 导入。

- [ ] **Step 3: 在 API 中新增路由**

在 `app/api/procurement.py` 追加：

```python
@procurement_bp.post("/orders/batch")
@login_required
def create_batch_orders():  # type: ignore[no-untyped-def]
    """批量创建采购订单（拆单 + 并单统一入口）。"""
    json_data = request.get_json(silent=True) or {}

    if "orders" not in json_data or not isinstance(json_data["orders"], list):
        return error_response(message="请求格式错误：缺少 orders 数组", code=400)

    orders = json_data["orders"]
    if len(orders) == 0:
        return error_response(message="orders 不能为空", code=400)
    if len(orders) > 10:
        return error_response(message="单次最多创建 10 个订单", code=400)

    user_cd: str = g.current_user

    try:
        result = PurchaseRegisterService.batch_create(orders, user_cd)
        return success_response(data=result, message=f"成功创建{result['count']}个采购订单", code=201)
    except ValueError as e:
        return error_response(message=str(e), code=400)
    except Exception:
        db.session.rollback()
        raise
```

- [ ] **Step 4: 运行测试**

```bash
uv run pytest tests/ -x -q --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add app/services/procurement_service.py app/repositories/procurement_repository.py app/api/procurement.py
git commit -m "feat(procurement): 批量创建订单 API + pg_advisory_xact_lock 并发控制"
```

---

### Task C2: 批量校验 API + 智能合并预览 API（后端）

**Files:**
- Modify: `app/services/procurement_service.py`
- Modify: `app/api/procurement.py`
- Modify: `app/repositories/procurement_repository.py`

- [ ] **Step 1: 新增 batch_validate 方法**

在 `app/services/procurement_service.py` 的 `PurchaseRegisterService` 中追加：

```python
@staticmethod
def batch_validate(orders_data: list[dict[str, Any]]) -> dict[str, Any]:
    """批量订单预校验，返回每个需求行的可用数量。"""
    from collections import defaultdict
    from app.repositories.procurement_repository import PurchasePlanRepository

    req_line_qty: dict[tuple[str, int], float] = defaultdict(float)
    for order in orders_data:
        for d in order.get("details", []):
            ref_pid = d.get("ref_pcplanid")
            ref_lno = d.get("ref_pclineno")
            if ref_pid and ref_lno is not None:
                req_line_qty[(str(ref_pid), int(ref_lno))] += float(d.get("rgsqty", 0))

    checks = []
    valid = True
    for (pid, lno), total_qty in req_line_qty.items():
        available = PurchasePlanRepository.get_available_qty(pid, lno)
        ok = total_qty <= available
        if not ok:
            valid = False
        checks.append({
            "pcplanid": pid, "pclineno": lno,
            "available_qty": available, "requested_qty": total_qty,
            "valid": ok,
        })

    return {"valid": valid, "checks": checks}
```

- [ ] **Step 2: 新增 merge_preview 方法**

在 `app/services/procurement_service.py` 中新增 `PurchasePlanMergeService` 类（或追加到现有类）：

```python
class PurchasePlanMergeService:
    """智能合并服务。"""

    @staticmethod
    def merge_preview() -> dict[str, Any]:
        """扫描可合并的需求行，按 itemcd 分组，推荐供应商。"""
        from app.repositories.procurement_repository import PurchasePlanRepository

        details = PurchasePlanRepository.get_mergeable_details()
        if not details:
            return {"mergeable": [], "unmergeable": [], "summary": {"mergeable_groups": 0, "unmergeable_items": 0, "estimated_orders": 0}}

        # 按 itemcd 分组
        from collections import defaultdict
        groups = defaultdict(list)
        for d in details:
            groups[d["itemcd"]].append(d)

        mergeable = []
        unmergeable = []
        for itemcd, lines in groups.items():
            total_qty = sum(float(l["available_qty"]) for l in lines)
            suppliers = PurchasePlanMergeService._get_suggested_suppliers(itemcd)
            group_data = {
                "itemcd": itemcd,
                "itemnm": lines[0].get("itemnm", ""),
                "total_qty": total_qty,
                "source_count": len(lines),
                "source_lines": [
                    {"pcplanid": l["pcplanid"], "pclineno": l["pclineno"],
                     "qty": l["available_qty"], "dept": l.get("deptnm", "")}
                    for l in lines
                ],
                "suggested_suppliers": suppliers,
            }
            if len(lines) >= 2:
                mergeable.append(group_data)
            else:
                unmergeable.append(group_data)

        return {
            "mergeable": mergeable,
            "unmergeable": unmergeable,
            "summary": {
                "mergeable_groups": len(mergeable),
                "unmergeable_items": len(unmergeable),
                "estimated_orders": len(mergeable),
            }
        }

    @staticmethod
    def _get_suggested_suppliers(itemcd: str) -> list[dict[str, Any]]:
        """根据供应商-商品关联和价格推荐供应商。"""
        from app.models.inventory import SupplierPrice
        from app.models.master import Supplier, CustItems
        from datetime import date, timedelta

        today = date.today()
        six_months_ago = today - timedelta(days=180)

        rows = (
            db.session.query(SupplierPrice, Supplier.supp_nm)
            .join(Supplier, SupplierPrice.supp_cd == Supplier.supp_cd)
            .filter(
                SupplierPrice.itemcd == itemcd,
                Supplier.useflg == "1",
                db.or_(SupplierPrice.is_current == True,
                       SupplierPrice.effective_date >= six_months_ago)
            )
            .order_by(SupplierPrice.itemprice)
            .limit(5)
            .all()
        )
        return [
            {"supp_cd": sp.supp_cd, "supp_nm": supp_nm,
             "min_qty": float(sp.min_qty) if sp.min_qty else 0,
             "itemprice": float(sp.itemprice) if sp.itemprice else 0}
            for sp, supp_nm in rows
        ]
```

- [ ] **Step 3: 在 Repository 中新增 get_mergeable_details**

在 `app/repositories/procurement_repository.py` 的 `PurchasePlanRepository` 中追加：

```python
@staticmethod
def get_mergeable_details() -> list[dict[str, Any]]:
    """查询可合并的需求明细：已审核 + 有可用余额。"""
    rows = db.session.execute(
        sa.text("""
            SELECT v.pcplanid, v.lineno AS pclineno, v.itemcd, v.itemnm,
                   v.available_qty, v.deptnm
            FROM v_requisition_execution v
            JOIN tpc02_pcplandt d ON v.pcplanid = d.pcplanid AND v.lineno = d.lineno
            JOIN tpc01_pcplan p ON v.pcplanid = p.pcplanid
            WHERE p.auditflg = '2'
              AND v.available_qty > 0
              AND d.useflg = '1'
            ORDER BY v.itemcd, v.pcplanid, v.lineno
        """)
    ).fetchall()
    return [
        {"pcplanid": r.pcplanid, "pclineno": r.pclineno, "itemcd": r.itemcd,
         "itemnm": r.itemnm, "available_qty": float(r.available_qty), "deptnm": r.deptnm}
        for r in rows
    ]
```

- [ ] **Step 4: 在 API 中新增路由**

在 `app/api/procurement.py` 追加：

```python
@procurement_bp.post("/orders/batch/validate")
@login_required
def validate_batch_orders():  # type: ignore[no-untyped-def]
    """批量订单预校验。"""
    json_data = request.get_json(silent=True) or {}
    orders = json_data.get("orders", [])
    if not orders:
        return error_response(message="orders 不能为空", code=400)
    try:
        result = PurchaseRegisterService.batch_validate(orders)
        return success_response(data=result)
    except Exception:
        raise

@procurement_bp.post("/requisitions/merge-preview")
@login_required
def merge_preview():  # type: ignore[no-untyped-def]
    """智能合并预览 — 自动扫描可合并需求行并推荐供应商。"""
    try:
        result = PurchasePlanMergeService.merge_preview()
        return success_response(data=result)
    except Exception:
        raise
```

- [ ] **Step 5: 运行测试**

```bash
uv run pytest tests/ -x -q --tb=short
```

- [ ] **Step 6: Commit**

```bash
git add app/services/procurement_service.py app/repositories/procurement_repository.py app/api/procurement.py
git commit -m "feat(procurement): batch validate + merge-preview API"
```

---

### Task C3: 前端 — 拆单 UI（订单创建表单）

**Files:**
- Modify: `frontend/src/views/procurement/PurchaseRegisterList.vue`
- Modify: `frontend/src/api/master.ts`

- [ ] **Step 1: 新增 API 函数**

在 `frontend/src/api/master.ts` 追加：

```typescript
// 批量订单
export const batchCreateOrders = (data: { orders: Array<{ suppliercd: string; memo?: string; details: Array<{ itemcd: string; rgsqty: number; units?: string; ref_pcplanid: string; ref_pclineno: number; unitprice?: number }> }> }) =>
  request.post('/procurement/orders/batch', data)

export const validateBatchOrders = (data: { orders: any[] }) =>
  request.post('/procurement/orders/batch/validate', data)
```

- [ ] **Step 2: 在订单创建表单中添加"拆单"能力**

在 `PurchaseRegisterList.vue` 的订单创建流程中（Step 2-3 区域），为每行需求明细添加"拆单"按钮。关键逻辑：

```typescript
// 拆分行接口
interface SplitLine {
  id: string
  suppliercd: string
  suppliernm: string
  itemcd: string
  rgsqty: number
  unitprice: number
  ref_pcplanid: string
  ref_pclineno: number
}

// 拆分管理
const splitGroups = ref<Map<string, SplitLine[]>>(new Map())

function generateId() { return Date.now().toString(36) + Math.random().toString(36).slice(2) }

function handleSplit(detail: any) {
  const key = `${detail.ref_pcplanid}_${detail.ref_pclineno}`
  if (splitGroups.value.has(key)) return // 已经拆分过

  const remaining = detail.available_qty || detail.auditqty
  const half1 = Math.ceil(remaining / 2)
  const half2 = remaining - half1

  splitGroups.value.set(key, [
    { id: generateId(), suppliercd: '', suppliernm: '', itemcd: detail.itemcd, rgsqty: half1, unitprice: 0, ref_pcplanid: detail.ref_pcplanid, ref_pclineno: detail.ref_pclineno },
    { id: generateId(), suppliercd: '', suppliernm: '', itemcd: detail.itemcd, rgsqty: half2, unitprice: 0, ref_pcplanid: detail.ref_pcplanid, ref_pclineno: detail.ref_pclineno },
  ])
}

function handleRemoveSplitLine(key: string, lineId: string) {
  const lines = splitGroups.value.get(key)
  if (!lines) return
  const idx = lines.findIndex(l => l.id === lineId)
  if (idx < 0) return
  lines.splice(idx, 1)
  if (lines.length <= 1) {
    splitGroups.value.delete(key) // 只剩1行，恢复为非拆分状态
  }
}
```

- [ ] **Step 3: 构建批量提交数据**

```typescript
function buildBatchOrders() {
  const orders: any[] = []
  const supplierMap = new Map<string, any>()

  splitGroups.value.forEach((lines, key) => {
    lines.forEach(line => {
      if (!line.suppliercd) return
      const sKey = line.suppliercd
      if (!supplierMap.has(sKey)) {
        supplierMap.set(sKey, { suppliercd: line.suppliercd, memo: '', details: [] })
      }
      supplierMap.get(sKey).details.push({
        itemcd: line.itemcd,
        rgsqty: line.rgsqty,
        unitprice: line.unitprice,
        ref_pcplanid: line.ref_pcplanid,
        ref_pclineno: line.ref_pclineno,
      })
    })
  })

  // 未拆分的明细
  unSplitDetails.value.forEach(d => {
    if (!d.suppliercd) return
    const sKey = d.suppliercd
    if (!supplierMap.has(sKey)) {
      supplierMap.set(sKey, { suppliercd: d.suppliercd, memo: '', details: [] })
    }
    supplierMap.get(sKey).details.push({
      itemcd: d.itemcd,
      rgsqty: d.available_qty || d.auditqty,
      unitprice: d.unitprice,
      ref_pcplanid: d.ref_pcplanid,
      ref_pclineno: d.ref_pclineno,
    })
  })

  return { orders: Array.from(supplierMap.values()) }
}

async function handleBatchSubmit() {
  const data = buildBatchOrders()
  if (data.orders.length === 0) { ElMessage.warning('请至少分配一个供应商'); return }

  // 先校验
  try { await validateBatchOrders(data) } catch (e: any) { ElMessage.error(e?.response?.data?.message || '校验失败'); return }

  // 提交
  try {
    const res = await batchCreateOrders(data)
    ElMessage.success(`成功创建 ${(res.data as any).count} 个订单`)
    router.push('/procurement/orders')
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '创建失败') }
}
```

- [ ] **Step 4: 在模板中添加拆单按钮和拆分行的 UI**

在订单创建表单的需求明细表格中，每行增加"拆单"按钮，表格下方显示拆分后的行。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/procurement/PurchaseRegisterList.vue frontend/src/api/master.ts
git commit -m "feat(procurement): 订单创建表单增加拆单功能"
```

---

### Task C4: 前端 — 智能合并 UI（需求列表页）

**Files:**
- Modify: `frontend/src/views/procurement/PurchasePlanList.vue`
- Modify: `frontend/src/api/master.ts`

- [ ] **Step 1: 新增 API 函数**

在 `frontend/src/api/master.ts` 追加：

```typescript
// 智能合并
export const getMergePreview = () =>
  request.post('/procurement/requisitions/merge-preview')
```

- [ ] **Step 2: 在 PurchasePlanList.vue 中添加【智能合并】按钮**

在页面头部按钮区域增加：

```vue
<el-button type="warning" size="small" @click="handleMergePreview">智能合并</el-button>
```

- [ ] **Step 3: 实现合并预览弹窗**

```typescript
const mergeDialogVisible = ref(false)
const mergeGroups = ref<any[]>([])
const unmergeableItems = ref<any[]>([])
const mergeLoading = ref(false)

async function handleMergePreview() {
  mergeLoading.value = true
  try {
    const res = await getMergePreview()
    const d = res.data as any
    mergeGroups.value = (d.mergeable || []).map((g: any) => ({ ...g, checked: true, selectedSupplier: g.suggested_suppliers?.[0]?.supp_cd || '' }))
    unmergeableItems.value = d.unmergeable || []
    mergeDialogVisible.value = true
  } catch { ElMessage.error('加载失败') }
  finally { mergeLoading.value = false }
}

async function handleMergeConfirm() {
  const selected = mergeGroups.value.filter(g => g.checked)
  if (selected.length === 0) { ElMessage.warning('请至少选择一个合并组'); return }

  const orders = selected.map(g => ({
    suppliercd: g.selectedSupplier,
    memo: `合并采购 — ${g.itemnm}`,
    details: g.source_lines.map((l: any) => ({
      itemcd: g.itemcd,
      rgsqty: l.qty,
      ref_pcplanid: l.pcplanid,
      ref_pclineno: l.pclineno,
    }))
  }))

  try {
    const res = await batchCreateOrders({ orders })
    ElMessage.success(`成功创建 ${(res.data as any).count} 个订单`)
    mergeDialogVisible.value = false
    fetchList()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '创建失败') }
}
```

- [ ] **Step 4: 添加合并预览弹窗模板**

```vue
<el-dialog title="智能合并推荐" v-model="mergeDialogVisible" width="700px" :close-on-click-modal="false">
  <div v-if="mergeGroups.length > 0">
    <h4 style="margin-bottom:12px;">以下商品可合并采购（同类商品多个需求）</h4>
    <div v-for="g in mergeGroups" :key="g.itemcd" style="padding:10px;margin-bottom:8px;border:1px solid #e0e0e0;border-radius:6px;">
      <el-checkbox v-model="g.checked">
        <strong>{{ g.itemcd }} {{ g.itemnm }}</strong> — {{ g.source_count }}个需求单 共{{ g.total_qty }}个
      </el-checkbox>
      <div style="margin-left:24px;color:#909399;font-size:12px;">来源：{{ g.source_lines.map((l:any)=>`${l.pcplanid}(${l.qty})`).join(' + ') }}</div>
      <div style="margin-left:24px;margin-top:6px;">
        选择供应商：
        <el-select v-model="g.selectedSupplier" size="small" style="width:200px;">
          <el-option v-for="s in g.suggested_suppliers" :key="s.supp_cd" :label="`${s.supp_nm} (¥${s.itemprice})`" :value="s.supp_cd" />
        </el-select>
      </div>
    </div>
  </div>
  <div v-if="unmergeableItems.length > 0">
    <h4 style="margin-bottom:8px;color:#909399;">以下商品无可合并（仅1个需求单）</h4>
    <div v-for="u in unmergeableItems" :key="u.itemcd" style="padding:6px;color:#909399;font-size:13px;">
      ○ {{ u.itemcd }} {{ u.itemnm }} — {{ u.source_lines?.[0]?.pcplanid || '-' }}
    </div>
  </div>
  <div style="margin-top:12px;padding:8px;background:#f5f5f5;border-radius:4px;text-align:right;">
    将生成 <strong>{{ mergeGroups.filter(g=>g.checked).length }}</strong> 个采购订单
  </div>
  <template #footer>
    <el-button @click="mergeDialogVisible=false">取消</el-button>
    <el-button type="primary" @click="handleMergeConfirm">确认合并</el-button>
  </template>
</el-dialog>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/procurement/PurchasePlanList.vue frontend/src/api/master.ts
git commit -m "feat(procurement): 智能合并扫描 + 预览 + 批量创建"
```

---

### Task C5: 集成测试（后端）

**Files:**
- Create: `tests/test_procurement_batch.py`

- [ ] **Step 1: 编写集成测试**

```python
"""采购批量订单 + 拆单并单集成测试。"""
import pytest
from app.services.procurement_service import PurchaseRegisterService, PurchasePlanMergeService


class TestBatchCreate:
    """批量创建订单（拆单场景）。"""

    def test_batch_create_split_order(self, app, auth_headers):
        """拆单：同一需求行分配给两个供应商，生成两个订单。"""
        with app.app_context():
            orders = [
                {
                    "suppliercd": "SUP001",
                    "memo": "拆单-供应商A",
                    "details": [
                        {"ref_pcplanid": "PP000180", "ref_pclineno": 1,
                         "itemcd": "MB5000", "rgsqty": 60, "unitprice": 100}
                    ]
                },
                {
                    "suppliercd": "SUP002",
                    "memo": "拆单-供应商B",
                    "details": [
                        {"ref_pcplanid": "PP000180", "ref_pclineno": 1,
                         "itemcd": "MB5000", "rgsqty": 40, "unitprice": 105}
                    ]
                }
            ]
            result = PurchaseRegisterService.batch_create(orders, "TEST")
            assert result["count"] == 2
            assert len(result["created_orders"]) == 2

    def test_batch_create_exceed_available(self, app):
        """超量校验：总量超过可用余额应失败。"""
        with app.app_context():
            orders = [
                {
                    "suppliercd": "SUP001",
                    "details": [
                        {"ref_pcplanid": "PP000180", "ref_pclineno": 1,
                         "itemcd": "MB5000", "rgsqty": 99999}
                    ]
                }
            ]
            with pytest.raises(ValueError, match="超过可用余额"):
                PurchaseRegisterService.batch_create(orders, "TEST")

    def test_batch_create_max_10_orders(self, app):
        """超过10个订单应失败。"""
        with app.app_context():
            orders = [{"suppliercd": f"SUP{i:03d}", "details": []} for i in range(11)]
            with pytest.raises(ValueError, match="最多创建10个"):
                PurchaseRegisterService.batch_create(orders, "TEST")


class TestMergePreview:
    """智能合并预览。"""

    def test_merge_preview_returns_groups(self, app):
        """合并预览应返回按 itemcd 分组的结果。"""
        with app.app_context():
            result = PurchasePlanMergeService.merge_preview()
            assert "mergeable" in result
            assert "unmergeable" in result
            assert "summary" in result

    def test_merge_preview_only_mergeable_has_suggested_suppliers(self, app):
        """可合并组应有供应商推荐。"""
        with app.app_context():
            result = PurchasePlanMergeService.merge_preview()
            for g in result["mergeable"]:
                assert "suggested_suppliers" in g
                assert "source_count" in g
                assert g["source_count"] >= 2  # 至少2个需求单才能合并
```

- [ ] **Step 2: 运行测试**

```bash
uv run pytest tests/test_procurement_batch.py -v --tb=short
```

- [ ] **Step 3: 修复问题直到全部通过**

- [ ] **Step 4: Commit**

```bash
git add tests/test_procurement_batch.py
git commit -m "test(procurement): 批量订单 + 合并预览集成测试"
```

---

### Task C6: 端到端联调 + 修复

- [ ] **Step 1: 启动后端服务**

```bash
uv run flask run --debug &
```

- [ ] **Step 2: 启动前端**

```bash
cd frontend && npm run dev &
```

- [ ] **Step 3: 手动测试清单**

| 场景 | 操作 | 预期结果 |
|------|------|---------|
| 供应商新增 | 供应商管理 → 新增 → 填写信息 → 保存 | 列表刷新，新供应商出现 |
| 供应商删除（有关联） | 删除有采购订单的供应商 | 409 错误提示 |
| 供应商商品关联 | 详情 → 供应商品 → 新增 → 选物料 | 关联成功，两侧可见 |
| 供应商报价 | 详情 → 价格报价 → 新增 | 校验已关联 + 价格录入成功 |
| 拆单 | 新建订单 → 选需求 → 拆单 → 分配供应商 → 提交 | 生成2个订单 |
| 并单 | 需求列表 → 智能合并 → 预览 → 确认 | 生成合并订单 |
| 校验失败 | 拆单总量>可用余额 → 提交 | 后端返回 400 |

- [ ] **Step 4: 修复联调发现的问题**

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "chore(procurement): 端到端联调修复"
```

---

## 实施总结

| Phase | 任务数 | 预计工时 | 依赖 |
|-------|--------|---------|------|
| A: 供应商 CRUD | 3 (A1-A3) | 2.5 天 | 无 |
| B: 商品关联+价格 | 3 (B1-B3) | 2.5 天 | A |
| C: 拆单/并单 | 6 (C1-C6) | 7 天 | B |
| **合计** | **12** | **12 天** | |

**关键文件汇总：**

| 文件 | Phase |
|------|-------|
| `app/repositories/system_repository.py` | A, B |
| `app/services/system_service.py` | A, B |
| `app/api/system.py` | A, B |
| `app/services/procurement_service.py` | C |
| `app/repositories/procurement_repository.py` | C |
| `app/api/procurement.py` | C |
| `frontend/src/views/procurement/SupplierList.vue` | A, B |
| `frontend/src/views/procurement/PurchaseRegisterList.vue` | C |
| `frontend/src/views/procurement/PurchasePlanList.vue` | C |
| `frontend/src/api/master.ts` | A, B, C |
| `tests/test_procurement_batch.py` | C |
