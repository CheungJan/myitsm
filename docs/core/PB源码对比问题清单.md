# PB 源码对比 — 问题清单（按优先级排序）

> 检查时间：2026-05-16 | 范围：F2（销售/仓储/采购/质检/ITSM）+ F3（押金/考勤/价格/调拨/结算/财务/门户/合同/通知/SLA/MES/IoT）

## P0 — 阻塞试运行（整单/整模块缺失）

| # | 模块 | 问题 | PB 源 | 当前状态 |
|---|------|------|-------|---------|
| 1 | **ITSM** | 免费更换工单整单缺失 | `itsm02.pbl` u_itsm_free_replace + w_r_itsm_replace | TIT28 主表+明细模型已建，API/Service/Repo 全缺 |
| 2 | **仓储** | 盘盈盘亏模块缺失 | `wh_syc.pbl` u_wh_overlost_add/audit | TWH17/18/18EID 模型已建，API/Service/Repo 全缺 |
| 3 | **采购** | 采购退货 API 路由缺失 | `purchase.pbl` TPC16_RPCBILL / TPC17 | Service/Repo 已实现，仅 API 蓝图未注册路由 |

## P1 — ITSM 附表缺失（模型已有，影响工单完整性）

| # | 模块 | 问题 | PB 使用场景 | 当前状态 |
|---|------|------|-----------|---------|
| 4 | **ITSM** | 收费记录 (TIT26_PAYLIST) | 日常维护窗口 tab，关单时写入 | 模型已建，无 Service/Repo/API |
| 5 | **ITSM** | 维护单责任豁免 (TIT10_LIABILITY) | 日常维护回收入库时 UPDATE | 模型已建，无 Service/Repo/API |
| 6 | **ITSM** | 责任豁免字典 (TIT02_LIABILITYREG) | 责任豁免配置 | 模型已建，无 Service/Repo/API |
| 7 | **ITSM** | 附件管理 (TIT11_MAINTENANCE_ATTC) | 回收入库时引用 | 模型已建，无 Service/Repo/API |
| 8 | **ITSM** | 未关单跟踪 (TIT29_NOCLOSE_TRACK) | 超时未关单监控 | 模型已建，无 Service/Repo/API |
| 9 | **ITSM** | 报修信息 (TIT05_REPAIRINFO) | 客户报修登记 | 模型已建，无 Service/Repo/API |
| 10 | **ITSM** | 时间点级别 (TIT01_TIMEPOINT_AREA) | SLA 区域响应时间 | 模型已建，无 Service/Repo/API |
| 11 | **ITSM** | 开通选择明细 (TIT19_ON_CHOOSEDT) | 免费更换窗口 INSERT | 模型已建，无 Service/Repo/API |
| 12 | **ITSM** | 换机配件明细 (TIT10_POS_DETAIL) | 日常维护换机流程 | 模型已建，无 Service/Repo/API |
| 13 | **ITSM** | 状态变更轨迹 (TIT10_MAIN_TRACK) | 报表引用 | 模型已建，无 Service/Repo/API |

## P2 — API 不完整（部分工单缺少写操作）

| # | 模块 | 问题 | 当前状态 |
|---|------|------|---------|
| 14 | **ITSM** | 日常保养 (TIT17) 只有 list+get，无 create/update/transition | PB 有完整 u_itsm_maintenance_plan |
| 15 | **采购** | 采购计划状态 (TPC03) 无 API | 模型已建，Service/Repo/API 全缺 |
| 16 | **调拨** | 调拨入/出库 (u_trans_in/out) 无 API | transactions.py 只有单据查询和错账更正 |

## P3 — 报表缺失

| # | 模块 | 缺失报表 |
|---|------|---------|
| 17 | **ITSM** | 9 个报表：归档统计/完成率/客户汇总/维护日报/未关单/操作频率/审批统计/异常汇总/每日明细 |
| 18 | **QC** | 2 个报表：产品统计 (u_qc_rep_cptj) / 结果报表 (u_qc_rep_result) |
| 19 | **押金** | 押金报表 (u_deposit_report) / 资产报表 (u_asset_report) |
| 20 | **考勤** | 考勤统计报表 (u_kq_rep_tj) |

## P4 — F3 功能缺失

| # | 模块 | 问题 |
|---|------|------|
| 21 | **押金** | 缺少确认/审核流程 (u_deposit_confrim) |
| 22 | **考勤** | 缺少批量导入 (u_kq_imp) / 考核评分 (u_pf_list) |
| 23 | **价格** | 缺少标签管理 (u_mm_label, TMM40_LABEL) / POS状态 (u_mc_posstatus) |
| 24 | **全局** | 8 个模块均未实现 DELETE 端点 |

## P5 — 前端字段展示不足

| # | 模块 | 问题 |
|---|------|------|
| 25 | **销售/仓储/采购/ITSM** | 列表页展示列数普遍只有 PB DataWindow 的 40-60%，缺少关键业务字段 |

---

## 本次会话已修复（feature/f2-business-chain 未提交）

- 归档模块（TIT12）→ ArchiveList.vue + archive_service/repo
- 质检录入 → QcInput.vue + qc_service/repo/schema
- 状态机扩展 → state_machine.py +100 行
- 仓库服务/ITSM API 字段扩展
