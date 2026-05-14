# BOM 管理 CRUD 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补全 F1 物料管理中缺失的 BOM 配置功能 — 后端 9 端点 CRUD API + 前端 BOM 管理页面 + 物料页面字段扩展。

**Architecture:** 遵循现有三层架构（API → Service → Repository），BOM 模块独立蓝图 `/api/v1/bom`。前端复用 F1 的 el-table/el-form 模式，BomList.vue 采用左侧列表+右侧明细编辑的双面板布局。

**Tech Stack:** Flask + SQLAlchemy + Pydantic v2 + Alembic | Vue 3 + Element Plus + TypeScript

---

## File Map

| 层 | 文件 | 操作 |
|----|------|------|
| Schema | `app/schemas/bom.py` | Create |
| Repository | `app/repositories/bom_repository.py` | Create |
| Service | `app/services/bom_service.py` | Create |
| API | `app/api/bom.py` | Create |
| App init | `app/__init__.py` | Modify |
| API Doc | `docs/core/API接口文档.md` | Modify |
| Frontend API | `frontend/src/api/master.ts` | Modify |
| Frontend page | `frontend/src/views/master/BomList.vue` | Create |
| Frontend page | `frontend/src/views/master/ItemList.vue` | Modify |
| Router | `frontend/src/router/index.ts` | Modify |
| Menu | `frontend/src/layout/AsideMenu.vue` | Modify |
| Tests | `tests/test_bom_api.py` | Create |

---

### Task 1: BOM Schema

**Files:** Create `app/schemas/bom.py`

- [ ] **Step 1: Create BOM Schema**

```python
"""BOM 管理模块请求/响应 Schema。"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class BomCreateRequest(BaseModel):
    """创建 BOM。"""

    bomcd: str = Field(..., max_length=6, description="BOM编码（整机物料编码）")
    bomnm: str = Field(..., max_length=50, description="BOM名称")

    @field_validator("bomcd")
    @classmethod
    def bomcd_must_be_6_chars(cls, v: str) -> str:
        if len(v.strip()) != 6:
            raise ValueError("BOM编码必须为6位")
        return v.strip().upper()


class BomUpdateRequest(BaseModel):
    """更新 BOM。"""

    bomnm: str | None = Field(None, max_length=50, description="BOM名称")
    useflg: str | None = Field(None, max_length=1, description="有效标志")


class BomDtCreateRequest(BaseModel):
    """添加 BOM 明细。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    bomqty: Decimal = Field(..., description="BOM数量")
    itemtyp: str = Field("0", max_length=1, description="物料类型(0=外设,1=核心)")


class BomDtUpdateRequest(BaseModel):
    """更新 BOM 明细。"""

    bomqty: Decimal | None = Field(None, description="BOM数量")
    itemtyp: str | None = Field(None, max_length=1, description="物料类型")
```

- [ ] **Step 2: Verify syntax**

```bash
uv run python -c "from app.schemas.bom import BomCreateRequest, BomDtCreateRequest; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add app/schemas/bom.py && git commit -m "feat(bom): add BOM create/update/detail schema"
```

---

### Task 2: BOM Repository

**Files:** Create `app/repositories/bom_repository.py`

- [ ] **Step 1: Create Repository**

