# M005 Phase 1 device_change 检索口径对齐（2026-04-20）

## 文档信息
- 归档时间：2026-04-20
- 关键步骤主题：`M005 (itsm02.pbl)` 对象 `u_itsm_device_change` 查询口径补齐
- 对应主文档：`docs/core/项目整体计划与进展_2026-03-11.md`

## 范围定义

### PB 对象范围
- 对象：`u_itsm_device_change`
- 关联 DataWindow：`d_itsm_device_change_grid_list`

### SQL 映射范围
- 本次新增映射：`S076`
  - 设备变更扩展列表查询口径对齐

## 已落地产物清单
- `app/repositories/device_change_repository.py`
- `app/services/device_change_service.py`
- `app/api/device_change.py`
- `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`（新增 `S076`）
- `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`（M005 备注补充对齐说明）
- `docs/core/项目整体计划与进展_2026-03-11.md`（同步第7/8章与快照口径）

## PB 规则对齐说明
- 列表检索维度补齐：支持 `custcard`、`new_store_card`、`device_change_id`、`new_tel`、`begin_date/end_date` 条件。
- 查询结果补齐：返回 `custcard/custnm`，便于界面联动展示。
- 保留现有分页与状态过滤能力，避免破坏已上线调用。

## 针对性校验记录
- `python -m compileall app/repositories/device_change_repository.py app/services/device_change_service.py app/api/device_change.py`：通过
- `ruff check app/repositories/device_change_repository.py app/services/device_change_service.py app/api/device_change.py`：通过

## 阶段结论
- 结论：`device_change` 已完成本轮 `itsm02` 检索口径对齐，纳入 `M005 Phase 1` 持续收口范围。
- 后续：继续按“对象完成即回写、模块阶段收口再汇总”的策略推进余项，避免重复重构。
