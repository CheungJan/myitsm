# docs 文档整理索引（2026-04-14）

## 1. 整理原则

- 本次执行“安全整理”：以迁移归档为主，仅删除无内容空目录（如 `docs/image/`）。
- 已将 `AGENTS.md` 与总计划中的必读清单路径统一到 `docs/core/`。
- 目标：降低 `docs/` 根目录噪音，保留主链路文档可见性。

### 1.1 第二轮追加整理（同日）

- 已将根目录历史草案/查询脚本迁入：`docs/archive/2026-04-dba-history/`
  - `CCGL兼容层DDL_最小执行草案.sql`
  - `CCGL兼容层DDL草案.sql`
  - `_q_ccgl.sql`、`_q_ccgllsgl.sql`
  - `q_ccgl.sql`、`q_ccgl_readonly.sql`、`q_ccgllsgl.sql`、`q_ccgllsgl_readonly.sql`、`q_test_lg.sql`
- 已将参数/连接样例迁入：`docs/archive/2026-04-source-material/`
  - `EXPDP_CCGL_FULL.par`
  - `IMPDP_CCGL_TO_CCGL_MIG_FULL.par`
  - `tnsnames.ora`
- 已将导入模板迁入：`docs/tmp/import_tasks/`
  - `巡访计划实施2026.xlsx`

## 2. 核心文档位置（当前主链路）

以下核心文档已统一迁移到 `docs/core/`：

- `docs/core/项目整体计划与进展_2026-03-11.md`：项目主进度与阶段结论
- `docs/core/PB_TO_PYTHON_OPTIMIZATION_REQUIREMENTS.md`：优化需求基线
- `docs/core/数据库字典_精简后_最终版.md`：数据库结构与字段语义口径
- `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`：PB 模块映射主清单
- `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`：SQL 映射主清单
- `docs/core/PB_TO_PYTHON_DOD_CHECKLIST.md`：DoD 验收清单
- `docs/core/PB_TO_PYTHON_RELEASE_ROLLBACK_CHECKLIST.md`：发布/回滚清单
- `docs/core/数据库操作.txt`：Oracle 接入口径与操作说明
- `docs/core/ITSM业务单据结构与优化分析_2026-04-08.md`：ITSM 重构分析依据
- `ddl/`：当前 DDL 与验证脚本

> 已新增统一入口：`docs/core/CORE_DOCS_INDEX.md`
>
> 说明：核心文档实体已完成迁移，后续按 `docs/core/` 路径作为唯一主路径维护。

## 3. 本次归档位置

### 3.1 历史实施脚本与阶段文档

- 目录：`docs/archive/2026-04-dba-history/`
- 内容：`DBA_*.sql|md`、`SQL_*.sql`、`P1_BATCH*.md`、上线检查/签字类文档等历史执行资产。

### 3.2 数据中间产物

- 目录：`docs/archive/2026-04-data-intermediate/`
- 内容：`db_*.csv`、`数据库表来源对照_*.csv`、`状态码来源对照_代码抽取.csv`、缺失对象核查中间文件。

### 3.3 原始来源资料

- 目录：`docs/archive/2026-04-source-material/`
- 内容：原始字典、提取文本、历史说明 Excel 导出件等。

## 4. 临时目录（可周期清理）

### 4.1 日志

- 目录：`docs/tmp/logs/`
- 内容：`*.log` 运行日志。

### 4.2 截图

- 目录：`docs/tmp/screenshots/`
- 内容：导入/报错/表格截图。

### 4.3 导入任务材料

- 目录：`docs/tmp/import_tasks/保养单任务/`
- 内容：批量导入相关说明、样例、截图。

## 5. 后续建议

- 每周清理一次 `docs/tmp/`（日志、截图、一次性导入材料）。
- 历史执行 SQL 统一按“阶段+日期”归档到 `docs/archive/`，避免再次回流到根目录。
- 保持 `AGENTS.md` 必读清单与 `docs/core/CORE_DOCS_INDEX.md` 一致，新增核心文档需同步更新两处。
