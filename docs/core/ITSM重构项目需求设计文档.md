# ITSM 重构项目需求设计文档

**文档版本**: v1.1  
**创建时间**: 2026-04-27  
**更新时间**: 2026-04-27（新增双库合并方案）  
**目标**: 将 PowerBuilder ITSM 系统重构为 Python + Flask + PostgreSQL 技术栈  
**状态**: 待确认

---

## 一、源码分析概览

### 1.1 代码规模统计

| 指标 | 数值 |
|------|------|
| PB 模块（.pbl 文件夹） | **25 个** |
| 源文件总数 | **1,205 个** |
| 总代码量 | **~18,051K 字符** |
| SQL 操作总数 | **4,049 条** |
| 文件类型 | .sru（UserObject）、.srd（DataWindow）、.srw（Window）、.srs（Structure） |

### 1.2 模块代码量排行（Top 10）

| 排名 | 模块 | 文件数 | 代码量 | SQL数 | 业务域 |
|------|------|--------|--------|-------|--------|
| 1 | itsm.pbl | 116 | 2,267K | 512 | **ITSM 核心**（维修/开通/翻新/归档） |
| 2 | wh.pbl | 98 | 1,718K | 548 | **仓储管理**（出入库/盘点） |
| 3 | itsm02.pbl | 94 | 1,710K | 358 | **ITSM 扩展**（设备变更/门店关闭/保养/免费更换） |
| 4 | sale.pbl | 82 | 1,692K | 514 | **销售/预计划**（预计划/实施/服务计划） |
| 5 | lsgldata.pbl | 107 | 1,671K | 383 | **历史数据管理**（零售/合同/固定资产） |
| 6 | new_deposit.pbl | 89 | 1,421K | 294 | **押金管理/新版预计划** |
| 7 | report.pbl | 60 | 1,219K | 353 | **报表**（库存/客户/BOM） |
| 8 | base_cust.pbl | 76 | 887K | 172 | **主数据**（客户/物料/BOM/供应商） |
| 9 | trans.pbl | 35 | 674K | 101 | **调拨流转** |
| 10 | purchase.pbl | 35 | 508K | 113 | **采购管理** |

### 1.3 全部模块职能概览

| 模块 | 文件数 | 职能描述 |
|------|--------|---------|
| **app_main.pbl** | 12 | 应用主框架（菜单导航、已开模块管理、桌面面板） |
| **app_system.pbl** | 21 | 系统管理（用户/角色/组/权限/区域/仓库/菜单） |
| **app_objects.pbl** | 13 | 公共控件基类（按钮、下拉框、数据选择器） |
| **app_d.pbl** | 42 | 系统级 DataWindow（用户、区域、仓库等表单/列表） |
| **app_dddw.pbl** | 52 | 下拉数据窗口（各类编码、客户、物料等下拉选项） |
| **base_objects.pbl** | 45 | 框架基础控件（dw、tab、tree、textbox 等39个控件） |
| **base_attrib.pbl** | 17 | 属性定义类（颜色、登录、编辑、页面等16个NVO） |
| **base_srv.pbl** | 41 | 基础服务（应用管理、文件操作、字符串、日期等工具类） |
| **base_dwsrv.pbl** | 14 | DataWindow 服务（排序、查找、下拉搜索、必填列等） |
| **base_cust.pbl** | 76 | 主数据管理（客户/门店、物料/商品、BOM、供应商） |
| **itsm.pbl** | 116 | **ITSM核心**（新机开通、旧机翻新、日常维护、回收入库、归档、报表） |
| **itsm02.pbl** | 94 | **ITSM扩展**（设备变更、门店关闭、保养、免费更换、考核、派工报表） |
| **sale.pbl** | 82 | 销售域（预计划管理、实施计划、服务计划、话务台、销售单据） |
| **purchase.pbl** | 35 | 采购管理（采购计划、采购登记审批） |
| **wh.pbl** | 98 | 仓储管理（10+种入库、10+种出库、资产盘点） |
| **wh_syc.pbl** | 30 | 仓储辅助（溢余/盘亏处理、辅助出入库） |
| **trans.pbl** | 35 | 调拨流转（调入/调出管理、异常处理） |
| **lsgldata.pbl** | 107 | 零售管理数据（门店经营数据/日经营/收入产出/合同/固定资产） |
| **new_deposit.pbl** | 89 | 押金管理（押金确认/报表）与新版预计划、资产报表 |
| **report.pbl** | 60 | 综合报表（库存、客户信息、BOM变更、设备追踪） |
| **price.pbl** | 18 | 价格管理（商品定价、标签打印、POS状态） |
| **qc.pbl** | 24 | 质检管理（质检结果录入/审核/报表） |
| **appraisal.pbl** | 17 | 供应商考核（考核管理/审批/信息维护） |
| **kq.pbl** | 29 | 考勤/打印（考勤导入、外勤巡线报表、打印控件） |
| **dw2xls.pbl** | 38 | Excel 导出工具库 |

---

## 二、核心业务流程分析

### 2.1 预计划管理流程（sale.pbl）

预计划是整个 ITSM 系统的业务起点，驱动后续所有维护单据的创建。

**计划类型编码（plantyp）**：

| 类型码 | 含义 | 关联单据表 | 当前实现 |
|--------|------|-----------|---------|
| 00 | 新机开通 | TIT13_MAINTENANCE_OPEN | 正常 |
| 10 | 设备变更 | TIT16_DEVICE_CHANGE | 正常 |
| 20 | 旧机翻新 | TIT15_MAINTENANCE_RENOVATE | 正常 |
| **30** | **取机** | **TIT10_MAINTENANCEDAY** | **⚠️ 问题：借用日常维护单** |
| 40 | 关门 | —（已注释） | **⚠️ 功能未实现** |

