# 设备 install_date 初始化与追踪 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 回填 install_date + 扩展 EidTrack 12字段 + ETK码表入库

**Spec:** `docs/superpowers/specs/2026-05-12-device-install-date-tracking.md`

**Architecture:** 纯数据层任务，不涉及API/Service变更。EidTrack 沿用现有 old→new 字段模式。

---

### 任务 1：ETK 码表 + EidTrack 扩展 + 模型更新

- [ ] **1.1 插入 ETK 码表**

```sql
INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, created_at, updated_at) VALUES
('ETK', 'A', '属性变更', '1', 1, now(), now()),
('ETK', 'C', '客户分配', '1', 2, now(), now()),
('ETK', 'R', '回收',   '1', 3, now(), now()),
('ETK', 'T', '客户转移', '1', 4, now(), now());
```

- [ ] **1.2 EidTrack 加 12 列**

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

验证：
```bash
psql -U cheungjan -d myitsm -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='tmm43_eid_track' AND column_name LIKE '%install%' OR column_name LIKE '%cust_cd%' OR column_name LIKE '%asset_type%';"
```

- [ ] **1.3 更新 EidTrack 模型**

`app/models/master.py` — EidTrack 类新增 12 字段：

```python
install_date = db.Column(db.DateTime, comment="安装日期")
n_install_date = db.Column(db.DateTime, comment="新安装日期")
cust_cd = db.Column(db.String(20), comment="变更前客户")
n_cust_cd = db.Column(db.String(20), comment="变更后客户")
asset_type = db.Column(db.String(10), comment="资产类型")
n_asset_type = db.Column(db.String(10), comment="新资产类型")
recyclable = db.Column(db.String(1), comment="可回收标志")
n_recyclable = db.Column(db.String(1), comment="新可回收标志")
recycle_status = db.Column(db.String(10), comment="回收状态")
n_recycle_status = db.Column(db.String(10), comment="新回收状态")
asset_owner = db.Column(db.String(20), comment="资产所属方")
n_asset_owner = db.Column(db.String(20), comment="新资产所属方")
```

- [ ] **1.4 Commit**

```bash
git add app/models/master.py
git commit -m "feat(eidtrack): add 12 asset/customer tracking columns to model"
```

---

### 任务 2：install_date 四级回填

- [ ] **2.1 第1级：plan_cust.imple_date**

```sql
UPDATE tmm43_eid e SET install_date = p.imple_date
FROM tmm35_cust_pos_rl r JOIN plan_cust p ON r.cust_cd = p.custcd AND p.status = '1'
WHERE e.eid = r.eid AND r.useflg = '1' AND e.install_date IS NULL AND p.imple_date IS NOT NULL;
```

- [ ] **2.2 第2级：customers.opendate**

```sql
UPDATE tmm43_eid e SET install_date = c.opendate
FROM tmm35_cust_pos_rl r JOIN tmm22_customers c ON r.cust_cd = c.cust_cd
WHERE e.eid = r.eid AND r.useflg = '1' AND e.install_date IS NULL AND c.opendate IS NOT NULL;
```

- [ ] **2.3 第3级：customers.replacedate**

```sql
UPDATE tmm43_eid e SET install_date = c.replacedate
FROM tmm35_cust_pos_rl r JOIN tmm22_customers c ON r.cust_cd = c.cust_cd
WHERE e.eid = r.eid AND r.useflg = '1' AND e.install_date IS NULL AND c.replacedate IS NOT NULL;
```

- [ ] **2.4 第4级：plan_cust.gendate（兜底）**

```sql
UPDATE tmm43_eid e SET install_date = p.gendate
FROM tmm35_cust_pos_rl r JOIN plan_cust p ON r.cust_cd = p.custcd AND p.status = '1'
WHERE e.eid = r.eid AND r.useflg = '1' AND e.install_date IS NULL AND p.gendate IS NOT NULL;
```

- [ ] **2.5 验证**

```bash
psql -U cheungjan -d myitsm -c "SELECT COUNT(*) AS filled FROM tmm43_eid WHERE install_date IS NOT NULL;"
psql -U cheungjan -d myitsm -c "SELECT COUNT(*) AS still_null FROM tmm43_eid WHERE install_date IS NULL;"
```

Expected: filled > 0, still_null = 库存设备数

- [ ] **2.6 Commit**

```bash
git commit -m "data: backfill install_date with 4-level priority strategy" --allow-empty
```

---

### 任务 3：API 验证

- [ ] **3.1 验证资产 API 返回 install_date**

```bash
TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/login -H 'Content-Type: application/json' -d '{"user_id":"admin","password":"admin123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")
curl -s "http://localhost:5001/api/v1/assets?location=customer&per_page=1" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
r=json.load(sys.stdin)['data']['items'][0]
print(f'install_date={r.get(\"install_date\",\"MISSING\")}')
"
```

Expected: 有日期值，非 NULL

---

### 任务 4：前端验证

- [ ] **4.1 资产详情弹窗 install_date 非空显示**

打开 `/master/assets`，筛选"客户设备"，点击详情，确认"安装日期"有值。
