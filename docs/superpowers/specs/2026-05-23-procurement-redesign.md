---
类型: 技术设计文档
阅读状态: 待评审
tags:
  - 采购需求
  - 采购订单
  - 重构设计
  - Vue3
  - Flask
  - PostgreSQL
更新日期: 2026-05-23
创建日期: 2026-05-23
作者: CJ
版本: v1.0
笔记位置: myitsm
笔记绝对路径: /Users/cheungjan/Desktop/obsidian_cj/CJdocs/myitsm/未命名.md
---


---

# 采购管理模块重构设计规格文档

## 一、设计目标

重构原有 PowerBuilder 采购计划管理系统为 Vue3 + Flask + PostgreSQL 技术栈，解决以下核心问题：

1. **PP 与 PR 无明细关联**——采购需求(TPC01/TPC02)与采购订单(TPC12/TPC13)无关联字段，无法追溯执行情况
2. **TPC03 汇总表数据不一致**——应用层维护导致可靠性差
3. **采购订单录入无余额校验**——可超计划采购

## 二、模块命名与职责边界

| 新名称 | 旧名称 | 核心表 | 职责 |
|--------|--------|--------|------|
| 采购需求 | 采购计划 | TPC01/TPC02 | 业务部门提"买什么、买多少"，审批锁定可采购额度 |
| 采购订单 | 采购登记 | TPC12/TPC13 | 采购部门执行"向谁买、什么价"，必须关联来源需求单 |
| 采购结算单 | 采购单据 | TPC14 | 财务结算，含发票/仓库/客户信息 |
| 采购退货 | 采购退货 | TPC16/TPC17 | 退货给供应商，关联原采购订单 |
| 执行看板 | TPC03 汇总 | 视图 | 实时计算，替代 TPC03 应用层维护 |

### 业务概念对应

```
采购需求(PR) ──→ TPC01/TPC02    关注：买什么、买多少
     │  审批通过，锁定可采购额度
     ▼
采购订单(PO) ──→ TPC12/TPC13    关注：向谁买、什么价格、何时交货
     │  关联来源需求单（TPC20）
     ▼
采购结算单    ──→ TPC14         关注：发票、仓库入库、客户
     │
     ▼ （逆向）
采购退货      ──→ TPC16/TPC17   关注：退货原因、数量、关联原订单
```

## 三、数据模型设计

### 3.1 新增：TPC20 需求-订单关联表

```sql
CREATE TABLE tpc20_requisition_order_link (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pcplanid VARCHAR(20) NOT NULL,           -- 来源需求单号
    pclineno INTEGER NOT NULL,               -- 来源需求行号
    rgstbillid VARCHAR(20) NOT NULL,          -- 采购订单号
    rgstlineno INTEGER NOT NULL,              -- 订单行号
    linkqty DECIMAL(12,2) NOT NULL DEFAULT 0, -- 关联数量
    linkstatus VARCHAR(20) DEFAULT 'ordered', -- ordered/partial_in/completed/cancelled
    gendate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upddate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opercd VARCHAR(20),

    CONSTRAINT fk_link_pcplan FOREIGN KEY (pcplanid, pclineno)
        REFERENCES tpc02_pcplandt(pcplanid, lineno) ON DELETE RESTRICT,
    CONSTRAINT fk_link_register FOREIGN KEY (rgstbillid, rgstlineno)
        REFERENCES tpc13_registerdt(rgstbillid, lineno) ON DELETE CASCADE,
    CONSTRAINT uk_link_unique UNIQUE(pcplanid, pclineno, rgstbillid, rgstlineno)
);

CREATE INDEX idx_link_pcplan ON tpc20_requisition_order_link(pcplanid, pclineno);
CREATE INDEX idx_link_register ON tpc20_requisition_order_link(rgstbillid, rgstlineno);
```

**设计要点**：多对多关联，一个需求行可拆分给多个供应商，一个订单可合并多个需求单。

### 3.2 扩展：TPC13 订单明细冗余字段

```sql
ALTER TABLE tpc13_registerdt ADD COLUMN ref_pcplanid VARCHAR(20);
ALTER TABLE tpc13_registerdt ADD COLUMN ref_pclineno INTEGER;
CREATE INDEX idx_registerdt_ref ON tpc13_registerdt(ref_pcplanid, ref_pclineno);
```

冗余设计，提高订单详情页查询效率，避免每次 JOIN TPC20。

### 3.3 调整：TPC16/TPC17 退货表

**已有表增强**，添加关联字段和审核字段：

```sql
-- 关联原采购订单（精确追溯退货来源）
ALTER TABLE tpc16_rpcbill ADD COLUMN ref_rgstbillid VARCHAR(8);
ALTER TABLE tpc17_rpcbilldt ADD COLUMN ref_rgstlineno INTEGER;

-- 审核控制字段（原表缺失，需补充）
ALTER TABLE tpc16_rpcbill ADD COLUMN auditflg CHAR(1) DEFAULT '0';   -- 0=未审批, 1=送审中, 2=已审批, 9=作废
ALTER TABLE tpc16_rpcbill ADD COLUMN auditman CHAR(6);              -- 审核人
ALTER TABLE tpc16_rpcbill ADD COLUMN auditdate TIMESTAMP;            -- 审核日期
```

