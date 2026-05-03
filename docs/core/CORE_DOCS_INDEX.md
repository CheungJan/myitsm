# 核心文档索引（docs/core）

## 说明

- 本目录用于提供核心文档统一入口。
- 核心文档实体已统一迁移至 `docs/core/`，后续重构开工前统一从本目录读取。
- 旧重构（2026-03-11 版）相关文档已归档至 `docs/archive/`，仅作历史参考。

---

## A 类：项目管理文档（当前重构主线）

1. **ITSM 重构项目需求设计文档**（PB 源码全面分析 + 优化方案 + 重构路线图）
   - `docs/core/ITSM重构项目需求设计文档.md`
   - 版本：v1.1 | 创建：2026-04-27

2. **项目整体实施计划**（后端/数据库迁移/前端/部署/里程碑）
   - `docs/core/项目整体实施计划.md`
   - 版本：v1.1 | 创建：2026-04-27

3. **系统功能对比分析与扩展规划**（已有功能映射 + Tier-1/2/3 优先级）
   - `docs/core/系统功能对比分析与扩展规划.md`
   - 版本：v1.1 | 创建：2026-04-27

4. **全阶段模型字段核对报告**（阶段1-5全部124个模型与数据库字典逐表核对）
   - `docs/core/全阶段模型字段核对报告.md`
   - 版本：v1.0 | 创建：2026-04-27

5. **阶段1 模型字段核对报告**（32张骨架表与数据库字典逐表核对，历史参考）
   - `docs/core/阶段1_模型字段核对报告.md`

## B 类：技术参考文档（重构基线）

6. **重构优化需求基线**（P0-P4 优化方案）
   - `docs/core/PB_TO_PYTHON_OPTIMIZATION_REQUIREMENTS.md`

7. **数据库字典主口径**（表结构、字段语义、字段说明）
   - `docs/core/数据库字典_精简后_最终版.md`

8. **PB 模块映射主清单**（25个 PB 模块 → Python 模块映射）
   - `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`

9. **PB SQL 映射主清单**（关键 SQL 语句迁移映射）
   - `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`

## C 类：交付与验收文档

10. **迁移验收清单（DoD）**
   - `docs/core/PB_TO_PYTHON_DOD_CHECKLIST.md`

11. **发布与回滚清单**
    - `docs/core/PB_TO_PYTHON_RELEASE_ROLLBACK_CHECKLIST.md`

---

## 归档文档说明

以下文档为旧重构（2026-03-11 版，未完成）产生的资料，已统一归档至 `docs/archive/`，仅作历史参考：

- `docs/archive/old_refactor_core/` — 旧重构核心文档（含项目整体计划与进展_2026-03-11.md、HISTORY_INDEX.md、history/ 执行明细等）
- `docs/archive/old_refactor_docs/` — 旧重构根目录文档（数据库状态码字典、缺陷对照、里程碑验收等）
- `docs/archive/old_refactor_ddl/` — 旧重构 DDL 脚本
- `docs/archive/old_refactor_tmp/` — 旧重构临时文件
- `docs/archive/2026-04-data-intermediate/` — 数据库中间数据
- `docs/archive/2026-04-dba-history/` — DBA 操作历史
- `docs/archive/2026-04-source-material/` — 源材料

---

## 项目目录结构

```
myitsm/
├── AGENTS.md                 # 项目规则与约定
├── app/                      # 重构后的 Python 后端代码（Flask）
│   ├── api/                  # API 蓝图层（18个模块）
│   ├── models/               # SQLAlchemy 数据模型（124个）
│   ├── services/             # 业务逻辑层
│   ├── repositories/         # 数据访问层
│   ├── schemas/              # Pydantic 请求/响应校验
│   └── extensions/           # Flask 扩展初始化
├── tests/                    # 测试用例（128个）
├── migrations/               # Flask-Migrate 数据库迁移
├── docs/
│   ├── core/                 # 核心文档（本索引所在目录）
│   └── archive/              # 归档文档（旧重构资料）
├── PBsrc/                    # PB 原始源码（25个 .pbl 模块 + 参考数据）
├── _backup/                  # 备份（旧重构代码 app_old/）
├── pyproject.toml            # Python 项目配置
└── wsgi.py                   # WSGI 入口
```

## 后续建议

- 新增核心文档时，优先写入 `docs/core/`，并同步更新本索引。
- 归档文档不做日常维护，如需参考请直接查看 `docs/archive/` 对应子目录。
