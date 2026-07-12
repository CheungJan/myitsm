---
类型: 技术分析
阅读状态: 未开始
tags: [plantyp, ITSM, 主子表, CRUD, 业务操作, PB对照, 新机开通]
更新日期: 2026-07-10
创建时间: 2026-07-10
---

# ITSM 单据主子表与业务操作现状分析

> 逐 plantyp 梳理：预计划实施确认生成的下游 ITSM 单据 → 涉及表（主表+子表+公用附表）→ 当前 CRUD/状态机/业务操作完整度 → PB 对照 → 缺失与待补齐。

---

## 一、plantyp=00 新机开通（对照基线）

### 1.1 涉及表

| 表 | 模型 | 角色 | 说明 |
|---|------|------|------|
| `tit13_maintenance_open` | `MaintenanceOpen` | **主表** | 新机开通单 |
| `tit14_equipment_open` | `EquipmentOpen` | **子表** | 开通设备明细（一单多设备） |
| `tit23_maintenance_d2d` | `MaintenanceD2D` | 公用附表 | 上门服务记录（跨单据复用） |
| `tit24_maintenance_rv` | `MaintenanceRV` | 公用附表 | 客户回访记录 |
| `tit25_accessories_update` | `AccessoriesUpdate` | 公用附表 | 配件更新记录 |
| `tit26_paylist` | `PayList` | 公用附表 | 收费记录 |
| `tit27_close_bills` | `CloseBills` | 公用附表 | 关单记录 |
| `tit21_maintenance_dispatch` | `MaintenanceDispatch` | 公用附表 | 派工记录 |
| — | — | 关单联动 | — |
| `tmm43_eid` + `tmm43_eid_track` | `Eid` / `EidTrack` | 资产表 | 关单写 type='C'（客户分配） |
| `tmm35_cust_pos_rl` | `CustPosRl` | 客户设备关系 | 关单绑定设备→门店 |
| `twh15_out` + `twh16_outdteid` | `StockOut` / `StockOutDetailEid` | 出库表 | OV=1 销售出库 |

### 1.2 CRUD / 业务操作现状

| 操作 | PB 模块 | 重构现状 | 说明 |
|------|---------|---------|------|
| **列表查询** | `u_itsm_open` 查询窗口 | ✅ 完整 | `GET /maintenance-open` |
| **详情查看** | `u_itsm_open` 详情窗口 | ✅ 完整 | `GET /maintenance-open/<id>`，含 equipments 子表 |
| **创建** | `USP_PLAN_IMPLE` 自动生成 | ✅ 完整 | `implement()` 路由到 `MaintenanceOpenService.create()` |
| **状态流转** | PB 状态机 1→2→3→5→9 | ✅ 完整 | `transition()` 支持 1→2→5/4→3→9 全路径 |
| **编辑** | `u_itsm_open` 修改窗口 | ✅ 完整 | `PUT /maintenance-open/<id>` |
| **派工** | `u_itsm_rep_dispatch` | ✅ 有 API | `POST /dispatch` |
| **上门服务** | `w_r_itsm_d2d` | ✅ 已集成 | `POST /d2d`，`MaintenanceOpenList.vue` 集成 `ItsmSubTables.vue` |
| **客户回访** | `w_r_itsm_rv` | ✅ 已集成 | `POST /rv`，前端已集成 |
| **配件更新** | TIT25 模块 | ✅ 已集成 | `POST /accessories-update`，前端已集成 |
| **收费记录** | TIT26 模块 | ✅ 已集成 | `POST /paylist`，前端已集成 |
| **关单** | `u_itsm_open` 关单按钮 | ✅ 完整 | `transition(to_status='5')`，含 EidTrack + rl + 回写 |
| **关单联动** | `usp_plan_confrim` | ✅ 完整 | type='C' + rl绑定 + plan_status='01' |

### 1.3 PB 状态机 vs 重构状态机

```
PB TIT13 状态：1(新建) → 2(分配) → 3(关闭) → 5(已解决) → 9(作废)
                                     ↑_关单入口（工程师完成服务后关单）

重构版本：    1(新建) → 2(分配) → 5(已解决) → 3(关闭) → 9(作废)
                       ↘ 4(未解决) ↗           ↘ 9(作废)
              state_machine.py:69-88 完整流转已就绪（_do_transition 校验）
```

