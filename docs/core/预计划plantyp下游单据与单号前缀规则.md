---
类型: 技术参考
阅读状态: 未开始
tags: [plantyp, 预计划, ITSM, 下游单据, 单号前缀, IdMaster, 系统字典]
更新日期: 2026-07-10
创建时间: 2026-07-10
---

# 预计划 plantyp 下游单据与单号前缀规则

> 本文档是 plantyp 五种计划类型的**权威参考**，涵盖：系统字典定义、实施确认后生成的下游 ITSM 单据、单号前缀规则、PB 原版对照、以及 2026-07-10 完成的命名单号统一修正。

---

## 一、plantyp 计划类型定义

### 1.1 权威来源

系统字典 `tmm31_syscodes`（`code_typ='PL'`）为唯一权威来源。前端通过 `useDict('PL')` 动态读取，后端 `sales_service.py` 硬编码了 5 个 plantyp 路由。

| plantyp | 系统字典名称 | 业务含义 |
|---------|------------|---------|
| `00` | 新机开通 | 新门店/新客户首次安装 POS 设备 |
| `10` | 磁卡号变更 | 已有关店客户变更磁卡号，可含设备转移 |
| `20` | 旧机翻新 | 门店旧设备回收并更换新设备 |
| `30` | 取机回收 | 从门店取回设备（不再使用） |
| `40` | 门店关闭 | 门店停业，回收所有设备 |

### 1.2 历史名称对照

| plantyp | 旧名称（已废弃） | 新名称（当前） | 修正时间 |
|---------|----------------|--------------|---------|
| `00` | 全新开通 | 新机开通 | 2026-07-10 |
| `10` | 设备变更 | **磁卡号变更** | 2026-07-10 |
| `30` | 设备取回 | **取机回收** | 2026-07-10 |
| `40` | 门店关门 | **门店关闭** | 2026-07-10 |

> **注意**：`plantyp=10` 的 PB 模块名 `u_itsm_device_change` 和数据库表名 `tit16_device_change` 仍保留 "device_change" 字样（历史原因），但业务名称统一为"磁卡号变更"。

---

## 二、实施确认 → 下游单据路由

### 2.1 路由表

入口：`app/services/sales_service.py:622` `PlanCustService.implement()`

```python
_PLANTYP_SERVICE_MAP: dict[str, tuple[str, str]] = {
    "00": ("MaintenanceOpenService",    "new_opening_id"),    # 新机开通 → TIT13
    "10": ("DeviceChangeService",       "device_change_id"),  # 磁卡号变更 → TIT16
    "20": ("MaintenanceRenovateService","renew_id"),          # 旧机翻新 → TIT15
    "30": ("RecycleTaskService",        "recycle_id"),        # 取机回收 → TIT20
    "40": ("StoreCloseService",         "store_close_id"),    # 门店关闭 → TIT18
}
```

### 2.2 各类型详表

| plantyp | 下游 Service | Repository | 数据库表 | 主键字段 | 初始状态 |
|---------|-------------|------------|---------|---------|---------|
| `00` | `MaintenanceOpenService` | `MaintenanceOpenRepository` | `tit13_maintenance_open` | `new_opening_id` | `current_status=1` |
| `10` | `DeviceChangeService` | `DeviceChangeRepository` | `tit16_device_change` | `device_change_id` | `current_status=1`, `change_type='CK'` |
| `20` | `MaintenanceRenovateService` | `MaintenanceRenovateRepository` | `tit15_maintenance_renovate` | `renew_id` | `current_status=1` |
| `30` | `RecycleTaskService` | `RecycleTaskRepository` | `tit20_recycle_task` | `recycle_id` | `task_status=1` |
| `40` | `StoreCloseService` | `StoreCloseRepository` | `tit18_store_close` | `store_close_id` | `current_status=1` |

### 2.3 实施确认的附加动作

`implement()` 在创建下游单据之外，还执行：

1. **幂等防重**：`imple_billid` 非空则拒绝
2. **前置校验**：`imple_date` 非空、实施请求呼出（servetyp=2）全部完成
3. **押金联动**：写入 `Deposit` + `DepositDetail`
4. **状态流转**：`plan_status` 02 → 04（实施中）
5. **方案 A 自动出库**：商用仓库来源 + posid 已选 → 自动创建 OV=1 销售出库草稿
6. **客户推进**：TEMP → PENDING

---

## 三、单号前缀规则

### 3.1 生成机制

所有下游单据通过统一流水线生成：

