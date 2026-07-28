# 上门记录 / 配件更换 / 收费 Tab 优化方案

> 状态：讨论中 | 创建：2026-07-19 | 更新：2026-07-19

---

## 1. 现状与问题

### 1.1 当前 Tab 结构

```
[客户信息] [派工] [通知记录] [上门服务] [回访] [配件更新] [收费] [设备资产]
```

### 1.2 三个 Tab 的数据关系

| Tab | 数据表 | 干什么 | 与主表关系 |
|-----|--------|--------|-----------|
| 上门服务 | TIT23 | 到店/离店考勤、是否解决 | 故障代码来自主表 `TIT10.faultcode` |
| 配件更新 | TIT25 | 更换配件、价格、操作类型 | 故障代码来自主表 `TIT10.faultcode` |
| 收费 | TIT26 | 收费类型、金额、收款日期 | 无设备/配件字段 |

### 1.3 痛点

**配件更换 + 收费 重复录入**：当配件更换涉及收费（如购买配件），用户必须在"配件更新"和"收费"两个 tab 分别创建记录——同一个维修动作拆成两次录入。这是 PB 历史债：PB 早期资产表（TMM43_EID）无属性字段区分"硬件更换"和"非硬件服务"，所以拆成两张表。现在资产表已完善，拆分前提不成立。

### 1.4 为什么上门记录不合并？

上门记录是**考勤/轨迹**类信息——记录工程师到没到、几点到、几点走。维修记录是**执行**类信息——换了什么、收了多少。两者关注点不同：

- 一个维护单可能**上门 3 次**才修好，但只有 1 次涉及配件更换和收费
- TIT23 跨单据复用（日常/开通/翻新/保养都用）
- 不是每次上门都有配件操作和收费

**结论**：上门记录独立保留不变，配件更新 + 收费合并。

### 1.5 故障代码存哪里？

`faultcode` 和 `device_id` 已在主表 `TIT10_MAINTENANCEDAY` 中：

```python
# app/models/itsm.py MaintenanceDaily
device_id = db.Column(db.String(13), comment="故障设备编号")     # 第 163 行
faultcode = db.Column(db.String(80), comment="故障编码")         # 第 167 行
```

子表（TIT23/TIT25）无需额外存储，直接读取主表即可。

---

## 2. 优化方案：两 Tab

```
当前:  [上门服务] [配件更新] [收费]          三Tab
优化后: [上门记录] [维修记录]                 两Tab
```

| Tab | 干什么 | 数据 | 变更 |
|-----|--------|------|------|
| **上门记录** | 到店/离店考勤、是否解决 | TIT23 | **不变** |
| **维修记录** | 故障诊断 + 配件更换 + 收费 | TIT25 扩展（吸收 TIT26） | 加 4 字段 |

### 2.1 TIT25 扩展（仅 4 个字段）

吸收 TIT26 的独有字段，扩展 C_TYPE 枚举：

```sql
ALTER TABLE tit25_accessories_update ADD COLUMN paytype VARCHAR(30);     -- 收费类型
ALTER TABLE tit25_accessories_update ADD COLUMN payje NUMERIC(10,3);     -- 收款金额
ALTER TABLE tit25_accessories_update ADD COLUMN paydate TIMESTAMP;       -- 收款日期
ALTER TABLE tit25_accessories_update ADD COLUMN memo VARCHAR(250);       -- 备注
```

**C_TYPE 扩展**（保持向后兼容）：

| C_TYPE | 含义 | 来源 |
|--------|------|------|
| `1` | 维修（更换配件修复） | 现有 |
| `2` | 购买（购买新配件） | 现有 |
| `3` | 非更换服务（上门费/检测费等） | 新增 ← 原 TIT26 |
| `4` | 整机更换 | 新增 |

### 2.2 维修记录表单（按 C_TYPE 动态显示）