**当前流程**：
```
预计划创建 (PLAN_CUST)
  ├── 分配计划类型 (plantyp)
  ├── 关联客户 (CUSTCD)
  ├── 提交 → 生成对应维护单据
  ├── 作废 → 级联取消关联单据 (CURRENT_STATUS='9')
  └── 完成 → 执行实施确认
```

**作废逻辑（源码 u_plan_befor.sru L605-663）**：预计划作废时按 plantyp 查找并取消对应维护单，逻辑硬编码且没有事务包裹。

### 2.2 ITSM 维修单业务流程（itsm.pbl + itsm02.pbl）

**单据类型总览**：

| 类型码 | 单据名称 | 主表 | 主键 | 核心对象 |
|--------|---------|------|------|---------|
| MD | 日常维护单 | TIT10_MAINTENANCEDAY | MAINTENANCE_ID | u_itsm_rcwh_h（3,174行） |
| MO | 新机开通单 | TIT13_MAINTENANCE_OPEN | NEW_OPENING_ID | u_itsm_open（42,483字符） |
| MR | 旧机翻新单 | TIT15_MAINTENANCE_RENOVATE | RENEW_ID | u_itsm_renovate（43,045字符） |
| BY | 保养维护单 | TIT17_MAINTENANCE | DAILY_MAINTENANCE_ID | u_itsm_maintenance_daily |
| BG | 设备变更单 | TIT16_DEVICE_CHANGE | DEVICE_CHANGE_ID | u_itsm_device_change |
| GB | 门店关闭 | TIT18_STORE_CLOSE | — | u_itsm_store_close |

**统一状态流转**（CURRENT_STATUS 字段）：

| 状态值 | 含义 | 可流转到 |
|--------|------|---------|
| 0/00 | 草稿/新建 | 1, 9 |
| 1/01 | 已派工/待处理 | 3, 9 |
| 3/05 | 已完成 | — |
| 9/09 | 已取消/作废 | — |

**公用附表**：

| 表名 | 用途 | 复用单据 |
|------|------|---------|
| TIT23_MAINTENANCE_D2D | 上门服务记录（到店/离店/催单） | MD, MO, MR, BY, BG |
| TIT24_MAINTENANCE_RV | 客户回访记录 | MD, BY |
| TIT25_ACCESSORIES_UPDATE | 配件更新记录 | MD |
| TIT21_MAINTENANCE_DISPATCH | 派工记录 | 所有单据 |
| TIT27_CLOSE_BILLS | 关单记录 | MD, BY |
| TIT10_MAIN_TRACK | 状态变更轨迹 | MD |

### 2.3 仓储管理流程（wh.pbl）

**出入库类型（20个 UserObject，代码高度重复）**：

| 分类 | 业务对象 | 行数 | 说明 |
|------|---------|------|------|
| **入库** | u_wh_pcin | 956 | 采购入库 |
| | u_wh_salein | 948 | 销售退货入库 |
| | u_wh_servicein | 965 | 服务返还入库 |
| | u_wh_allocatein | 965 | 调拨入库 |
| | u_wh_lendin | 970 | 借出归还入库 |
| | u_wh_scin | 952 | 生产入库 |
| | u_wh_qcin | 956 | 质检入库 |
| | u_wh_sct | 948 | 库存调整 |
| **出库** | u_wh_pcout | 980 | 采购退货出库 |
| | u_wh_saleout | 982 | 销售出库 |
| | u_wh_serviceout | 992 | 服务领用出库 |
| | u_wh_allocateout | 995 | 调拨出库 |
| | u_wh_lendout | 987 | 借出出库 |
| | u_wh_scout | 982 | 生产出库 |
| | u_wh_qcout | 984 | 质检出库 |
| | u_wh_out | 978 | 通用出库 |
| | u_wh_salecl | 956 | 销售冲销 |

> **⚠️ 关键问题**：出库类 u_wh_pcout 和 u_wh_saleout **代码相似度高达 79.8%**。所有出入库对象结构完全一致（16-17 个事件处理器），仅在业务类型码和个别 SQL 条件上有差异。

### 2.4 客户主数据管理（base_cust.pbl）

**核心表**：
- **TMM22_CUSTOMERS**：客户/门店主表（被 17 个模块引用，是系统最核心的主数据表）
- **TMM35_CUST_POS_RL**：门店设备关联表（被 9 个模块引用）
- **TMM12_ITEMS**：物料/商品主表（被 15 个模块引用）
- **TMM19_SUPPLIERS**：供应商主表
- **TMM41_BOM/TMM42_BOMDT**：BOM 清单

### 2.5 采购管理（purchase.pbl）

**核心流程**：采购计划 → 采购登记 → 审批
- u_pc_plan：采购计划管理（1,019 行，10 条 SQL）
- u_pc_register_examine：采购登记审批（1,254 行）

### 2.6 调拨流转（trans.pbl）

- u_trans_in：调入管理（764 行，17 条 SQL — SQL 密度最高）
- u_trans_out：调出管理（620 行，16 条 SQL）

### 2.7 双数据库架构分析（CCGLPDB + LGREPORTPDB）

原系统采用 **两个 Oracle 数据库**，通过 DB Link 实现跨库访问：

