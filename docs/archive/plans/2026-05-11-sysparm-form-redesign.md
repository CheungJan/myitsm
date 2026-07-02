# 系统参数表单化改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将系统参数页从单行表格改为 3 分组可编辑表单，新增 `PUT /sysparms/SYSPARM` 接口。

**Architecture:** 后端在 Repository→Service→API 三层各加一个 update 方法，URL 固定 `SYSPARM` 定位单例记录。前端用 `el-form` 分组展示 6 个有效字段，废弃字段不渲染，`GET /sysparms/SYSPARM` 加载初始值。

**Tech Stack:** Flask + SQLAlchemy（后端），Vue 3 + Element Plus（前端）

**Spec:** `docs/superpowers/specs/2026-05-11-sysparm-form-redesign.md`

---

### Task 1: 后端测试 — 验证 PUT /sysparms 行为

**Files:** Create `tests/test_sysparm_api.py`

- [ ] **Step 1: 写失败的集成测试**

```python
"""系统参数更新 API 测试。"""
import pytest
from app import create_app
from app.extensions import db


@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
        yield c


def login(client):
    resp = client.post("/api/v1/login", json={"user_id": "admin", "password": "admin123"})
    return resp.get_json()["data"]["token"]


def test_update_sysparm_success(client):
    """PUT /sysparms/SYSPARM 应正确更新参数值。"""
    token = login(client)
    resp = client.put(
        "/api/v1/sysparms/SYSPARM",
        json={"costtype": "2", "poinvaliddays": 30},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 200
    assert data["data"]["costtype"] == "2"
    assert data["data"]["poinvaliddays"] == 30


def test_update_sysparm_not_found(client):
    """PUT /sysparms/NOEXIST 应返回 404。"""
    token = login(client)
    resp = client.put(
        "/api/v1/sysparms/NOEXIST",
        json={"costtype": "2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["code"] == 404


def test_sysparm_requires_auth(client):
    """未登录调用应返回 401。"""
    resp = client.put("/api/v1/sysparms/SYSPARM", json={"costtype": "2"})
    assert resp.status_code == 401
```

- [ ] **Step 2: 运行测试，验证失败**

```bash
uv run pytest tests/test_sysparm_api.py -v
```

Expected: `test_update_sysparm_success` FAIL（端点不存在 404），`test_sysparm_requires_auth` 可能 PASS 或 FAIL

---

### Task 2: Repository 层 — `update_sysparm`

**Files:** Modify `app/repositories/system_repository.py`，在已有 `get_sysparm_by_cd` 方法后添加。

- [ ] **Step 1: 添加 `update_sysparm` 方法**

```python
@staticmethod
def update_sysparm(parm_cd: str, data: dict[str, Any]) -> SysParm | None:
    """更新系统参数（单例表）。"""
    r = db.session.get(SysParm, parm_cd)
    if r:
        for k, v in data.items():
            setattr(r, k, v)
        db.session.commit()
    return r
```

- [ ] **Step 2: 验证**

```bash
grep -A6 "def update_sysparm" app/repositories/system_repository.py
```

---

### Task 3: Service 层 — `update_sysparm`

**Files:** Modify `app/services/system_service.py`，在已有 `get_sysparm` 方法后添加。

- [ ] **Step 1: 添加 `update_sysparm` 方法**

```python
def update_sysparm(self, parm_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """更新系统参数。"""
    r = self._repo.update_sysparm(parm_cd, data)
    return r.to_dict() if r else None
```

- [ ] **Step 2: 验证**

```bash
grep -A3 "def update_sysparm" app/services/system_service.py
```

---

### Task 4: API 端点 — `PUT /sysparms/<parm_cd>`

**Files:** Modify `app/api/system.py`，在已有 `get_sysparm` 端点后添加。

- [ ] **Step 1: 添加 PUT 端点**

```python
@system_bp.put("/sysparms/<parm_cd>")
@login_required
def update_sysparm(parm_cd: str):  # type: ignore[no-untyped-def]
    """更新系统参数（单例表）。"""
    body = request.get_json(silent=True) or {}
    r = _service.update_sysparm(parm_cd, body)
    return success_response(data=r) if r else error_response("参数不存在", 404)
```

- [ ] **Step 2: 验证**

```bash
# 重启 Flask
kill $(lsof -ti :5001) 2>/dev/null; sleep 1
nohup uv run flask run --debug --port 5001 > /tmp/flask.log 2>&1 & sleep 3

TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/login -H 'Content-Type: application/json' -d '{"user_id":"admin","password":"admin123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")

# 测试更新
curl -s -X PUT http://localhost:5001/api/v1/sysparms/SYSPARM \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"costtype":"2","poinvaliddays":30}' | python3 -c "
import sys,json;d=json.load(sys.stdin)
assert d['code']==200, f'FAIL: {d}'
print('OK: costtype={}, poinvaliddays={}'.format(d['data']['costtype'],d['data']['poinvaliddays']))
"

# 恢复
curl -s -X PUT http://localhost:5001/api/v1/sysparms/SYSPARM \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"costtype":"1","poinvaliddays":1}' > /dev/null
echo "已恢复默认值"
```

