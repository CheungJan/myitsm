# 资产台账功能优化 Spec

> **Status**: 待审核 | **参考**: PB base_cust.pbl, asset-ledger-bom-redesign-0925ee.md

## 背景

当前 `/master/assets` 只有 5 列纯列表 + 分页，无筛选/详情/编辑。CustPosRl 模型已扩展但资产属性放错位置，需迁至 `tmm43_eid`。

## 核心决策：资产属性归属

**资产属性 → `tmm43_eid`（设备固有）**，`tmm35_cust_pos_rl` 精简为客户关系表。

| 字段 | 归属表 | 原因 |
|------|--------|------|
| `asset_type` | tmm43_eid | 设备固有 |
| `recyclable` | tmm43_eid | 设备固有 |
| `recycle_status` | tmm43_eid | 设备固有 |
| `asset_owner` | tmm43_eid | 设备固有（制造商/客户） |
| `install_date` | tmm43_eid | 设备安装历史 |
| `cust_cd` | tmm35_cust_pos_rl | 客户关系 |
| `sysinfo/softinfo` | tmm35_cust_pos_rl | 保留原位置 |

`CustPosRl` 现有资产字段（asset_type/recyclable/recycle_status/install_date）将在迁移后删除。

## 目标

左侧客户分组树 + 右侧设备表格（含 BOM 展开） + 顶部筛选 + 详情/编辑弹窗。

## 不做

- 资产类型树（asset_type 全库 NULL，等 EID 初始化后加）
- EID 资产属性存量初始化（独立数据任务）
- Edit/Delete 对 CustPosRl 关系记录的变更（本轮只做 Eid 资产属性编辑）

---

## 设计

### 左侧：客户分组树

复用 `tmm21_custclass` 树（`GET /custclasses/tree`）。点击节点 → 查该分类下所有客户的设备。

### 右侧：设备表格

**未选中客户**：所有客户的所有设备，每个 EID 一行

| 列 | 字段 | 来源 |
|----|------|------|
| 设备 SN | eid | CustPosRl |
| 商品名 | item_nm | tmm12_items |
| 客户名 | cust_nm | tmm22_customers |
| 管理单位 | parentcd_nm | tmm22_customers.parentcd → tmm21_custclass.class_nm |
| 资产类型 | asset_type | **tmm43_eid** |
| 回收状态 | recycle_status | **tmm43_eid** |
| 资产所属方 | asset_owner | **tmm43_eid** → AO 码表 |
| 生产日期 | prddate | tmm43_eid |
| 仓库 | whcd | tmm43_eid |
| 操作 | 详情/编辑 | — |

**选中客户后**：展示该客户的整机（BOM 展开行），通过 `tmm44_pos_r_eid` 关联配件。

### 顶部筛选栏

- 搜索（SN/客户名/物料名）
- 资产类型（AT 码表）
- 回收状态（RS 码表）
- 资产所属方（AO 码表）

### 详情弹窗（7 组）

| 分组 | 字段 |
|------|------|
| 基础信息 | eid, item_nm, cust_nm, parentcd_nm |
| 资产属性 | asset_type, recyclable, recycle_status, asset_owner, install_date |
| 机型信息 | itemcd, item_nm, item_anm, itemsize, wunit（tmm12_items） |
| 序列号信息 | eid, itemtyp, prddate, whcd, qcflg, refid, sflg, etyp, new_old, isunit（tmm43_eid） |
| 配件明细 | 通过 tmm44_pos_r_eid 关联（posid→eid），显示配件编码/名称/SN/规格 |
| 软件信息 | sysinfo, softinfo（tmm35_cust_pos_rl） |
| 运维信息 | status, posupddate, maintenancedate |

### 编辑弹窗

可编辑：`asset_type`, `recyclable`, `recycle_status`, `asset_owner`（仅admin）, `install_date`（操作 tmm43_eid 表）

---

## 模型变更

### tmm43_eid（新增 5 列）

```python
asset_type = db.Column(db.String(10), comment="资产类型（AT码表）")
recyclable = db.Column(db.Boolean, default=False, comment="可回收标志")
recycle_status = db.Column(db.String(10), comment="回收状态（RS码表）")
asset_owner = db.Column(db.String(10), default="CUSTOMER", comment="资产所属方（AO码表）")
install_date = db.Column(db.DateTime, comment="安装日期")
```

### tmm35_cust_pos_rl（删除资产字段）

```python
# 以下字段将从模型中移除（数据已迁至 tmm43_eid）：
# asset_type, recyclable, recycle_status, install_date
```

### tmm44_pos_r_eid（新增模型）

```python
class PosREid(BaseModel):
    """POS与EID关联表（TMM44_POS_R_EID）— 整机与配件父子关系。"""
    __tablename__ = "tmm44_pos_r_eid"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    posid = db.Column(db.String(50), comment="整机POS编码（关联 CustPosRl.eid）")
    eid = db.Column(db.String(50), comment="配件EID（关联 tmm43_eid.eid）")
    useflg = db.Column(db.String(1), default="1")
```

---

## 关联查询 JOIN 逻辑

