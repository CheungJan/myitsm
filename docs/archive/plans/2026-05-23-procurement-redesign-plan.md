# 采购管理模块重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将采购管理模块从旧命名+弱关联架构重构为采购需求→订单→结算单→退货四模块强关联架构

**Architecture:** 后端 Flask 四层（API→Service→Repository→Model），前端 Vue 3 + Element Plus + composables，PostgreSQL 新增 TPC20 关联表 + 两个实时计算视图替代 TPC03

**Spec:** `docs/superpowers/specs/2026-05-23-procurement-redesign.md`

**Tech Stack:** Flask 2.3+, SQLAlchemy 2.0+, Alembic, Vue 3.3+, Element Plus 2.3+, TypeScript

---

## File Structure Map

| 文件 | 职责 | 阶段 |
|------|------|------|
| `app/api/procurement.py` | 路由 + 参数校验 + 协议转换 | 1, 3 |
| `app/services/procurement_service.py` | 业务编排 + 事务边界 | 1, 3 |
| `app/repositories/procurement_repository.py` | SQL 封装 + 查询条件 | 3 |
| `app/schemas/procurement.py` | Pydantic 请求/响应 Schema | 1, 3 |
| `app/models/procurement.py` | SQLAlchemy ORM 模型 | 2, 5 |
| `frontend/src/api/procurement.ts` | Axios API 封装 | 1, 4 |
| `frontend/src/config/menu.ts` | 侧边栏菜单 | 1 |
| `frontend/src/router/index.ts` | 前端路由 | 1 |
| `frontend/src/views/procurement/*.vue` | 页面组件 | 1, 4, 6 |
| `migrations/versions/` | Alembic 迁移脚本 | 2, 5 |

---

### Task 1: 后端 API 路由 + 注释命名统一

**Files:**
- Modify: `app/api/procurement.py` (full file)
- Modify: `app/services/procurement_service.py` (class comments only)

**范围：** 路由路径 + 函数名 + 注释，不涉及业务逻辑变更。

- [ ] **Step 1: 重写 `app/api/procurement.py` 路由路径和注释**

将所有 `/plans` → `/requisitions`，`/registers` → `/orders`，`/bills` → `/settlements`，更新函数名和 docstring。