**后端状态机已完整**（`app/services/state_machine.py`），前端流转按钮待暴露（见 1.4 待补齐清单）。

### 1.4 待补齐清单（plantyp=00 优先级 P0）

| # | 功能 | 涉及文件 | 说明 |
|---|------|---------|------|
| 1 | 开通单编辑（PUT） | `api/itsm.py` + `itsm_service.py` | ✅ 已完成（2026-07-11） |
| 2 | 前端流转按钮暴露中间态 | `MaintenanceOpenList.vue` 等 | ✅ 已完成（2026-07-11），5 种单据详情页均已加入 |
| 3 | 前端开通单详情页集成附表 | `MaintenanceOpenList.vue` | ✅ 已完成（2026-07-11），`ItsmSubTables.vue` 嵌入 5 个页面 |
| 4 | 前端开通单设备明细增删 | `MaintenanceOpenList.vue` | ✅ 已完成（2026-07-11），TIT14 子表增删改后端+前端 |
| 5 | 派工集成 | API + 前端 | ✅ 已有 API，`ItsmSubTables.vue` 展示派工记录；新增派工入口为 P2 增强 |

---

## 二、plantyp=10 磁卡号变更

### 2.1 涉及表

| 表 | 模型 | 角色 |
|---|------|------|
| `tit16_device_change` | `DeviceChange` | **主表** |
| `tmm22_customers_history` | `CustomerHistory` | 磁卡号变更历史（关单写入） |
| `tit23_maintenance_d2d` | `MaintenanceD2D` | 公用附表 |
| `tit24_maintenance_rv` | `MaintenanceRV` | 公用附表 |
| `tit21_maintenance_dispatch` | `MaintenanceDispatch` | 派工 |
| `tit27_close_bills` | `CloseBills` | 关单 |
| — | — | 关单联动 |
| `tmm35_cust_pos_rl` | `CustPosRl` | 设备转移（含设备转移路径） |
| `tmm43_eid_track` | `EidTrack` | type='T'（客户转移） |
| `tmm22_customers` | `Customer` | 客户主表同步 + 源门店无效化 |

### 2.2 CRUD / 业务操作现状

| 操作 | 重构现状 | 说明 |
|------|---------|------|
| 列表/详情 | ✅ | `GET /device-change` |
| 创建 | ✅ | `implement()` 路由创建，`change_type='CK'` |
| 状态流转 | ✅ | 支持全状态机 1→2→5/4→3→9 |
| 编辑 | ✅ | `PUT /device-change/<id>` |
| 派工 | ✅ | `POST /dispatch` |
| 附表操作 | ✅ | D2D/RV/派工/关单 API 就绪，前端 `ItsmSubTables.vue` 已集成 |
| 关单联动 | ✅ | type='T' + rl 转移 + 客户合并 + 回写 |

### 2.3 待补齐

| # | 功能 | 优先级 |
|---|------|--------|
| 1 | 编辑（PUT） | ✅ 已完成（2026-07-11） |
| 2 | 中间态流转 | ✅ 已完成（2026-07-11） |
| 3 | 前端附表集成 | ✅ 已完成（2026-07-11） |
| 4 | 前端新增附表操作入口 | P2 | `ItsmSubTables.vue` 仅展示，新增按钮待补 |

---

## 三、plantyp=20 旧机翻新

### 3.1 涉及表

| 表 | 模型 | 角色 |
|---|------|------|
| `tit15_maintenance_renovate` | `MaintenanceRenovate` | **主表** |
| `tit15_equipment_renovate` | `EquipmentRenovate` | **子表**（旧机→新机映射） |
| `tit23_maintenance_d2d` | `MaintenanceD2D` | 公用附表 |
| `tit24_maintenance_rv` | `MaintenanceRV` | 公用附表 |
| — | — | 关单联动 |
| `tmm43_eid` + `tmm43_eid_track` | `Eid` / `EidTrack` | 旧机 type='R' + 新机 type='C' |
| `tmm35_cust_pos_rl` | `CustPosRl` | 旧机失效 / 新机新建 |
| `twh13_in` | `StockIn` | 旧机回收入库草稿（IV=7） |

### 3.2 待补齐

