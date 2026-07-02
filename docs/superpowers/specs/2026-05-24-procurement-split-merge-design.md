---
类型: 技术设计文档
阅读状态: 待评审
tags:
  - 采购订单
  - 拆单
  - 并单
  - 设计规格
更新日期: 2026-05-24
创建日期: 2026-05-24
作者: CJ
版本: v1.0
---

# 采购订单拆分与合并功能设计规格

## 一、设计目标

解决当前"需求单 → 订单"一对一模式的不足：

1. **拆单**：同一需求行的商品分配给多个供应商
2. **并单**：多个需求单的同类商品合并采购

两个功能独立，不设计组合场景（符合行业惯例）。

## 二、基础现状

以下基础设施已存在，无需变更：

| 组件 | 位置 | 状态 |
|------|------|------|
| `RequisitionOrderLink` 模型 | `app/models/procurement.py:273` | `tpc20_requisition_order_link`，UK `(pcplanid, pclineno, rgstbillid, rgstlineno)` |
| `RequisitionOrderLinkRepository` | `app/repositories/procurement_repository.py:353` | `create_links()` 批量写入 |
| `PurchasePlanRepository.get_available_qty()` | `app/repositories/procurement_repository.py:134` | 查询 `v_requisition_execution` |
| `PurchaseRegisterService.create()` | `app/services/procurement_service.py:184` | 单订单创建，已有 TPC20 关联 + 余额校验 |

**数据库无需变更**，TPC20 现有结构已支持拆单和并单。

## 三、API 设计

### 3.1 端点清单

| 方法 | 路径 | 用途 | 优先级 |
|------|------|------|--------|
| POST | `/orders/batch` | 批量创建订单（拆单+并单统一入口） | P1 |
| POST | `/orders/batch/validate` | 预校验数量余额 | P1 |
| POST | `/requisitions/merge-preview` | 智能合并扫描 + 供应商推荐 | P2 |

### 3.2 统一批量创建端点

**设计决策**：拆单和并单底层操作相同（创建订单 + 写 TPC20），使用统一端点，不做 `/orders/merge-create`。

```
POST /orders/batch

Request:
{
  "orders": [
    {
      "suppliercd": "SUP001",
      "memo": "拆单-供应商A",
      "details": [
        {
          "ref_pcplanid": "PP000180", "ref_pclineno": 1,
          "itemcd": "MB5000", "rgsqty": 60, "unitprice": 100
        }
      ]
    },
    {
      "suppliercd": "SUP002",
      "details": [
        {
          "ref_pcplanid": "PP000180", "ref_pclineno": 1,
          "itemcd": "MB5000", "rgsqty": 40, "unitprice": 105
        }
      ]
    }
  ]
}
```

- 同一 `ref_pcplanid/ref_pclineno` 出现在不同 order → 拆单
- 不同 `ref_pcplanid` 出现在同一 order → 并单
- 单次最多 10 个订单

### 3.3 智能合并预览端点

```
POST /requisitions/merge-preview
（无必传入参，后端自动扫描）

Response:
{
  "code": 200,
  "data": {
    "mergeable": [
      {
        "itemcd": "MB5000", "itemnm": "电源",
        "total_qty": 100, "source_count": 3,
        "source_lines": [
          {"pcplanid": "PP000180", "pclineno": 1, "qty": 50, "dept": "部门A"},
          {"pcplanid": "PP000181", "pclineno": 1, "qty": 30, "dept": "部门B"},
          {"pcplanid": "PP000183", "pclineno": 2, "qty": 20, "dept": "部门D"}
        ],
        "suggested_suppliers": [...]
      }
    ],
    "unmergeable": [
      {"itemcd": "MT7002", "itemnm": "显示器", "source_count": 1, ...}
    ],
    "summary": { "mergeable_groups": 1, "unmergeable_items": 1, "estimated_orders": 1 }
  }
}
```

后端自动筛选：`auditflg='2'`（已审核）+ `available_qty > 0`，按 `itemcd` 分组，区分可合并组（count ≥ 2）和无可合并项（count = 1）。

## 四、并发控制

### 4.1 问题

两个用户同时对同一需求行下单，都可能通过余额校验，导致超量。

### 4.2 方案：pg_advisory_xact_lock

使用 PostgreSQL 事务级 advisory lock，以 `(pcplanid, pclineno)` 的哈希值作为锁 key：

