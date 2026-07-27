---
类型: 设计文档
阅读状态: 未开始
tags: [ITSM, UI优化, 五区域布局, 前端重构, PB对照]
更新日期: 2026-07-11
创建时间: 2026-07-11
---

# ITSM 业务单据详情页 UI/UX 优化统一设计方案

> 整合 Windsurf 规划与讨论共识，参考 PB 五区域模式 + 行业 ITSM 设计，统一改造 7 类 ITSM 单据详情页。

---

## 一、前置决策（已定稿）

| # | 决策点 | 方案 | 理由 |
|---|--------|------|------|
| 1 | **布局形式** | **左右分栏**（左侧列表 30% + 右侧详情 70%） | 行业 ITSM 标准 + PB 原生模式，弹窗为过渡方案 |
| 2 | **改造范围** | **P0: 5 个下游单据（MO/MR/BG/RC/GB）→ P2: MD/BY** | 预计划下游最优先 |
| 3 | **通知方式** | **Phase 1: 站内消息表 → Phase 2: 企微/钉钉** | 先不依赖外部服务 |
| 4 | **计费规则** | `asset_owner='01'` → 收费；保修期内 → 免费；其余 → 价格表 | 基于资产属性自动判断 |
| 5 | **历史单据匹配** | **`store_id`** | PB 用门店匹配，物理位置不变 |
| 6 | **资产 API** | **新增 `/customers/<id>/assets`** | 当前只有模型无 API |

---

## 二、现状与问题

当前 7 个 ITSM 详情页均使用 `el-dialog` 单弹窗，仅展示主表摘要 + 操作按钮 + `ItsmSubTables.vue`。

| 缺陷 | 影响 |
|------|------|
| 缺少门店/客户基础信息 | 只显示 `store_id` 编码，PB 实际还展示 `cust_nm`、`address`、`phone`、`contactor`、`comm_mode`（通讯方式）、`zf_type`（支付方式）、`is_contract`（合同标志）、`soft_edition`（软件版本）、`s_status`（门店状态）、`levels`（优先级/客户等级）等 TMM22 字段 |
| 摘要区字段缺失 | 未展示 `request_time`、`expected_completion_time`（考核时间）、`first_time`、`leave_time`、`close_time`、`revisit_time`、`create_time`、`firstor`、`is_old`、`is_success` 等 PB 主表字段 |
| 布局拥挤 | 弹窗内多个区域堆叠，按钮与表格无明确分区 |
| 缺少历史同业务单据 | PB 默认展示本门店历史上同类型所有单据 |
| Tab 结构与 PB 不一致 | 缺失客户信息、设备信息、分配记录等业务 Tab |
| 未利用资产属性 | 收费可基于 `asset_owner` 自动判断，不必依赖固定 Tab |
| 飞信已停用 | 需替换为站内通知/企业通讯 |

---

## 三、目标交互设计

### 3.1 PB 五区域 → 重构适配

| 区域 | 位置 | 内容 |
|------|------|------|
| ① 查询区 | 页面顶部 | 状态、门店、日期、类型筛选栏 |
| ② 列表区 | **左侧 30%** | 任务单据列表，点击行加载右侧详情 |
| ③ 摘要区 | **右上** | 主表关键字段 + 门店/客户信息卡片 |
| ④ Tab 区 | **右下** | 按业务类型区分的 Tab |
| ⑤ 操作区 | 摘要区下方 | 编辑、状态流转、新增子表 |

### 3.2 布局原型

```
┌──────────────────────────────────────────────────────────┐
│ ① 查询栏: [状态▾] [门店▾] [日期范围] [搜索]               │
├──────────────┬───────────────────────────────────────────┤
│ ② 单据列表   │ ③ 摘要卡片                                 │
│ (30%)       │ ┌─────────────────────────────────────┐   │
│              │ │ 🏪 内3 (00011136)  │ 💳 98881234     │   │
│ MO005134 ◀   │ │ 📍 江月路88号      │ 📞 56909730     │   │
│ MO005133     │ │ 🏷️ 新机开通 MO005134 │ 🔴 实施中       │   │
│ MO005132     │ └─────────────────────────────────────┘   │
│              │ ⑤ 操作: [编辑] [分配] [已解决] [关单] [作废]│
│              ├───────────────────────────────────────────┤
│              │ ④ Tab: [客户信息] [服务记录] [回访] [设备]  │
│              │ ┌─────────────────────────────────────┐   │
│              │ │ 客户: 内3 | 磁卡号: 98881234         │   │
│              │ │ 历史开通单:                           │   │
│              │ │ MO005134  2026-07-11  实施中          │   │
│              │ │ MO002243  2019-08-23  已关闭          │   │
│              │ └─────────────────────────────────────┘   │
└──────────────┴───────────────────────────────────────────┘
```

