# 资产台账功能优化 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 资产台账改为左客户树 + 右设备表格（含BOM）+ 详情/编辑弹窗，资产属性迁至 tmm43_eid。

**Spec:** `docs/superpowers/specs/2026-05-11-asset-ledger-redesign.md`

**Architecture:** 资产属性从 CustPosRl 迁至 Eid 表；新增 tmm44_pos_r_eid 模型处理 BOM 关系。

---

### 任务 1：系统字典 — AT/RS/AO 码表

- [ ] **1.1 插入码表数据**

```sql
INSERT INTO tmm31_syscodes (code_typ, code_cd, code_nm, useflg, sort_no, created_at, updated_at) VALUES
('AO', '01', '制造商',   '1', 1, now(), now()),
('AO', '02', '客户',     '1', 2, now(), now()),
('AT', '01', '新机',     '1', 1, now(), now()),
('AT', '02', '旧机',     '1', 2, now(), now()),
('AT', '03', '翻新机',   '1', 3, now(), now()),
('AT', '04', '报废',     '1', 4, now(), now()),
('RS', '01', '无需回收', '1', 1, now(), now()),
('RS', '02', '待回收',   '1', 2, now(), now()),
('RS', '03', '已回收',   '1', 3, now(), now()),
('RS', '04', '已报废',   '1', 4, now(), now());
```

---

### 任务 2：数据库 — EID 加资产列 + 回填 + CustPosRl 清理

- [ ] **2.1 tmm43_eid 新增 5 列 + tmm44_pos_r_eid 建表**

```sql
ALTER TABLE tmm43_eid ADD COLUMN IF NOT EXISTS asset_type VARCHAR(10);
ALTER TABLE tmm43_eid ADD COLUMN IF NOT EXISTS recyclable BOOLEAN DEFAULT false;
ALTER TABLE tmm43_eid ADD COLUMN IF NOT EXISTS recycle_status VARCHAR(10);
ALTER TABLE tmm43_eid ADD COLUMN IF NOT EXISTS asset_owner VARCHAR(10) DEFAULT 'CUSTOMER';
ALTER TABLE tmm43_eid ADD COLUMN IF NOT EXISTS install_date TIMESTAMP;

CREATE TABLE IF NOT EXISTS tmm44_pos_r_eid (
    id SERIAL PRIMARY KEY,
    posid VARCHAR(50),
    eid VARCHAR(50),
    useflg VARCHAR(1) DEFAULT '1',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

- [ ] **2.2 从 CustPosRl 回填资产属性到 Eid**

```sql
UPDATE tmm43_eid e SET asset_type = r.asset_type, recyclable = r.recyclable,
    recycle_status = r.recycle_status, install_date = r.install_date
FROM tmm35_cust_pos_rl r WHERE e.eid = r.eid;
```

- [ ] **2.3 资产所属方初始化（制造商判断）**

```sql
UPDATE tmm43_eid e SET asset_owner = 'MANUFACTURER', recyclable = true
FROM tmm35_cust_pos_rl r WHERE e.eid = r.eid
  AND (EXISTS (SELECT 1 FROM plan_cust p WHERE p.custcd = r.cust_cd AND p.is_rent = '1' AND p.status = '1')
    OR EXISTS (SELECT 1 FROM tmm61_deposit d WHERE d.custcd = r.cust_cd AND d.amount_money > 0));
