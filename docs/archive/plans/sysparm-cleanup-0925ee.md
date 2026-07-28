# 系统参数清理与重新规划

本计划旨在清理 `tmc71_sysparm` 表中的零售业务遗留参数，重新规划 ITSM 业务所需的全局参数，并更新前端系统参数页面。

## 问题分析

**根因：** ITSM 系统基于原终端销售系统代码修改，导致 `tmc71_sysparm` 表保留了零售业务参数，但 ITSM 设备管理业务实际不使用。

**当前参数分类：**

| 参数 | 业务领域 | ITSM是否需要 | 处理方案 |
|------|---------|------------|---------|
| `allowmultilogon` | 认证登录 | ✅ 是 | 保留 |
| `costtype` | 零售业务成本核算 | ❌ 否 | 列标记为废弃 |
| `centralwarehouse` | 零售业务配货 | ❌ 否 | 列标记为废弃 |
| `poinvaliddays` | 零售业务采购 | ❌ 否 | 列标记为废弃 |
| `soinvaliddays` | 零售业务销售 | ❌ 否 | 列标记为废弃 |
| `shopbilltype` | 零售业务门店 | ❌ 否 | 列标记为废弃 |
| `autobackpath` | 通用备份路径 | ✅ 是 | 保留（前端可编辑） |
| `invoicesharepath` | 发票共享路径 | ✅ 是 | 保留（前端可编辑） |

## 实施步骤

### 步骤 1：重新定义全局系统参数 vs 模块级配置

**原则：**
- **全局系统参数**：跨模块共享、系统级别的配置，放在 `tmc71_sysparm`
- **模块级配置**：各模块自己的业务配置，放在各模块的配置表

**全局系统参数（应放在 `tmc71_sysparm`，前端可编辑，管理员权限）：**
- `allowmultilogon` - 多点登录控制（已实现）
- `autobackpath` - 自动备份路径（已有字段，复用）
- `invoicesharepath` - 发票共享路径（已有字段，复用）
- `jwt_expiration_seconds` - JWT 会话超时时间（待新增）
- `log_retention_days` - 系统日志保留天数（待新增）
- `max_upload_size_mb` - 文件上传大小限制（待新增）

**模块级配置（应放在各模块自己的配置表）：**
- IoT 设备心跳间隔 → IoT 模块配置表（`TIO01_DEVICE_CONN` 已有）
- SLA 响应时间等级 → SLA 模块配置表（`TIT01_TIMEPOINT_AREA` 已有）
- 库存预警阈值 → 库存模块配置表（`TIV01_INVLIMIT` 已有）
- 维护单归档规则 → ITSM 模块配置表（`TIT04_ARCHIVECODE` 已有）
- 免责条例 → ITSM 模块配置表（`TIT02_LIABILITYREG` 已有）
- 设备保修期 → 可在设备表或新增配置表
- 通知配置 → 通知模块配置表

### 步骤 2：数据库层面处理

**数据库现状：**
- `tmc71_sysparm` 表有一条记录（`parm_cd='SYSPARM'`）
- **零售业务遗留参数（当前有值，需标记废弃，前端不展示）：**
- `costtype` = 2（先进先出）
- `centralwarehouse` = 99
- `poinvaliddays` = 18（采购失效天数）
- `soinvaliddays` = 17（销售失效天数）
- `shopbilltype` = 1

**选项 A：保留表结构，标记废弃**
- 在 `parm_desc` 字段标注 `[已废弃-零售业务遗留]`
- 前端过滤掉标记为废弃的参数

**选项 B：删除废弃列**
- 删除 `costtype`、`centralwarehouse`、`poinvaliddays`、`soinvaliddays`、`shopbilltype`、`invoicesharepath` 列
- 需要数据库迁移脚本

**推荐选项 A**：保留表结构，标记废弃，避免破坏性变更。（已确认采用）

### 步骤 2.1：后端模型新增字段

修改 `app/models/system.py` 中的 `SysParm` 模型，新增以下字段：
- `jwt_expiration_seconds` - JWT 会话超时时间（秒），类型：Integer，默认值：28800（8小时）
- `log_retention_days` - 系统日志保留天数，类型：Integer，默认值：30
- `max_upload_size_mb` - 文件上传大小限制（MB），类型：Integer，默认值：10

**后端API/Service/Repository层无需修改**：
- 现有的 `PUT /api/v1/sysparms/<parm_cd>` API 已支持动态字段更新
- `SystemService.update_sysparm()` 方法使用 `setattr(r, k, v)` 动态更新任意字段
- `SystemRepository.update_sysparm()` 方法已支持动态字段更新

### 步骤 3：更新前端系统参数页面

修改 `frontend/src/views/system/ParamsList.vue`：
- 展示全局系统参数：`allowmultilogon`, `autobackpath`, `invoicesharepath`
- 新增参数字段：`jwt_expiration_seconds`, `log_retention_days`, `max_upload_size_mb`
- 隐藏零售业务废弃参数：`costtype`, `centralwarehouse`, `poinvaliddays`, `soinvaliddays`, `shopbilltype`
- 添加管理员权限控制

### 步骤 4：创建/更新项目文档

**数据库相关文档：**
- 创建 `docs/core/数据库变更记录_系统参数清理.md` - 记录数据库表结构变更、字段标记废弃等
- 创建 Alembic 迁移脚本 - 新增3个字段 + 更新 parm_desc 字段标记废弃
- 更新 `docs/core/数据库字典_精简后_最终版.md` - 更新 `TMC71_SYSPARM` 表说明和字段废弃标记
- 更新 `docs/core/数据库ER关系文档.md` - 更新 `TMC71_SYSPARM` 表的ER图说明
- 更新 `docs/core/数据迁移执行方案_v2.md` - 更新 `tmc71_sysparm` 迁移说明（如果涉及数据迁移）
- 更新数据库变更日志 - 记录数据库变更历史

**项目文档：**
- 创建 `docs/core/系统参数清理优化方案.md` - 记录系统参数清理的优化内容和决策
- 更新 `docs/core/项目整体实施计划.md` - 添加系统参数清理到实施计划
- 更新 `docs/core/CHANGELOG.md` - 记录系统参数清理的变更
- 更新 `docs/superpowers/plans/2026-05-08-frontend-vue3-setup.md` - 在前端总体规划中添加系统参数页面规划章节（展示6个全局参数，隐藏5个零售废弃参数，添加3个新增字段）
- 更新 `docs/core/API接口文档.md` - 记录系统参数API的说明（`PUT /api/v1/sysparms/{parm_cd}`）
- 更新 `docs/core/客户主数据字段规范.md` - 删除零售业务参数说明（如果文档中包含）

### 步骤 5：测试验证

- 验证 `allowmultilogon` 参数正常工作
- 确认前端页面只展示 ITSM 相关参数
- 验证废弃参数不影响业务逻辑

## 待确认事项

无（已全部确认）

## 实施顺序

1. 确认 ITSM 业务所需全局参数
2. 选择数据库处理方案（A 或 B）
3. 执行数据库变更（如选 B）或更新描述字段（如选 A）
4. 更新前端页面
5. 更新文档
6. 测试验证
