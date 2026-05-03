# AGENTS.md

## 作用范围
- 本文件作用于项目根目录（`myitsm/`）全目录树。
- 若子目录存在更深层 `AGENTS.md`，以更深层规则优先。

## 目录结构识别约定（重构关键）
- `app/` 为重构后的 Python 后端代码目录（Flask 应用工厂模式）。
- `PBsrc/` 为 PB 原始源码目录，包含 25 个 `.pbl` 模块及参考数据文件。
- `docs/core/` 为核心文档目录，`docs/archive/` 为归档文档目录（旧重构资料）。
- `_backup/` 为备份目录（存放旧重构代码 `app_old/`）。
- PB→Python 重构时，必须按 `PBsrc/` 下 `.pbl` 模块边界建立映射与迁移清单，禁止跨模块混迁。
- 若出现目录命名歧义，先在 `docs` 内补充映射说明，再开展代码迁移。

## 关键参考产物约定
- 核心文档统一入口：`docs/core/CORE_DOCS_INDEX.md`（先看索引，再按索引打开原文档）。
- 涉及数据库表结构、字段语义、字段说明、口径对齐时，优先参考 `docs/core/数据库字典_精简后_最终版.md`。
- 涉及代码重构优化方案、业务模型改进时，优先参考 `docs/core/PB_TO_PYTHON_OPTIMIZATION_REQUIREMENTS.md`。
- 涉及功能范围确认、缺失功能规划、扩展需求时，优先参考 `docs/core/系统功能对比分析与扩展规划.md`。
- 若实现逻辑与参考产物存在冲突，先记录差异并在 `docs` 补充说明后再实施变更。

## 重构开工前必读清单（每次任务开始前执行）
1. `AGENTS.md`（确认当前作用域规则与限制）。
2. `docs/core/项目整体实施计划.md`（确认当前阶段目标、整体里程碑与优先级）。
   `docs/core/ITSM重构项目需求设计文档.md`（确认 PB 源码分析结论、P0-P4 优化方案与重构路线图）。
3. `docs/core/PB_TO_PYTHON_OPTIMIZATION_REQUIREMENTS.md`（**确认优化需求**：业务流程改进、数据模型优化方案，如客户生命周期、资产属性等）。
4. `docs/core/系统功能对比分析与扩展规划.md`（**确认功能范围**：已有功能映射、缺失功能优先级分类、Tier-1/2/3 扩展规划，避免遗漏已确认需求）。
5. `docs/core/数据库字典_精简后_最终版.md`（确认表结构、字段语义与口径）。
6. `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`（确认模块边界与责任归属）。
7. `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`（确认关键 SQL 映射与一致性校验口径）。
8. `docs/core/PB_TO_PYTHON_DOD_CHECKLIST.md` 与 `docs/core/PB_TO_PYTHON_RELEASE_ROLLBACK_CHECKLIST.md`（确认交付验收与回滚要求）。
9. `/.pre-commit-config.yaml` 与 `/.github/workflows/quality-gate.yml`（确认本地与 CI 质量门禁一致）。

未完成以上核对前，不得开始模块代码迁移与提交。

## 项目阶段与目标
- 当前阶段：全部后端开发已完成（阶段1-5），进入数据库迁移与前端开发阶段。
- 核心目标：完成 Oracle→PostgreSQL 数据迁移、前端页面开发、系统联调上线。

### 阶段路线图与已确认需求

| 阶段 | 状态 | 内容 | PR |
|------|------|------|-----|
| 阶段1 | **已完成** | 基础架构（Flask工厂+SQLAlchemy模型+JWT认证+统一状态机） | PR#2 |
| 阶段2 | **已完成** | ITSM核心迁移（30+表+Repository/Service/API+P0优化1-4） | PR#3 |
| 阶段3 | **已完成** | 仓储统一模型(TWH*) + 采购(TPC*) + 销售(TSL*) + **[Tier-1] SLA服务级别管理** | PR#4 |
| 阶段4 | **已完成** | 辅助模块（考勤TKQ/库存预警TIV/价格TIP/押金）+ **[Tier-1] 合同管理(THT01) + 发票管理(TAC01) + 通知系统** | PR#5 |
| ═══ | ═══ | **═══ PB→Python 等价重构完成线 ═══** | |
| 阶段5 | **已完成** | **[Tier-2]** 结算(G4,4表) + 财务(G5,5表) + 门户(G9,3表) + **[Tier-3]** MES(G7,4表) + IoT(G8,4表) | PR#6 |
| ═══ | ═══ | **═══ 全部后端开发完成线（124模型/128测试） ═══** | |