```
┌─ 新增维修记录 ──────────────────────────────────────────┐
│ 服务类型: [维修更换 ▾] [购买 ▾] [非更换服务 ▾] [整机更换 ▾] │
│                                                         │
│ ── 基本信息 ──                                          │
│ 故障代码: [来自主表 TIT10.faultcode，只读展示]             │
│ 工程师: [____]                                           │
│                                                         │
│ ── 配件/设备信息（C_TYPE=1,2,4 显示）──                    │
│ 配件类型: [____]  整机ID: [____]                         │
│ 旧配件ID: [____]  新配件ID: [____]  价格: [____]          │
│                                                         │
│ ── 费用信息（全部类型可选）──                               │
│ 收费类型: [上门费/检测费/配件费/软件服务费/其他]            │
│ 金额: [____]  收款日期: [____]                            │
│ 收据号: [____]  送货单: [____]  备注: [____]             │
└─────────────────────────────────────────────────────────┘
```

#### 字段必填规则

| 字段 | 1=维修 | 2=购买 | 3=非更换 | 4=整机更换 |
|------|:---:|:---:|:---:|:---:|
| engineer_id | 必填 | 必填 | 必填 | 必填 |
| accessories_type | 必填 | 必填 | — | — |
| device_id | 选填 | — | — | 必填 |
| old_accessories_id | 选填 | — | — | — |
| new_accessories_id | 必填 | 必填 | — | 必填 |
| price | 选填 | 必填 | — | 选填 |
| paytype | 选填 | 必填 | 必填 | 选填 |
| payje | 选填 | 必填 | 必填 | 选填 |

---

## 3. 与 PB 方案的一致性

参考文档 `docs/core/故障代码体系优化技术文档.md` 第 3.7 节：

| 对比项 | PB 方案 | myitsm 方案 |
|--------|---------|-------------|
| C_TYPE 扩展 | 1=维修, 2=购买, 3=非更换, 4=整机更换 | 相同 ✅ |
| TIT25 加字段 | payje/paytype/paydate/memo | 相同 ✅ |
| TIT26 处理 | 数据迁移，表保留 | 相同 ✅ |
| 前端合并 | 合并 tabpage_5 + tabpage_7 | 合并为"维修记录" tab ✅ |
| D2D 处理 | 独立保留 (tabpage_3) | 独立保留 ✅ |

---

## 4. 数据迁移

```sql
-- TIT26 → TIT25（C_TYPE='3' 非更换服务）
INSERT INTO tit25_accessories_update (
    maintenance_id, business_operation_id, store_id, engineer_id,
    receipt_id, delivery_id, paytype, payje, paydate, memo,
    create_time, creator, update_time, updator,
    auditflg, c_type
)
SELECT
    maintenance_id, business_operation_id, store_id, engineer_id,
    receipt_id, delivery_id, paytype, payje, paydate, memo,
    create_time, creator, update_time, updator,
    useflg, '3'
FROM tit26_paylist
WHERE useflg = '1';
```

---

## 5. 后端 API

```
# 维修记录（替代配件更新 + 收费）
GET    /api/v1/itsm/repair-records/<maintenance_id>
POST   /api/v1/itsm/repair-records
PUT    /api/v1/itsm/repair-records/<id>

# 上门记录（不变）
沿用现有 /api/v1/itsm/d2d/...
```

---

## 6. 实施步骤

| 阶段 | 任务 | 涉及文件 |
|------|------|---------|
| 1 | Alembic：TIT25 加 paytype/payje/paydate/memo | 迁移脚本 |
| 2 | 更新 AccessoriesUpdate 模型 | `app/models/itsm.py` |
| 3 | 数据迁移 TIT26→TIT25 | SQL |
| 4 | 后端 RepairRecordService + API | `app/services/` `app/api/itsm.py` |
| 5 | 前端 RepairRecordTab.vue（按 C_TYPE 动态表单） | `frontend/src/views/itsm/` |
| 6 | 前端 MaintenanceList.vue：移除"收费"tab，"配件更新"→"维修记录" | `MaintenanceList.vue` |
| 7 | 测试 | `tests/` |

---

## 7. 验收标准

- [ ] 维修记录 tab 可创建 4 种类型（维修/购买/非更换/整机更换）
- [ ] 表单按 C_TYPE 动态显示/隐藏配件面板
- [ ] 配件更换+收费在一个表单内完成
- [ ] 历史 TIT26 数据在维修记录 tab 正常显示（C_TYPE=3）
- [ ] TIT23 上门记录 tab 不受影响
- [ ] 旧 Accessories/PayList API 保持兼容
