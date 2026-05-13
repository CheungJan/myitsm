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
| 前端框架 | Vue 3.4 + Element Plus + TypeScript + Vite |
| 包管理 | [uv](https://docs.astral.sh/uv/)（Python 后端）+ npm（前端） |
| 质量门禁 | black / isort / ruff / mypy --strict / pytest / bandit |

## 项目结构

```
myitsm/
├── AGENTS.md                 # 项目规则与约定
├── README.md                 # 本文件
├── app/                      # 后端代码
│   ├── __init__.py           # Flask 应用工厂
│   ├── api/                  # API 蓝图层（20个模块，205个端点）
│   ├── models/               # SQLAlchemy 数据模型（142个业务模型）
│   ├── services/             # 业务逻辑层
│   ├── repositories/         # 数据访问层
│   ├── schemas/              # Pydantic 请求/响应 Schema
│   ├── extensions/           # Flask 扩展初始化
│   └── utils/                # 工具函数（统一响应等）
├── frontend/                 # Vue 3 + Element Plus 前端（F1 已完成）
├── tests/                    # 测试用例（148个）
├── scripts/                  # 运维脚本
├── migrations/               # Flask-Migrate 数据库迁移（版本链）
├── docs/
│   ├── core/                 # 核心文档（22个，索引见 CORE_DOCS_INDEX.md）
│   ├── superpowers/          # 头脑风暴设计文档+实施计划
│   └── archive/              # 归档文档（旧重构资料）
├── PBsrc/                    # PB 原始源码（25个 .pbl 模块）
├── _backup/                  # 备份（旧重构代码）
├── pyproject.toml            # Python 项目配置
├── uv.lock                   # uv 依赖锁文件
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

# 运行迁移（自动创建全部 142 张业务表）
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
- **端点总数**：205个，覆盖20个蓝图

完整接口文档见 [`docs/core/API接口文档.md`](docs/core/API接口文档.md)。

## 业务模块

| 模块 | 说明 | 模型数 |
|------|------|--------|
| 系统管理 | 用户/部门/菜单/权限/参数/字典 | 11 |
| 主数据 | 客户/物料/设备SN/供应商/区域/分类 | 25 |
| ITSM核心 | 维护/开通/翻新/变更/保养/关店/回收 | 33 |
| 仓储管理 | 仓库/入库/出库/库存/盘点/调拨 | 15 |
| 采购管理 | 计划/登记/单据/评价/验收 | 11 |
| 销售管理 | 预计划/销售单/延期 | 3 |
| 财务 | 科目/应收/应付/收付款/折旧/合同/发票 | 7 |
| 考勤 | 考勤记录/月度汇总 | 2 |
| 库存预警 | 预警/库存明细/价格规则 | 4 |
| 押金 | 押金主表/明细/出入/型号标准 | 5 |
| 结算 | 规则/账单/批次 | 4 |
| 通知 | 模板/发送记录 | 2 |
| SLA | 服务级别定义/工单监控 | 2 |
| 门户 | 门户用户/自助报修/评价 | 3 |
| MES | 工单/工序/物料消耗 | 4 |
| IoT | 设备接入/数据/报警 | 4 |
| 质检 | 质检结果/明细 | 3 |
| 其他 | 调拨科目/资产属性 | 4 |

**总计**：142个业务模型 / 148个测试 / 143张数据表 / 6项质量门禁

## 文档

核心文档统一入口：[`docs/core/CORE_DOCS_INDEX.md`](docs/core/CORE_DOCS_INDEX.md)

| 文档 | 说明 |
|------|------|
| [项目整体实施计划](docs/core/项目整体实施计划.md) | 里程碑、数据库迁移、前端规划、部署方案 |
| [前端开发方案](docs/superpowers/plans/2026-05-08-frontend-vue3-setup.md) | Vue 3 + Element Plus，F1 已完成 |
| [系统功能对比分析](docs/core/系统功能对比分析与扩展规划.md) | 已有功能映射 + Tier-1/2/3 |
| [API接口文档](docs/core/API接口文档.md) | 205个端点完整说明 |
| [数据库ER关系文档](docs/core/数据库ER关系文档.md) | 142模型跨域关联+统计汇总（**权威**） |
| [数据库字典（PG版）](docs/core/数据库字典_PostgreSQL当前版.md) | 142表字段/类型/索引（**权威**） |
| [数据库变更追踪](docs/core/数据库变更追踪_迁移后.md) | 迁移后→P0 变更记录 |
| [P0数据治理记录](docs/core/P0数据治理记录.md) | 批量修复+自动纠正+回滚方案 |

## 贡献

1. 从最新分支创建功能分支
2. 遵循 `AGENTS.md` 中的编码与架构约定
3. 确保所有质量门禁通过（`black/isort/ruff/mypy --strict/pytest/bandit`）
4. 提交 PR 并等待审阅

## 许可证

私有项目，仅供内部使用。