```python
"""
采购管理 API。

路由前缀：/api/v1/procurement
采购需求→订单→结算单→退货→供应商评价全链路。
"""

from __future__ import annotations

from flask import Blueprint, g, request

from app.api.auth import login_required
from app.schemas.procurement import (
    ProcurementQuery,
    PurchaseBillCreate,
    PurchasePlanCreate,
    PurchasePlanDetailCreate,
    PurchasePlanStatusCreate,
    PurchasePlanStatusUpdate,
    PurchaseRegisterCreate,
    PurchaseRegisterDetailCreate,
    ReturnPurchaseBillCreate,
    ReturnPurchaseBillDetailCreate,
    SupplierAppraisalCreate,
    SupplierAppraisalDetailCreate,
)
from app.services.procurement_service import (
    PurchaseBillService,
    PurchasePlanService,
    PurchasePlanStatusService,
    PurchaseRegisterService,
    ReturnPurchaseService,
    SupplierAppraisalService,
)
from app.utils.response import error_response, success_response

__all__ = ["procurement_bp"]

procurement_bp = Blueprint("procurement", __name__)


# ---- 采购需求 ----

@procurement_bp.get("/requisitions")
@login_required
def list_requisitions():  # type: ignore[no-untyped-def]
    """采购需求列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = PurchasePlanService.list_records(
        auditflg=params.auditflg,
        pctyp=params.pctyp,
        start_date=params.start_date,
        end_date=params.end_date,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@procurement_bp.get("/requisitions/<pcplanid>")
@login_required
def get_requisition(pcplanid: str):  # type: ignore[no-untyped-def]
    """采购需求详情。"""
    data = PurchasePlanService.get(pcplanid)
    if data is None:
        return error_response(message="采购需求不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/requisitions")
@login_required
def create_requisition():  # type: ignore[no-untyped-def]
    """创建采购需求。"""
    json_data = request.get_json(silent=True) or {}
    body = PurchasePlanCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [PurchasePlanDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = PurchasePlanService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.post("/requisitions/<pcplanid>/audit")
@login_required
def audit_requisition(pcplanid: str):  # type: ignore[no-untyped-def]
    """审核采购需求。"""
    user_cd: str = g.current_user
    result = PurchasePlanService.audit(pcplanid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 采购订单 ----

@procurement_bp.get("/orders")
@login_required
def list_orders():  # type: ignore[no-untyped-def]
    """采购订单列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = PurchaseRegisterService.list_records(
        suppliercd=params.suppliercd,
        auditflg=params.auditflg,
        page=params.page,
        per_page=params.per_page,
    )
    return success_response(data=data)


@procurement_bp.get("/orders/<rgstbillid>")
@login_required
def get_order(rgstbillid: str):  # type: ignore[no-untyped-def]
    """采购订单详情。"""
    data = PurchaseRegisterService.get(rgstbillid)
    if data is None:
        return error_response(message="采购订单不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/orders")
@login_required
def create_order():  # type: ignore[no-untyped-def]
    """创建采购订单。"""
    json_data = request.get_json(silent=True) or {}
    body = PurchaseRegisterCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [PurchaseRegisterDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = PurchaseRegisterService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.post("/orders/<rgstbillid>/audit")
@login_required
def audit_order(rgstbillid: str):  # type: ignore[no-untyped-def]
    """审核采购订单。"""
    user_cd: str = g.current_user
    result = PurchaseRegisterService.audit(rgstbillid, user_cd)
    if not result.get("success"):
        return error_response(message=str(result.get("error", "")), code=400)
    return success_response(data=result)


# ---- 采购结算单 ----

@procurement_bp.get("/settlements")
@login_required
def list_settlements():  # type: ignore[no-untyped-def]
    """采购结算单列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = PurchaseBillService.list_records(
        whcd=params.whcd, page=params.page, per_page=params.per_page
    )
    return success_response(data=data)


@procurement_bp.get("/settlements/<pcbillid>")
@login_required
def get_settlement(pcbillid: str):  # type: ignore[no-untyped-def]
    """采购结算单详情。"""
    data = PurchaseBillService.get(pcbillid)
    if data is None:
        return error_response(message="采购结算单不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/settlements")
@login_required
def create_settlement():  # type: ignore[no-untyped-def]
    """创建采购结算单。"""
    body = PurchaseBillCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = PurchaseBillService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


# ---- 采购退货 ----

@procurement_bp.get("/returns")
@login_required
def list_returns():  # type: ignore[no-untyped-def]
    """采购退货列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = ReturnPurchaseService.list_records(
        whcd=params.whcd, page=params.page, per_page=params.per_page
    )
    return success_response(data=data)


@procurement_bp.get("/returns/<pcbillid>")
@login_required
def get_return(pcbillid: str):  # type: ignore[no-untyped-def]
    """采购退货详情。"""
    data = ReturnPurchaseService.get(pcbillid)
    if data is None:
        return error_response(message="采购退货单不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/returns")
@login_required
def create_return():  # type: ignore[no-untyped-def]
    """创建采购退货单。"""
    json_data = request.get_json(silent=True) or {}
    body = ReturnPurchaseBillCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [ReturnPurchaseBillDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = ReturnPurchaseService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


# ---- 供应商评价 ----

@procurement_bp.get("/supplier-appraisals")
@login_required
def list_appraisals():  # type: ignore[no-untyped-def]
    """供应商评价列表。"""
    params = ProcurementQuery.model_validate(request.args.to_dict())
    data = SupplierAppraisalService.list_records(
        auditflg=params.auditflg, page=params.page, per_page=params.per_page
    )
    return success_response(data=data)


@procurement_bp.get("/supplier-appraisals/<appid>")
@login_required
def get_appraisal(appid: str):  # type: ignore[no-untyped-def]
    """供应商评价详情。"""
    data = SupplierAppraisalService.get(appid)
    if data is None:
        return error_response(message="供应商评价不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/supplier-appraisals")
@login_required
def create_appraisal():  # type: ignore[no-untyped-def]
    """创建供应商评价。"""
    json_data = request.get_json(silent=True) or {}
    body = SupplierAppraisalCreate.model_validate(json_data)
    raw_details = json_data.get("details", [])
    details = [SupplierAppraisalDetailCreate.model_validate(d).model_dump() for d in raw_details]
    user_cd: str = g.current_user
    data = SupplierAppraisalService.create(body.model_dump(exclude_none=True), details, user_cd)
    return success_response(data=data, message="创建成功", code=201)


# ---- 采购需求执行看板 (原 TPC03，已冻结) ----

@procurement_bp.get("/plan-status")
@login_required
def list_plan_status():  # type: ignore[no-untyped-def]
    """@deprecated 采购需求执行看板（原 TPC03，后续迁移至视图）。"""
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    data = PurchasePlanStatusService.list_all(page=page, per_page=per_page)
    return success_response(data=data)


@procurement_bp.get("/plan-status/<itemcd>")
@login_required
def get_plan_status(itemcd: str):  # type: ignore[no-untyped-def]
    """@deprecated 采购需求执行看板详情。"""
    data = PurchasePlanStatusService.get(itemcd)
    if data is None:
        return error_response(message="不存在", code=404)
    return success_response(data=data)


@procurement_bp.post("/plan-status")
@login_required
def create_plan_status():  # type: ignore[no-untyped-def]
    """@deprecated 创建采购需求状态汇总（已冻结，不再使用）。"""
    body = PurchasePlanStatusCreate.model_validate(request.get_json(silent=True) or {})
    user_cd: str = g.current_user
    data = PurchasePlanStatusService.create(body.model_dump(exclude_none=True), user_cd)
    return success_response(data=data, message="创建成功", code=201)


@procurement_bp.put("/plan-status/<itemcd>")
@login_required
def update_plan_status(itemcd: str):  # type: ignore[no-untyped-def]
    """@deprecated 更新采购需求状态汇总（已冻结，不再使用）。"""
    body = PurchasePlanStatusUpdate.model_validate(request.get_json(silent=True) or {})
    data = PurchasePlanStatusService.update(itemcd, body.model_dump(exclude_none=True))
    if data is None:
        return error_response(message="不存在", code=404)
    return success_response(data=data)
```