Expected: `OK: costtype=2, poinvaliddays=30` + 恢复成功

- [ ] **Step 3: 运行测试验证**

```bash
uv run pytest tests/test_sysparm_api.py -v
```

Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add app/repositories/system_repository.py app/services/system_service.py app/api/system.py tests/test_sysparm_api.py
git commit -m "feat(sysparm): add PUT /sysparms/<parm_cd> update endpoint"
```

---

### Task 5: 前端 API — `updateSysparm`

**Files:** Modify `frontend/src/api/system.ts`

- [ ] **Step 1: 添加 API 函数**

在已有的 `fetchSysparms()` 函数后面添加：

```typescript
export function updateSysparm(parmCd: string, data: Record<string, unknown>) {
    return request.put<never, { data: Record<string, unknown> }>(`/sysparms/${parmCd}`, data)
}
```

- [ ] **Step 2: 验证**

```bash
grep "updateSysparm" frontend/src/api/system.ts
```

---

### Task 6: 前端页面 — ParamsList.vue 重写为分组表单

**Files:** 重写 `frontend/src/views/system/ParamsList.vue`

- [ ] **Step 1: 读取当前文件**

```bash
cat frontend/src/views/system/ParamsList.vue
```

- [ ] **Step 2: 写入新表单组件**

```vue
<template>
    <div class="page">
        <el-card header="系统参数（当前已生效）">
            <el-form :model="form" label-width="140px" style="max-width:600px">
                <el-divider content-position="left">仓储配置</el-divider>
                <el-form-item label="成本核算方式">
                    <el-select v-model="form.costtype" style="width:240px">
                        <el-option label="移动加权" value="1" />
                        <el-option label="先进先出" value="2" />
                    </el-select>
                </el-form-item>
                <el-form-item label="中心仓库编码">
                    <el-input v-model="form.centralwarehouse" style="width:240px" />
                </el-form-item>

                <el-divider content-position="left">采购/销售配置</el-divider>
                <el-form-item label="采购计划失效天数">
                    <el-input-number v-model="form.poinvaliddays" :min="1" :max="365" />
                </el-form-item>
                <el-form-item label="销售单失效天数">
                    <el-input-number v-model="form.soinvaliddays" :min="1" :max="365" />
                </el-form-item>
                <el-form-item label="门店单据类型">
                    <el-input-number v-model="form.shopbilltype" :min="0" :max="99" />
                </el-form-item>

                <el-divider content-position="left">系统安全</el-divider>
                <el-form-item label="允许多点登录">
                    <el-switch v-model="form.allowmultilogon" active-value="1" inactive-value="0" />
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchSysparms, updateSysparm } from '@/api/system'

const form = reactive({
    costtype: '1', centralwarehouse: '', poinvaliddays: 1,
    soinvaliddays: 1, shopbilltype: '1', allowmultilogon: '1',
})
const saving = ref(false)

onMounted(async () => {
    try {
        const res = await fetchSysparms()
        const list = (res.data || []) as Record<string,unknown>[]
        if (list.length > 0) {
            const r = list[0]
            form.costtype = (r.costtype as string) || '1'
            form.centralwarehouse = (r.centralwarehouse as string) || ''
            form.poinvaliddays = Number(r.poinvaliddays) || 1
            form.soinvaliddays = Number(r.soinvaliddays) || 1
            form.shopbilltype = (r.shopbilltype as string) || '1'
            form.allowmultilogon = (r.allowmultilogon as string) || '1'
        }
    } catch { /* */ }
})

async function handleSave() {
    saving.value = true
    try {
        await updateSysparm('SYSPARM', { ...form })
        ElMessage.success('保存成功')
    } catch { /* */ }
    finally { saving.value = false }
}
</script>

<style lang="scss" scoped>
.page { padding: 16px; }
</style>
```

- [ ] **Step 3: 验证 HMR 编译**

```bash
tail -2 /tmp/vite.log 2>&1 | grep hmr
```

Expected: HMR update line，无 error

- [ ] **Step 4: 浏览器验证**

打开 `http://localhost:3000/system/params`：
- 表单显示 3 个分组，6 个字段值正确加载
- 修改成本核算方式 → 点保存 → 提示成功
- 刷新页面 → 值保持修改后的结果

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/system.ts frontend/src/views/system/ParamsList.vue
git commit -m "feat(sysparm): redesign params page as grouped edit form"
```

---

### Task 7: 文档更新

**Files:** Modify `docs/core/API接口文档.md`

- [ ] **Step 1: 在系统参数行加 PUT**

将 API 文档中的系统参数行从：
```
| GET | `/sysparms` | 系统参数列表 |
| GET | `/sysparms/<parm_cd>` | 指定系统参数 |
```
改为：
```
| GET | `/sysparms` | 系统参数列表 |
| GET | `/sysparms/<parm_cd>` | 指定系统参数 |
| PUT | `/sysparms/<parm_cd>` | 更新系统参数 |
```

- [ ] **Step 2: Commit**

```bash
git add docs/core/API接口文档.md
git commit -m "docs: add PUT /sysparms to API doc"
```