```python
import hashlib

def _lock_requisition_line(pcplanid: str, pclineno: int) -> None:
    """获取需求行的 advisory lock，防止并发超量"""
    key = int(hashlib.md5(f"{pcplanid}:{pclineno}".encode()).hexdigest()[:16], 16)
    db.session.execute(sa.text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})

def batch_create(orders_data, creator):
    # 1. 收集涉及的所有需求行，逐一获取 advisory lock
    req_lines = set()
    for order in orders_data:
        for d in order["details"]:
            req_lines.add((d["ref_pcplanid"], d["ref_pclineno"]))
    
    for pcplanid, pclineno in req_lines:
        _lock_requisition_line(pcplanid, pclineno)
    
    # 2. 查询已关联数量（锁已获取，串行化保证）
    # 3. 校验：已关联 + 新数量 ≤ auditqty
    # 4. 写入 TPC20 + tpc12/tpc13
    # 5. COMMIT 自动释放所有 advisory lock
```

**为什么不用 FOR UPDATE**：首次拆单/并单时 TPC20 可能无已有记录，`FOR UPDATE` 无法锁空结果集。

`pg_advisory_xact_lock` 的优势：不依赖行是否存在、事务结束自动释放、不需要改表结构。

### 4.3 事务边界

`batch_create` 整个操作为一个事务。校验失败回滚所有订单（全部成功或全部失败）。

## 五、前端设计

### 5.1 拆单流程

**入口**：`PurchaseRegisterList.vue` → 【新建订单】→ 订单创建表单

```
选择需求单 → 显示明细行
  └── 点击[拆单] → 行内展开多条分配行
       ├── 60个 → 供应商A
       └── 40个 → 供应商B
  → 调 validate API 校验
  → 调 POST /orders/batch 提交
```

### 5.2 并单流程

**入口**：`PurchasePlanList.vue` → 【智能合并】按钮

```
点击【智能合并】
  → 后端自动扫描 audited+available 的需求
  → 弹窗展示分组结果：
      可合并：[✓] 电源(3个需求) [✓] 网线(2个需求)
      无可合并：○ 显示器(仅1个需求)
  → 用户勾选 + 选供应商
  → POST /orders/batch 提交
```

### 5.3 文件变更

| 文件 | 变更 | 内容 |
|------|------|------|
| `src/api/master.ts` | 新增 API 函数 | `batchCreateOrders`, `validateBatchOrders`, `getMergePreview` |
| `PurchaseRegisterList.vue` | 修改 | 订单创建表单新增拆分行功能 |
| `PurchasePlanList.vue` | 修改 | 新增【智能合并】按钮 + 合并预览弹窗 |

## 六、后端文件变更

| 文件 | 变更 | 内容 |
|------|------|------|
| `app/api/procurement.py` | 新增 3 个路由 | `/orders/batch`, `/orders/batch/validate`, `/requisitions/merge-preview` |
| `app/services/procurement_service.py` | 新增 2 个方法 | `batch_create()`, `merge_preview()` |
| `app/repositories/procurement_repository.py` | 新增 1 个方法 | `get_available_for_merge()` 查询可合并需求行 |
| `app/schemas/procurement.py` | 新增 Schema | `BatchOrderCreateRequest`, `MergePreviewResponse` |

## 七、测试用例

### 拆单
```
输入：PP000180-行1 电源×100 (auditqty=100, available=100)
操作：拆分为 SUP001×60 + SUP002×40
预期：
  - 生成 PO001（SUP001, 电源×60）+ PO002（SUP002, 电源×40）
  - TPC20 有 2 条记录，均关联 PP000180-行1
  - 视图 ordered_qty=100, available_qty=0
```

### 并单
```
输入：PP000180(电源×50) + PP000181(电源×30) + PP000183(电源×20)
操作：智能扫描 → 确认合并 → 生成给 SUP001
预期：
  - 生成 PO001（SUP001, 电源×100）
  - TPC20 有 3 条记录，分别关联三个需求单
```

### 并发
```
输入：PP000180-行1 available=50
操作：用户A下单40 + 用户B同时下单30
预期：先到的事务获取 advisory lock 成功，后到的事务在 lock 处等待，等第一个事务提交后校验失败（超量）
```

## 八、实施计划

| 阶段 | 内容 | 工期 |
|------|------|------|
| Phase 1 | 拆单功能（API + 前端） | 3天 |
| Phase 2 | 并单功能（智能扫描 + 预览 + 执行） | 2天 |
| Phase 3 | 联调测试 | 2天 |

### Phase 1 详细

| 任务 | 工期 |
|------|------|
| `POST /orders/batch` + `batch/validate` | 1天 |
| 前端拆单 UI（订单创建表单） | 1.5天 |
| 联调 | 0.5天 |

## 九、相关文档

- 原始设计方案：`docs/采购订单拆分与合并功能设计方案.md`
- 采购重构设计：`docs/superpowers/specs/2026-05-23-procurement-redesign.md`
- 需求审核分析：`docs/core/采购需求审核数量问题技术分析报告.md`
