# PB→Python 重构优化需求文档

**文档版本**: v1.0  
**创建时间**: 2026-04-08  
**作者**: Cascade  
**关联文档**: 
- `项目整体计划与进展_2026-03-11.md`（进度追踪）
- `PB_TO_PYTHON_MODULE_MAPPING.csv`（模块映射）
- `PB_TO_PYTHON_SQL_MAPPING.csv`（SQL映射）

---

## 1. 文档说明

本文档汇总 PB→Python 重构过程中识别出的**系统性优化需求**，作为后续重构实施的指导性文档。与原计划文档的区别：

- **项目整体计划**: 记录已完成/进行中的任务状态（what & when）
- **本需求文档**: 记录待实现的优化方案和设计思路（how & why）

---

## 2. 整体业务架构分析

### 2.1 系统业务域划分

基于源码全面分析，系统包含以下核心业务域：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        企业 ITSM-ERP 系统架构                        │
├─────────────────────────────────────────────────────────────────────┤
│  销售/计划层 (sale.pbl) - 80+ 对象                                   │
│    ├── u_plan_befor: 预计划管理（客户选择/新建）→ 优化1, 3          │
│    ├── u_plan_imple: 实施计划确认                                    │
│    ├── u_serve_plan: 服务计划                                        │
│    └── u_server_call: 话务台呼出                                   │
├─────────────────────────────────────────────────────────────────────┤
│  ITSM 核心层 (itsm.pbl + itsm02.pbl) - 116+ 对象                     │
│    ├── u_itsm_archive: 日常维护归档                                │
│    ├── u_itsm_open: 维修单派工 → 优化2                              │
│    ├── u_itsm_renovate: 实施日报 → 优化2, 4                           │
│    ├── u_itsm_rcwh_h: 回收入库 → 优化4                              │
│    └── 状态流转: 草稿→派工→实施→完成/取消 → 优化2                   │
├─────────────────────────────────────────────────────────────────────┤
│  仓储管理层 (wh.pbl) - 98+ 对象 ⚠️ 代码重复严重                     │
│    ├── 入库: 采购/销售退货/服务返还等 10+ 种 → 优化5                 │
│    ├── 出库: 销售/服务领用/借出等 10+ 种 → 优化5                     │
│    └── 盘点: 资产盘点（u_wh_asset_c_a）→ 优化4                      │
├─────────────────────────────────────────────────────────────────────┤
│  采购管理层 (purchase.pbl) - 35+ 对象                               │
│    ├── u_pc_plan: 采购计划                                          │
│    └── u_pc_register_examine: 采购登记审批                          │
├─────────────────────────────────────────────────────────────────────┤
│  调拨流转层 (trans.pbl) - 23+ 对象                                   │
│    ├── u_trans_in: 调入管理                                         │
│    └── u_trans_out: 调出管理                                        │
├─────────────────────────────────────────────────────────────────────┤
│  主数据层 (base_cust.pbl) - 76+ 对象 → 优化1, 3, 4                   │
│    ├── u_mm_customer: 客户主数据 → 优化1                            │
│    ├── u_mm_item: 物料/商品                                         │
│    ├── u_mm_bom: BOM清单                                            │
│    └── 资产属性: TMM62_ASSET_ATTRIB_LIST → 优化4                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块依赖关系

```
                    ┌─────────────────┐
                    │  M003 base_srv  │ (登录基础)
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ M002 app_   │      │ M006 base_  │      │ M004/M005   │
│ _system     │◄────►│ cust        │─────►│ itsm/itsm02 │
│ (权限基础)  │      │ (客户/资产)  │      │ (ITSM核心)  │
└─────────────┘      └─────────────┘      └─────────────┘
       ▲                                          ▲
       │         ┌─────────────────┐              │
       │         │ M001 app_main   │              │
       └─────────┤ (菜单/已开模块)  ├──────────────┘
                 └─────────────────┘
```

---

## 3. 核心优化需求清单

### 优化1: 预计划客户生命周期管理（P0级）

#### 问题描述
- **来源**: `sale.pbl` u_plan_befor, u_plan_imple
- **痛点**: 预计划新建客户直接写入 `TMM22_CUSTOMERS`，但预计划后续可能取消，导致正式客户表存在大量"幽灵客户"
- **数据量**: PLAN_CUST 表中存在历史预计划数据，部分未转正

#### 优化方案