- [ ] **Step 2: 更新 `app/services/procurement_service.py` 类注释**

```python
# 修改类 docstring：
class PurchasePlanService:
    """采购需求服务 (原采购计划，TPC01/TPC02)。"""

class PurchaseRegisterService:
    """采购订单服务 (原采购登记，TPC12/TPC13)。"""

class PurchaseBillService:
    """采购结算单服务 (原采购单据，TPC14)。"""

class ReturnPurchaseService:
    """采购退货服务 (TPC16/TPC17)。"""

class PurchasePlanStatusService:
    """@deprecated 采购需求执行看板服务 (原 TPC03，已冻结)。"""

class SupplierAppraisalService:
    """供应商评价服务 (TPC20/TPC21)。"""
```

- [ ] **Step 3: 验证后端路由未破坏**

```bash
uv run flask routes 2>&1 | grep procurement
```
确认路由 `/requisitions`、`/orders`、`/settlements`、`/returns` 正确注册。

- [ ] **Step 4: 提交**

```bash
git add app/api/procurement.py app/services/procurement_service.py
git commit -m "refactor(procurement): 后端API路由命名统一 — plans→requisitions, registers→orders, bills→settlements"
```

---

### Task 2: 前端 API 函数命名统一

**Files:**
- Modify: `frontend/src/api/procurement.ts` (full file)

- [ ] **Step 1: 重写 `frontend/src/api/procurement.ts`**

```typescript
import request from './request'

export interface ProcRecord { [key:string]: unknown }
export interface ProcPage { items: ProcRecord[]; total: number }

// ---- 采购需求 ----

export function fetchRequisitions(p?:Record<string,string>){
    return request.get<never,{data:ProcPage}>('/procurement/requisitions',{params:p})
}
export function fetchRequisitionDetail(pcplanid:string){
    return request.get<never,{data:ProcRecord}>('/procurement/requisitions/'+pcplanid)
}
export function createRequisition(body:Record<string,unknown>){
    return request.post<never,{data:ProcRecord}>('/procurement/requisitions',body)
}

// ---- 采购订单 ----

export function fetchOrders(p?:Record<string,string>){
    return request.get<never,{data:ProcPage}>('/procurement/orders',{params:p})
}
export function fetchOrderDetail(rgstbillid:string){
    return request.get<never,{data:ProcRecord}>('/procurement/orders/'+rgstbillid)
}
export function createOrder(body:Record<string,unknown>){
    return request.post<never,{data:ProcRecord}>('/procurement/orders',body)
}
export function fetchAvailableItems(p?:Record<string,string>){
    return request.get<never,{data:ProcRecord[]}>('/procurement/available-items',{params:p})
}

// ---- 采购结算单 ----

export function fetchSettlements(p?:Record<string,string>){
    return request.get<never,{data:ProcPage}>('/procurement/settlements',{params:p})
}
export function fetchSettlementDetail(pcbillid:string){
    return request.get<never,{data:ProcRecord}>('/procurement/settlements/'+pcbillid)
}
export function createSettlement(body:Record<string,unknown>){
    return request.post<never,{data:ProcRecord}>('/procurement/settlements',body)
}

// ---- 采购退货 ----

export interface ReturnPurchaseRecord {
    pcbillid: string; custcd: string; whcd: string; pcamt: number;
    invoiceflg: string; memo: string; gendate: string; opercd: string;
    ref_rgstbillid?: string;
    details?: ReturnPurchaseDetail[];
    [key:string]: unknown
}
export interface ReturnPurchaseDetail {
    itemcd: string; rpcqty: number; eid: string; units: string;
    ref_rgstlineno?: number;
    [key:string]: unknown
}
export interface ReturnPurchasePage { items: ReturnPurchaseRecord[]; total: number }

export function fetchReturns(p?:Record<string,string>){
    return request.get<never,{data:ReturnPurchasePage}>('/procurement/returns',{params:p})
}
export function fetchReturnDetail(pcbillid:string){
    return request.get<never,{data:ReturnPurchaseRecord}>('/procurement/returns/'+pcbillid)
}
export function createReturn(body:Record<string,unknown>){
    return request.post<never,{data:ReturnPurchaseRecord}>('/procurement/returns',body)
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/procurement.ts
git commit -m "refactor(procurement): 前端API函数命名统一 — fetchRequisitions/fetchOrders/fetchSettlements/fetchReturns"
```

