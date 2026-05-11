# 系统参数清理与重新规划 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 清理 tmc71_sysparm 零售遗留参数，新增 ITSM 全局参数，前端改为 3 分组表单。

**Spec:** `docs/superpowers/specs/2026-05-11-sysparm-cleanup.md`

**Status:** ✅ 已实施完成（2026-05-11）

---

### 步骤 1：后端模型与数据库变更

- [x] **1.1 修改后端模型（新增3个字段）**

`app/models/system.py` SysParm 类新增：
```python
jwt_expiration_seconds = db.Column(db.Integer, default=28800, comment="JWT超时(秒)")
log_retention_days = db.Column(db.Integer, default=30, comment="日志保留天数")
max_upload_size_mb = db.Column(db.Integer, default=10, comment="上传大小限制(MB)")
```

- [x] **1.2 创建 Alembic 迁移脚本**

```bash
uv run flask db migrate -m "add_jwt_log_upload_sysparm_cols"
```
生成：`migrations/versions/db6aef9f5043_add_jwt_log_upload_sysparm_cols.py`

- [x] **1.3 执行数据库迁移**

```bash
uv run flask db upgrade
```

- [x] **1.4 更新 parm_desc 标记废弃字段**

```sql
UPDATE tmc71_sysparm SET parm_desc = '[已废弃-零售业务遗留] ' || COALESCE(parm_desc, '');
```

- [x] **1.5 填默认值**

```sql
UPDATE tmc71_sysparm SET jwt_expiration_seconds=28800, log_retention_days=30, max_upload_size_mb=10;
```

---

### 步骤 2：前端页面更新

- [x] **2.1 重写 ParamsList.vue**

废弃 5 个零售字段（costtype/centralwarehouse/poinvaliddays/soinvaliddays/shopbilltype）。
6 个有效参数分 3 组：

| 分组 | 字段 | 控件 |
|------|------|------|
| 认证安全 | allowmultilogon, jwt_expiration_seconds | switch, number |
| 系统运维 | log_retention_days, max_upload_size_mb | number ×2 |
| 路径配置 | autobackpath, invoicesharepath | text ×2 |

- [x] **2.2 验证 HMR**

```bash
tail -1 /tmp/vite.log | grep hmr
```

---

### 步骤 3：测试验证

- [x] **3.1 API 测试**

```bash
TOKEN=... 
curl -X PUT /sysparms/SYSPARM -d '{"jwt_expiration_seconds":3600}' → 200
```

- [x] **3.2 页面验证**

打开 `/system/params`：3 组 6 字段，无零售参数，修改保存生效

---

**改动清单：**

| 文件 | 改动 |
|------|------|
| `app/models/system.py` | SysParm 加 3 列 |
| `migrations/versions/db6aef9f5043_*.py` | DDL 迁移 |
| `frontend/src/views/system/ParamsList.vue` | 6 字段 3 分组 |