**表结构变更**:
```sql
-- TMM22_CUSTOMERS 增加状态管理字段
ALTER TABLE TMM22_CUSTOMERS ADD (
    CustomerStatus  VARCHAR2(20) DEFAULT 'TEMP',  -- TEMP/PENDING/ACTIVE/INVALID/BLACKLIST
    SourceType      VARCHAR2(20),                 -- PREPLAN/MANUAL/IMPORT/API
    VerifiedAt      DATE,                         -- 转正时间
    PreplanId       VARCHAR2(50),                 -- 关联预计划单号
    ValidUntil      DATE                          -- 临时客户有效期（TEMP状态超期自动清理）
);

-- PLAN_CUST 增加客户关联字段（已有）
-- CUSTCD: 关联客户代码（可为临时客户）
-- NEW_CUSTCD: 新门店代码
-- PLAN_STATUS: 计划状态（00/01/02...）
```

**状态机设计**:
```python
class CustomerStatus(Enum):
    TEMP = "TEMP"         # 临时（预计划新建）
    PENDING = "PENDING"   # 待确认（预计划提交）
    ACTIVE = "ACTIVE"     # 正式客户（预计划完成）
    INVALID = "INVALID"   # 已作废（预计划取消）

class CustomerLifecycleService:
    """客户生命周期管理服务"""
    
    def create_temp_from_plan(self, plan_no: str, cust_info: dict) -> str:
        """从预计划创建临时客户"""
        pass
    
    def promote_to_active(self, customer_id: str, plan_no: str) -> None:
        """预计划完成时转正"""
        # TEMP → ACTIVE
        # 更新 VerifiedAt = sysdate
        pass
    
    def mark_invalid(self, customer_id: str, reason: str) -> None:
        """预计划取消时标记失效"""
        # TEMP → INVALID
        pass
```

**触发时机**:
- 预计划提交 → 创建临时客户（TEMP）
- 预计划执行完成 → 转正（ACTIVE）
- 预计划作废/取消 → 标记失效（INVALID）

**验收标准**:
- [ ] 存量客户数据状态初始化
- [ ] 临时客户转正/失效流程验证
- [ ] 客户查询支持按状态过滤

---

### 优化2: ITSM 维修单状态机重构（P1级）

#### 问题描述
- **来源**: `itsm.pbl` u_itsm_open, u_itsm_renovate, u_itsm_archive
- **痛点**: 状态流转逻辑分散在多个对象中，维护困难
- **现状**: `TIT13_MAINTENANCE_OPEN.CURRENT_STATUS` 字段控制状态，但流转逻辑硬编码

#### 优化方案

**状态定义**:
```python
class MaintenanceState(Enum):
    DRAFT = "00"           # 草稿/预计划
    PLANNED = "01"         # 已计划
    DISPATCHED = "04"      # 已派工
    IN_PROGRESS = "02"     # 实施中
    COMPLETED = "05"       # 已完成
    CANCELLED = "09"       # 已取消
```

**状态机模型**:
```python
class StateMachine:
    """维修单统一状态机"""
    
    TRANSITIONS = {
        MaintenanceState.DRAFT: [
            MaintenanceState.PLANNED,
            MaintenanceState.CANCELLED
        ],
        MaintenanceState.PLANNED: [
            MaintenanceState.DISPATCHED,
            MaintenanceState.CANCELLED
        ],
        MaintenanceState.DISPATCHED: [
            MaintenanceState.IN_PROGRESS,
            MaintenanceState.CANCELLED
        ],
        MaintenanceState.IN_PROGRESS: [
            MaintenanceState.COMPLETED,
            MaintenanceState.CANCELLED
        ],
    }
    
    def can_transition(self, from_state: MaintenanceState, 
                       to_state: MaintenanceState) -> bool:
        """检查状态流转是否合法"""
        pass
    
    def transition(self, maintenance_id: str, 
                   to_state: MaintenanceState,
                   operator: str,
                   remark: str = None) -> None:
        """执行状态流转，记录日志"""
        pass
```

**事件驱动设计**:
```python
class MaintenanceEventHandler:
    """维修单事件处理器"""
    
    def on_dispatch(self, maintenance_id: str, engineer_id: str):
        """派工事件"""
        # 1. 状态流转: PLANNED → DISPATCHED
        # 2. 发送通知给工程师
        # 3. 记录派工日志
        pass
    
    def on_complete(self, maintenance_id: str):
        """完成事件"""
        # 1. 状态流转: IN_PROGRESS → COMPLETED
        # 2. 更新完工时间
        # 3. 触发回访任务
        pass
```