**字段说明**：
- `ref_rgstbillid` / `ref_rgstlineno`：关联原采购订单行，精确追溯退货来源
- `auditflg`：审核状态控制，审批通过后方可出库退货
- `auditman` / `auditdate`：记录审批责任人及时间，满足审计要求

**业务流程**：
```
创建退货单(auditflg='0') → 提交审核 → 审批通过(auditflg='2') → 仓库出库 → 供应商收货
```

### 3.4 新增视图：v_requisition_execution

```sql
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
WHERE p.useflg = '1';
```

完全替代 TPC03，实时计算执行状态。

### 3.5 新增视图：v_item_requisition_status

```sql
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
HAVING SUM(dt.auditqty) - COALESCE(SUM(link_stats.ordered_qty), 0) > 0;
```

用于采购订单录入时查询有余额的商品及来源需求单。

### 3.6 TPC03 处理

- 即刻起冻结 TPC03，不再写入
- 前端"采购计划执行看板"改为查询 `v_requisition_execution` 视图
- TPC03 表保留不删，标注 `@deprecated`，后续归档

### 3.7 触发器设计（后续参考）

> ⚠️ **暂不做，阶段2后评估**。以下设计草稿供后续参考，用于自动维护数据一致性。

#### 3.7.1 入库后自动更新关联状态

```sql
-- 触发器：采购入库完成后，自动更新 TPC20 关联表状态
CREATE OR REPLACE FUNCTION update_link_status_on_in()
RETURNS TRIGGER AS $$
DECLARE
    v_inqty DECIMAL(12,2);
    v_rgsqty DECIMAL(12,2);
    v_ratio DECIMAL(5,4);
BEGIN
    v_inqty := NEW.inqty;
    v_rgsqty := NEW.rgsqty;
    
    IF v_rgsqty > 0 THEN
        v_ratio := v_inqty / v_rgsqty;
        
        UPDATE tpc20_requisition_order_link
        SET 
            linkstatus = CASE 
                WHEN v_ratio >= 1 THEN 'completed'
                WHEN v_ratio > 0 THEN 'partial_in'
                ELSE 'ordered'
            END,
            upddate = CURRENT_TIMESTAMP
        WHERE rgstbillid = NEW.rgstbillid
          AND rgstlineno = NEW.lineno;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_link_status_on_in
    AFTER UPDATE OF inqty ON tpc13_registerdt
    FOR EACH ROW
    WHEN (OLD.inqty IS DISTINCT FROM NEW.inqty)
    EXECUTE FUNCTION update_link_status_on_in();
```

**作用**：入库完成后自动更新 TPC20 的 `linkstatus`，避免应用层遗漏。

#### 3.7.2 订单创建时校验余额（数据库层兜底）

```sql
-- 触发器：插入 TPC20 时校验采购数量不超过需求余额
CREATE OR REPLACE FUNCTION check_available_qty()
RETURNS TRIGGER AS $$
DECLARE
    v_audit_qty DECIMAL(12,2);
    v_ordered_qty DECIMAL(12,2);
    v_available DECIMAL(12,2);
BEGIN
    -- 查询需求单的审批数量
    SELECT auditqty INTO v_audit_qty
    FROM tpc02_pcplandt
    WHERE pcplanid = NEW.pcplanid AND lineno = NEW.pclineno;
    
    -- 查询已关联的订单数量
    SELECT COALESCE(SUM(linkqty), 0) INTO v_ordered_qty
    FROM tpc20_requisition_order_link
    WHERE pcplanid = NEW.pcplanid 
      AND pclineno = NEW.pclineno
      AND id <> NEW.id;  -- 排除当前记录
    
    v_available := v_audit_qty - v_ordered_qty;
    
    IF NEW.linkqty > v_available THEN
        RAISE EXCEPTION '采购数量(%)超过需求余额(%)', NEW.linkqty, v_available;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_available_qty
    BEFORE INSERT OR UPDATE ON tpc20_requisition_order_link
    FOR EACH ROW
    EXECUTE FUNCTION check_available_qty();
```

**作用**：数据库层强制校验，防止超量采购（应用层校验+数据库层兜底）。

#### 3.7.3 退货时校验退货数量