| # | 功能 | 优先级 |
|---|------|--------|
| 1 | 翻新单编辑 + 子表增删 | ✅ 已完成（2026-07-11） |
| 2 | 中间态流转 | ✅ 已完成（2026-07-11） |
| 3 | 前端附表集成 | ✅ 已完成（2026-07-11） |
| 4 | 前端新增附表操作入口 | P2 | `ItsmSubTables.vue` 仅展示，新增按钮待补 |

---

## 四、plantyp=30 取机回收

### 4.1 涉及表

| 表 | 模型 | 角色 |
|---|------|------|
| `tit20_recycle_task` | `RecycleTask` | **主表**（重构新增，独立于 TIT10） |
| `tit20_recycle_task_dtl` | `RecycleTaskDtl` | **子表**（回收设备明细） |
| — | — | 关单联动 |
| `tmm43_eid_track` | `EidTrack` | type='R'（回收） |
| `tmm35_cust_pos_rl` | `CustPosRl` | 设备关系失效 |
| `twh13_in` | `StockIn` | 回收入库草稿（IV=7） |

### 4.2 待补齐

| # | 功能 | 优先级 |
|---|------|--------|
| 1 | 子表明细的增删 API | ✅ 已完成（2026-07-11） |
| 2 | 前端 RecycleTask 详情页+明细 | ✅ 已完成（2026-07-11） |
| 3 | 派工/分配 | ✅ 已有 API，`ItsmSubTables.vue` 展示；新增入口为 P2 增强 |

---

## 五、plantyp=40 门店关闭

### 5.1 涉及表

| 表 | 模型 | 角色 |
|---|------|------|
| `tit18_store_close` | `StoreClose` | **主表** |
| — | — | 关单联动 |
| `tmm43_eid_track` | `EidTrack` | type='R'（批量回收） |
| `tmm35_cust_pos_rl` | `CustPosRl` | 全部门店设备失效 |
| `tmm22_customers` | `Customer` | s_status + 名称前缀 |
| `twh13_in` | `StockIn` | 回收入库草稿（IV=7） |

### 5.2 待补齐

| # | 功能 | 优先级 |
|---|------|--------|
| 1 | 编辑 | ✅ 已完成（2026-07-11） |
| 2 | 中间态 | ✅ 已完成（2026-07-11） |
| 3 | 前端附表 | ✅ 已完成（2026-07-11） |
| 4 | 前端新增附表操作入口 | P2 | `ItsmSubTables.vue` 仅展示，新增按钮待补 |

---

## 六、公用附表（跨所有 ITSM 单据类型）

| 表 | 前端 API | 当前前端集成状态 |
|---|---------|---------------|
| `tit23_maintenance_d2d` 上门服务 | `POST/GET /d2d` | ✅ 5 个 ITSM 详情页已集成展示 |
| `tit24_maintenance_rv` 客户回访 | `POST/GET /rv` | ✅ 5 个 ITSM 详情页已集成展示 |
| `tit25_accessories_update` 配件更新 | `POST/GET /accessories-update` | ✅ 5 个 ITSM 详情页已集成展示 |
| `tit26_paylist` 收费记录 | `POST/GET /paylist` | ✅ 5 个 ITSM 详情页已集成展示 |
| `tit21_maintenance_dispatch` 派工 | `POST/GET /dispatch` | ✅ 5 个 ITSM 详情页已集成展示 |
| `tit27_close_bills` 关单记录 | `POST/GET /close-bills` | ✅ 5 个 ITSM 详情页已集成展示 |

**共性问题**：6 个公用附表的后端 API 已就绪，前端 5 个 ITSM 详情页已集成 `ItsmSubTables.vue` 展示；**前端新增入口**（新增 D2D/RV/配件/收费/派工/关单）仍待补齐。

---

## 七、各 plantyp 关单联动对比

| plantyp | eid_track type | rl 操作 | 客户主表 | 回写计划 | 入库草稿 | 完成度 |
|---------|---------------|---------|---------|---------|---------|--------|
| `00` 新机开通 | C（客户分配） | 新建绑定 | — | ✅ status='01' | — | ✅ 完整 |
| `10` 磁卡号变更 | T（客户转移） | 旧失效+新激活 | 同步+源无效化 | ✅ | — | ✅ 完整 |
| `20` 旧机翻新 | R（回收）+C（分配） | 旧失效+新新建 | — | ✅ | IV=7 | ✅ 完整 |
| `30` 取机回收 | R（回收） | 失效 | — | ✅ | IV=7 | ✅ 完整 |
| `40` 门店关闭 | R（回收批量） | 全失效 | s_status+前缀 | ✅ | IV=7 | ✅ 完整 |