| 数据库 | 用途 | 核心表 |
|--------|------|--------|
| **CCGLPDB**（主库） | ITSM 业务主库，承载客户、物料、维护单、仓储等全部核心业务表 | TIT*、TMM*、TWH*、PLAN_* 等 |
| **LGREPORTPDB**（零售库） | 零售经营数据管理，承载门店日经营数据、收入产出、合同等 | T_D_*、经营数据表 |

**跨库访问方式**：LGREPORTPDB 中的代码通过 Oracle DB Link `@CCGL_23`、`@CCGL_24` 访问 CCGLPDB 中的主数据表。

#### 跨库引用统计

| 引用方式 | 涉及文件数 | 说明 |
|---------|-----------|------|
| `@CCGL_23` DB Link | **19 个文件** | LGREPORTPDB → CCGLPDB 跨库查询（集中在 lsgldata.pbl 和 report.pbl） |
| `@CCGL_24` DB Link | **1 个文件** | 跨库更新客户 USEFLG（report.pbl/u_mm_cust_useflg_modify.sru） |
| `CCGLLSGL` 连接名 | **24 个文件** | PB 代码中建立第二数据库连接（itrans.ServerName = "ccgllsgl"） |
| `USP_*` 存储过程 | **100 个文件** | CCGLPDB 中的存储过程（入库/出库/状态变更等） |

#### 通过 @CCGL_23 跨库访问的 CCGLPDB 表

| 被跨库访问的表 | 说明 | 引用模块 |
|--------------|------|----------|
| TMM22_CUSTOMERS | 客户/门店主表 | lsgldata.pbl, report.pbl |
| TMM35_CUST_POS_RL | 门店设备关联 | lsgldata.pbl, report.pbl |
| TMM31_SYSCODES | 系统编码 | lsgldata.pbl |
| TMM21_CUSTCLASS | 客户分类 | lsgldata.pbl |
| TMM46_AREA | 区域表 | lsgldata.pbl |
| TMM47_COMMODE | 通讯方式 | lsgldata.pbl |

#### 跨库访问的典型场景

1. **零售数据报表关联客户信息**：lsgldata.pbl 中的报表需要关联 CCGLPDB 的客户表获取门店名称、设备信息等
   ```sql
   -- 示例：门店经营数据查询关联客户主数据
   FROM tmm35_cust_pos_rl@ccgl_23 t, tmm22_customers@ccgl_23 c
   WHERE t.custcd = c.custcd
   ```
2. **客户信息同步**：report.pbl 中通过 `@CCGL_24` 跨库更新客户使用标志
   ```sql
   update tmm22_customers@ccgl_24 b set b.useflg = '0' where b.custcd in(...)
   ```
3. **lsgldata 模块双连接模式**：16+ 个业务对象通过 `itrans.ServerName = "ccgllsgl"` 建立到 LGREPORTPDB 的第二连接，同时访问本地（CCGLPDB）和远程（LGREPORTPDB）数据

#### 核心存储过程（CCGLPDB）

| 存储过程 | 用途 | 引用文件数 |
|---------|------|----------|
| USP_WH_IN | 入库核心逻辑（更新库存） | 多处 |
| USP_WH_OUT | 出库核心逻辑（扣减库存） | 多处 |
| USP_CREATE_PCPLAN | 创建采购计划 | n_tr.sru |
| USP_PLANSTATUS | 更新计划状态 | n_tr.sru |
| USP_QCSTATUS | 质检状态更新 | n_tr.sru |

---

## 三、源码问题与优化点清单

### 3.1 P0级问题（必须解决）

#### 问题1：取机业务使用日常维护单据（⚠️ 严重）

- **位置**：`sale.pbl/u_plan_befor.sru` L647, `itsm.pbl/u_itsm_rcwh_h.sru`
- **现象**：预计划类型 `plantyp='30'`（取机）创建的是 `TIT10_MAINTENANCEDAY`（日常维护单），而非专用的取机/回收业务单据
- **影响**：
  - 取机业务与日常维护维修混在一起，无法独立统计和管理
  - 回收入库逻辑（u_itsm_rcwh_h，3,174 行代码）混在日常维护流程中，代码臃肿
  - 无法追踪旧机回收的完整生命周期（回收 → 入库 → 翻新/报废）
- **优化方案**：
  - 新建独立的取机/回收任务表 `TIT20_RECYCLE_TASK` 及明细表 `TIT20_RECYCLE_TASK_DTL`
  - 预计划 plantyp='30' 时创建回收任务而非日常维护单
  - 回收任务有独立的状态机（待分配 → 已分配 → 回收中 → 已完成）

#### 问题2：资产属性缺失（⚠️ 严重）

- **位置**：`base_cust.pbl` TMM35_CUST_POS_RL
- **现象**：门店设备关联表 TMM35_CUST_POS_RL 缺少资产类型（新机/旧机/翻新机/报废）、可回收标志、回收状态等关键字段
- **影响**：
  - 无法判断设备是否可回收
  - 无法追踪设备的生命周期（新机 → 在用 → 旧机 → 翻新/报废）
  - 预计划关门/翻新时无法自动识别需回收的设备
- **优化方案**：
  - 扩展 TMM35_CUST_POS_RL 增加：ASSET_TYPE（资产类型）、RECYCLABLE_FLAG（可回收标志）、RECYCLE_STATUS（回收状态）、ASSET_STATUS（资产状态）、CREATED_FROM（来源）、SOURCE_ID（来源单号）、WARRANTY_EXPIRE（保修到期日）

#### 问题3：预计划客户生命周期失控（⚠️ 严重）

