# M005 Phase 1 liability_sum 落地与映射扩展（2026-04-20）

## 文档信息
- 归档时间：2026-04-20
- 关键步骤主题：`M005 (itsm02.pbl)` 对象 `u_itsm_liability_sum` 三层落地、路由注册与 SQL 映射扩展
- 对应主文档：`docs/core/项目整体计划与进展_2026-03-11.md`

## 范围定义

### PB 对象范围
- 对象：`u_itsm_liability_sum`
- 关联 DataWindow：`d_itsm_liability_main`、`d_itsm_liability_list`

### SQL 映射范围
- 本次新增映射：`S066~S068`（见 `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`）
  - `S066`：免责汇总主列表查询
  - `S067`：免责汇总明细联动查询
  - `S068`：免责汇总批量审核（`is_finish=3`）

## 已落地产物清单
- `app/repositories/liability_sum_repository.py`
- `app/services/liability_sum_service.py`
- `app/api/liability_sum.py`
- `app/__init__.py`（新增 `liability_sum_bp` 注册）
- `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`（M005 增补 `u_itsm_liability_sum`）
- `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`（新增 `S066~S068`）
- `docs/core/项目整体计划与进展_2026-03-11.md`（同步第6/7/8章口径）

## PB 规则对齐说明
- 主列表口径：基于 `TIT10_MAINTENANCEDAY` 与 `TIT10_MAINTENANCE_LIABILITY` 联查，过滤无效/作废数据。
- 明细联动口径：按 `maintenance_id + type` 查询 `TIT10_MAINTENANCE_LIABILITY`。
- 审核动作口径：批量更新 `IS_FINISH='3'`，并回写 `OPERCD/UPDDATE`。

## 针对性校验记录
- `python -m compileall app/repositories/liability_sum_repository.py app/services/liability_sum_service.py app/api/liability_sum.py app/__init__.py`：通过
- `ruff check app/repositories/liability_sum_repository.py app/services/liability_sum_service.py app/api/liability_sum.py app/__init__.py`：通过

## 阶段结论
- 结论：`liability_sum` 已完成本轮开发落地与映射扩展，纳入 `M005 Phase 1` 持续收口范围。
- 后续：继续按 `M005_itsm02_模块对象映射清单` 推进剩余高优先对象，并持续回写 `S` 段映射与一致性校验结果。