---

## 八、plantyp=00 新机开通端到端验证路径

以下为当前可走的完整业务链路：

```
1. 前端 销售管理→预计划→新建
   plantyp=00, 填写客户/磁卡号/机型/押金
   → plan_status='00'（计划中）

2. 预计划→计划确认（u_plan_befor_new 等价）
   → plan_status='02'（分派中）
   → 客户 TEMP→PENDING

3. 预计划→实施确认（u_plan_imple 等价）
   → MaintenanceOpenRepository.create() → 生成 MO 开通单
   → plan_status='04'（实施中）
   → 客户 PENDING（等待开通完成）

4. 仓库→销售出库（create_outbound）
   → OV=1 出库草稿 → 审核 → is_outflag='1'

5. ITSM→新机开通→关单（transition to_status='5'）
   → tmm43_eid_track type='C'（客户分配）
   → tmm35_cust_pos_rl 设备绑定门店
   → plan_status='01'（计划完成）
   → 客户 PENDING→ACTIVE
```

**当前缺失环节**：
- 步骤 2 和步骤 3 之间缺少"派工"（分配工程师）
- 步骤 3 和步骤 5 之间缺少"上门服务记录"（D2D）+ "配件更新"
- 步骤 5 之后缺少"客户回访"（RV）

---

## 九、PB vs 重构 ITSM 单据状态机总览

| ITSM 单据 | PB 状态机 | 重构后端状态机 | 前端流转按钮 |
|----------|---------|-------------|------------|
| TIT13 新机开通 | 1→2→3→5→9 | ✅ 完整（`state_machine.py`） | ✅ `MaintenanceOpenList.vue` 已加 |
| TIT16 磁卡号变更 | 1→2→3→5→9 | ✅ 完整 | ✅ `DeviceChangeList.vue` 已加 |
| TIT15 旧机翻新 | 1→2→3→5→9 | ✅ 完整 | ✅ `RenovateList.vue` 已加 |
| TIT18 门店关闭 | 1→2→3→5→9 | ✅ 完整 | ✅ `StoreCloseList.vue` 已加 |
| TIT20 回收任务 | 1→2→3→5→9 | ✅ 完整 | ✅ `RecycleTaskList.vue` 已加 |
| TIT10 日常维护 | 1→2→3→5→9 | ✅ 完整 + 前端就绪 | ✅ |

> 后端 `state_machine.py:69-88` 已定义 `TRANSITIONS`：1→2/9, 2→5/4/9, 4→2/3, 5→3/9。`_do_transition()` 通过 `StateMachine.validate_transition()` 校验。所有 ITSM 单据共享同一状态机。

---

## 十、优先级建议

| 优先级 | 内容 | 说明 |
|--------|------|------|
| **P0** | plantyp=00 新机开通端到端补全 | ✅ 已完成（2026-07-11） |
| **P0** | 开通单编辑 PUT + 前端流转按钮 | ✅ 已完成（2026-07-11），5 种单据均已补齐 |
| **P1** | 所有 ITSM 单据详情页集成公用附表 | ✅ 已完成（2026-07-11），`ItsmSubTables.vue` 嵌入 5 个页面 |
| **P1** | 回收任务明细 DELETE 端点 | ✅ 已完成（2026-07-11） |
| **P2** | plantyp=20/30 子表 CRUD UI | ✅ 已完成（2026-07-11），TIT14/TIT15_EQUIPMENT/TIT20_DTL 增删后端+前端 |
| **P2** | is_outflag 1692 条历史数据回填 | ✅ 已完成（2026-07-11） |
| **P3** | 免费更换代码清理 | ✅ 已完成（2026-07-11），移除 create/transition 端点，保留 GET 查询 |

---

## 十一、变更记录

| 日期 | 变更内容 |
|------|---------|
| 2026-07-10 | 初始版本：逐 plantyp 分析 ITSM 单据→表→CRUD→PB 对照→缺失清单 |
| 2026-07-11 | 刷新：编辑/流转/前端附表/子表增删已实现，更新 CRUD 与待补齐清单 |
