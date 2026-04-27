# M005 Phase 1 timepoint_levels 落地与映射扩展（2026-04-20）

## 文档信息
- 归档时间：2026-04-20
- 关键步骤主题：`M005 (itsm02.pbl)` 对象 `u_itsm_timepoint_levels` 三层落地、路由注册与 SQL 映射扩展
- 对应主文档：`docs/core/项目整体计划与进展_2026-03-11.md`

## 范围定义

### PB 对象范围
- 对象：`u_itsm_timepoint_levels`
- 关联 DataWindow：`d_itsm_tp_levels_list_query`、`d_itsm_cust_levels`

### SQL 映射范围
- 本次新增映射：`S081~S085`
  - `S081`：等级定义列表查询
  - `S082`：按等级查询客户
  - `S083`：等级定义保存
  - `S084`：客户等级批量分配
  - `S085`：客户等级批量清空

## 已落地产物清单
- `app/repositories/timepoint_levels_repository.py`
- `app/services/timepoint_levels_service.py`
- `app/api/timepoint_levels.py`
- `app/__init__.py`（新增 `timepoint_levels_bp` 注册）
- `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`（M005 增补 `u_itsm_timepoint_levels`）
- `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`（新增 `S081~S085`）
- `docs/core/项目整体计划与进展_2026-03-11.md`（同步第7/8章与快照口径）

## PB 规则对齐说明
- 等级定义：维护 `TIT01_TIMEPOINT_AREA` 的 `levels/explain/timepoint/beforetm/aftertm/useflg`。
- 客户分配：批量将选中客户写入 `TMM22_CUSTOMERS.LEVELS`。
- 客户清空：批量清空 `TMM22_CUSTOMERS.LEVELS`。
- 兼容列表检索：支持等级客户分页检索，并保留有效标记过滤。

## 针对性校验记录
- `python -m compileall app/repositories/timepoint_levels_repository.py app/services/timepoint_levels_service.py app/api/timepoint_levels.py app/__init__.py`：通过
- `ruff check app/repositories/timepoint_levels_repository.py app/services/timepoint_levels_service.py app/api/timepoint_levels.py app/__init__.py`：通过

## 阶段结论
- 结论：`timepoint_levels` 已完成本轮开发落地与映射扩展，纳入 `M005 Phase 1` 持续收口范围。
- 后续：继续推进 `u_itsm_rep_*` 等剩余对象，并维持“对象完成即回写、模块阶段收口再汇总”的文档策略。