```python
"""BOM 管理数据访问层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.master import Bom, BomDt


class BomRepository:
    """BOM 数据访问。"""

    @staticmethod
    def list_boms(page: int = 1, per_page: int = 20, search: str | None = None) -> tuple[list[Bom], int]:
        q = db.session.query(Bom)
        if search:
            q = q.filter(db.or_(Bom.bomcd.ilike(f"%{search}%"), Bom.bomnm.ilike(f"%{search}%")))
        q = q.order_by(Bom.bomcd)
        total = q.count()
        return q.offset((page - 1) * per_page).limit(per_page).all(), total

    @staticmethod
    def get_bom(bomcd: str) -> Bom | None:
        return db.session.get(Bom, bomcd)

    @staticmethod
    def create_bom(data: dict[str, Any]) -> Bom:
        bom = Bom(**data)
        db.session.add(bom)
        db.session.commit()
        return bom

    @staticmethod
    def update_bom(bom: Bom, data: dict[str, Any]) -> Bom:
        for k, v in data.items():
            setattr(bom, k, v)
        db.session.commit()
        return bom

    @staticmethod
    def delete_bom(bom: Bom) -> None:
        db.session.delete(bom)
        db.session.commit()

    @staticmethod
    def list_details(bomcd: str) -> list[BomDt]:
        return list(db.session.query(BomDt).filter(BomDt.bomcd == bomcd).order_by(BomDt.itemcd).all())

    @staticmethod
    def get_detail(bomcd: str, itemcd: str) -> BomDt | None:
        return db.session.get(BomDt, (bomcd, itemcd))

    @staticmethod
    def add_detail(data: dict[str, Any]) -> BomDt:
        dt = BomDt(**data)
        db.session.add(dt)
        db.session.commit()
        return dt

    @staticmethod
    def update_detail(dt: BomDt, data: dict[str, Any]) -> BomDt:
        for k, v in data.items():
            setattr(dt, k, v)
        db.session.commit()
        return dt

    @staticmethod
    def delete_detail(dt: BomDt) -> None:
        db.session.delete(dt)
        db.session.commit()
```

- [ ] **Step 2: Verify import**

```bash
uv run python -c "from app.repositories.bom_repository import BomRepository; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add app/repositories/bom_repository.py && git commit -m "feat(bom): add BOM repository with CRUD for master and detail"
```

---

### Task 3: BOM Service

**Files:** Create `app/services/bom_service.py`

- [ ] **Step 1: Create Service**

```python
"""BOM 管理业务逻辑层。"""

from __future__ import annotations

from typing import Any

from app.repositories.bom_repository import BomRepository


class BomService:
    """BOM 业务逻辑。"""

    @staticmethod
    def list_boms(page: int = 1, per_page: int = 20, search: str | None = None) -> dict[str, Any]:
        items, total = BomRepository.list_boms(page=page, per_page=per_page, search=search)
        return {"items": [i.to_dict() for i in items], "total": total}

    @staticmethod
    def get_bom(bomcd: str) -> dict[str, Any] | None:
        bom = BomRepository.get_bom(bomcd)
        if not bom:
            return None
        data = bom.to_dict()
        data["details"] = [d.to_dict() for d in BomRepository.list_details(bomcd)]
        return data

    @staticmethod
    def create_bom(data: dict[str, Any]) -> dict[str, Any]:
        return BomRepository.create_bom(data).to_dict()

    @staticmethod
    def update_bom(bomcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        bom = BomRepository.get_bom(bomcd)
        if not bom:
            return None
        return BomRepository.update_bom(bom, data).to_dict()

    @staticmethod
    def delete_bom(bomcd: str) -> bool:
        bom = BomRepository.get_bom(bomcd)
        if not bom:
            return False
        BomRepository.delete_bom(bom)
        return True

    @staticmethod
    def add_detail(bomcd: str, data: dict[str, Any]) -> dict[str, Any]:
        data["bomcd"] = bomcd
        return BomRepository.add_detail(data).to_dict()

    @staticmethod
    def update_detail(bomcd: str, itemcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        dt = BomRepository.get_detail(bomcd, itemcd)
        if not dt:
            return None
        return BomRepository.update_detail(dt, data).to_dict()

    @staticmethod
    def delete_detail(bomcd: str, itemcd: str) -> bool:
        dt = BomRepository.get_detail(bomcd, itemcd)
        if not dt:
            return False
        BomRepository.delete_detail(dt)
        return True
```

- [ ] **Step 2: Verify import**

```bash
uv run python -c "from app.services.bom_service import BomService; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add app/services/bom_service.py && git commit -m "feat(bom): add BOM service layer wrapping repository"
```

---

### Task 4: BOM API Blueprint

**Files:** Create `app/api/bom.py`, Modify `app/__init__.py`

- [ ] **Step 1: Create API blueprint**

