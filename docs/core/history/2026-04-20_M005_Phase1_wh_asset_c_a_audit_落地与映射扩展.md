# M005 Phase 1 wh_asset_c_a_audit 落地与映射扩展（2026-04-20）

## 文档信息
- 归档时间：2026-04-20
- 关键步骤主题：`M005 (itsm02.pbl)` 对象 `u_itsm_wh_asset_c_a_audit` 三层落地、路由注册与 SQL 映射扩展
- 对应主文档：`docs/core/项目整体计划与进展_2026-03-11.md`

## 范围定义

### PB 对象范围
- 对象：`u_itsm_wh_asset_c_a_audit`
- 关联 DataWindow：`d_asset_auditbill_browse`、`d_asset_auditbilldt`

### SQL 映射范围
- 本次新增映射：`S086~S090`
  - `S086`：待审核作废单列表查询
  - `S087`：作废单明细查询
  - `S088`：作废单审批（含过程 `usp_asset_c_a`）
  - `S089`：作废单作废
  - `S090`：刷新重取待审核列表

## 已落地产物清单
- `app/repositories/asset_audit_repository.py`
- `app/services/asset_audit_service.py`
- `app/api/asset_audit.py`
- `app/__init__.py`（新增 `asset_audit_bp` 注册）
- `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`（M005 增补 `u_itsm_wh_asset_c_a_audit`）
- `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`（新增 `S086~S090`）
- `docs/core/项目整体计划与进展_2026-03-11.md`（同步第7/8章与快照口径）

## PB 规则对齐说明
- 待审核口径：仅返回 `auditflg='1'` 且 `useflg<>'9'` 的作废单。
- 审批动作：审核后置 `auditflg='2'`、记录 `auditman/auditdate`，并调用 `usp_asset_c_a` 执行库存处理。
- 作废动作：作废按钮更新 `useflg='9'` 并回写审核人/审核时间。
- 主从联动：按 `opbillid` 拉取明细，兼容 `custcd_like='%'` 场景。

## 针对性校验记录
- `python -m compileall app/repositories/asset_audit_repository.py app/services/asset_audit_service.py app/api/asset_audit.py app/__init__.py`：通过
- `ruff check app/repositories/asset_audit_repository.py app/services/asset_audit_service.py app/api/asset_audit.py app/__init__.py`：通过

## 阶段结论
- 结论：`wh_asset_c_a_audit` 已完成本轮开发落地与映射扩展，纳入 `M005 Phase 1` 持续收口范围。
- 后续：继续推进 `u_itsm_rep_*` 报表对象，并保持“对象完成即回写、模块阶段收口再汇总”的策略。
