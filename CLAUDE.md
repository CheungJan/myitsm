# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目规则

项目规则与约定在 `AGENTS.md`，所有任务开始前必须阅读。CLAUDE.md 仅补充 Claude Code 特定配置与常用命令。

## uv 虚拟环境

项目使用 [uv](https://docs.astral.sh/uv/) 管理 Python 虚拟环境和依赖。

```bash
# 虚拟环境位置
.venv/                          # uv 自动创建，已加入 .gitignore

# Python 版本（由 .python-version 文件指定）
cat .python-version              # 当前：3.12

# 安装依赖（首次运行自动创建 .venv）
uv sync                         # 生产依赖
uv sync --extra dev             # 含开发依赖（black/isort/ruff/mypy/pytest）

# 激活虚拟环境
source .venv/bin/activate       # 手动激活（macOS/Linux）
# 退出：deactivate

# 不激活直接运行（推荐）
uv run python -c "print('hello')"
uv run flask run --debug
uv run pytest

# 依赖管理
uv add <package>                # 安装新包（写入 pyproject.toml）
uv add --dev <package>          # 安装开发依赖
uv remove <package>             # 移除包
uv lock --upgrade-package <pkg> # 升级单个包
uv sync --reinstall             # 强制重建 venv（遇到问题时）
```

> **注意**：所有命令优先使用 `uv run` 而非手动 `source .venv/bin/activate`，确保始终在正确的 venv 中执行。

## 常用命令

```bash
# 安装依赖
uv sync --extra dev

# 数据库迁移
uv run flask db upgrade                  # 应用所有迁移
uv run flask db migrate -m "描述"        # 生成新迁移

# 运行服务
uv run flask run --debug                 # 开发服务器（默认 5000 端口）

# 测试
uv run pytest                            # 全部测试
uv run pytest tests/test_itsm_api.py     # 单文件测试
uv run pytest -x -q                      # 快速模式

# 代码质量（提交前全部通过）
uv run black app/ tests/                 # 格式化
uv run isort app/ tests/                 # 导入排序
uv run ruff check app/ tests/            # 静态检查
uv run mypy --strict app/                # 类型检查
uv run bandit -r app/ -c pyproject.toml  # 安全检查
```

## 数据库连接

```bash
# 环境变量（.env 文件自动加载）
DATABASE_URL=postgresql://cheungjan@localhost:5432/myitsm
TEST_DATABASE_URL=postgresql://cheungjan@localhost:5432/myitsm_test

# 直接连接（重构目标库 PostgreSQL）
psql -U cheungjan -d myitsm
```

### PB 原库 Oracle（CCGLPDB）

PB 源码中涉及存储过程（Stored Procedure）、触发器（Trigger）、函数（Function）等数据库对象，在 `.pbl` 源码文件中查不到实现时，使用以下命令连接原库查看：

```bash
# 连接命令（TNS_ADMIN 需指向 tnsnames.ora 所在目录）
export TNS_ADMIN=/Users/cheungjan/Downloads/instantclient_23_26/network/admin
sqlplus ccgl/ccgl@CCGL_TEST
```

连接后常用查询：

```sql
-- 查看存储过程/函数源码（按名称搜索）
SELECT text FROM all_source WHERE name = 'USP_WH_OUT' ORDER BY line;

-- 查看触发器源码
SELECT trigger_body FROM all_triggers WHERE trigger_name = 'TRG_XXX';

-- 列出所有存储过程
SELECT object_name, object_type, status FROM all_objects
WHERE object_type IN ('PROCEDURE','FUNCTION','TRIGGER','PACKAGE')
  AND owner = 'CCGL'
ORDER BY object_type, object_name;

-- 模糊搜索含特定关键字的存储过程
SELECT DISTINCT name, type FROM all_source
WHERE owner = 'CCGL' AND UPPER(text) LIKE '%USP_WH%'
ORDER BY type, name;
```

> **用途**：分析 PB 调用的 `usp_*`、`ufn_*` 等数据库存储过程与触发器的业务逻辑，作为 Python 重构的参考依据。

## 架构概览

```
app/
├── api/            # Flask 蓝图层：参数校验 + 协议转换 + 响应组装
├── services/       # 业务逻辑层：编排 + 事务边界
├── repositories/   # 数据访问层：SQL 封装
├── models/         # SQLAlchemy 模型（138 个，对应 139 张表）
├── schemas/        # Pydantic v2 请求/响应 Schema
├── extensions/     # Flask 扩展初始化（db/migrate/cors）
└── utils/          # 工具函数（统一响应格式）
```

- **分层规则**：API → Service → Repository，禁止跨层反向调用。API 层禁止直接写 SQL。
- **响应格式**：`{ code, message, data, request_id }`
- **认证**：JWT Bearer Token（除 `/health`、`/login` 外均需认证）
- **测试**：128 个 API 集成测试，SQLite 内存库，事务回滚隔离

## 新增前端模块清单（新增页面/菜单必做，缺一不可）

新增一个前端页面并显示在侧边栏菜单中，必须完成以下**4步**：

| # | 文件/操作 | 内容 | 说明 |
|---|----------|------|------|
| 1 | `frontend/src/config/menu.ts` | 在对应 parent 下加 `{ menu_cd, menu_nm, path }` | 前端菜单树的唯一硬编码来源 |
| 2 | `frontend/src/router/index.ts` | 加路由 `{ path, name, component }` | 路径需与 menu.ts 的 path 一致 |
| **3** | `tmc01_menus` 表 | `INSERT` menu_cd/menu_nm/parent_cd | 后台菜单定义 |
| **4** | `tmc02_menusdt` 表 | `INSERT` menu_cd/func_cd='view'/**useflg='1'** | ⚠️ **useflg 必须为 '1'**，NULL 会导致管理员的全部权限查询（`useflg=='1'` 过滤）被排除 |

验证：退出重新登录 → 菜单出现。

开发时如果菜单不显示，按顺序排查：
1. `SELECT useflg FROM tmc02_menusdt WHERE menu_cd='xxx'` — 检查是否为 '1'
2. `SELECT * FROM tmc01_menus WHERE menu_cd='xxx'` — 检查是否存在
3. `frontend/src/config/menu.ts` — 检查是否已添加
4. 退出重新登录（清除权限缓存）

## 可用 MCP 工具

| MCP | 用途 |
|-----|------|
| `postgres` | 数据库探查（restricted 模式，连接 ortopbitsmdb） |
| `github` | PR/Issue/代码搜索 |
| `context7` | 实时技术文档查询 |
| `playwright` | 前端 E2E 测试 |

## 可用 Skills

| 分类 | Skills |
|------|--------|
| 后端 | `python-backend` `sqlalchemy-alembic-expert-best-practices-code-review` `rest-api-design` |
| 前端 | `frontend-design` `frontend-vue-development` |
| 质量 | `code-review` `security-review` `test-driven-development` `systematic-debugging` |
| 流程 | `writing-plans` `executing-plans` `verification-before-completion` `finishing-a-development-branch` |
| 迁移 | `legacy-modernizer` |
| 测试 | `webapp-testing` |
| Agent | `subagent-driven-development` `using-superpowers` |