```python
"""BOM 管理 API 蓝图。"""

from __future__ import annotations

from flask import Blueprint, request

from app.api.auth import login_required
from app.schemas.bom import BomCreateRequest, BomDtCreateRequest, BomDtUpdateRequest, BomUpdateRequest
from app.services.bom_service import BomService
from app.utils.response import error_response, success_response

bom_bp = Blueprint("bom", __name__)


@bom_bp.get("")
@login_required
def list_boms():  # type: ignore[no-untyped-def]
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search")
    return success_response(data=BomService.list_boms(page=page, per_page=per_page, search=search))


@bom_bp.post("")
@login_required
def create_bom():  # type: ignore[no-untyped-def]
    body = request.get_json(silent=True) or {}
    try:
        req = BomCreateRequest(**body)
    except Exception as e:
        return error_response(str(e), 400)
    return success_response(data=BomService.create_bom(req.model_dump()), code=201)


@bom_bp.get("/<bomcd>")
@login_required
def get_bom(bomcd: str):  # type: ignore[no-untyped-def]
    data = BomService.get_bom(bomcd)
    if data is None:
        return error_response("BOM不存在", 404)
    return success_response(data=data)


@bom_bp.put("/<bomcd>")
@login_required
def update_bom(bomcd: str):  # type: ignore[no-untyped-def]
    body = request.get_json(silent=True) or {}
    try:
        req = BomUpdateRequest(**body)
    except Exception as e:
        return error_response(str(e), 400)
    data = req.model_dump(exclude_none=True)
    if not data:
        return error_response("无更新字段", 400)
    result = BomService.update_bom(bomcd, data)
    if result is None:
        return error_response("BOM不存在", 404)
    return success_response(data=result)


@bom_bp.delete("/<bomcd>")
@login_required
def delete_bom(bomcd: str):  # type: ignore[no-untyped-def]
    if not BomService.delete_bom(bomcd):
        return error_response("BOM不存在", 404)
    return success_response(message="已删除")


@bom_bp.post("/<bomcd>/details")
@login_required
def add_detail(bomcd: str):  # type: ignore[no-untyped-def]
    if BomService.get_bom(bomcd) is None:
        return error_response("BOM不存在", 404)
    body = request.get_json(silent=True) or {}
    try:
        req = BomDtCreateRequest(**body)
    except Exception as e:
        return error_response(str(e), 400)
    return success_response(data=BomService.add_detail(bomcd, req.model_dump()), code=201)


@bom_bp.put("/<bomcd>/details/<itemcd>")
@login_required
def update_detail(bomcd: str, itemcd: str):  # type: ignore[no-untyped-def]
    body = request.get_json(silent=True) or {}
    try:
        req = BomDtUpdateRequest(**body)
    except Exception as e:
        return error_response(str(e), 400)
    data = req.model_dump(exclude_none=True)
    if not data:
        return error_response("无更新字段", 400)
    result = BomService.update_detail(bomcd, itemcd, data)
    if result is None:
        return error_response("明细不存在", 404)
    return success_response(data=result)


@bom_bp.delete("/<bomcd>/details/<itemcd>")
@login_required
def delete_detail(bomcd: str, itemcd: str):  # type: ignore[no-untyped-def]
    if not BomService.delete_detail(bomcd, itemcd):
        return error_response("明细不存在", 404)
    return success_response(message="已删除")
```

- [ ] **Step 2: Register blueprint in app/__init__.py**

Add import:
```python
from app.api.bom import bom_bp
```

Add registration after inventory:
```python
app.register_blueprint(bom_bp, url_prefix="/api/v1/bom")
```

- [ ] **Step 3: Verify routes**

```bash
uv run python -c "from app import create_app; app=create_app(); [print(r) for r in app.url_map.iter_rules() if '/bom' in str(r)]"
```

Expected: 7 routes listed (GET/POST/DELETE `/bom`, GET/PUT/DELETE `/bom/<bomcd>`, POST `/bom/<bomcd>/details`, PUT/DELETE `/bom/<bomcd>/details/<itemcd>`)