---

### 优化3: 客户-预计划-实施单关联追踪（P1级）

#### 问题描述
- **来源**: `sale.pbl` u_plan_befor, `itsm.pbl` 各维修单对象
- **痛点**: 无法追溯客户从预计划到最终实施的全生命周期

#### 优化方案

**数据链路设计**:
```
PLAN_CUST (预计划)
    ├── PLANNO (PK)
    ├── CUSTCD → TMM22_CUSTOMERS (关联客户)
    ├── NEW_CUSTCD (新门店代码)
    ├── PLAN_STATUS (计划状态)
    ├── RECYCLE_ID → TIT20_RECYCLE_TASK (优化4: 回收任务)
    └── 实施完成 ──→ TIT13_MAINTENANCE_OPEN (维护单)
                          ├── MAINTENANCE_ID (PK)
                          ├── REQUEST_PAPER_ID (关联预计划)
                          └── 客户来源标记
```

**关联追踪服务**:
```python
class CustomerLifecycleTraceService:
    """客户全生命周期追踪服务"""
    
    def get_customer_journey(self, custcd: str) -> list[dict]:
        """
        获取客户全生命周期轨迹。
        
        返回:
            [
                {type: 'preplan', date: '2026-01-01', plan_no: 'P001', status: 'completed'},
                {type: 'maintenance', date: '2026-01-05', maintenance_id: 'M001', type: '新机开通'},
                {type: 'recycle', date: '2026-03-01', recycle_id: 'R001', assets: ['POS001']},
                ...
            ]
        """
        pass
```

---

### 优化4: 资产属性管理与旧机回收任务独立化（P0级）

#### 问题描述
- **来源**: `base_cust.pbl` TMM62_ASSET_ATTRIB_LIST, `itsm.pbl` u_itsm_renovate
- **痛点**: 
  1. 原有资产属性表缺失，无法分清客户资产属性和后续处理
  2. 旧机翻新/回收作为日常维护单处理，不便于统计分析
  3. 关门/旧机翻新无法自动触发回收任务

#### 优化方案

**4.1 资产属性模型**

**现状分析**:
- 已有资产配置表 `TMM35_CUST_POS_RL`（门店设备关联表）
- 已有字段：CUSTCD, EID, ITEMCD, STARTDATE, SYSINFO, STATUS, TYPFLG, MAINTENANCEDATE
- **缺失**：资产类型、可回收标志、回收状态、来源追溯等字段

**扩展方案（推荐）**:
```sql
-- 扩展 TMM35_CUST_POS_RL（复用现有表，避免数据迁移）
ALTER TABLE TMM35_CUST_POS_RL ADD (
    -- 资产类型（标准化设备生命周期）
    ASSET_TYPE      VARCHAR2(10),   -- NEW:新机 | OLD:旧机 | RENOVATED:翻新机 | SCRAP:报废
    
    -- 可回收管理（用于预计划触发回收任务）
    RECYCLABLE_FLAG CHAR(1) DEFAULT '0',  -- 1:可回收 | 0:不可回收
    RECYCLE_STATUS  VARCHAR2(10),   -- NONE:无需 | PENDING:待回收 | ASSIGNED:已分配 | 
                                    -- IN_PROGRESS:回收中 | COMPLETED:已完成 | CANCELLED:取消
    
    -- 来源追溯（关联预计划/维护单）
    CREATED_FROM    VARCHAR2(20),   -- PLAN_CUST:预计划 | MAINTENANCE:维护单 | MANUAL:手工
    SOURCE_ID       VARCHAR2(20),   -- 来源单号（如预计划号）
    
    -- 补充字段
    WARRANTY_EXPIRE DATE,           -- 保修到期日
    ASSET_STATUS    VARCHAR2(10)    -- ACTIVE:在用 | RETURNED:已回收 | SCRAPPED:已报废
);
```

**备选方案对比**:

| 方案 | 做法 | 数据迁移 | 建议 |
|------|------|---------|------|
| 扩展 TMM35 | ALTER TABLE 增加字段 | 无需迁移 | ✅ **推荐** |
| 新建 TMM63 | 创建新表，导数据 | 需同步TMM35数据 | ❌ 数据冗余 |