---

### Task 3: 菜单 + 路由 + 页面标题命名统一

**Files:**
- Modify: `frontend/src/config/menu.ts:51-58`
- Modify: `frontend/src/router/index.ts:109-215`
- Modify: `frontend/src/views/procurement/PurchasePlanList.vue` (页面标题 + 弹窗标题 + imports)
- Modify: `frontend/src/views/procurement/PurchaseRegisterList.vue` (页面标题 + 弹窗标题 + imports)
- Modify: `frontend/src/views/procurement/PurchaseBillList.vue` (页面标题 + 弹窗标题 + imports)
- Modify: `frontend/src/views/procurement/ReturnPurchaseList.vue` (imports)

- [ ] **Step 1: 更新菜单 `frontend/src/config/menu.ts`**

将第 51-58 行修改为：
```typescript
        menu_cd: 'procurement', menu_nm: '采购管理',
        children: [
            { menu_cd: 'proc-requisitions', menu_nm: '采购需求', path: '/procurement/requisitions' },
            { menu_cd: 'proc-orders', menu_nm: '采购订单', path: '/procurement/orders' },
            { menu_cd: 'proc-settlements', menu_nm: '采购结算单', path: '/procurement/settlements' },
            { menu_cd: 'suppliers', menu_nm: '供应商管理', path: '/procurement/suppliers' },
            { menu_cd: 'appraisals', menu_nm: '供应商评价', path: '/procurement/appraisals' },
            { menu_cd: 'proc-returns', menu_nm: '采购退货', path: '/procurement/returns' }
        ]
```

- [ ] **Step 2: 更新路由 `frontend/src/router/index.ts`**

修改采购模块路由段（约 109-215 行）：

```typescript
                    // 采购需求
                    path: 'procurement/requisitions',
                    name: 'RequisitionList',
                    component: () => import('@/views/procurement/PurchasePlanList.vue'),
                    meta: { title: '采购需求' }
                },
                {
                    // 采购订单
                    path: 'procurement/orders',
                    name: 'OrderList',
                    component: () => import('@/views/procurement/PurchaseRegisterList.vue'),
                    meta: { title: '采购订单' }
                },
                {
                    // ... 其他路由保持不变 ...
                    // 采购结算单
                    path: 'procurement/settlements',
                    name: 'SettlementList',
                    component: () => import('@/views/procurement/PurchaseBillList.vue'),
                    meta: { title: '采购结算单' }
                },
                // ...
                {
                    // 采购退货
                    path: 'procurement/returns',
                    name: 'ReturnPurchaseList',
                    component: () => import('@/views/procurement/ReturnPurchaseList.vue'),
                    meta: { title: '采购退货' }
                },
```

- [ ] **Step 3: 更新 `PurchasePlanList.vue` 页面标题和 imports**

将模板中：
- `<h2>采购计划</h2>` → `<h2>采购需求</h2>`
- `新建计划` → `新建需求`
- `'计划详情 — '` → `'需求详情 — '`
- `新建采购计划` → `新建采购需求`

将 script 中 imports：
```typescript
import {fetchRequisitions, fetchRequisitionDetail, createRequisition, type ProcRecord} from '@/api/procurement'
```
将函数调用：
- `fetchProcPlans` → `fetchRequisitions`
- `fetchProcPlanDetail` → `fetchRequisitionDetail`
- `createProcPlan` → `createRequisition`

- [ ] **Step 4: 更新 `PurchaseRegisterList.vue` 页面标题和 imports**