- [ ] **Step 4: Commit**

```bash
git add app/api/bom.py app/__init__.py && git commit -m "feat(bom): add BOM API blueprint with 9 endpoints"
```

---

### Task 5: Frontend BOM API 类型与函数

**Files:** Modify `frontend/src/api/master.ts`

- [ ] **Step 1: Add BOM types and API functions**

Insert after the ItemRecord interface:

```typescript
// ---- BOM 类型 ----

export interface BomRecord {
    bomcd: string
    bomnm: string
    useflg: string
    gendate: string
    details?: BomDetailRecord[]
}

export interface BomDetailRecord {
    bomcd: string
    itemcd: string
    bomqty: number
    itemtyp: string
    item_nm?: string
}

export interface BomListPage {
    items: BomRecord[]
    total: number
}

// ---- BOM API ----

export function fetchBoms(params?: { page?: number | string; per_page?: number | string; search?: string }) {
    return request.get<never, { data: BomListPage }>('/bom', { params })
}

export function fetchBom(bomcd: string) {
    return request.get<never, { data: BomRecord }>(`/bom/${bomcd}`)
}

export function createBom(data: { bomcd: string; bomnm: string }) {
    return request.post<never, { data: BomRecord }>('/bom', data)
}

export function updateBom(bomcd: string, data: { bomnm?: string; useflg?: string }) {
    return request.put<never, { data: BomRecord }>(`/bom/${bomcd}`, data)
}

export function deleteBom(bomcd: string) {
    return request.delete<never, unknown>(`/bom/${bomcd}`)
}

export function addBomDetail(bomcd: string, data: { itemcd: string; bomqty: number; itemtyp: string }) {
    return request.post<never, { data: BomDetailRecord }>(`/bom/${bomcd}/details`, data)
}

export function updateBomDetail(bomcd: string, itemcd: string, data: { bomqty?: number; itemtyp?: string }) {
    return request.put<never, { data: BomDetailRecord }>(`/bom/${bomcd}/details/${itemcd}`, data)
}

export function deleteBomDetail(bomcd: string, itemcd: string) {
    return request.delete<never, unknown>(`/bom/${bomcd}/details/${itemcd}`)
}
```

Also, expand ItemRecord with missing fields:

```typescript
export interface ItemRecord {
    item_cd: string; item_nm: string; class_cd: string
    itemanm: string; unit: string; spec: string; useflg: string
    // 库存管理
    upperlimit?: number; lowerlimit?: number; minorder?: number
    // 周期
    newperiod?: number; oldperiod?: number
    // 规格
    itembrcd?: string; itemsize?: string
    // 采购
    pcrep?: string; purchasetyp?: string; keeper?: string
    // 其他
    backup?: string; typflg?: string; consume?: string
    [key: string]: unknown
}
```

- [ ] **Step 2: TypeScript compile check**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1 | tail -3
```

Expected: exit 0, no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/master.ts && git commit -m "feat(bom): add BOM API types and functions, expand ItemRecord"
```

---

### Task 6: BOM 管理页面

**Files:** Create `frontend/src/views/master/BomList.vue`, Modify `frontend/src/router/index.ts`

- [ ] **Step 1: Create BomList.vue**

