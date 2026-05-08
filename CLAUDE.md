# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目规则

项目规则与约定在 `AGENTS.md`，所有任务开始前必须阅读。CLAUDE.md 仅补充 Claude Code 特定配置与常用命令。

## 常用命令

```bash
# 安装依赖（自动创建 .venv）
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

# 直接连接
psql -U cheungjan -d myitsm
```

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

## 可用 MCP 工具

| MCP | 用途 |
|-----|------|
| `postgres` | 数据库探查（restricted 模式，连接 ortopbitsmdb） |
| `github` | PR/Issue/代码搜索 |
| `context7` | 实时技术文档查询 |
| `playwright` | 前端 E2E 测试 |

## 可用 Skills

`python-backend` `sqlalchemy-alembic-expert-best-practices-code-review` `rest-api-design`
`frontend-design` `frontend-vue-development` `code-review` `security-review`
`legacy-modernizer` `webapp-testing`