将模板中：
- `<h2>采购登记</h2>` → `<h2>采购订单</h2>`
- `'采购登记 — '` → `'采购订单 — '`
- `登记号` → `订单号`

将 script 中 imports：
```typescript
import {fetchOrders} from '@/api/procurement';import type {ProcRecord} from '@/api/procurement'
```
将 `fetchProcRegisters` → `fetchOrders`

- [ ] **Step 5: 更新 `PurchaseBillList.vue` 页面标题和 imports**

将模板中：
- `<h2>采购单据</h2>` → `<h2>采购结算单</h2>`
- `'采购单据 — '` → `'结算单 — '`

将 script 中 imports：
```typescript
import {fetchSettlements} from '@/api/procurement';import type {ProcRecord} from '@/api/procurement'
```
将 `fetchProcBills` → `fetchSettlements`

- [ ] **Step 6: 更新 `ReturnPurchaseList.vue` imports**

将 script 中 imports：
```typescript
import {fetchReturns, type ReturnPurchaseRecord} from '@/api/procurement'
```
将 `fetchReturnPurchase` → `fetchReturns`

- [ ] **Step 7: 提交**

```bash
git add frontend/src/config/menu.ts frontend/src/router/index.ts \
  frontend/src/views/procurement/PurchasePlanList.vue \
  frontend/src/views/procurement/PurchaseRegisterList.vue \
  frontend/src/views/procurement/PurchaseBillList.vue \
  frontend/src/views/procurement/ReturnPurchaseList.vue
git commit -m "refactor(procurement): 前端菜单/路由/页面标题命名统一 — 采购需求/订单/结算单/退货"
```

---

### Task 4: TPC20 关联表模型 + 迁移 + 视图

**Files:**
- Create: `migrations/versions/xxxx_tpc20_link_and_views.py`
- Modify: `app/models/procurement.py` (新增 TPC20 模型)

- [ ] **Step 1: 新增 TPC20 模型到 `app/models/procurement.py`**

在 `SupplierAppraisalDt` 类之后、`PurchaseCheckInDt` 之前插入：

```python
# ---------------------------------------------------------------------------
# 采购需求-订单关联表
# ---------------------------------------------------------------------------


class RequisitionOrderLink(BaseModel):
    """采购需求与采购订单关联表（TPC20_REQUISITION_ORDER_LINK）。"""

    __tablename__ = "tpc20_requisition_order_link"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pcplanid = db.Column(db.String(20), nullable=False, comment="来源需求单号")
    pclineno = db.Column(db.Integer, nullable=False, comment="来源需求行号")
    rgstbillid = db.Column(db.String(20), nullable=False, comment="采购订单号")
    rgstlineno = db.Column(db.Integer, nullable=False, comment="订单行号")
    linkqty = db.Column(db.Numeric(12, 2), default=0, comment="关联数量")
    linkstatus = db.Column(
        db.String(20), default="ordered",
        comment="关联状态: ordered/partial_in/completed/cancelled"
    )
    gendate = db.Column(db.DateTime, comment="创建日期")
    upddate = db.Column(db.DateTime, comment="更新日期")
    opercd = db.Column(db.String(20), comment="操作员")

    __table_args__ = (
        db.UniqueConstraint(
            "pcplanid", "pclineno", "rgstbillid", "rgstlineno",
            name="uk_link_unique"
        ),
    )
```

- [ ] **Step 2: 扩展 TPC13 模型（添加冗余字段）**

在 `PurchaseRegisterDt` 类中添加：

```python
    ref_pcplanid = db.Column(db.String(20), comment="来源需求单号")
    ref_pclineno = db.Column(db.Integer, comment="来源需求行号")
```

- [ ] **Step 3: 生成并编辑迁移**

```bash
uv run flask db migrate -m "新增TPC20需求订单关联表+TPC13冗余字段+视图"
```

编辑生成的迁移文件，保留以下 upgrade 操作并补充视图：