- **位置**：`sale.pbl/u_plan_befor.sru`, `base_cust.pbl/u_mm_customer.sru`
- **现象**：预计划新建客户直接写入 TMM22_CUSTOMERS，预计划取消后客户记录成为"幽灵数据"，无状态标记
- **影响**：客户表存在大量无效临时数据，查询效率和数据质量下降
- **优化方案**：
  - TMM22_CUSTOMERS 增加 CustomerStatus（TEMP/PENDING/ACTIVE/INVALID）、SourceType（PREPLAN/MANUAL/IMPORT）、PreplanId 等字段
  - 实现客户生命周期状态机（临时 → 待确认 → 正式/失效）

#### 问题4：磁卡号变更直接删除历史记录（⚠️ 严重）

- **位置**：`itsm02.pbl/u_itsm_device_change.sru`
- **现象**：设备变更 CHANGE_TYPE='CK'（改磁卡号）时，直接删除/覆盖旧磁卡号记录，导致历史数据丢失
- **影响**：无法追溯磁卡号变更历史，审计追溯困难，报表数据缺失
- **优化方案**：
  - 新建 TMM22_CUSTOMERS_HISTORY 表，变更前自动保存旧磁卡号信息
  - 变更流程改为"先存历史 → 再更新主表"

### 3.2 P1级问题（重要优化）

#### 问题5：仓储出入库代码严重重复

- **位置**：`wh.pbl` 20 个 UserObject
- **现象**：所有出入库类型各有独立对象，结构完全一致（16-17 个事件处理器），出库类相似度达 79.8%
- **代码量**：20 个文件共 ~500K 字符，仅业务类型码和少量条件不同
- **优化方案**：
  - 统一为 StockMovement（库存移动）模型，通过 movement_type 区分业务类型
  - 入库/出库各用一个通用服务，按类型参数化差异逻辑
  - 预计从 20 个对象精简为 **2 个核心服务 + 1 个类型枚举**

#### 问题6：ITSM 状态机逻辑硬编码分散

- **位置**：`itsm.pbl` 多个 u_itsm_*.sru
- **现象**：状态流转（CURRENT_STATUS 字段）逻辑分散在 u_itsm_open、u_itsm_renovate、u_itsm_rcwh_h 等多个对象中，每个对象独立硬编码状态判断和流转
- **代码量**：仅状态相关代码在 itsm.pbl 中出现 **50+ 处**引用
- **优化方案**：
  - 实现统一 StateMachine 类，集中管理状态定义和流转规则
  - 所有单据类型共享状态机，支持事件驱动（派工/完工/取消等事件触发状态变更+日志记录）

#### 问题7：预计划作废缺少事务保护

- **位置**：`sale.pbl/u_plan_befor.sru` L605-663
- **现象**：作废时依次查找并更新各类型单据，每个 UPDATE 独立执行，没有事务包裹
- **影响**：如果中间某条 UPDATE 失败，会导致部分单据被取消、部分未取消的不一致状态
- **优化方案**：Python 重构时在 Service 层统一事务管理

#### 问题8：客户全生命周期追踪缺失

- **现象**：无法追溯客户从预计划 → 实施 → 维护 → 回收的完整链路
- **优化方案**：建立客户生命周期追踪服务，关联 PLAN_CUST → 维护单 → 回收任务

#### 问题9：关门功能未实现

- **位置**：`sale.pbl/u_plan_befor.sru` L659（已注释代码）
- **现象**：plantyp='40'（关门）的处理逻辑被注释，TIT18_STORE_CLOSE 表存在但流程不完整
- **优化方案**：重构时实现完整的门店关闭流程

#### 问题10：双数据库架构增加复杂度（⚠️ 重要）

- **位置**：lsgldata.pbl（16+ 文件）、report.pbl（6+ 文件）
- **现象**：原系统使用 CCGLPDB（业务主库）和 LGREPORTPDB（零售库）两个数据库，通过 Oracle DB Link `@CCGL_23`/`@CCGL_24` 跨库查询/更新，PB 代码中通过 `itrans.ServerName = "ccgllsgl"` 建立第二数据库连接
- **影响**：
  - 19 个文件使用 `@CCGL_23` 跨库查询，1 个文件使用 `@CCGL_24` 跨库更新
  - 24 个文件建立双连接访问两个库
  - 跨库事务无法保证一致性
  - PostgreSQL 不支持 Oracle DB Link 语法
- **优化方案**：重构时合并为单一 PostgreSQL 数据库，消除所有跨库访问

### 3.3 P2级问题（改进项）

#### 问题10：新版/旧版预计划并存

- **现象**：sale.pbl 有 u_plan_befor，new_deposit.pbl 又有 u_plan_befor_new（46,559字符 vs 45,600字符），代码近乎重复
- **优化方案**：统一为一套预计划管理服务

#### 问题11：报表逻辑散落各处

- **现象**：报表对象分布在 itsm.pbl（8个报表对象）、itsm02.pbl（7个）、report.pbl（25个）、kq.pbl（3个）、lsgldata.pbl（多个）
- **优化方案**：统一报表服务层，按业务域归类

#### 问题12：lsgldata.pbl 零售数据管理模块庞大

- **现象**：107 个文件，34 个业务对象，涉及门店经营数据统计、合同管理、固定资产等
- **优化方案**：按子域拆分为独立服务模块

#### 问题13：DataWindow SQL 硬编码在界面层

- **现象**：大量业务 SQL 嵌入 .srd DataWindow 定义文件（共 52 个下拉数据窗口、几百个表单/列表数据窗口）
- **优化方案**：Python 重构时所有 SQL 沉淀到 Repository 层

---

## 四、重构后功能模块设计