```
_gen_itsm_id(id_type, name, model_cls, pk_field)    # itsm_repository.py:50
  └─ 查 tmm34_idmaster 表是否有该 id_type 记录
     ├─ 有 → current_no + step (step=1)
     └─ 无 → 从业务表 MAX(主键) 提取当前最大序号 → 初始化 IdMaster
        └─ _gen_master_id(prefix, name, init_current_no)  # procurement_repository.py:50
           └─ 返回 f"{prefix}{next_no:06d}"[:8]
```

**格式**：`前缀（2位字母）+ 6位自增数字`，总长不超过 8 位。

### 3.2 各类型单号前缀

| plantyp | `id_type` | **前缀** | 单号格式 | IdMaster 当前序号 | 下一张单号 |
|---------|-----------|---------|---------|------------------|----------|
| `00` | `MO` | **MO** | `MO000001` | 5133 | MO005134 |
| `10` | `BG` | **BG** | `BG000001` | 699 | BG000700 |
| `20` | `MR` | **MR** | `MR000001` | 3935 | MR003936 |
| `30` | `RC` | **RC** | `RC000001` | 0（新号段） | RC000001 |
| `40` | `GB` | **GB** | `GB000001` | 1 | GB000002 |

### 3.3 PB 原版对照

| plantyp | PB 前缀 | PB 来源 | 重构前缀 | 差异说明 |
|---------|--------|---------|---------|---------|
| `00` | MO | `UF_GET_BILLNOU('MO')` | MO | ✅ 一致 |
| `10` | **BG** | `UF_GET_BILLNOU('BG')` | BG | ✅ 一致（2026-07-10 从 MC 修正为 BG） |
| `20` | MR | `UF_GET_BILLNOU('MR')` | MR | ✅ 一致 |
| `30` | MD（走 TIT10） | `UF_GET_BILLNOU('MD')` | **RC**（独立 TIT20） | ⚠️ 刻意重构：从日常维护单剥离为独立表+独立号段 |
| `40` | **GB** | `UF_GET_BILLNOU('GB')` | GB | ✅ 一致（2026-07-10 从 ST 修正为 GB） |

### 3.4 plantyp=30 取机回收的独立化说明

PB 原版中，取机回收混在 `tit10_maintenanceday`（日常维护单）中，使用 `MD` 前缀 + `source_type='RECYCLE'` 标记区分。重构版本（优化 4.2）将其独立为 `tit20_recycle_task` 表 + `RC` 前缀。

选择 `RC`（而非 `RT`）的原因：`RT` 在 IdMaster 中已被"采购退货单号"占用（current_no=13）。

---

## 四、plantyp=10 磁卡号变更的特殊说明

### 4.1 变更类型统一为 CK

重构版本对齐 PB `USP_PLAN_IMPLE` 硬编码，`_build_downstream_payload`（`sales_service.py:249`）始终传 `change_type='CK'`。三种 `CHANGE_TYPE` 的语义与来源见 §3.1。

`device_id` 取值规则（`sales_service.py:250`）：
- 优先 `new_posid`（换设备场景）
- 为空则回退 `posid`（不换设备，源磁卡号设备转移到新磁卡号下）
- 都为空则 `None`（纯磁卡号变更，无设备）

### 4.2 关单时的两条处理路径

关单时不依赖 `CHANGE_TYPE` 字段值，而是按 `device_id + new_store_id` 是否非空隐式区分：

| 路径 | 触发条件 | 处理逻辑 | 对齐 PB |
|------|---------|---------|---------|
| **纯磁卡号变更** | `device_id` 为空 **或** `new_store_id` 为空 | `_sync_customer_and_history`：同步客户主表（custcard/custnm/address/phoneno）+ 写 `TMM22_CUSTOMERS_HISTORY` + 回写 `plan_status='01'` | `USP_PLAN_CONFRIM` V_NEW_POSID 为空分支 |
| **含设备转移** | `device_id` 非空 **且** `new_store_id` 非空 | 在上述基础上追加：`_write_eid_track_on_close_bg`（type='T'）+ `_transfer_rl_on_close_bg`（旧 rl 失效/新 rl 新建，`maintenancetyp='BG'`）+ 目标客户 `useflg='0'` 合并；设备 `sflg` 保持原值不变 | `USP_PLAN_CONFRIM` V_NEW_POSID 非空分支 |

**设备 `sflg` 处理**：磁卡号变更设备从旧客户转到新客户，物理位置不动，不经过仓库，`sflg` 保持原值不变（对齐 PB `USP_PLAN_CONFRIM` 不更新 `tmm43_eid.sflg`）。

