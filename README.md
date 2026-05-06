# MyITSM — 企业综合运营管理平台

融合 **ITSM（IT服务管理）**、**仓储/采购/销售**、**MES（制造执行）**、**IoT（物联网监控）** 及 **租赁/资产管理** 的综合企业运营管理平台。

以"**设备全生命周期管理**"与"**客户业务闭环**"为双向驱动核心。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python 3.11+ / Flask 3.0（应用工厂模式） |
| ORM | SQLAlchemy + Flask-Migrate（Alembic） |
| 数据库 | PostgreSQL 16+（CCGLPDB + LGREPORTPDB 双库合并） |
| 请求校验 | Pydantic v2 |
| 认证 | JWT（PyJWT） |
| 包管理 | [uv](https://docs.astral.sh/uv/)（快速依赖管理 + 虚拟环境 + lockfile） |
| 质量门禁 | black / isort / ruff / mypy --strict / pytest / bandit |

## 项目结构

```
myitsm/
├── AGENTS.md                 # 项目规则与约定
├── README.md                 # 本文件
├── app/                      # 后端代码
│   ├── __init__.py           # Flask 应用工厂
│   ├── api/                  # API 蓝图层（18个模块）
│   ├── models/               # SQLAlchemy 数据模型（124个业务模型）
│   ├── services/             # 业务逻辑层
│   ├── repositories/         # 数据访问层
│   ├── schemas/              # Pydantic 请求/响应 Schema
│   ├── extensions/           # Flask 扩展初始化
│   └── utils/                # 工具函数（统一响应等）
├── tests/                    # 测试用例（128个）
├── migrations/               # Flask-Migrate 数据库迁移
├── docs/
│   ├── core/                 # 核心文档（索引见 CORE_DOCS_INDEX.md）
│   └── archive/              # 归档文档（旧重构资料）
├── PBsrc/                    # PB 原始源码（25个 .pbl 模块）
├── _backup/                  # 备份（旧重构代码）
├── pyproject.toml            # Python 项目配置
├── uv.lock                   # uv 依赖锁文件（确保团队版本一致）
├── wsgi.py                   # WSGI 入口
└── .env.example              # 环境变量模板
```

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 16+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)（Python 包管理器）

### 1. 安装 uv

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 验证安装
uv --version
```

### 2. 克隆仓库

```bash
git clone https://github.com/CheungJan/myitsm.git
cd myitsm
```

### 3. 安装依赖（自动创建虚拟环境）

```bash
# 一条命令完成：创建 .venv 虚拟环境 + 安装全部依赖（含开发工具）
uv sync --extra dev
```

> **说明**：
> - `uv sync` 会自动创建 `.venv` 虚拟环境并安装所有依赖，无需手动创建或激活。
> - 依赖版本由 `uv.lock` 锁定，确保团队所有成员版本一致。
> - 后续执行命令统一使用 `uv run <命令>` 前缀，无需手动激活虚拟环境。

### 4. 环境变量配置

```bash
cp .env.example .env
```

编辑 `.env` 文件（按实际数据库配置修改）：

```ini
FLASK_ENV=development
SECRET_KEY=your-random-secret-key
DATABASE_URL=postgresql://cheungjan@localhost:5432/myitsm
TEST_DATABASE_URL=postgresql://cheungjan@localhost:5432/myitsm_test
```

> 数据库连接格式：`postgresql://用户名:密码@主机:端口/数据库名`，密码为空时省略 `:密码` 部分。

### 5. 数据库初始化

```bash
# 创建数据库（用户名按实际配置）
createdb -U cheungjan myitsm
createdb -U cheungjan myitsm_test

# 运行迁移（自动创建全部 124 张业务表）
uv run flask db upgrade
```

### 6. 启动开发服务器

```bash
uv run flask run --debug
# 或
uv run python wsgi.py
```

服务启动后访问 `http://localhost:5000/api/v1/health` 验证。

### 7. 运行测试

```bash
uv run pytest
```

### 8. 代码质量检查

```bash
# 格式化
uv run black app/ tests/
uv run isort app/ tests/

# 静态检查
uv run ruff check app/ tests/
uv run mypy --strict app/

# 安全检查
uv run bandit -r app/ -c pyproject.toml
```

## API 概览

- **统一前缀**：`/api/v1`
- **统一响应**：`{ code, message, data, request_id }`
- **认证方式**：JWT Bearer Token（`POST /api/v1/login` 获取）
- **端点总数**：183个，覆盖18个业务模块

完整接口文档见 [`docs/core/API接口文档.md`](docs/core/API接口文档.md)。

## 业务模块

| 模块 | 说明 | 模型数 |
|------|------|--------|
| 系统管理 | 用户/部门/菜单/权限/系统参数 | 11 |
| 主数据 | 客户/门店/设备/产品/数据字典 | 13 |
| ITSM核心 | 日常维护/新机开通/旧机翻新/设备变更/门店关闭/保养/回收 | 34 |
| 仓储管理 | 仓库/入库/出库/库存余额/流水 | 15 |
| 采购管理 | 采购计划/登记/单据/供应商评价 | 10 |
| 销售管理 | 预计划/销售单据/延期 | 4 |
| SLA管理 | SLA定义/工单监控/达标率统计 | 2 |
| 考勤管理 | 考勤记录/月度汇总 | 2 |
| 库存价格 | 库存预警/价格规则/调价 | 4 |
| 押金管理 | 押金主表/变更明细/型号标准 | 5 |
| 合同发票 | 合同/发票 | 2 |
| 通知系统 | 通知模板/发送记录 | 2 |
| 结算管理 | 结算规则/账单/结算批次 | 4 |
| 财务管理 | 会计科目/应收/应付/收付款/折旧 | 5 |
| 客户门户 | 门户用户/自助报修/服务评价 | 3 |
| MES制造 | 生产工单/工序定义/工单工序/物料消耗 | 4 |
| IoT监控 | 设备接入/数据采集/报警规则/报警记录 | 4 |

**总计**：124个业务模型 / 128个测试 / 6项质量门禁

## 文档

核心文档统一入口：[`docs/core/CORE_DOCS_INDEX.md`](docs/core/CORE_DOCS_INDEX.md)

| 文档 | 说明 |
|------|------|
| [项目整体实施计划](docs/core/项目整体实施计划.md) | 里程碑、数据库迁移、前端规划、部署方案 |
| [系统功能对比分析](docs/core/系统功能对比分析与扩展规划.md) | 已有功能映射 + Tier-1/2/3 扩展规划 |
| [API接口文档](docs/core/API接口文档.md) | 183个端点完整说明 |
| [全阶段模型字段核对报告](docs/core/全阶段模型字段核对报告.md) | 124个模型逐表核对 |
| [数据库字典](docs/core/数据库字典_精简后_最终版.md) | 表结构与字段语义 |

## 贡献

1. 从最新分支创建功能分支
2. 遵循 `AGENTS.md` 中的编码与架构约定
3. 确保所有质量门禁通过（`black/isort/ruff/mypy --strict/pytest/bandit`）
4. 提交 PR 并等待审阅

## 许可证

私有项目，仅供内部使用。