### 3.3 行业对标

| 系统 | 布局模式 | 可借鉴 |
|------|---------|--------|
| ServiceNow | 左列表 + 右详情 + 顶部 Activity Stream | 左右分栏 + 摘要卡片 |
| Jira Service Management | 中列表 + 右详情面板 | Issue 详情右侧滑出 |
| Zammad | 中列表 + 右详情，Tab 切换 | 客户信息默认 Tab + 历史工单 |

**一致模式**：列表与详情共存于同一页面，不依赖弹窗。

---

## 四、各业务类型 Tab 设计

### 4.1 Tab 矩阵

| Tab | MO新机 | BG磁卡变更 | MR翻新 | RC回收 | GB关门 | MD维护 | BY保养 |
|-----|--------|----------|--------|--------|--------|--------|--------|
| **客户信息**(默认) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **服务记录(D2D)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **回访(RV)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **设备资产** | ✅ TIT14 | ❌ | ✅ TIT15 | ✅ TIT20 | ✅ 全部 | ✅ 全部 | ✅ TIT17 |
| **收费** | 自动判断 | ✅ | 自动判断 | ❌ | ❌ | 自动判断 | ❌ |
| **分配记录** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **配件/更换** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **通知记录** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

### 4.2 客户信息 Tab（默认，所有类型共用）

**固定内容**（来源 `TMM22_CUSTOMERS` 与 PB 客户信息界面 `d_itsm_customers_form_levels.srd`）：

- **基础信息**：门店名称 `cust_nm`、编码 `cust_cd`、客户简称 `custanm`、客户条码 `custbrcd`、磁卡号 `cust_card`
- **联系信息**：地址 `address`、邮编 `zipcd`、电话 `phoneno`、传真 `faxno`、联系人 `contactor`
- **财务信息**：税号 `taxno`、开户银行 `banknm`、银行账号 `bankaccno`、押金金额 `yj_money`
- **分类/状态**：客户类别 `classcd`、门店类型 `busityp`、门店状态 `s_status`、环线位置 `location`、划区 `area`、客户等级/优先级 `levels`、POS 数量 `pos_n`
- **通讯/支付/合同**：通讯方式 `comm_mode`、支付方式 `zf_type`、合同标志 `is_contract`
- **软件/系统**：操作系统 `opersystem`、数据库版本 `data_base`、软件版本 `soft_edition`、内核版本 `systemcode`
- **扩展**：客户生命周期状态 `customer_status`、首次开通日期 `opendate`、最近更换日期 `replacedate`、备注 `backup`

**历史同业务单据列表**（按 `store_id` 匹配，`create_time` 倒序）：

| 业务类型 | 查询表 | 筛选字段 |
|----------|--------|---------|
| 新机开通 | `tit13_maintenance_open` | `store_id` |
| 旧机翻新 | `tit15_maintenance_renovate` | `store_id` |
| 磁卡号变更 | `tit16_device_change` | `store_id` |
| 取机回收 | `tit20_recycle_task` | `cust_cd` |
| 门店关闭 | `tit18_store_close` | `store_id` |
| 日常维护 | `tit10_maintenanceday` | `store_id` |
| 日常保养 | `tit17_maintenance` | `store_id` |

### 4.3 设备资产 Tab

**字段**（来自 `tmm35_cust_pos_rl` + `tmm43_eid`）：

| 字段 | 来源 | 说明 |
|------|------|------|
| EID | `tmm43_eid.eid` | 设备唯一标识 |
| 型号 | `tmm43_eid.itemcd` / `item_nm` | 关联 `tmm12_items` |
| 资产归属 | `tmm43_eid.asset_owner` | 01=客户 / 02=公司 |
| 设备状态 | `tmm43_eid.sflg` | S=已销售 / 1=在门店 / 3=待检 |
| 安装日期 | `tmm35_cust_pos_rl.posupddate` | — |
| 来源单据 | `tmm35_cust_pos_rl.maintenanceno` | ITSM 单号 |
| 回收状态 | `tmm43_eid.recycle_status` | — |
| 是否可回收 | `tmm43_eid.recyclable` | Y/N |