```python
def upgrade():
    # TPC20 关联表
    op.create_table('tpc20_requisition_order_link',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('pcplanid', sa.String(length=20), nullable=False),
        sa.Column('pclineno', sa.Integer(), nullable=False),
        sa.Column('rgstbillid', sa.String(length=20), nullable=False),
        sa.Column('rgstlineno', sa.Integer(), nullable=False),
        sa.Column('linkqty', sa.Numeric(precision=12, scale=2), server_default='0'),
        sa.Column('linkstatus', sa.String(length=20), server_default='ordered'),
        sa.Column('gendate', sa.DateTime()),
        sa.Column('upddate', sa.DateTime()),
        sa.Column('opercd', sa.String(length=20)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pcplanid', 'pclineno', 'rgstbillid', 'rgstlineno', name='uk_link_unique')
    )
    op.create_index('idx_link_pcplan', 'tpc20_requisition_order_link', ['pcplanid', 'pclineno'])
    op.create_index('idx_link_register', 'tpc20_requisition_order_link', ['rgstbillid', 'rgstlineno'])

    # TPC13 冗余字段
    with op.batch_alter_table('tpc13_registerdt') as batch_op:
        batch_op.add_column(sa.Column('ref_pcplanid', sa.String(length=20)))
        batch_op.add_column(sa.Column('ref_pclineno', sa.Integer()))
        batch_op.create_index('idx_registerdt_ref', ['ref_pcplanid', 'ref_pclineno'])

    # 实时视图（通过 op.execute 执行 SQL）
    op.execute("""
        CREATE OR REPLACE VIEW v_requisition_execution AS
        SELECT
            p.pcplanid, p.plandate, p.auditflg, p.auditman, p.auditdate, p.useflg,
            dt.lineno, dt.itemcd, i.itemnm, i.spec, i.wunit,
            dt.rgstqty AS plan_qty,
            dt.auditqty AS audit_qty,
            COALESCE(link_stats.ordered_qty, 0) AS ordered_qty,
            COALESCE(link_stats.received_qty, 0) AS received_qty,
            dt.auditqty - COALESCE(link_stats.ordered_qty, 0) AS available_qty,
            CASE
                WHEN COALESCE(link_stats.ordered_qty, 0) = 0 THEN '未开始'
                WHEN COALESCE(link_stats.received_qty, 0) >= dt.rgstqty THEN '已完成'
                WHEN COALESCE(link_stats.received_qty, 0) > 0 THEN '执行中'
                ELSE '已下单'
            END AS execution_status,
            CASE WHEN dt.rgstqty > 0
                THEN ROUND(COALESCE(link_stats.received_qty, 0) / dt.rgstqty * 100, 2)
                ELSE 0
            END AS execution_rate
        FROM tpc01_pcplan p
        JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
        LEFT JOIN tmm12_items i ON dt.itemcd = i.itemcd
        LEFT JOIN (
            SELECT l.pcplanid, l.pclineno,
                SUM(l.linkqty) AS ordered_qty,
                SUM(CASE WHEN rd.inqty >= rd.rgsqty THEN l.linkqty ELSE 0 END) AS received_qty
            FROM tpc20_requisition_order_link l
            JOIN tpc13_registerdt rd ON l.rgstbillid = rd.rgstbillid AND l.rgstlineno = rd.lineno
            JOIN tpc12_register r ON rd.rgstbillid = r.rgstbillid
            WHERE r.useflg <> '9'
            GROUP BY l.pcplanid, l.pclineno
        ) link_stats ON dt.pcplanid = link_stats.pcplanid AND dt.lineno = link_stats.pclineno
        WHERE p.useflg = '1'
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_item_requisition_status AS
        SELECT
            dt.itemcd, i.itemnm, i.spec, i.wunit,
            SUM(dt.auditqty) AS total_audit_qty,
            SUM(dt.auditqty) - COALESCE(SUM(link_stats.ordered_qty), 0) AS available_for_order,
            json_agg(DISTINCT jsonb_build_object(
                'pcplanid', dt.pcplanid, 'pclineno', dt.lineno,
                'plandate', p.plandate, 'auditqty', dt.auditqty,
                'available_qty', dt.auditqty - COALESCE(link_stats.ordered_qty, 0)
            ) ORDER BY p.plandate) AS plan_details
        FROM tpc02_pcplandt dt
        JOIN tpc01_pcplan p ON dt.pcplanid = p.pcplanid AND p.useflg = '1' AND p.auditflg = '2'
        LEFT JOIN tmm12_items i ON dt.itemcd = i.itemcd
        LEFT JOIN (
            SELECT l.pcplanid, l.pclineno, SUM(l.linkqty) AS ordered_qty
            FROM tpc20_requisition_order_link l
            JOIN tpc12_register r ON l.rgstbillid = r.rgstbillid
            WHERE r.useflg <> '9'
            GROUP BY l.pcplanid, l.pclineno
        ) link_stats ON dt.pcplanid = link_stats.pcplanid AND dt.lineno = link_stats.pclineno
        WHERE dt.auditqty > 0
        GROUP BY dt.itemcd, i.itemnm, i.spec, i.wunit
        HAVING SUM(dt.auditqty) - COALESCE(SUM(link_stats.ordered_qty), 0) > 0
    """)


def downgrade():
    op.execute("DROP VIEW IF EXISTS v_item_requisition_status")
    op.execute("DROP VIEW IF EXISTS v_requisition_execution")
    with op.batch_alter_table('tpc13_registerdt') as batch_op:
        batch_op.drop_index('idx_registerdt_ref')
        batch_op.drop_column('ref_pclineno')
        batch_op.drop_column('ref_pcplanid')
    op.drop_table('tpc20_requisition_order_link')
```