### 4.1 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          前端（Vue/React，后续规划）                      │
├─────────────────────────────────────────────────────────────────────────┤
│                          API 网关 (/api/v1)                              │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────────┤
│  认证鉴权  │  系统管理  │  主数据    │  ITSM     │  仓储     │  销售/采购/调拨  │
│  (auth)   │ (system) │  (master) │  (itsm)  │  (wh)   │  (sale/pur/trans) │
├──────────┴──────────┴──────────┴──────────┴──────────┴──────────────────┤
│                          Service 层（业务编排）                           │
├──────────┴──────────┴──────────┴──────────┴──────────┴──────────────────┤
│                          Repository 层（数据访问）                        │
├─────────────────────────────────────────────────────────────────────────┤
│                   PostgreSQL（重构目标库）/ Oracle（兼容过渡）             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 模块映射表（PB → Python）

| 编号 | PB 模块 | Python 模块 | 优先级 | 说明 |
|------|---------|------------|--------|------|
| M001 | app_main.pbl | app.api.shell | P0 | 主菜单 + 已开模块管理 |
| M002 | app_system.pbl | app.api.system | P0 | 用户/角色/权限/菜单管理 |
| M003 | base_srv.pbl | app.api.auth | P0 | 登录认证/会话管理 |
| M004 | itsm.pbl | app.api.maintenance | P0 | ITSM核心（维护单CRUD+统一状态机） |
| M005 | itsm02.pbl | app.api.itsm_ext | P0 | ITSM扩展（设备变更/保养/关门等） |
| M006 | base_cust.pbl | app.api.master | P0 | 客户+物料+供应商主数据 |
| M007 | sale.pbl | app.api.sale | P1 | 预计划管理+销售单据 |
| M008 | purchase.pbl | app.api.purchase | P1 | 采购计划+采购登记 |
| M009 | wh.pbl + wh_syc.pbl | app.api.warehouse | P1 | **统一库存移动模型** |
| M010 | trans.pbl | app.api.transfer | P1 | 调拨管理 |
| M011 | lsgldata.pbl | app.api.retail | P2 | 零售数据管理 |
| M012 | new_deposit.pbl | app.api.deposit | P2 | 押金管理 |
| M013 | report.pbl | app.api.report | P2 | 综合报表 |
| M014 | price.pbl | app.api.price | P2 | 价格管理 |
| M015 | qc.pbl | app.api.quality | P2 | 质检管理 |
| M016 | appraisal.pbl | app.api.appraisal | P2 | 供应商考核 |
| M017 | kq.pbl | app.api.attendance | P3 | 考勤管理 |
| — | base_objects.pbl + base_attrib.pbl + base_dwsrv.pbl + app_objects.pbl | — | — | PB 框架基础控件，Python 不需迁移 |
| — | dw2xls.pbl | — | — | Excel 导出，用 Python 库替代 |
| — | app_d.pbl + app_dddw.pbl | — | — | DataWindow 定义，SQL 沉淀到 Repository |

### 4.3 核心业务表清单

#### 4.3.1 ITSM 业务表

| 表名 | 说明 | 引用模块数 |
|------|------|-----------|
| TIT10_MAINTENANCEDAY | 日常维护单主表 | 5 |
| TIT10_POS_DETAIL | 维护单换机配件明细 | 2 |
| TIT10_MAIN_TRACK | 状态变更轨迹 | 2 |
| TIT10_MAINTENANCE_LIABILITY | 责任豁免/未达 | 3 |
| TIT13_MAINTENANCE_OPEN | 新机开通单主表 | 3 |
| TIT14_EQUIPMENT_OPEN | 开通设备明细 | 3 |
| TIT15_MAINTENANCE_RENOVATE | 旧机翻新单主表 | 3 |
| TIT15_EQUIPMENT_RENOVATE | 翻新设备映射 | 1 |
| TIT16_DEVICE_CHANGE | 设备变更单主表 | 4 |
| TIT17_MAINTENANCE | 保养维护单主表 | 1 |
| TIT17_CUST_POS_DAILY | 保养设备明细 | 1 |
| TIT17_MAINTENANCE_PLAN | 保养计划 | 1 |
| TIT18_STORE_CLOSE | 门店关闭 | 3 |
| **TIT20_RECYCLE_TASK** | **新增：回收任务主表** | — |
| **TIT20_RECYCLE_TASK_DTL** | **新增：回收任务明细** | — |
| TIT21_MAINTENANCE_DISPATCH | 派工记录 | 3 |
| TIT23_MAINTENANCE_D2D | 上门服务记录（公用） | 5 |
| TIT24_MAINTENANCE_RV | 客户回访记录 | 3 |
| TIT25_ACCESSORIES_UPDATE | 配件更新记录 | 4 |
| TIT27_CLOSE_BILLS | 关单记录 | 3 |
| TIT28_FREE_REPLACE | 免费更换主表 | 2 |
| TIT28_FREE_REPLACE_DT | 免费更换明细 | 2 |

#### 4.3.2 主数据表

| 表名 | 说明 | 引用模块数 |
|------|------|-----------|
| TMM22_CUSTOMERS | 客户/门店主表 | **17**（全系统最核心） |
| **TMM22_CUSTOMERS_HISTORY** | **新增：客户变更历史** | — |
| TMM35_CUST_POS_RL | 门店设备关联 | 9 |
| TMM12_ITEMS | 物料/商品主表 | 15 |
| TMM19_SUPPLIERS | 供应商主表 | 5 |
| TMM41_BOM / TMM42_BOMDT | BOM 清单 | 8 |
| TMM43_EID | 设备编码主表 | 9 |
| PLAN_CUST | 预计划 | 5 |

