# M005 Phase 1 rep_batch2 落地与映射扩展（2026-04-20）

## 文档信息
- 归档时间：2026-04-20
- 关键步骤主题：`M005 (itsm02.pbl)` 第二批四条报表对象批量落地（**M005 报表对象全部收口**）
- 对应主文档：`docs/core/项目整体计划与进展_2026-03-11.md`

## 范围定义

### PB 对象范围
- `u_itsm_rep_cust_info`
- `u_itsm_rep_maintenance_daily`
- `u_itsm_rep_maintenance_daily_m`
- `u_itsm_rep_maintenance_daily_ym`

### SQL 映射范围
- 本次新增映射：`S096~S099`
  - `S096`：客户信息报表查询（`d_cust_info`）
  - `S097`：日常保养报表查询（`d_itsm_maintenance_daily_report`）
  - `S098`：日常维护月度汇总报表（`d_itsm_maintenance_plan_report`，参数 START_DATE/END_DATE）
  - `S099`：日常维护年月汇总报表（`d_itsm_maintenance_plan_ym_report`，参数 IN_YM YYYYMM）

## 已落地产物清单
- `app/repositories/rep_cust_info_repository.py`
- `app/services/rep_cust_info_service.py`
- `app/api/rep_cust_info.py`
- `app/repositories/rep_maintenance_daily_repository.py`
- `app/services/rep_maintenance_daily_service.py`
- `app/api/rep_maintenance_daily.py`
- `app/repositories/rep_maintenance_daily_m_repository.py`
- `app/services/rep_maintenance_daily_m_service.py`
- `app/api/rep_maintenance_daily_m.py`
- `app/repositories/rep_maintenance_daily_ym_repository.py`
- `app/services/rep_maintenance_daily_ym_service.py`
- `app/api/rep_maintenance_daily_ym.py`
- `app/__init__.py`（新增四个报表蓝图注册）

## PB 规则对齐说明

### rep_cust_info
- 数据源：`TMM21_CUSTCLASS + TMM22_CUSTOMERS + TMM46_AREA + TMM35_CUST_POS_RL`
- 过滤参数：`custcard/classcd/custnm/busityp/useflg/opendate_from/opendate_to/pptcode/zftype`
- 设备关联：`TMM35_CUST_POS_RL`（USEFLG='1'）取每门店最新设备

### rep_maintenance_daily
- 数据源：`TIT17_MAINTENANCE + TMM22_CUSTOMERS + TIT17_CUST_POS_DAILY`
- 按 `daily_maintenance_id` GROUP BY 聚合，支持日期区间/磁卡号/工程师/状态/配件过滤
- 主键逻辑来自 `d_itsm_maintenance_daily_report.srd`

### rep_maintenance_daily_m（月度汇总）
- 数据源：`V_ITSM_MD_SUM`
- 参数：`START_DATE/END_DATE`（date 类型）
- 关键规则：`NVL(close_date,:start_date)>=:start_date AND NVL(close_date,:end_date)<=:end_date+1`
- 输出列：`area/store_sum/store_sum1/count_sum/store_sum0/double_count`

### rep_maintenance_daily_ym（年月汇总）
- 数据源：`TIT17_MAINTENANCE_PLAN + TIT17_MAINTENANCE + TMM22_CUSTOMERS`
- 参数：`IN_YM`（YYYYMM 字符串，service 层做6位正则校验）
- 关键规则：计划数从 `TIT17_MAINTENANCE_PLAN WHERE PLAN_YYMM=:in_ym`，完成数从 `TIT17_MAINTENANCE` 取 `current_status='3'` 且 `close_time` 在当月范围内
- 输出列：`area/plan_qty/count_sum`

## 校验记录
- `python -m compileall`（本批 12 个新文件 + `app/__init__.py`）：✅ 通过
- `ruff check`（同范围）：✅ 通过

## 阶段结论
- **M005 全部 7 条报表对象落地完成**（分两批：batch1 3个 + batch2 4个）。
- M005 itsm02.pbl 模块所有已识别报表对象均已完成三层架构落地，进入一致性校验阶段。
