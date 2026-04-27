# PB→Python 模块迁移 DoD 清单

## 1. 适用范围
- 适用于 `e:/project/myitsm/src` 下所有按 `.pbl` 模块边界实施的迁移任务。
- 每次仅允许一个模块进入 DoD 验收，禁止跨模块混验。

## 2. 模块基础信息
- PB 模块目录：
- Python 目标包：
- 负责人：
- 计划开始时间：
- 计划完成时间：

## 3. DoD 必选项（全部满足）

### 3.1 功能等价
- [ ] 已完成模块内功能点清单梳理。
- [ ] 每个功能点存在 PB→Python 映射关系（引用 `PB_TO_PYTHON_MODULE_MAPPING.csv`）。
- [ ] 核心业务路径已通过等价性校验（输入、处理、输出一致）。

### 3.2 SQL 与数据一致性
- [ ] 关键 SQL 已完成映射（引用 `PB_TO_PYTHON_SQL_MAPPING.csv`）。
- [ ] 每条关键 SQL 存在一致性校验 SQL 或校验用例。
- [ ] 与 `数据库字典_精简后_最终版.md` 的表结构与字段语义口径一致。

### 3.3 架构与代码规范
- [ ] 代码严格落在 `api/services/repositories/models/schemas/extensions` 分层中。
- [ ] `api` 层无 SQL，事务边界在 `service` 层。
- [ ] 公共函数/方法具备完整类型注解，导入顺序符合规范。
- [ ] 无 `print`，日志使用 `logging` 且包含 `request_id/trace_id`。

### 3.4 质量门禁
- [ ] `black` 通过。
- [ ] `isort` 通过。
- [ ] `ruff` 通过。
- [ ] `mypy --strict` 通过。
- [ ] `pytest`（模块相关用例）通过。
- [ ] `bandit` 通过。

### 3.5 接口与契约
- [ ] API 路径符合 `/api/v1` 版本前缀。
- [ ] 响应结构符合 `{ code, message, data }`。
- [ ] 请求/响应 schema 校验齐全。
- [ ] 异常响应包含 `request_id`。

### 3.6 发布与回滚准备
- [ ] 已完成灰度范围与放量节奏说明。
- [ ] 已完成回滚步骤确认并演练。
- [ ] 已指定发布窗口联系人与值班人员。

## 4. 验收记录
- 验收日期：
- 验收人：
- 遗留问题：
- 结论（通过/不通过）：