- [ ] **Step 4: 执行迁移**

```bash
uv run flask db upgrade
```

- [ ] **Step 5: 验证**

```bash
psql -U cheungjan -d myitsm -c "\dt tpc20*"
psql -U cheungjan -d myitsm -c "SELECT * FROM v_requisition_execution LIMIT 3"
psql -U cheungjan -d myitsm -c "SELECT * FROM v_item_requisition_status LIMIT 3"
```

- [ ] **Step 6: 提交**

```bash
git add app/models/procurement.py migrations/versions/
git commit -m "feat(procurement): 新增TPC20需求订单关联表+TPC13冗余字段+执行视图"
```

---

### Task 5: 后端订单创建关联逻辑 + 余额校验 + 可用商品查询

**Files:**
- Modify: `app/schemas/procurement.py` (新增 OrderCreate schema 含 ref 字段)
- Modify: `app/repositories/procurement_repository.py` (新增 link 写入 + 可用商品查询)
- Modify: `app/services/procurement_service.py` (创建订单时写入 TPC20)
- Modify: `app/api/procurement.py` (新增 /available-items 端点)

- [ ] **Step 1: 新增 Schema 到 `app/schemas/procurement.py`**

```python
class OrderDetailCreate(BaseModel):
    """采购订单明细（含来源需求关联）。"""

    itemcd: str = Field(..., max_length=6, description="物料编码")
    rgsqty: float = Field(..., gt=0, description="采购数量")
    units: str | None = Field(None, max_length=4)
    rgstprice: float | None = Field(None, description="单价")
    deliverdate: datetime | None = Field(None, description="交付日期")
    ref_pcplanid: str = Field(..., max_length=20, description="来源需求单号")
    ref_pclineno: int = Field(..., description="来源需求行号")


class OrderCreate(BaseModel):
    """创建采购订单。"""

    suppliercd: str = Field(..., max_length=8)
    pcrep: str | None = Field(None, max_length=6)
    rgstdate: datetime | None = Field(None)
    memo: str | None = Field(None, max_length=255)
    details: list[OrderDetailCreate] = Field(..., min_length=1)
```

- [ ] **Step 2: 新增 Repository 方法到 `app/repositories/procurement_repository.py`**

```python
class RequisitionOrderLinkRepository:
    """需求-订单关联表数据访问。"""

    @staticmethod
    def create_links(details: list[dict[str, Any]]) -> None:
        from app.models.procurement import RequisitionOrderLink
        now = datetime.now(UTC)
        for d in details:
            link = RequisitionOrderLink(
                pcplanid=d["ref_pcplanid"],
                pclineno=d["ref_pclineno"],
                rgstbillid=d["rgstbillid"],
                rgstlineno=d["rgstlineno"],
                linkqty=d["rgsqty"],
                gendate=now,
            )
            db.session.add(link)

    @staticmethod
    def get_available_items(suppliercd: str | None = None) -> list[dict[str, Any]]:
        sql = sa.text(
            "SELECT * FROM v_item_requisition_status"
            + (" WHERE itemcd IN (SELECT itemcd FROM tip02_supplier_price WHERE supp_cd = :supp_cd)" if suppliercd else "")
        )
        params = {"supp_cd": suppliercd} if suppliercd else {}
        result = db.session.execute(sql, params)
        return [dict(row._mapping) for row in result]
```

同时在 `PurchaseRegisterRepository.create` 中已写入的 TPC13 明细需增加 `ref_pcplanid` / `ref_pclineno` 字段。

- [ ] **Step 3: 更新 Service 层 `app/services/procurement_service.py`**

修改 `PurchaseRegisterService.create` 方法，在创建订单后写入 TPC20 关联：