### 4.4 收费自动判断逻辑

```python
def should_charge(store_id: str) -> dict:
    """判断门店是否需要收费及收费原因。"""
    assets = db.session.query(CustPosRl).filter(
        CustPosRl.cust_cd == store_id,
        CustPosRl.useflg == "1",
    ).join(Eid, CustPosRl.eid == Eid.eid).all()

    chargeable = []
    for a in assets:
        if a.eid.asset_owner == "01":        # 客户资产
            chargeable.append({"eid": a.eid, "reason": "客户资产"})

    # 保修期内免费（预留，需补充保修到期日字段）
    # if a.eid.warranty_expire and a.eid.warranty_expire > datetime.now():
    #     continue

    return {
        "should_charge": len(chargeable) > 0,
        "chargeable_assets": chargeable,
        "count": len(chargeable),
    }
```

### 4.5 摘要区字段清单（PB 对照）

#### 4.5.1 所有业务类型共用字段

| 字段 | 说明 |
|------|------|
| `request_time` | 请求时间 |
| `expected_completion_time` | 考核时间/预计完成时间 |
| `first_time` | 首次时间 |
| `leave_time` | 离开时间 |
| `close_time` | 关单时间 |
| `revisit_time` | 回访时间 |
| `create_time` | 创建时间 |
| `update_time` | 更新时间 |
| `creator` | 创建人 |
| `updator` | 更新人 |
| `firstor` | 首次操作人 |
| `current_status` | 当前状态 |
| `is_old` | 是否补单 |
| `is_success` | 成功标志 |
| `short_description` | 简述 |
| `detail_description` | 详细描述 |

#### 4.5.2 各业务类型特有字段

| 类型 | 特有字段 |
|------|----------|
| **MO 新机开通** | `new_opening_id`、`company_id`、`store_id`、`requset_paper_id`、`device_id`、`count`、`deliver_no` |
| **MR 旧机翻新** | `renew_id`、`company_id`、`store_id`、`requset_paper_id`、`old_device_id`、`new_device_id`、`count`、`deliver_no`、`is_back` |
| **BG 磁卡号变更** | `device_change_id`、`store_id`、`change_type`、`requset_paper_id`、`device_id`、`new_store_card`、`new_store_id`、`new_contactor`、`new_tel`、`new_address`、`is_store_inside_change` |
| **GB 门店关闭** | `store_close_id`、`store_id`、`close_type`、`requset_paper_id`、`temp_close_date_begin`、`temp_close_date_end` |
| **RC 回收任务** | `recycle_id`、`cust_cd`、`task_status`、`asset_count`、`plan_date`、`actual_date` |
| **MD 日常维护** | `maintenance_id`、`company_id`、`store_id`、`fault_type`、`fault_cd`、`urgency`、`repair_type`、`is_old`、`is_free` |
| **BY 日常保养** | `daily_maintenance_id`、`company_id`、`store_id`、`maintenance_type`、`plan_date`、`finish_date` |

### 4.6 摘要区布局建议

```
┌────────────────────────────────────────────────────────────┐
│  单号：MO005134        状态：实施中      是否补单：否      │
│  门店：内3（00011136）  磁卡号：98881234  客户等级：3      │
│  请求时间：2026-07-11  考核时间：2026-07-12  创建人：OP001 │
│  关单时间：-           回访时间：-         成功标志：-     │
└────────────────────────────────────────────────────────────┘
```

客户卡片与单据摘要分行展示，超出字段可折叠或放入客户信息 Tab。

---

## 五、需要新增的 API

### 5.1 后端

| 端点 | 说明 | 实现位置 |
|------|------|---------|
| `GET /system/customers/<cust_cd>` | 客户完整信息（含 TMM22 全部字段） | `api/system.py` |
| `GET /system/customers/<cust_cd>/assets` | 门店在网资产列表 | `api/system.py` |
| `GET /itsm/<type>?store_id=xxx` | 按门店查历史同业务单据 | `api/itsm.py`（已有 `store_id` 参数） |
| `POST /notifications` | 发送站内通知 | 新模块 |
| `GET /notifications?user_cd=xxx` | 查询通知列表 | 新模块 |

### 5.2 前端 API 函数

```typescript
// master.ts 新增
fetchCustomerDetail(cust_cd: string)
fetchCustomerAssets(cust_cd: string)

// itsm.ts 新增
fetchHistoryByStore(type: string, store_id: string)
```

