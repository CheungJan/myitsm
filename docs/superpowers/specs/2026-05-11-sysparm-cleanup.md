# 系统参数清理与重新规划 Spec

> **Status**: 待实施 | **参考**: `sysparm-cleanup-0925ee.md`

## 背景

`tmc71_sysparm` 中 6 个已实现参数有 5 个是零售业务遗留，ITSM 不需要。需清理并重新规划 ITSM 全局参数。

## 目标

1. 标记 5 个零售字段为废弃，前端隐藏
2. 保留 + 新增 4 个 ITSM 全局参数
3. 前端只展示有效的 ITSM 参数

## 不做

- 删除废弃列（保留表结构）
- 改动后端 API/Service/Repository（`setattr` 已动态处理）
- 触及其他模块

---

## 设计

### 参数清单

**保留（ITSM 全局）：**

| 参数 | 控件 | 默认值 | 说明 |
|------|------|--------|------|
| `allowmultilogon` | switch | 1 | 多点登录 |
| `autobackpath` | text | — | 自动备份路径 |
| `invoicesharepath` | text | — | 发票共享路径 |

**新增（ITSM 全局）：**

| 参数 | 控件 | 类型 | 默认值 |
|------|------|------|--------|
| `jwt_expiration_seconds` | number | Integer | 28800 |
| `log_retention_days` | number | Integer | 30 |
| `max_upload_size_mb` | number | Integer | 10 |

**废弃（零售遗留，前端隐藏）：**
`costtype`, `centralwarehouse`, `poinvaliddays`, `soinvaliddays`, `shopbilltype`

### 后端

**Model**: `SysParm` 新增 3 列
```python
jwt_expiration_seconds = db.Column(db.Integer, default=28800, comment="JWT超时(秒)")
log_retention_days = db.Column(db.Integer, default=30, comment="日志保留天数")
max_upload_size_mb = db.Column(db.Integer, default=10, comment="上传大小限制(MB)")
```

Alembic 迁移自动生成。API/Service/Repository **无需改动**（`setattr` 动态处理任意字段名）。

### 前端

**ParamsList.vue** 改为展示 6 个有效参数（3 保留 + 3 新增），3 个分组：

```
[认证安全]
  允许多点登录      [switch]

[系统运维]
  JWT会话超时(秒)    [number]
  日志保留天数       [number]
  文件上传限制(MB)   [number]

[路径配置]
  自动备份路径       [text]
  发票共享路径       [text]
```

隐藏废弃字段不渲染。

### 数据

存量记录无需迁移——废弃列保留原值不读取，新列用默认值填充。

---

## 改动文件

| 文件 | 改动 |
|------|------|
| `app/models/system.py` | SysParm 加 3 列 |
| `frontend/src/views/system/ParamsList.vue` | 6 字段分组表单 |

生成 Alembic 迁移后 `migrations/versions/` 新增 1 个文件。

---

## 验证

1. `curl -X PUT /sysparms/SYSPARM -d '{"jwt_expiration_seconds":3600}'` → 200
2. 系统参数页面显示 6 个字段，废弃 5 个不渲染
3. 修改参数值 → 保存 → 刷新 → 值保持