```sql
SELECT
    r.id, r.eid, r.cust_cd, r.item_cd,
    r.sysinfo, r.softinfo, r.posupddate, r.status, r.maintenancedate,
    c.cust_nm, c.class_cd, c.parentcd,
    i.item_nm,
    e.asset_type, e.recyclable, e.recycle_status, e.asset_owner, e.install_date,
    e.prddate, e.whcd, e.qcflg, e.refid, e.sflg, e.etyp, e.new_old, e.isunit,
    cc.class_nm AS cust_class_nm,
    cc_parent.class_nm AS parentcd_nm
FROM tmm35_cust_pos_rl r
LEFT JOIN tmm22_customers c ON r.cust_cd = c.cust_cd
LEFT JOIN tmm12_items i ON r.item_cd = i.item_cd
LEFT JOIN tmm43_eid e ON r.eid = e.eid
LEFT JOIN tmm21_custclass cc ON c.class_cd = cc.class_cd
LEFT JOIN tmm21_custclass cc_parent ON TRIM(c.parentcd) = cc_parent.class_cd
WHERE r.useflg = '1'
  AND (c.class_cd IN (:class_cds))
  AND (r.eid ILIKE :search OR c.cust_nm ILIKE :search)
  AND (e.asset_type = :asset_type)
ORDER BY r.id
```

---

## 系统字典配置

### AO — 资产所属方

| code_cd | code_nm |
|---------|---------|
| '01' | 制造商 |
| '02' | 客户 |

### AT — 资产类型

| code_cd | code_nm | 说明 |
|---------|---------|------|
| '01' | 新机 | asset_type=NEW |
| '02' | 旧机 | asset_type=USED |
| '03' | 翻新机 | asset_type=REFURB |
| '04' | 报废 | asset_type=SCRAP |

### RS — 回收状态

| code_cd | code_nm | 说明 |
|---------|---------|------|
| '01' | 无需回收 | - |
| '02' | 待回收 | PENDING |
| '03' | 已回收 | RECYCLED |
| '04' | 已报废 | SCRAPPED |

全量 SQL 见实施计划。

---

## 数据初始化

```sql
-- 1. tmm43_eid 加 5 列 + 迁移
ALTER TABLE tmm43_eid ADD COLUMN asset_type VARCHAR(10);
ALTER TABLE tmm43_eid ADD COLUMN recyclable BOOLEAN DEFAULT false;
ALTER TABLE tmm43_eid ADD COLUMN recycle_status VARCHAR(10);
ALTER TABLE tmm43_eid ADD COLUMN asset_owner VARCHAR(10) DEFAULT 'CUSTOMER';
ALTER TABLE tmm43_eid ADD COLUMN install_date TIMESTAMP;

-- 2. 从 CustPosRl 回填到 Eid（按 eid 匹配）
UPDATE tmm43_eid e SET
    asset_type = r.asset_type,
    recyclable = r.recyclable,
    recycle_status = r.recycle_status,
    install_date = r.install_date
FROM tmm35_cust_pos_rl r
WHERE e.eid = r.eid;

-- 3. 资产所属方初始化（通过 cust_cd 关联 plan_cust + deposit）
UPDATE tmm43_eid e SET asset_owner = 'MANUFACTURER', recyclable = true
FROM tmm35_cust_pos_rl r
WHERE e.eid = r.eid
  AND (EXISTS (SELECT 1 FROM plan_cust p WHERE p.custcd = r.cust_cd AND p.is_rent = '1' AND p.status = '1')
    OR EXISTS (SELECT 1 FROM tmm61_deposit d WHERE d.custcd = r.cust_cd AND d.amount_money > 0));
```

---

## 影响的现有代码

| 文件 | 引用 | 处理 |
|------|------|------|
| `models/master.py:242-252` | CustPosRl.asset_type/recyclable/recycle_status/install_date | 删除 |
| `models/master.py` Eid | 无资产字段 | 新增 5 列 |
| `frontend/AssetList.vue:16,18` | asset_type/install_date 表格列 | 整体重写 |
| `models/itsm.py:928` | asset_type（同名但无关） | 不动 |

无其他代码引用这四个资产字段。

---

## 后端改动

| 端点 | 变更 |
|------|------|
| `GET /assets` | 扩展参数 + JOIN tmm43_eid |
| `GET /assets/<id>` | 新增：单条详情（含 EID 资产字段） |
| `PUT /assets/<id>` | 新增：更新 tmm43_eid 资产属性 |
| `GET /assets/bom?cust_cd=` | 新增：按客户查 BOM |

---

## 前端改动

| 文件 | 改动 |
|------|------|
| `api/master.ts` | 加 `fetchAssetById`, `updateAsset`, `fetchAssetBom` |
| `views/master/AssetList.vue` | 重写：左树右表 + 展开BOM + 详情/编辑弹窗 |

---

## 权限控制

| 操作 | 运维人员 | 资产管理员 |
|------|:--:|:--:|
| 查看列表/详情/BOM | ✅ | ✅ |
| 编辑资产属性 | ❌ | ✅ `hasPerm('assets','edit')` |
| 编辑 asset_owner | ❌ | ✅ 仅 admin |

---

## 错误处理

沿用全局约定：`IntegrityError`→409, `DataError`→400, 前端 `ElMessage.error`。

---

## 验证

1. 左侧树点击客户分类 → 右侧过滤
2. 搜索 SN → 全局搜索
3. 详情弹窗显示 EID 资产字段 + 客户/物料解析名
4. 编辑 asset_type → PUT /assets/<id> → 刷新保持
5. BOM 接口返回正确的主机-配件关系