**存量数据处理**:
```sql
-- 初始化存量数据的 ASSET_TYPE
UPDATE TMM35_CUST_POS_RL
SET ASSET_TYPE = CASE
    WHEN EXISTS(SELECT 1 FROM TIT15_EQUIPMENT_RENOVATE er 
                WHERE er.DEVICE_ID = EID AND er.IS_FINISH = '1') 
    THEN 'RENOVATED'
    WHEN STARTDATE > SYSDATE - 365 THEN 'NEW'
    ELSE 'OLD'
END,
RECYCLE_STATUS = 'NONE',
RECYCLABLE_FLAG = '0',
ASSET_STATUS = CASE USEFLG WHEN '1' THEN 'ACTIVE' ELSE 'RETURNED' END
WHERE ASSET_TYPE IS NULL;
```

**资产服务**（基于 TMM35_CUST_POS_RL）:
```python
class AssetService:
    """门店资产管理服务（基于 TMM35_CUST_POS_RL）"""
    
    def get_recyclable_assets(self, custcd: str) -> list[dict]:
        """
        获取门店可回收资产列表（查询 TMM35_CUST_POS_RL）。
        
        SQL:
            SELECT * FROM TMM35_CUST_POS_RL
            WHERE CUSTCD = :custcd
              AND ASSET_TYPE IN ('OLD', 'RENOVATED')
              AND RECYCLABLE_FLAG = '1'
              AND RECYCLE_STATUS = 'NONE'
        """
        pass
    
    def mark_recyclable(self, custcd: str, plan_type: str) -> int:
        """
        标记门店可回收资产（更新 TMM35_CUST_POS_RL）。
        
        SQL:
            UPDATE TMM35_CUST_POS_RL
            SET RECYCLABLE_FLAG = '1', RECYCLE_STATUS = 'PENDING'
            WHERE CUSTCD = :custcd
        """
        pass
    
    def create_from_plan(self, plan_no: str, custcd: str) -> int:
        """
        预计划完成时，在 TMM35_CUST_POS_RL 创建新资产记录。
        
        SQL:
            INSERT INTO TMM35_CUST_POS_RL
            (CUSTCD, EID, ITEMCD, STARTDATE, ASSET_TYPE, CREATED_FROM, SOURCE_ID, USEFLG)
            VALUES (:custcd, :eid, :itemcd, SYSDATE, 'NEW', 'PLAN_CUST', :plan_no, '1')
        """
        pass
```

**4.2 旧机回收任务独立化**

**新增表结构**:
```sql
-- 旧机回收任务主表（独立于日常维护单）
CREATE TABLE TIT20_RECYCLE_TASK (
    RECYCLE_ID      VARCHAR2(12) PRIMARY KEY,   -- 回收任务ID
    RECYCLE_TYPE    VARCHAR2(2),                -- 回收类型
    PLANNO          VARCHAR2(10),               -- 来源预计划单号
    MAINTENANCE_ID  VARCHAR2(8),                -- 关联维护单号
    CUSTCD          CHAR(8) NOT NULL,           -- 门店代码
    TASK_STATUS     VARCHAR2(2),                -- 任务状态
    ASSET_COUNT     NUMBER DEFAULT 0,         -- 应回收资产数量
    ASSET_LIST      VARCHAR2(500),            -- 资产清单JSON
    ASSIGNED_TO     VARCHAR2(6),                -- 分配人员
    ASSIGNED_DATE   DATE,                       -- 分配日期
    COMPLETE_DATE   DATE,                       -- 完成日期
    ACTUAL_COUNT    NUMBER DEFAULT 0,         -- 实际回收数量
    DISPOSITION     VARCHAR2(2),              -- 处置方式
    TARGET_WAREHOUSE VARCHAR2(10),              -- 目标仓库
    USEFLG          CHAR(1) DEFAULT '1',
    GENDATE         DATE,
    OPERCD          CHAR(6),
    REMARK          VARCHAR2(200)
);

-- 回收任务明细表
CREATE TABLE TIT20_RECYCLE_TASK_DTL (
    RECYCLE_ID      VARCHAR2(12),
    ASSET_ID        VARCHAR2(20),
    ASSET_TYPE      VARCHAR2(10),
    EXPECTED_STATUS VARCHAR2(10),
    ACTUAL_STATUS   VARCHAR2(10),
    RECOVERED_DATE  DATE,
    WAREHOUSE_CD    VARCHAR2(10),
    REMARK          VARCHAR2(200),
    PRIMARY KEY (RECYCLE_ID, ASSET_ID)
);
```