```

- [ ] **2.4 验证**

```bash
psql -U cheungjan -d myitsm -c "SELECT asset_owner, COUNT(*) FROM tmm43_eid GROUP BY asset_owner;"
psql -U cheungjan -d myitsm -c "\d tmm44_pos_r_eid"
```

---

### 任务 3：模型更新 — Eid 加字段 + PosREid 新模型 + CustPosRl 删字段

- [ ] **3.1 Eid 模型新增 5 个资产字段**

`app/models/master.py` — `Eid` 类新增：

```python
asset_type = db.Column(db.String(10), comment="资产类型（AT码表）")
recyclable = db.Column(db.Boolean, default=False, comment="可回收标志")
recycle_status = db.Column(db.String(10), comment="回收状态（RS码表）")
asset_owner = db.Column(db.String(10), default="CUSTOMER", comment="资产所属方（AO码表）")
install_date = db.Column(db.DateTime, comment="安装日期")
```

- [ ] **3.2 新增 PosREid 模型**

`app/models/master.py` — 新增类：

```python
class PosREid(BaseModel):
    """POS与EID关联表（TMM44_POS_R_EID）。"""
    __tablename__ = "tmm44_pos_r_eid"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    posid = db.Column(db.String(50), comment="整机POS编码")
    eid = db.Column(db.String(50), comment="配件EID")
    useflg = db.Column(db.String(1), default="1")
```

- [ ] **3.3 CustPosRl 删除资产字段**

移除 `asset_type`, `recyclable`, `recycle_status`, `install_date` 四列。

- [ ] **3.4 Commit**

---

### 任务 4：Repository — JOIN tmm43_eid + BOM 查询

**文件:** `app/repositories/system_repository.py`

- [ ] **4.1 增强 `get_cust_pos_rl`，JOIN tmm43_eid**

在 Task 2 的 JOIN 基础上，增加 `LEFT JOIN tmm43_eid e ON r.eid = e.eid`，SELECT 列表加 `e.asset_type, e.recyclable, e.recycle_status, e.asset_owner, e.install_date, e.prddate, e.whcd, e.qcflg`。

- [ ] **4.2 新增 `get_asset_by_id` 和 `update_asset`**（操作 tmm43_eid）

```python
@staticmethod
def get_asset_detail(asset_id: int) -> dict | None:
    """资产详情，含 EID + Item + Customer 全字段。"""
    r = db.session.get(CustPosRl, asset_id)
    if not r: return None
    d = r.to_dict()
    if r.eid:
        e = db.session.get(Eid, (r.item_cd, r.eid))
        if e: d.update({k: v for k, v in e.to_dict().items() if k not in d})
    if r.item_cd:
        item = db.session.get(Item, r.item_cd)
        if item: d["item_nm"] = item.item_nm
    return d

@staticmethod
def update_asset_eid(itemcd: str, eid: str, data: dict) -> Eid | None:
    """更新 tmm43_eid 资产属性。"""
    e = db.session.get(Eid, (itemcd, eid))
    if e:
        for k, v in data.items(): setattr(e, k, v)
        db.session.commit()
    return e
```

- [ ] **4.3 Commit**

---

### 任务 5：Service — 详情 + 更新

- [ ] **5.1 `get_asset` 和 `update_asset`**

```python
def get_asset(self, asset_id: int) -> dict | None:
    return self._repo.get_asset_detail(asset_id)

def update_asset(self, itemcd: str, eid: str, data: dict) -> dict | None:
    e = self._repo.update_asset_eid(itemcd, eid, data)
    return e.to_dict() if e else None
```

---

### 任务 6：API — 扩展列表 + 详情/更新 + BOM

- [ ] **6.1 更新端点**

`GET /assets` — 加 `class_cd`, `search`, `asset_type` 参数
`GET /assets/<id>` — 详情（含 EID 资产属性）
`PUT /assets/<id>` — 更新 tmm43_eid 资产属性（asset_owner 仅 admin）

- [ ] **6.2 验证**

```bash
curl "GET /assets?per_page=2" → 含 eid/asset_type/cust_nm/item_nm
curl "PUT /assets/1" -d '{"asset_type":"01"}' → 200
```

---

### 任务 7：前端 — API + 页面重写

- [ ] **7.1 `api/master.ts`** — 加 `fetchAssetById`, `updateAsset`
- [ ] **7.2 `AssetList.vue`** — 左树右表 + 详情/编辑弹窗 + 7 分组 + AT/RS/AO 码表下拉

---

### 任务 8：文档更新

- [ ] **8.1 API 文档** — 加 GET/PUT /assets/<id>
