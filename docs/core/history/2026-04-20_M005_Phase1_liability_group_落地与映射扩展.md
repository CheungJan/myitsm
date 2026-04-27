# M005 Phase 1 liability_group 落地与映射扩展（2026-04-20）

## 文档信息
- 归档时间：2026-04-20
- 关键步骤主题：`M005 (itsm02.pbl)` 对象 `u_itsm_liability_group` 三层落地、路由注册与 SQL 映射扩展
- 对应主文档：`docs/core/项目整体计划与进展_2026-03-11.md`

## 范围定义

### PB 对象范围
- 对象：`u_itsm_liability_group`
- 关联 DataWindow：`d_itsm_liability_main`、`d_itsm_liability_list`

### SQL 映射范围
- 本次新增映射：`S072~S075`（见 `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`）
  - `S072`：免责分部门主列表查询（按用户部门过滤）
  - `S073`：免责分部门明细联动查询
  - `S074`：编辑后状态回显（`IS_FINISH`）
  - `S075`：免责分部门明细保存

## 已落地产物清单
- `app/repositories/liability_group_repository.py`
- `app/services/liability_group_service.py`
- `app/api/liability_group.py`
- `app/__init__.py`（新增 `liability_group_bp` 注册）
- `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`（M005 增补 `u_itsm_liability_group`）
- `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`（新增 `S072~S075`）
- `docs/core/项目整体计划与进展_2026-03-11.md`（同步第7/8章与快照口径）

## PB 规则对齐说明
- 部门过滤口径：按当前用户 `user_cd` 查 `TMC13_USERS.DEPTCD`，再映射 `TIT02_LIABILITYREG.LIABCD`，用于 `A.DEPTNM` 过滤。
- 状态过滤口径：主列表限定 `A.IS_FINISH in ('1','2')`，并支持豁免/类型/处理标志筛选。
- 明细编辑口径：已审核记录（`IS_FINISH='3'`）禁止修改。

## 针对性校验记录
- `python -m compileall app/repositories/liability_group_repository.py app/services/liability_group_service.py app/api/liability_group.py app/__init__.py`：通过
- `ruff check app/repositories/liability_group_repository.py app/services/liability_group_service.py app/api/liability_group.py app/__init__.py`：通过

## 阶段结论
- 结论：`liability_group` 已完成本轮开发落地与映射扩展，纳入 `M005 Phase 1` 持续收口范围。
- 后续：继续推进 `M005` 剩余对象，按“对象完成即回写、模块阶段收口再汇总”的文档策略执行，避免重复重构。