**回收任务服务**:
```python
class RecycleTaskService:
    """旧机回收任务管理服务"""
    
    def create_from_plan(self, plan_no: str, plan_type: str) -> str:
        """
        从预计划创建回收任务。
        触发条件:
            - PLAN_TYPE in ('01': 旧机翻新, '02': 关门)
            - 门店有可回收资产
        """
        pass
    
    def assign_task(self, recycle_id: str, user_id: str) -> None:
        """分配回收任务给人员"""
        pass
    
    def complete_recycle(self, recycle_id: str, 
                        actual_assets: list[str],
                        disposition: str) -> None:
        """完成回收任务，处置资产"""
        pass
    
    def get_recycle_stats(self, start_date: date, end_date: date) -> dict:
        """回收统计分析（独立于维护单统计）"""
        pass
```

**4.3 预计划自动触发回收任务**

```python
class PlanTriggerService:
    """预计划自动触发服务"""
    
    def process_plan_completion(self, plan_no: str) -> dict:
        """
        处理预计划执行完成后的自动触发逻辑。
        
        触发规则:
            PLAN_TYPE = '01' (旧机翻新) ──┐
            PLAN_TYPE = '02' (关门)     ──┼── 检查可回收资产 ──→ 创建回收任务
            PLAN_TYPE = '03' (新机开通) ──┼── 创建新资产记录
            PLAN_TYPE = '04' (设备变更) ──┴── 触发资产变更
        """
        pass
```

**状态流转**:
```
预计划（PLAN_CUST）
    │
    ├── PLAN_TYPE in ('01', '02') ──→ 检查门店可回收资产
    │                                      │
    │                                      ├── 可回收数量 > 0 ──→ 创建回收任务
    │                                      │       │
    │                                      │       ├── TASK_STATUS = '00'（待分配）
    │                                      │       ├── 分配人员 ──→ '01'（已分配）
    │                                      │       ├── 开始回收 ──→ '02'（回收中）
    │                                      │       ├── 完成回收 ──→ '03'（已完成）
    │                                      │       └── 更新资产状态 → RECYCLED
    │                                      │
    │                                      └── 无可回收资产 ──→ 标记无需回收
    │
    └── 其他计划类型 ──→ 相应处理流程
```

---

### 优化5: 仓储出入库统一模型（P1级）

#### 问题描述
- **来源**: `wh.pbl` 16+ 种出入库对象（u_wh_*in/out.sru）
- **痛点**: 代码高度重复，每种出入库类型一个对象
- **统计**: 入库类 8 个对象，出库类 8 个对象，结构雷同

#### 优化方案

**统一模型设计**:
```python
class StockMovementType(Enum):
    """库存移动类型"""
    # 入库类型
    PURCHASE_IN = "01"      # 采购入库
    SALE_RETURN_IN = "02"   # 销售退货入库
    SERVICE_RETURN_IN = "03" # 服务返还入库
    TRANSFER_IN = "04"      # 调拨入库
    LEND_RETURN_IN = "05"   # 借出归还入库
    
    # 出库类型
    SALE_OUT = "11"         # 销售出库
    SERVICE_OUT = "12"      # 服务领用出库
    TRANSFER_OUT = "13"     # 调拨出库
    LEND_OUT = "14"         # 借出出库
    QC_OUT = "15"           # 质检出库

class StockMovement:
    """统一库存移动记录"""
    movement_id: str
    movement_type: StockMovementType
    warehouse_cd: str
    items: list[MovementItem]
    ref_bill_type: str      # 关联单据类型
    ref_bill_id: str        # 关联单据号
    operator: str
    created_at: datetime

class MovementItem:
    itemcd: str
    quantity: int
    batch_id: str
    unit_price: Decimal
    
class StockMovementService:
    """统一库存移动服务"""
    
    def move(self, movement: StockMovement) -> str:
        """
        执行库存移动。
        
        根据 movement_type 决定:
            - 影响科目（库存商品/服务成本/采购在途）
            - 审批流程
            - 关联单据类型
            - 库存变动方向（+/-）
        """
        pass
    
    def get_stock_balance(self, warehouse_cd: str, itemcd: str) -> int:
        """查询库存余额"""
        pass
    
    def get_movement_history(self, 
                            filters: MovementFilter) -> list[StockMovement]:
        """查询库存移动历史"""
        pass
```

---

## 4. 优化实施路线图

### 4.1 优先级矩阵