> **后端开发全部完成**。后续重点：数据库迁移(Oracle→PostgreSQL) + 前端页面开发 + IoT中间件建设。
> 完整功能范围与优先级分类见 `docs/core/系统功能对比分析与扩展规划.md`。
> 项目整体实施计划见 `docs/core/项目整体实施计划.md`。

## 重构总原则（必须遵守）
1. 等价迁移优先（实现阶段）：在完成源码分析与优化点识别后，先保证行为一致，再实施优化。
2. 小步快跑：按模块拆分，单次变更可回滚、可验证。
3. 不做无关扩展：未明确要求时，不新增业务功能。Tier-1 扩展功能（SLA/合同/发票/通知）属于已确认需求，不受此条限制。
4. 变更可追踪：所有改动必须有对应映射与验收依据。
5. 源码先行：重构代码前，必须先阅读对应 PB 源码（`.pbl` 下相关 `sru/srw/srf` 等对象）并完成流程分析。
6. 流程分析至少包含：关键事件入口、核心 SQL、状态流转、主子表关系、异常分支。
7. 问题先识别：若 PB 源码存在流程缺陷或可维护性问题，必须先形成“问题与优化点清单”，再执行 Python 重构。
8. 未完成“源码分析 + 优化点确认”前，不得直接进入实现提交阶段。

## 技术与架构约定
- 后端框架：Flask（应用工厂模式）。
- 目录分层：`api` / `services` / `repositories` / `models` / `schemas` / `extensions`。
- 分层职责：
  - `api`：参数校验、协议转换、返回组装。
  - `services`：业务编排、事务边界。
  - `repositories`：数据访问与 SQL 封装。
- 禁止事项：
  - 禁止在 `api` 层直接写 SQL。
  - 禁止跨层反向调用（如 repository 调 service）。

## 数据库与 SQL 迁移约定
- 统一使用 SQLAlchemy + Flask-Migrate（Alembic）。
- 数据库连接仅来自环境变量，禁止硬编码账号密码。
- 本项目 PB→Python 重构数据库固定为 PostgreSQL（原 CCGLPDB 业务主库 + LGREPORTPDB 零售库合并为单一 PostgreSQL 数据库）。
- 原双库架构中所有 `@CCGL_23`、`@CCGL_24` DB Link 跨库引用已消除，统一为单库内直接查询。
- 未经明确评审与文档变更，不得将 SQLite 作为业务重构数据库口径。
- SQLite 仅可用于本地临时测试或示例，不得作为迁移验收与发布依据。
- 应用连接变量统一为：`DATABASE_URL`（格式：`postgresql://user:password@host:port/dbname`）。
- 事务统一在 service 层管理，避免隐式自动提交。
- 每条关键 PB SQL 必须沉淀“映射关系”：
  - 来源：PB 模块/函数/SQL 片段。
  - 目标：Python repository 方法。
  - 验证：结果一致性校验 SQL/用例。

## API 与契约约定
- 统一前缀：`/api/v1`。
- 统一响应结构：`{ code, message, data }`。
- 请求与响应必须有 schema 校验（Pydantic 或 Marshmallow）。
- 错误响应统一包含 `request_id`。

## 命名、编码与文档约定
- 代码、注释、文档、评审意见统一中文。
- 编码 UTF-8，换行 LF，文件末尾保留单一换行。
- 导入顺序：标准库 → 第三方 → 本地；禁止 `from x import *`。
- 公共函数/方法必须有完整类型注解。

## 项目文档治理约定（计划与历史分层）
- 主文档 `docs/core/项目整体实施计划.md` 仅保留：阶段状态、当前进行项、关键里程碑、风险与下一步。
- 已完成工作的详细过程（SQL明细、排障日志、逐步执行记录、长篇验收过程）必须迁移到历史文档，不在主文档长期堆叠。
- 旧重构（2026-03-11 版）历史记录已归档至 `docs/archive/old_refactor_core/history/`，不再更新。
- 主文档中每个已完成事项至少保留：完成结论、完成时间、证据引用（代码路径/映射ID/验收记录）。
- 文档更新顺序：先更新核心文档，再同步更新 `docs/core/CORE_DOCS_INDEX.md` 索引，确保"索引可快速导航、核心文档可完整追溯"。

## 质量门禁（提交前必须通过）
- 格式与静态检查：`black`、`isort`、`ruff`。
- 类型检查：`mypy --strict`。
- 测试：`pytest`（优先运行与改动相关测试）。
- 安全：`bandit`。
- 未通过门禁不得合并。

## 可观测性与安全约定
- 日志统一 `logging`，禁止 `print`。
- 每请求贯穿 `request_id/trace_id`。
- 敏感字段必须脱敏输出。
- 密钥、令牌、连接串不得入库。

