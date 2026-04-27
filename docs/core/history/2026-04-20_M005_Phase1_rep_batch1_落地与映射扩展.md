# M005 Phase 1 rep_batch1 落地与映射扩展（2026-04-20）

## 文档信息
- 归档时间：2026-04-20
- 关键步骤主题：`M005 (itsm02.pbl)` 首批三条报表对象批量落地
- 对应主文档：`docs/core/项目整体计划与进展_2026-03-11.md`

## 范围定义

### PB 对象范围
- `u_itsm_rep_accessories_update`
- `u_itsm_rep_liability`
- `u_itsm_rep_paper_averagel`

### SQL 映射范围
- 本次新增映射：`S092~S095`
  - `S092`：配件更新报表查询
  - `S093`：责任认定报表主列表
  - `S094`：责任认定报表明细
  - `S095`：纸张平均报表聚合查询

## 已落地产物清单
- `app/repositories/accessories_update_report_repository.py`
- `app/services/accessories_update_report_service.py`
- `app/api/accessories_update_report.py`
- `app/repositories/rep_liability_report_repository.py`
- `app/services/rep_liability_report_service.py`
- `app/api/rep_liability_report.py`
- `app/repositories/paper_average_report_repository.py`
- `app/services/paper_average_report_service.py`
- `app/api/paper_average_report.py`
- `app/__init__.py`（新增三条报表蓝图注册）

## PB 规则对齐说明
- `rep_accessories_update`：按时间范围查询配件更新报表，支持维护单号/门店/磁卡号/配件类型过滤。
- `rep_liability`：主列表按时间范围与责任状态查询；明细按 `maintenance_id + type` 联动查询。
- `rep_paper_averagel`：按时间范围聚合统计，输出工程师达标率报表核心聚合列。

## 针对性校验记录
- `python -m compileall app/repositories/accessories_update_report_repository.py app/services/accessories_update_report_service.py app/api/accessories_update_report.py app/repositories/rep_liability_report_repository.py app/services/rep_liability_report_service.py app/api/rep_liability_report.py app/repositories/paper_average_report_repository.py app/services/paper_average_report_service.py app/api/paper_average_report.py app/__init__.py`：通过
- `ruff check app/repositories/accessories_update_report_repository.py app/services/accessories_update_report_service.py app/api/accessories_update_report.py app/repositories/rep_liability_report_repository.py app/services/rep_liability_report_service.py app/api/rep_liability_report.py app/repositories/paper_average_report_repository.py app/services/paper_average_report_service.py app/api/paper_average_report.py app/__init__.py`：通过

## 阶段结论
- 结论：M005 首批三条报表对象已批量落地，满足“很多对象时一次多处理几个”的执行策略。
- 后续：继续推进剩余报表对象（`u_itsm_rep_cust_info`、`u_itsm_rep_maintenance_daily*`）。
