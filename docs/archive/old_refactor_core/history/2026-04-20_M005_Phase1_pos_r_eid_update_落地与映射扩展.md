# M005 Phase 1 pos_r_eid_update 落地与映射扩展（2026-04-20）

## 文档信息
- 归档时间：2026-04-20
- 关键步骤主题：`M005 (itsm02.pbl)` 对象 `u_itsm_pos_r_eid_update` 三层落地、路由注册与 SQL 映射扩展
- 对应主文档：`docs/core/项目整体计划与进展_2026-03-11.md`

## 范围定义

### PB 对象范围
- 对象：`u_itsm_pos_r_eid_update`
- 关联 DataWindow：`d_itsm_free_replace_dt_list`、`d_itsm_pos_r_eid_choose_old`、`d_itsm_pos_r_eid_choose_new`

### SQL 映射范围
- 本次新增映射：`S069~S071`（见 `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`）
  - `S069`：配置更新待确认列表查询
  - `S070`：旧新配件选择明细联动查询
  - `S071`：配置确认（更新 `TMM44_POS_R_EID.POSID` 并回写 `is_finish=2`）

## 已落地产物清单
- `app/repositories/pos_r_eid_update_repository.py`
- `app/services/pos_r_eid_update_service.py`
- `app/api/pos_r_eid_update.py`
- `app/__init__.py`（新增 `pos_r_eid_update_bp` 注册）
- `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`（M005 增补 `u_itsm_pos_r_eid_update`）
- `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`（新增 `S069~S071`）
- `docs/core/项目整体计划与进展_2026-03-11.md`（同步第7/8章与快照口径）

## PB 规则对齐说明
- 列表口径：仅处理 `is_finish <> '0'` 的免费更换明细，并支持按磁卡号/单号/日期/确认状态过滤。
- 联动口径：按 `bill_id + business_id + device_id` 查询旧新配件选择明细。
- 确认口径：仅对旧配件中 `chooseflg='1'` 的行执行配置更新；若新设备配置中已存在相同配件，拦截并返回错误。
- 状态回写：确认成功后更新 `TIT28_FREE_REPLACE_DT.is_finish='2'`。

## 针对性校验记录
- `python -m compileall app/repositories/pos_r_eid_update_repository.py app/services/pos_r_eid_update_service.py app/api/pos_r_eid_update.py app/__init__.py`：通过
- `ruff check app/repositories/pos_r_eid_update_repository.py app/services/pos_r_eid_update_service.py app/api/pos_r_eid_update.py app/__init__.py`：通过

## 阶段结论
- 结论：`pos_r_eid_update` 已完成本轮开发落地与映射扩展，纳入 `M005 Phase 1` 持续收口范围。
- 后续：继续推进 `M005` 剩余高优对象（如 `u_itsm_liability_group`），并持续回写 `S` 段映射与一致性校验结果。
