# 设备安装日期初始化与追踪 Spec

> **Status**: 待实施 | **参考**: device-install-date-history-tracking-0925ee.md

## 背景

`tmm43_eid.install_date` 全库 NULL（165,550条），需回填并建立追踪机制。

## 目标

1. 回填 install_date（四级优先级）
2. 扩展 EidTrack 支持设备流转追踪（12字段）
3. type 码表入库

## 不做

- 业务流程自动更新（阶段2）
- CustPosRl 字段删除（已完成）

---

## 设计

### install_date 初始化（四级优先级）

```sql
-- 1. plan_cust.imple_date（预计划实施时间，最精确）
UPDATE tmm43_eid e SET install_date = p.imple_date
FROM tmm35_cust_pos_rl r JOIN plan_cust p ON r.cust_cd = p.custcd AND p.status = '1'
WHERE e.eid = r.eid AND r.useflg = '1' AND e.install_date IS NULL AND p.imple_date IS NOT NULL;

-- 2. customers.opendate（客户首次开通）
UPDATE tmm43_eid e SET install_date = c.opendate
FROM tmm35_cust_pos_rl r JOIN tmm22_customers c ON r.cust_cd = c.cust_cd
WHERE e.eid = r.eid AND r.useflg = '1' AND e.install_date IS NULL AND c.opendate IS NOT NULL;

-- 3. customers.replacedate（最后更换）
UPDATE tmm43_eid e SET install_date = c.replacedate
FROM tmm35_cust_pos_rl r JOIN tmm22_customers c ON r.cust_cd = c.cust_cd
WHERE e.eid = r.eid AND r.useflg = '1' AND e.install_date IS NULL AND c.replacedate IS NOT NULL;

-- 4. plan_cust.gendate（兜底）
UPDATE tmm43_eid e SET install_date = p.gendate
FROM tmm35_cust_pos_rl r JOIN plan_cust p ON r.cust_cd = p.custcd AND p.status = '1'
WHERE e.eid = r.eid AND r.useflg = '1' AND e.install_date IS NULL AND p.gendate IS NOT NULL;
```

### EidTrack 扩展（12 字段）

```sql
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS install_date TIMESTAMP;
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS n_install_date TIMESTAMP;
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS cust_cd VARCHAR(20);
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS n_cust_cd VARCHAR(20);
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS asset_type VARCHAR(10);
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS n_asset_type VARCHAR(10);
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS recyclable VARCHAR(1);
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS n_recyclable VARCHAR(1);
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS recycle_status VARCHAR(10);
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS n_recycle_status VARCHAR(10);
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS asset_owner VARCHAR(20);
ALTER TABLE tmm43_eid_track ADD COLUMN IF NOT EXISTS n_asset_owner VARCHAR(20);
```

### type 码表

| code_cd | code_nm | 说明 |
|---------|---------|------|
| A | 属性变更 | asset_type/owner 等变更 |
| C | 客户分配 | 从库存分配到客户 |
| R | 回收 | 从客户回收回库存 |
| T | 客户转移 | 从客户A转移到客户B |

```sql
INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, created_at, updated_at) VALUES
('ETK', 'A', '属性变更', '1', 1, now(), now()),
('ETK', 'C', '客户分配', '1', 2, now(), now()),
('ETK', 'R', '回收',   '1', 3, now(), now()),
('ETK', 'T', '客户转移', '1', 4, now(), now());
```

---

## 验证

1. `SELECT COUNT(*) FROM tmm43_eid WHERE install_date IS NOT NULL` — >0
2. `SELECT type, COUNT(*) FROM tmm43_eid_track` — 含 ETK 条目
3. 资产详情 install_date 非空显示