## 迁移执行顺序（推荐）
1. 建立 PB→Python 模块映射清单。
2. 建立 PB SQL→Repository 方法映射清单。
3. 按业务域逐模块迁移（先核心链路）。
4. 每模块完成后执行一致性校验与回归测试。
5. 阶段性灰度发布与回滚演练。

## 交付件最小集合
- `PB_TO_PYTHON_MODULE_MAPPING.csv`
- `PB_TO_PYTHON_SQL_MAPPING.csv`
- 模块级迁移说明与验收记录
- 回滚预案与发布检查清单

## 明确禁止
- 未经确认修改数据库主口径。
- 未经确认调整既有业务语义。
- 为“看起来更优雅”进行大规模无效重构。
- 跳过测试与校验直接交付。

## 工具使用约定
- 修改代码/配置/文档前必须先读取文件确认内容，避免覆盖他人修改。
- 使用 Git 进行版本管理，提交前确保质量门禁通过。
- 按需使用项目提供的 pre-commit 钩子（black/isort/ruff）进行本地检查。

## ITSM业务表结构约定（主子表+公用类型表）

### 业务单据结构模式
所有ITSM业务单据均采用**主表+子表+公用附表**的三层结构：

#### 1. 日常维护单（Maintenance Day）
| 表类型 | 表名 | 说明 |
|--------|------|------|
| 主表 | `TIT10_MAINTENANCEDAY` | 维护单主信息（CURRENT_STATUS） |
| 子表 | `TIT10_POS_DETAIL` | 维护单换机配件明细 |
| 公用附表 | `TIT23_MAINTENANCE_D2D` | 上门服务记录（公用） |
| 公用附表 | `TIT25_ACCESSORIES_UPDATE` | 配件更新记录 |
| 日志表 | `TIT10_MAIN_TRACK` | 状态变更轨迹 |

#### 2. 日常保养单（Maintenance）
| 表类型 | 表名 | 说明 |
|--------|------|------|
| 主表 | `TIT17_MAINTENANCE` | 保养单主信息（CURRENT_STATUS） |
| 子表 | `TIT17_CUST_POS_DAILY` | 保养设备明细 |
| 公用附表 | `TIT23_MAINTENANCE_D2D` | 上门服务记录（公用） |
| 公用附表 | `TIT24_MAINTENANCE_RV` | 客户回访记录 |
| 公用附表 | `TIT27_CLOSE_BILLS` | 关单记录 |

#### 3. 旧机翻新单（Renovate）
| 表类型 | 表名 | 说明 |
|--------|------|------|
| 主表 | `TIT15_MAINTENANCE_RENOVATE` | 翻新单主信息（CURRENT_STATUS） |
| 子表 | `TIT15_EQUIPMENT_RENOVATE` | 翻新设备附表（旧机→新机映射） |
| 公用附表 | `TIT23_MAINTENANCE_D2D` | 上门服务记录（公用） |

#### 4. 新机开通单（New Open）
| 表类型 | 表名 | 说明 |
|--------|------|------|
| 主表 | `TIT13_MAINTENANCE_OPEN` | 开通单主信息（CURRENT_STATUS） |
| 子表 | `TIT14_EQUIPMENT_OPEN` | 开通设备附表 |

#### 5. 设备变更单（Device Change）
| 表类型 | 表名 | 说明 |
|--------|------|------|
| 主表 | `TIT16_DEVICE_CHANGE` | 设备变更单主信息（CURRENT_STATUS） |
| 变更类型 | CHANGE_TYPE | CK=改磁卡号, BQ=信息变更, BG=设备变更 |
| 公用附表 | `TIT23_MAINTENANCE_D2D` | 上门服务记录 |
| **优化表** | `TMM22_CUSTOMERS_HISTORY` | **新增**：磁卡号变更历史记录 |

**⚠️ 老系统问题**：CHANGE_TYPE='CK'时直接删除旧磁卡号记录，导致历史无法追溯  
**✅ 优化方案**：新增`TMM22_CUSTOMERS_HISTORY`表，变更前保存旧磁卡号信息

### 重构实施原则（已全部完成）
1. **主表优先**：所有主表 CRUD 和状态机已实现。
2. **子表完整**：所有子表（配件明细、设备映射、回收明细等）已实现。
3. **公用附表复用**：`TIT23_MAINTENANCE_D2D`（上门服务）、`TIT24_MAINTENANCE_RV`（回访）作为公共服务已实现。
4. **状态机统一**：所有主表共享 `MaintenanceState` 状态机，CURRENT_STATUS 字段语义一致。
5. **关联查询**：主子表通过 `MAINTENANCE_ID` / `RENOVATE_ID` / `NEW_OPENING_ID` 关联。