```vue
<template>
    <div class="bom-layout">
        <div class="bom-left">
            <el-card header="BOM 列表">
                <div style="margin-bottom:8px;display:flex;gap:8px">
                    <el-input v-model="searchText" placeholder="搜索编码/名称" clearable size="small" @keyup.enter="loadData" />
                    <el-button type="primary" size="small" @click="openCreate">新建</el-button>
                </div>
                <el-table :data="boms" v-loading="loading" stripe highlight-current-row
                    @row-click="selectBom" size="small" max-height="500">
                    <el-table-column prop="bomcd" label="BOM编码" width="90" />
                    <el-table-column prop="bomnm" label="BOM名称" min-width="150" show-overflow-tooltip />
                    <el-table-column label="类型" width="90">
                        <template #default="{ row }">
                            <el-tag :type="bomType(row) === 'full' ? 'warning' : 'info'" size="small">
                                {{ bomType(row) === 'full' ? '全配件' : '主机+配件' }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="有效" width="55">
                        <template #default="{ row }">
                            <el-tag :type="row.useflg === '0' ? 'danger' : 'success'" size="small">{{ row.useflg === '0' ? '无效' : '有效' }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="70">
                        <template #default="{ row }">
                            <el-button type="danger" link size="small" @click.stop="handleDelete(row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <AppPagination v-model:current-page="page" v-model:page-size="perPage" :total="total" style="margin-top:8px;justify-content:flex-end" />
            </el-card>
        </div>
        <div class="bom-right">
            <el-card v-if="selectedBom">
                <template #header>
                    <span>{{ selectedBom.bomcd }} — {{ selectedBom.bomnm }}</span>
                    <el-button size="small" style="float:right" @click="openEdit">编辑</el-button>
                </template>
                <el-table :data="details" size="small" stripe max-height="450">
                    <el-table-column prop="itemcd" label="物料编码" width="90" />
                    <el-table-column prop="item_nm" label="物料名称" min-width="130" />
                    <el-table-column label="类型" width="80">
                        <template #default="{ row }">{{ row.itemtyp === '1' ? '核心配件' : '外设配件' }}</template>
                    </el-table-column>
                    <el-table-column prop="bomqty" label="数量" width="60" />
                    <el-table-column label="操作" width="70">
                        <template #default="{ row }">
                            <el-button type="danger" link size="small" @click="handleDeleteDetail(row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <el-button type="primary" size="small" style="margin-top:8px" @click="openAddDetail">添加配件</el-button>
            </el-card>
            <el-empty v-else description="选择左侧 BOM 查看明细" />
        </div>

        <!-- 新建/编辑 BOM 弹窗 -->
        <el-dialog :title="editingBomCd ? '编辑 BOM' : '新建 BOM'" v-model="dialogVisible" width="400px">
            <el-form :model="form" label-width="80px">
                <el-form-item label="BOM编码">
                    <el-input v-model="form.bomcd" :disabled="!!editingBomCd" maxlength="6" placeholder="6位物料编码" />
                </el-form-item>
                <el-form-item label="BOM名称">
                    <el-input v-model="form.bomnm" maxlength="50" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSave">保存</el-button>
            </template>
        </el-dialog>

        <!-- 添加配件弹窗 -->
        <el-dialog title="添加配件" v-model="detailDialogVisible" width="500px">
            <el-select v-model="newItemCd" filterable placeholder="搜索物料" size="small" style="width:100%;margin-bottom:8px">
                <el-option v-for="i in allItems" :key="i.item_cd" :label="`${i.item_cd} ${i.item_nm}`" :value="i.item_cd" />
            </el-select>
            <div style="display:flex;gap:8px">
                <el-input-number v-model="newItemQty" :min="1" placeholder="数量" size="small" />
                <el-select v-model="newItemTyp" size="small" style="width:130px">
                    <el-option label="外设配件" value="0" />
                    <el-option label="核心配件" value="1" />
                </el-select>
            </div>
            <template #footer>
                <el-button @click="detailDialogVisible = false">取消</el-button>
                <el-button type="primary" :disabled="!newItemCd" @click="handleAddDetail">添加</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchBoms, fetchBom, createBom, updateBom, deleteBom, addBomDetail, deleteBomDetail, fetchItems } from '@/api/master'
import type { BomRecord, BomDetailRecord } from '@/api/master'

const boms = ref<BomRecord[]>([]); const loading = ref(false); const searchText = ref('')
const page = ref(1); const perPage = ref(20); const total = ref(0)
const selectedBom = ref<BomRecord | null>(null); const details = ref<BomDetailRecord[]>([])
const allItems = ref<{ item_cd: string; item_nm: string }[]>([])

const dialogVisible = ref(false); const form = ref({ bomcd: '', bomnm: '' }); const editingBomCd = ref('')
const detailDialogVisible = ref(false); const newItemCd = ref(''); const newItemQty = ref(1); const newItemTyp = ref('0')

function bomType(row: BomRecord): string {
    if (!row.details) return ''
    return row.details.some(d => d.itemtyp === '1') ? 'full' : 'host'
}

async function loadData() {
    loading.value = true
    try {
        const res = await fetchBoms({ page: page.value, per_page: perPage.value, search: searchText.value || undefined })
        boms.value = res.data.items; total.value = res.data.total
    } catch { ElMessage.error('加载BOM失败') }
    finally { loading.value = false }
}

async function selectBom(row: BomRecord) {
    loading.value = true
    try {
        const res = await fetchBom(row.bomcd)
        selectedBom.value = res.data; details.value = res.data.details || []
    } catch { ElMessage.error('加载明细失败') }
    finally { loading.value = false }
}

function openCreate() { editingBomCd.value = ''; form.value = { bomcd: '', bomnm: '' }; dialogVisible.value = true }
function openEdit() { if (!selectedBom.value) return; editingBomCd.value = selectedBom.value.bomcd; form.value = { bomcd: selectedBom.value.bomcd, bomnm: selectedBom.value.bomnm }; dialogVisible.value = true }

async function handleSave() {
    try {
        if (editingBomCd.value) {
            await updateBom(editingBomCd.value, { bomnm: form.value.bomnm })
        } else {
            await createBom({ bomcd: form.value.bomcd.toUpperCase(), bomnm: form.value.bomnm })
        }
        dialogVisible.value = false; loadData()
    } catch { ElMessage.error('保存失败') }
}

async function handleDelete(row: BomRecord) {
    try {
        await ElMessageBox.confirm(`确定删除 BOM ${row.bomcd}？`, '确认')
        await deleteBom(row.bomcd)
        if (selectedBom.value?.bomcd === row.bomcd) { selectedBom.value = null; details.value = [] }
        loadData()
    } catch { /* cancelled */ }
}

async function openAddDetail() { detailDialogVisible.value = true; newItemCd.value = ''; newItemQty.value = 1; newItemTyp.value = '0'; if (!allItems.value.length) { try { const r = await fetchItems({ per_page: 999 }); allItems.value = r.data.items } catch { /**/ } } }

async function handleAddDetail() {
    if (!selectedBom.value) return
    try {
        await addBomDetail(selectedBom.value.bomcd, { itemcd: newItemCd.value, bomqty: newItemQty.value, itemtyp: newItemTyp.value })
        detailDialogVisible.value = false; selectBom(selectedBom.value)
    } catch { ElMessage.error('添加失败') }
}

async function handleDeleteDetail(row: BomDetailRecord) {
    if (!selectedBom.value) return
    try {
        await deleteBomDetail(selectedBom.value.bomcd, row.itemcd)
        selectBom(selectedBom.value)
    } catch { ElMessage.error('删除失败') }
}

onMounted(() => loadData())
</script>

<style lang="scss" scoped>
.bom-layout { display:flex; gap:12px; height:calc(100vh - 120px) }
.bom-left { width:420px; flex-shrink:0; overflow:auto }
.bom-right { flex:1; overflow:auto }
</style>
```