```sql
-- 触发器：校验退货数量不超过已入库数量
CREATE OR REPLACE FUNCTION check_return_qty()
RETURNS TRIGGER AS $$
DECLARE
    v_inqty DECIMAL(12,2);
    v_returned_qty DECIMAL(12,2);
    v_available DECIMAL(12,2);
BEGIN
    -- 查询原订单的入库数量
    SELECT inqty INTO v_inqty
    FROM tpc13_registerdt
    WHERE rgstbillid = NEW.ref_rgstbillid 
      AND lineno = NEW.ref_rgstlineno;
    
    -- 查询已退货数量
    SELECT COALESCE(SUM(rpcqty), 0) INTO v_returned_qty
    FROM tpc17_rpcbilldt
    WHERE ref_rgstbillid = NEW.ref_rgstbillid
      AND ref_rgstlineno = NEW.ref_rgstlineno;
    
    v_available := v_inqty - v_returned_qty;
    
    IF NEW.rpcqty > v_available THEN
        RAISE EXCEPTION '退货数量(%)超过可退余额(%)', NEW.rpcqty, v_available;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 阶段2后评估是否需要
-- CREATE TRIGGER trg_check_return_qty
--     BEFORE INSERT OR UPDATE ON tpc17_rpcbilldt
--     FOR EACH ROW
--     WHEN (NEW.ref_rgstbillid IS NOT NULL)
--     EXECUTE FUNCTION check_return_qty();
```

**实施建议**：
- **阶段2**：应用层维护关联状态，便于调试和回滚
- **阶段3稳定后**：评估加入触发器，减少应用层负担，强制数据一致性

## 四、API 路由设计

所有路由前缀 `/api/v1/procurement`。

### 4.1 采购需求

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/requisitions` | 需求列表（筛选项：auditflg / pctyp / start_date / end_date） |
| GET | `/requisitions/<pcplanid>` | 需求详情（含执行跟踪） |
| POST | `/requisitions` | 创建需求 |
| POST | `/requisitions/<pcplanid>/audit` | 审核需求 |

### 4.2 采购订单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/orders` | 订单列表 |
| GET | `/orders/<rgstbillid>` | 订单详情（含关联需求信息） |
| POST | `/orders` | 创建订单（必填 ref_pcplanid + ref_pclineno） |
| POST | `/orders/<rgstbillid>/audit` | 审核订单 |
| GET | `/available-items` | 查询可采购商品及来源需求单 |

### 4.3 采购结算单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/settlements` | 结算单列表 |
| GET | `/settlements/<pcbillid>` | 结算单详情 |
| POST | `/settlements` | 创建结算单 |

### 4.4 采购退货

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/returns` | 退货列表 |
| GET | `/returns/<pcbillid>` | 退货详情 |
| POST | `/returns` | 创建退货单（必填 ref_rgstbillid） |

### 4.5 执行看板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dashboard/requisition` | 需求执行看板数据（查询视图） |

### 4.6 采购类型码表 PU

已插入 6 个值：10=计划采购 / 11=补货采购 / 12=订单采购 / 13=紧急采购 / 22=资产采购 / 99=其他

字段 `tpc01_pcplan.pctyp` 和 `tmm12_items.purchasetyp` 已从 String(1) 扩展到 String(2)。

## 五、前端页面设计

### 5.1 页面清单

| 页面 | 路由 | 核心功能 |
|------|------|----------|
| 采购需求列表 | `/procurement/requisitions` | 筛选+列表+新建+审核入口 |
| 采购订单列表 | `/procurement/orders` | 筛选+列表+新建(关联需求) |
| 采购订单录入 | 弹窗/内嵌 | 选择来源需求单 + 数量校验 |
| 采购结算单列表 | `/procurement/settlements` | 列表+详情 |
| 采购退货列表 | `/procurement/returns` | 列表+新建(关联订单) |
| 执行看板 | `/procurement/dashboard` | 统计卡片+商品汇总+逾期预警 |

### 5.2 关键交互

**订单录入时的来源需求选择**：
1. 选择供应商 → 查询该供应商可提供的商品（`v_item_requisition_status`）
2. 弹窗展示可选商品，每行显示"来源需求单 + 计划余额"
3. 采购数量 ≤ 计划余额，系统校验拦截超量
4. 提交时自动写入 TPC20 关联表 + TPC13.ref_pcplanid

**需求详情页的执行跟踪**：
1. 汇总卡片：计划总量 / 已下单 / 已入库 / 完成进度条
2. 明细表格展开行：显示关联的采购订单号、数量、状态

## 六、实施阶段

| 阶段 | 内容 | 预计工作量 |
|------|------|-----------|
| **阶段1** | 命名统一：路由/API/菜单/页面标题/前端函数名 | 1 天 |
| **阶段2** | TPC20 关联表 + 视图 + 迁移 | 1 天 |
| **阶段3** | 后端 API 改造：订单创建关联逻辑 + 余额校验 | 1.5 天 |
| **阶段4** | 前端页面改造：订单录入关联弹窗 + 执行跟踪 | 2 天 |
| **阶段5** | TPC16/TPC17 字段补全 + 退货关联 | 0.5 天 |
| **阶段6** | 执行看板页面 | 1 天 |

## 七、暂不做的事项

- 触发器自动更新关联状态（阶段2先通过应用层维护，后续可加）
- 历史数据 PP-PR 关联追溯（仅影响旧数据，非核心流程）
- TPC03 数据修复（直接冻结，用视图替代）
- 采购结算单详细功能（保留模块但暂不增强）

---

**评审记录**

- [ ] 技术评审
- [ ] 业务评审



%%  %%