---

## 五、重构优化方案设计

### 5.1 优化方案1：取机业务独立化（P0）

**现状**：取机（plantyp='30'）创建 TIT10_MAINTENANCEDAY，与日常维修混在一起

**重构后**：

```
预计划(plantyp='30') → 创建 TIT20_RECYCLE_TASK（回收任务）
                         ├── 自动查询门店可回收资产 (TMM35_CUST_POS_RL)
                         ├── 生成回收任务明细 (TIT20_RECYCLE_TASK_DTL)
                         └── 独立状态流转：
                              待分配(00) → 已分配(01) → 回收中(02) → 已完成(03)
```

**Python 设计**：
```
app/
  api/recycle_task.py          # API 端点
  services/recycle_task_service.py    # 回收任务服务
  services/plan_trigger_service.py   # 预计划自动触发
  repositories/recycle_task_repository.py
  models/recycle_task.py       # TIT20 ORM 模型
```

### 5.2 优化方案2：资产属性扩展（P0）

**扩展 TMM35_CUST_POS_RL**（复用现有表，避免数据迁移）：

| 新增字段 | 类型 | 说明 |
|---------|------|------|
| ASSET_TYPE | VARCHAR(10) | NEW(新机)/OLD(旧机)/RENOVATED(翻新)/SCRAP(报废) |
| RECYCLABLE_FLAG | CHAR(1) | 1:可回收 / 0:不可回收 |
| RECYCLE_STATUS | VARCHAR(10) | NONE/PENDING/ASSIGNED/IN_PROGRESS/COMPLETED |
| ASSET_STATUS | VARCHAR(10) | ACTIVE(在用)/RETURNED(已回收)/SCRAPPED(已报废) |
| CREATED_FROM | VARCHAR(20) | 来源：PLAN_CUST/MAINTENANCE/MANUAL |
| SOURCE_ID | VARCHAR(20) | 来源单号 |
| WARRANTY_EXPIRE | DATE | 保修到期日 |

### 5.3 优化方案3：客户生命周期管理（P0）

**TMM22_CUSTOMERS 增加字段**：

| 新增字段 | 类型 | 说明 |
|---------|------|------|
| CustomerStatus | VARCHAR(20) | TEMP/PENDING/ACTIVE/INVALID/BLACKLIST |
| SourceType | VARCHAR(20) | PREPLAN/MANUAL/IMPORT/API |
| VerifiedAt | DATE | 转正时间 |
| PreplanId | VARCHAR(50) | 关联预计划单号 |
| ValidUntil | DATE | 临时客户有效期 |

**状态机**：
```
TEMP（预计划新建） → PENDING（预计划提交） → ACTIVE（预计划完成/转正）
     ↓                    ↓
  INVALID（预计划取消）  INVALID（预计划取消）
```

### 5.4 优化方案4：磁卡号变更历史（P0）

**新增表 TMM22_CUSTOMERS_HISTORY**：

| 字段 | 说明 |
|------|------|
| HISTORY_ID | 主键 |
| CUSTCD | 客户代码 |
| OLD_CUSTCARD | 原磁卡号 |
| NEW_CUSTCARD | 新磁卡号 |
| CHANGE_TYPE | 变更类型（CK/BQ/BG） |
| CHANGE_REASON | 变更原因 |
| DEVICE_CHANGE_ID | 关联变更单 |
| CHANGE_TIME | 变更时间 |

**流程改进**：变更前先存历史 → 再更新主表，保证数据可追溯。

### 5.5 优化方案5：统一 ITSM 状态机（P1）

```python
# 所有 ITSM 单据共享统一状态机
class MaintenanceState(Enum):
    DRAFT = "00"           # 草稿
    PLANNED = "01"         # 已计划
    DISPATCHED = "04"      # 已派工
    IN_PROGRESS = "02"     # 实施中
    COMPLETED = "05"       # 已完成
    CANCELLED = "09"       # 已取消

# 统一状态流转规则
TRANSITIONS = {
    DRAFT: [PLANNED, CANCELLED],
    PLANNED: [DISPATCHED, CANCELLED],
    DISPATCHED: [IN_PROGRESS, CANCELLED],
    IN_PROGRESS: [COMPLETED, CANCELLED],
}

# 状态变更时自动：
# 1. 校验流转合法性
# 2. 记录 TIT10_MAIN_TRACK 日志
# 3. 触发事件（派工通知、完工回访等）
```

### 5.6 优化方案6：仓储统一出入库模型（P1）

**将 20 个出入库对象精简为统一模型**：

```python
class StockMovementType(Enum):
    # 入库
    PURCHASE_IN = "01"       # 采购入库
    SALE_RETURN_IN = "02"    # 销售退货入库
    SERVICE_RETURN_IN = "03" # 服务返还入库
    TRANSFER_IN = "04"       # 调拨入库
    LEND_RETURN_IN = "05"    # 借出归还入库
    PRODUCTION_IN = "06"     # 生产入库
    QC_IN = "07"             # 质检入库
    ADJUST = "08"            # 库存调整
    # 出库
    SALE_OUT = "11"          # 销售出库
    SERVICE_OUT = "12"       # 服务领用出库
    TRANSFER_OUT = "13"      # 调拨出库
    LEND_OUT = "14"          # 借出出库
    PRODUCTION_OUT = "15"    # 生产出库
    QC_OUT = "16"            # 质检出库
    GENERAL_OUT = "17"       # 通用出库

# 统一服务入口
class StockMovementService:
    def move(type, warehouse, items, ref_bill) -> str
    def get_balance(warehouse, item) -> int
    def get_history(filters) -> list
```