- [ ] **Step 2: Add route**

In `frontend/src/router/index.ts`, add inside master children:

```typescript
{
    path: 'master/bom',
    name: 'BomList',
    component: () => import('@/views/master/BomList.vue'),
    meta: { title: 'BOM管理' }
}
```

- [ ] **Step 3: TypeScript compile check**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1 | tail -3
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/master/BomList.vue frontend/src/router/index.ts && git commit -m "feat(bom): add BOM management page with dual-panel layout"
```

---

### Task 7: 物料页面字段扩展

**Files:** Modify `frontend/src/views/master/ItemList.vue`

- [ ] **Step 1: Expand table columns and edit form**

Add columns after `spec` column in the table:

```vue
<el-table-column label="库存上限" width="80">
    <template #default="{ row }">{{ row.upperlimit ?? '-' }}</template>
</el-table-column>
<el-table-column label="库存下限" width="80">
    <template #default="{ row }">{{ row.lowerlimit ?? '-' }}</template>
</el-table-column>
<el-table-column label="最小订购" width="80">
    <template #default="{ row }">{{ row.minorder ?? '-' }}</template>
</el-table-column>
<el-table-column label="新品周期" width="80">
    <template #default="{ row }">{{ row.newperiod ?? '-' }}</template>
</el-table-column>
<el-table-column label="旧品周期" width="80">
    <template #default="{ row }">{{ row.oldperiod ?? '-' }}</template>