---

## 六、通用组件设计

### 6.1 `ItsmDetailLayout.vue`（新增）

```
Props:
  - type: 'open' | 'renovate' | 'device-change' | 'recycle' | 'store-close' | 'daily' | 'maintenance'
  - storeId: string
  - recordId: string
  - tabs: TabConfig[]

Slots:
  - summary: 摘要卡片内容
  - tab-{name}: 每个 Tab 的内容
  - actions: 操作按钮
```

### 6.2 `CustomerInfoTab.vue`（新增，替换部分 ItsmSubTables 功能）

```
Props:
  - storeId: string
  - businessType: string
  - currentRecordId: string

功能：
  - 显示客户摘要
  - 加载历史同业务单据列表
  - 点击历史单据可切换右侧详情
```

### 6.3 `ItsmSubTables.vue`（增强）

保留现有 6 个附表 Tab + 新增表单，但不再作为唯一附表容器。改为：
- 服务记录 Tab → 使用 `ItsmSubTables` 的 d2d Tab
- 回访 Tab → 使用 `ItsmSubTables` 的 rv Tab
- 收费 Tab → 内嵌自动判断逻辑 + `ItsmSubTables` 的 pay Tab

---

## 七、实施路线

| 阶段 | 内容 | 文件 | 优先级 |
|------|------|------|--------|
| **P0.1** | 创建 `ItsmDetailLayout.vue` 通用布局组件 | 新文件 | 最高 | ✅ |
| **P0.2** | 新增 3 个后端 API（客户详情/资产/历史单据） | `api/master.py` + `api/itsm.py` | 最高 | ✅ |
| **P0.3** | 改造 `MaintenanceOpenList.vue` 为新布局（样板） | `views/itsm/` | 最高 | ✅ |
| **P0.4** | 改造其余 4 个下游单据（MR/BG/RC/GB） | `views/itsm/` | 高 | ✅ |
| **P1.1** | 增强 `ItsmSubTables.vue`（补齐所有新增表单） | `views/itsm/` | 高 | ✅ |
| **P1.2** | 设备资产 Tab + 收费自动判断 | `views/itsm/` + `services/` | 高 | ✅ |
| **P2.1** | 改造 `MaintenanceList.vue`（MD 日常维护） | `views/itsm/` | 中 | ✅ |
| **P2.2** | 改造 `MaintenanceT17List.vue`（BY 日常保养） | `views/itsm/` | 中 | ✅ |
| **P3.1** | 站内消息通知系统（`tmc51_notifications`） | 新模块 | 中 |
| **P3.2** | 收费规则引擎（保修期 + 资产属性） | `services/` | 中 |
| **P4** | 响应式+交互动画+折叠面板 | `views/itsm/` | 低 |

---

## 八、预期改动文件清单

### 后端（5 个文件）

| 文件 | 改动 |
|------|------|
| `app/api/master.py` | + `GET /customers/<id>/detail` + `GET /customers/<id>/assets` |
| `app/api/itsm.py` | 已有 `store_id` 参数，确认历史查询可用 |
| `app/services/itsm_service.py` | + 收费判断 `should_charge()` |
| `app/models/master.py` | 新增 `Notification` 模型（P3） |
| `app/api/notification.py` | 新增通知模块（P3） |

### 前端（10 个文件）

| 文件 | 改动 |
|------|------|
| `views/itsm/ItsmDetailLayout.vue` | **新增** 通用布局组件 |
| `views/itsm/CustomerInfoTab.vue` | **新增** 客户信息 + 历史单据 |
| `views/itsm/ItsmSubTables.vue` | 增强：补齐所有新增表单 |
| `views/itsm/MaintenanceOpenList.vue` | 重写为五区域布局 |
| `views/itsm/RenovateList.vue` | 重写 |
| `views/itsm/DeviceChangeList.vue` | 重写 |
| `views/itsm/RecycleTaskList.vue` | 重写 |
| `views/itsm/StoreCloseList.vue` | 重写 |
| `views/itsm/MaintenanceList.vue` | 重写（P2） |
| `views/itsm/MaintenanceT17List.vue` | 重写（P2） |
| `api/itsm.ts` | + 历史单据 API |
| `api/master.ts` | + 客户详情/资产 API |

---

## 九、记录

- 创建时间：2026-07-11
- 合并来源：Windsurf `itsm-detail-ui-optimization-ecd184.md` + 讨论共识
- 作者：AI Assistant