**预计代码精简**：从 ~500K 字符 → ~50K 字符（减少 90%）

### 5.7 优化方案7：关门流程补全（P1）

**完善 plantyp='40' 的门店关闭流程**：

```
预计划(plantyp='40')
  ├── 1. 查询门店在用设备 (TMM35_CUST_POS_RL)
  ├── 2. 自动创建回收任务 (TIT20_RECYCLE_TASK)
  ├── 3. 创建门店关闭单 (TIT18_STORE_CLOSE)
  ├── 4. 冻结门店客户状态 (TMM22.CustomerStatus → INVALID)
  └── 5. 回收完成后 → 正式关闭门店
```

---

## 六、重构实施路线图

### 阶段1：P0 基础架构 + 核心优化（第1-3周）

| 任务 | PB 来源 | Python 目标 | 依赖 |
|------|---------|------------|------|
| Flask 应用工厂 + 基础中间件 | — | app/__init__.py, extensions.py | 无 |
| 登录认证/会话 | base_srv.pbl | app/api/auth.py, services/auth_service.py | 无 |
| 用户/角色/权限 | app_system.pbl | app/api/system/ | 认证 |
| 菜单管理 | app_main.pbl | app/api/shell.py | 权限 |
| 客户生命周期（优化3） | base_cust.pbl | app/services/customer_lifecycle_service.py | 无 |
| 资产属性扩展（优化2） | base_cust.pbl | app/services/asset_service.py | 客户 |
| 磁卡号历史（优化4） | itsm02.pbl | TMM22_CUSTOMERS_HISTORY DDL | 无 |

### 阶段2：ITSM 核心迁移 + 状态机（第4-6周）

| 任务 | PB 来源 | Python 目标 |
|------|---------|------------|
| 统一状态机（优化5） | itsm.pbl 多处 | app/services/state_machine.py |
| 日常维护单 CRUD | u_itsm_rcwh_h | app/api/maintenance.py |
| 新机开通单 CRUD | u_itsm_open | app/api/maintenance_open.py |
| 旧机翻新单 CRUD | u_itsm_renovate | app/api/maintenance_renovate.py |
| 保养维护单 CRUD | u_itsm_maintenance_daily | app/api/maintenance_daily.py |
| 设备变更单 + 磁卡号历史 | u_itsm_device_change | app/api/device_change.py |
| 取机/回收任务（优化1） | 新建 | app/api/recycle_task.py |
| 公用附表服务（D2D/回访） | itsm.pbl 公用 | app/services/d2d_service.py 等 |

### 阶段3：销售 + 仓储 + 采购（第7-10周）

| 任务 | PB 来源 | Python 目标 |
|------|---------|------------|
| 预计划管理 + 触发器（优化7） | sale.pbl | app/api/preplan.py |
| 关门流程补全（优化7） | sale.pbl + itsm02.pbl | app/services/store_close_service.py |
| **统一出入库模型（优化6）** | wh.pbl 20个对象 | app/api/warehouse.py（精简90%） |
| 采购管理 | purchase.pbl | app/api/purchase.py |
| 调拨管理 | trans.pbl | app/api/transfer.py |

### 阶段4：辅助模块 + 报表（第11-14周）

| 任务 | PB 来源 | Python 目标 |
|------|---------|------------|
| 零售数据管理 | lsgldata.pbl | app/api/retail/ |
| 押金管理 | new_deposit.pbl | app/api/deposit.py |
| 综合报表 | report.pbl + 各模块报表 | app/api/report/ |
| 质检管理 | qc.pbl | app/api/quality.py |
| 价格管理 | price.pbl | app/api/price.py |
| 供应商考核 | appraisal.pbl | app/api/appraisal.py |
| 考勤管理 | kq.pbl | app/api/attendance.py |

---

## 七、技术规范

### 7.1 目录结构

```
app/
├── __init__.py              # Flask 应用工厂
├── extensions.py            # SQLAlchemy, Migrate 等扩展
├── api/                     # API 层（路由 + 参数校验）
│   ├── auth.py
│   ├── system/
│   ├── master/              # 客户/物料/供应商
│   ├── maintenance.py       # ITSM 维护单
│   ├── recycle_task.py      # 回收任务
│   ├── warehouse.py         # 统一出入库
│   └── ...
├── services/                # 业务层（编排 + 事务）
│   ├── auth_service.py
│   ├── state_machine.py     # 统一状态机
│   ├── customer_lifecycle_service.py
│   ├── asset_service.py
│   ├── recycle_task_service.py
│   ├── stock_movement_service.py
│   └── ...
├── repositories/            # 数据访问层（SQL 封装）
├── models/                  # SQLAlchemy ORM 模型
└── schemas/                 # Pydantic/Marshmallow 校验
```

### 7.2 API 规范

- 统一前缀：`/api/v1`
- 统一响应：`{ "code": 200, "message": "ok", "data": {...} }`
- 统一错误：`{ "code": 4xx/5xx, "message": "...", "request_id": "..." }`
- 请求/响应均有 Schema 校验

### 7.3 数据库

- **原始架构**：Oracle 双库（CCGLPDB 业务主库 + LGREPORTPDB 零售库），通过 DB Link 跨库访问
- **目标架构**：合并为**单一 PostgreSQL 数据库**，消除跨库依赖
- ORM：SQLAlchemy + Flask-Migrate (Alembic)
- 连接配置通过环境变量，禁止硬编码
- 事务在 Service 层统一管理
- 原 Oracle 存储过程（USP_WH_IN/USP_WH_OUT 等）改写为 Python Service 层逻辑