### 4.3 老数据兼容

OP 前缀老数据（`CHANGE_TYPE='BG'/'BQ'`）仍可在关单时走 `_sync_customer_and_history`（兼容条件 `change_type in ("CK","BG","BQ")`），但不触发设备转移逻辑。

> 完整 PB 流程分析见 `docs/core/PB预计划plantyp10磁卡号变更业务流程分析.md`

---

## 五、系统字典维护

### 5.1 PL 字典（`tmm31_syscodes`，`code_typ='PL'`）

```sql
SELECT code_cd, code_nm FROM tmm31_syscodes WHERE code_typ = 'PL' ORDER BY code_cd;
```

| code_cd | code_nm | useflg |
|---------|---------|--------|
| 00 | 新机开通 | 1 |
| 10 | 磁卡号变更 | 1 |
| 20 | 旧机翻新 | 1 |
| 30 | 取机回收 | 1 |
| 40 | 门店关闭 | 1 |

### 5.2 IdMaster 号段（`tmm34_idmaster`）

与 plantyp 相关的号段记录：

```sql
SELECT id_type, prefix, current_no, idtypnm FROM tmm34_idmaster
WHERE id_type IN ('MO','BG','MR','RC','GB') ORDER BY id_type;
```

| id_type | prefix | name |
|---------|--------|------|
| BG | BG | 磁卡号变更单号 |
| GB | GB | 门店关闭单号 |
| MO | MO | 新机开通单号 |
| MR | MR | 旧机翻新单号 |
| RC | RC | 取机回收任务单号 |

> `RC` 号段在首次创建取机回收任务时自动初始化（从 `tit20_recycle_task` 表 `MAX(recycle_id)` 提取初始值，空表则从 0 开始）。

---

## 六、代码位置速查

| 功能 | 文件 | 行号 |
|------|------|------|
| plantyp 路由表 | `app/services/sales_service.py` | 184-190 |
| 实施确认入口 | `app/services/sales_service.py` | 622-769 |
| 下游 payload 构造 | `app/services/sales_service.py` | 226-276 |
| 单号生成 `_gen_itsm_id` | `app/repositories/itsm_repository.py` | 50-71 |
| 单号生成 `_gen_master_id` | `app/repositories/procurement_repository.py` | 50-76 |
| MO 前缀（新机开通） | `app/repositories/itsm_repository.py` | 181 |
| BG 前缀（磁卡号变更） | `app/repositories/itsm_repository.py` | 286 |
| MR 前缀（旧机翻新） | `app/repositories/itsm_repository.py` | 232 |
| RC 前缀（取机回收） | `app/repositories/itsm_repository.py` | 530 |
| GB 前缀（门店关闭） | `app/repositories/itsm_repository.py` | 344 |
| PlanCust 模型 plantyp 字段 | `app/models/sales.py` | 28 |
| DeviceChange 模型 | `app/models/itsm.py` | 456-491 |
| RecycleTask 模型 | `app/models/itsm.py` | 881-913 |
| StoreClose 模型 | `app/models/itsm.py` | 591-618 |
| PL 系统字典 | `app/models/master.py` | 364-379 |
| IdMaster 模型 | `app/models/master.py` | 382-397 |

---

## 七、完整 IdMaster 号段清单（参考）

以下是数据库中所有 ITSM 相关号段，供新增单据类型时参考避免冲突：

| id_type | prefix | name | 当前序号 |
|---------|--------|------|---------|
| BG | BG | 磁卡号变更单号 | 699 |
| BY | BY | 日常保养单ID | 21600 |
| FR(PB历史老版本使用) | FR | 免费更换单号 | — |
| GB | GB | 门店关闭单号 | 1 |
| GH(PB历史老版本遗留数据) | GH | 免费更换单号 | 1829 |
| MD | MD | 日常维护单 | 65453 |
| MO | MO | 新机开通单 | 5133 |
| MR | MR | 旧机翻新单 | 3935 |
| OP(PB历史老版本使用) | OP | 开通单号 | 2069 |
| RC | RC | 取机回收任务单号 | 0 |

> 完整清单见 `tmm34_idmaster` 表。

---

## 八、变更记录

| 日期 | 变更内容 |
|------|---------|
| 2026-07-10 | 初始版本：统一 plantyp 命名、修正单号前缀（MC→BG, ST→GB, R→RC）、更新系统字典 PL、修正 16 个文档文件中的名称引用 |
