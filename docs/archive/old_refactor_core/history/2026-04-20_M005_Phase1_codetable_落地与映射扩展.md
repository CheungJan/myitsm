# M005 Phase 1 codetable 落地与映射扩展（2026-04-20）

## 文档信息
- 归档时间：2026-04-20
- 关键步骤主题：`M005 (itsm02.pbl)` 对象 `u_itsm_codetable` 三层落地、路由注册与 SQL 映射扩展
- 对应主文档：`docs/core/项目整体计划与进展_2026-03-11.md`

## 范围定义

### PB 对象范围
- 对象：`u_itsm_codetable`
- 关联 DataWindow：`d_itsm_syscode_list`、`d_itsm_syscodes_form`

### SQL 映射范围
- 本次新增映射：`S077~S080`
  - `S077`：代码项列表查询
  - `S078`：代码项详情查询
  - `S079`：代码项保存
  - `S080`：代码项作废（系统代码不可删除）

## 已落地产物清单
- `app/repositories/codetable_repository.py`
- `app/services/codetable_service.py`
- `app/api/codetable.py`
- `app/__init__.py`（新增 `codetable_bp` 注册）
- `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`（M005 增补 `u_itsm_codetable`）
- `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`（新增 `S077~S080`）
- `docs/core/项目整体计划与进展_2026-03-11.md`（同步第7/8章与快照口径）

## PB 规则对齐说明
- 列表口径：按 `codetyp` 查询代码项，支持有效标志过滤。
- 编辑口径：按 `codetyp+codecd` 定位代码项。
- 删除约束：系统代码（`sysflg='Y'`）禁止删除；实现为“非系统代码逻辑作废（`useflg='0'`）”。

## 针对性校验记录
- `python -m compileall app/repositories/codetable_repository.py app/services/codetable_service.py app/api/codetable.py app/__init__.py`：通过
- `ruff check app/repositories/codetable_repository.py app/services/codetable_service.py app/api/codetable.py app/__init__.py`：通过

## 阶段结论
- 结论：`codetable` 已完成本轮开发落地与映射扩展，纳入 `M005 Phase 1` 持续收口范围。
- 后续：继续推进 `u_itsm_timepoint_levels` 等剩余对象，并维持“对象完成即回写、模块阶段收口再汇总”的文档策略。