#### 7.3.1 双库合并方案

**合并原则**：CCGLPDB 和 LGREPORTPDB 的所有表统一迁入一个 PostgreSQL 数据库，通过 Schema 或表前缀区分来源。

| 原数据库 | 迁移目标 | 说明 |
|---------|---------|------|
| CCGLPDB 全部表（TIT*、TMM*、TWH*、PLAN_*） | PostgreSQL 主 Schema (public) | 业务主表，直接迁移 |
| LGREPORTPDB 表（零售/经营数据） | PostgreSQL 主 Schema (public) | 合并到同一库，消除 DB Link |

**SQL 改造要点**：

| 改造项 | 原 Oracle 写法 | 目标 PostgreSQL 写法 |
|--------|---------------|---------------------|
| 跨库查询 | `FROM TMM22_CUSTOMERS@CCGL_23` | `FROM tmm22_customers`（同库直接访问） |
| 跨库更新 | `UPDATE tmm22_customers@ccgl_24` | `UPDATE tmm22_customers`（同库直接更新） |
| DB Link 连接 | `itrans.ServerName = "ccgllsgl"` | 不需要（单一连接） |
| 存储过程调用 | `CALL CCGL.USP_WH_IN(...)` | Python Service 方法 |
| DECODE 函数 | `DECODE(col, val1, res1, default)` | `CASE WHEN col = val1 THEN res1 ELSE default END` |
| 序列 | `seq_xxx.NEXTVAL` | `SERIAL` / `GENERATED ALWAYS AS IDENTITY` |
| 日期函数 | `SYSDATE` | `NOW()` / `CURRENT_TIMESTAMP` |
| 字符串截取 | `SUBSTR(str, 0, n)` | `SUBSTRING(str FROM 1 FOR n)`（注意起始位置差异） |
| NVL 函数 | `NVL(col, default)` | `COALESCE(col, default)` |

### 7.4 代码规范

- 语言：中文注释/文档
- 编码：UTF-8, LF 换行
- 格式化：black + isort + ruff
- 类型检查：mypy --strict
- 测试：pytest
- 安全：bandit
- 日志：logging（禁止 print）

---

## 八、代码精简预估

| 模块 | PB 原始代码量 | 重构后预估 | 精简比例 | 精简原因 |
|------|-------------|-----------|---------|---------|
| wh.pbl（仓储） | ~500K | ~50K | **90%** | 20个对象统一为1个服务 |
| itsm.pbl（ITSM核心） | ~2,267K | ~300K | **87%** | 状态机统一 + DataWindow SQL 沉淀 |
| itsm02.pbl（ITSM扩展） | ~1,710K | ~200K | **88%** | 同上 |
| sale.pbl（销售） | ~1,692K | ~150K | **91%** | 新旧预计划合并 + UI 代码不迁移 |
| app_*.pbl（框架） | ~696K | 0 | **100%** | PB 框架控件无需迁移 |
| base_*.pbl（基础） | ~1,734K | ~100K | **94%** | 服务/工具 Python 化 |
| **总计** | **~18,051K** | **~2,000K** | **~89%** | |

---

## 九、验收标准

### 9.1 功能验收

| 优化项 | 验收点 |
|--------|--------|
| 取机业务独立化 | 回收任务 CRUD 完整，预计划 plantyp='30' 正确触发 |
| 资产属性扩展 | 资产类型/回收状态字段可查询，存量数据已初始化 |
| 客户生命周期 | 临时客户创建/转正/失效流程正确 |
| 磁卡号变更历史 | 变更前自动保存历史，历史可查询 |
| 统一状态机 | 所有单据类型状态流转合法性校验通过 |
| 统一出入库 | 所有出入库类型通过统一接口完成，结果与 PB 一致 |
| 关门流程 | 门店关闭 → 设备回收 → 客户失效 全流程通过 |

### 9.2 性能要求

| 接口 | 响应时间要求 |
|------|------------|
| 客户查询（含状态过滤） | < 200ms |
| 维护单列表查询 | < 300ms |
| 状态流转操作 | < 100ms |
| 资产可回收判定 | < 100ms |
| 库存余额查询 | < 200ms |
| 报表查询 | < 2s |

---

## 十、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| Oracle 双库 → PostgreSQL 单库合并 | 高 | 合并 CCGLPDB + LGREPORTPDB 为单一 PostgreSQL 库；消除 19 个文件的 @CCGL_23 DB Link 引用和 24 个文件的双连接代码；建立 SQL 兼容性映射表（DECODE→CASE、SYSDATE→NOW()、序列→SERIAL、NVL→COALESCE、SUBSTR→SUBSTRING） |
| Oracle 存储过程改写 | 高 | USP_WH_IN/USP_WH_OUT 等 100 个文件引用的存储过程需改写为 Python Service 层逻辑，需逐一验证业务等价性 |
| 存量数据状态初始化复杂 | 高 | 编写专门迁移脚本，分批执行，保留原始数据备份 |
| 回收任务与日常维护单并行运行 | 中 | 增加 SOURCE_TYPE 字段区分，逐步迁移 |
| 仓储统一模型影响范围大 | 高 | 作为独立优化项，核心业务稳定后实施 |
| 老系统兼容层需要维护 | 中 | 建立兼容视图，逐步敛收 |

---

**文档状态**: 待用户确认  
**确认后下一步**: 按阶段路线图开始 Python + Flask + PostgreSQL 重构编码