</el-table-column>
<el-table-column label="采购负责人" width="100">
    <template #default="{ row }">{{ row.pcrep ?? '-' }}</template>
</el-table-column>
<el-table-column label="备注" min-width="130">
    <template #default="{ row }">{{ row.backup ?? '-' }}</template>
</el-table-column>
```

In the edit dialog form, add collapsed sections for:
- 库存管理 (upperlimit, lowerlimit, minorder)
- 周期管理 (newperiod, oldperiod)
- 采购管理 (pcrep, purchasetyp, keeper)

- [ ] **Step 2: TypeScript compile check**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/master/ItemList.vue && git commit -m "feat(item): expand item table with inventory/purchase/cycle fields"
```

---

### Task 8: 导航菜单更新 + API 文档 + 系统功能对比

**Files:** Modify `frontend/src/layout/AsideMenu.vue`, `docs/core/API接口文档.md`, `docs/core/系统功能对比分析与扩展规划.md`

- [ ] **Step 1: Add menu item**

In `AsideMenu.vue`, add after "物料管理" menu item:

```vue
<el-menu-item index="/master/bom">
    <el-icon><Box /></el-icon>
    <span>BOM管理</span>
</el-menu-item>
```

- [ ] **Step 2: Update API doc**

In `docs/core/API接口文档.md`, add after procurement section or near inventory:

```markdown
### 2.17 BOM 管理 `bom`

路由前缀：`/api/v1/bom`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/bom` | BOM列表(分页+搜索) |
| POST | `/bom` | 创建BOM |
| GET | `/bom/<bomcd>` | BOM详情(含明细) |
| PUT | `/bom/<bomcd>` | 更新BOM |
| DELETE | `/bom/<bomcd>` | 删除BOM |
| POST | `/bom/<bomcd>/details` | 添加BOM明细 |
| PUT | `/bom/<bomcd>/details/<itemcd>` | 更新BOM明细 |
| DELETE | `/bom/<bomcd>/details/<itemcd>` | 删除BOM明细 |
```

Update endpoint count: 207 → 216.

- [ ] **Step 3: Update system comparison doc**

In `docs/core/系统功能对比分析与扩展规划.md`, change BOM status from "已重构" to "完整" with note about CRUD.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/layout/AsideMenu.vue docs/core/API接口文档.md docs/core/系统功能对比分析与扩展规划.md && git commit -m "docs(bom): update menu, API doc, and system comparison for BOM module"
```

---

### Task 9: 端到端验证

- [ ] **Step 1: Start Flask and verify API**

```bash
pkill -f "flask run"; sleep 1; uv run flask run --debug -p 5001 &
sleep 3
TOKEN=$(curl -s http://localhost:5001/api/v1/login -H 'Content-Type: application/json' -d '{"user_id":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")
# Test GET list
curl -s "http://localhost:5001/api/v1/bom?page=1&per_page=3" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'code={d[\"code\"]} total={d[\"data\"][\"total\"]} items={len(d[\"data\"][\"items\"])}')"
# Expected: code=200 total=103 items=3
```

- [ ] **Step 2: Verify frontend page**

```bash
# Start frontend if not running
cd frontend && npm run dev &
# Visit http://localhost:3000/master/bom
```

- [ ] **Step 3: Run all tests**

```bash
uv run pytest -x -q tests/
# Expected: 148 passed
```

- [ ] **Step 4: Commit final fixes (if any)**

```bash
git add -A && git commit -m "chore(bom): final verification fixes" || echo "no changes"
```