```python
@staticmethod
def create(
    data: dict[str, Any],
    details: list[dict[str, Any]],
    creator: str,
) -> dict[str, Any]:
    # 校验余额
    for d in details:
        ref_pcplanid = d.get("ref_pcplanid")
        ref_pclineno = d.get("ref_pclineno")
        rgsqty = float(d.get("rgsqty", 0))
        if ref_pcplanid and ref_pclineno:
            available = PurchasePlanRepository.get_available_qty(ref_pcplanid, ref_pclineno)
            if rgsqty > available:
                raise ValueError(
                    f"采购数量({rgsqty})超过需求 {ref_pcplanid} 行 {ref_pclineno} 的可用余额({available})"
                )

    record = PurchaseRegisterRepository.create(data, creator)
    rgstbillid = record.rgstbillid

    for i, d in enumerate(details, 1):
        detail_data = {**d, "rgstbillid": rgstbillid, "lineno": i}
        PurchaseRegisterRepository.add_detail(detail_data)

    # 写入 TPC20 关联
    RequisitionOrderLinkRepository.create_links([
        {**d, "rgstbillid": rgstbillid, "rgstlineno": i}
        for i, d in enumerate(details, 1)
        if d.get("ref_pcplanid") and d.get("ref_pclineno")
    ])

    db.session.commit()
    return record.to_dict()
```

同时在 `PurchasePlanRepository` 新增余额查询：

```python
@staticmethod
def get_available_qty(pcplanid: str, pclineno: int) -> float:
    row = db.session.execute(
        sa.text(
            "SELECT available_qty FROM v_requisition_execution "
            "WHERE pcplanid = :pid AND lineno = :lno"
        ),
        {"pid": pcplanid, "lno": pclineno},
    ).fetchone()
    return float(row.available_qty) if row else 0.0
```

- [ ] **Step 4: 新增 `/available-items` API 端点**

在 `app/api/procurement.py` 采购订单段后添加：

```python
@procurement_bp.get("/available-items")
@login_required
def list_available_items():  # type: ignore[no-untyped-def]
    """查询可采购商品及来源需求单（用于订单录入时选择）。"""
    suppliercd: str | None = request.args.get("suppliercd")
    data = RequisitionOrderLinkRepository.get_available_items(suppliercd)
    return success_response(data=data)
```

- [ ] **Step 5: 提交**

```bash
git add app/schemas/procurement.py app/repositories/procurement_repository.py \
  app/services/procurement_service.py app/api/procurement.py
git commit -m "feat(procurement): 订单创建关联TPC20+余额校验+可用商品查询API"
```

---

### Task 6: TPC16/TPC17 退货表字段补全

**Files:**
- Create: `migrations/versions/xxxx_rpcbill_audit_fields.py`
- Modify: `app/models/procurement.py` (ReturnPurchaseBill 模型)

- [ ] **Step 1: 更新 `ReturnPurchaseBill` 模型**

在 `app/models/procurement.py` 中为 `ReturnPurchaseBill` 类添加字段：

```python
    ref_rgstbillid = db.Column(db.String(8), comment="来源采购订单号")
    auditflg = db.Column(db.String(1), default="0", comment="审核标志")
    auditman = db.Column(db.String(6), comment="审核人")
    auditdate = db.Column(db.DateTime, comment="审核日期")
```

为 `ReturnPurchaseBillDt` 添加：

```python
    ref_rgstlineno = db.Column(db.Integer, comment="来源订单行号")
```

- [ ] **Step 2: 生成并执行迁移**

```bash
uv run flask db migrate -m "TPC16/TPC17退货表补全审核字段+来源订单关联"
uv run flask db upgrade
```

- [ ] **Step 3: 提交**

```bash
git add app/models/procurement.py migrations/versions/
git commit -m "feat(procurement): TPC16/TPC17退货表补全审核字段+来源订单关联"
```

---

### Task 7: 前端集成验证

**Files:**
- Modify: `frontend/src/views/procurement/PurchasePlanList.vue` (验证页面正常工作)

- [ ] **Step 1: 启动开发服务器验证**

```bash
uv run flask run --debug &
cd frontend && npm run dev &
```

- [ ] **Step 2: 浏览器验证采购需求列表页**

访问 `http://localhost:5173/procurement/requisitions`，确认：
- 页面标题显示"采购需求"
- 列表数据正常加载
- 采购类型显示中文名称（如"计划采购"）
- 筛选功能正常（日期范围、审批标记、采购类型）

- [ ] **Step 3: 验证新建采购需求**

点击"新建需求"按钮，确认：
- 弹窗标题"新建采购需求"
- 采购类型下拉显示 6 个选项，默认选中"10-计划采购"
- 提交后列表刷新

- [ ] **Step 4: 验证采购订单页面**

访问 `http://localhost:5173/procurement/orders`，确认页面正常。

- [ ] **Step 5: 提交（如有微调）**

```bash
git add frontend/
git commit -m "chore(procurement): 前端集成验证通过，微调页面"
```