| 优化项 | 业务价值 | 技术复杂度 | 依赖关系 | 建议优先级 |
|--------|---------|-----------|---------|-----------|
| 优化1: 预计划客户生命周期 | 高 | 中 | 无 | **P0** |
| 优化2: ITSM状态机 | 高 | 中 | 依赖优化1 | P1 |
| 优化3: 客户关联追踪 | 中 | 中 | 依赖优化1,2 | P1 |
| 优化4: 资产/回收任务 | 高 | 高 | 依赖优化1 | **P0** |
| 优化5: 仓储统一模型 | 中 | 高 | 无 | P1 |

### 4.2 阶段划分

**阶段1: P0级优化（1-2周）**
- 优化1: 客户生命周期管理
  - TMM22_CUSTOMERS 表结构变更
  - CustomerLifecycleService 实现
  - 存量数据状态初始化
  
- 优化4.1: 资产属性模型（第一部分）
  - TMM35_CUST_POS_RL 表扩展（增加 ASSET_TYPE/RECYCLABLE_FLAG/RECYCLE_STATUS 等字段）
  - AssetService 基础功能
  - 存量资产数据初始化（ASSET_TYPE 字段）

**阶段2: P0级完成 + P1启动（2-4周）**
- 优化4.2: 回收任务独立化
  - TIT20_RECYCLE_TASK 表创建
  - RecycleTaskService 实现
  - PlanTriggerService 实现
  
- 优化2: ITSM状态机（可并行）
  - 状态机模型实现
  - 事件处理器框架

**阶段3: P1级完成（4-6周）**
- 优化3: 客户关联追踪
- 优化5: 仓储统一模型（可选，影响面大）

### 4.3 与原有模块重构的关系

当前 P0 模块重构进度：
- M001 (app_main): 菜单链路 + 已开模块管理 ✅
- M002 (app_system): 用户组 + 组权限 + 用户菜单权限 ✅
- M003 (base_srv): 登录/会话 ✅

**优化实施与模块重构的协调**:

```
当前状态 ──→ 下一步行动
─────────────────────────
M006 (base_cust) 待开始 ──┬──→ 结合优化1（客户生命周期）
                          ├──→ 结合优化4（资产管理）
                          └──→ 重构时直接实现优化方案

M004/M005 (itsm) 待开始 ──┬──→ 结合优化2（状态机）
                          ├──→ 结合优化4（回收任务）
                          └──→ 重构时替换原有逻辑
```

---

## 5. 验收标准汇总

### 5.1 功能验收

| 优化项 | 验收点 | 验证方式 |
|--------|--------|---------|
| 优化1 | 临时客户创建/转正/失效流程 | 单元测试 + 流程验证 |
| 优化1 | 存量客户状态正确性 | 数据比对脚本 |
| 优化2 | 状态流转合法性校验 | 状态机单元测试 |
| 优化2 | 事件触发正确性 | 集成测试 |
| 优化4.1 | 资产可回收判定 | 测试用例 |
| 优化4.1 | 存量资产数据完整性 | 数据校验 |
| 优化4.2 | 回收任务自动创建 | 流程测试 |
| 优化4.2 | 回收率统计准确性 | 报表验证 |
| 优化5 | 库存移动正确性 | 盘点比对 |

### 5.2 性能验收

- 客户查询（含状态过滤）< 200ms
- 资产可回收判定 < 100ms
- 状态流转操作 < 100ms
- 回收统计报表 < 2s

---

## 6. 风险与应对

| 风险项 | 影响 | 应对方案 |
|--------|------|---------|
| 存量数据状态初始化复杂 | 高 | 编写专门迁移脚本，分批次执行，保留原始数据备份 |
| 回收任务与原有维护单并行运行 | 中 | 增加 SOURCE_TYPE 字段区分，逐步迁移 |
| 状态机与原有硬编码逻辑冲突 | 中 | 保留原有字段，渐进式替换，支持回滚 |
| 仓储统一模型影响范围大 | 高 | 作为独立优化项，待核心业务稳定后实施 |

---

## 7. 附录

### 7.1 相关SQL脚本索引

- DDL脚本: `scripts/ddl/optimization_*.sql`
- 数据迁移脚本: `scripts/migration/customer_status_init.sql`
- 初始化脚本: `scripts/init/asset_data_import.sql`

### 7.2 设计文档索引

- 状态机设计: `docs/design/maintenance_state_machine.md`
- 资产模型设计: `docs/design/asset_management_model.md`
- 回收任务流程: `docs/design/recycle_task_workflow.md`

### 7.3 变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-04-08 | 初始版本，汇总5项核心优化需求 | Cascade |

---

**文档结束**
