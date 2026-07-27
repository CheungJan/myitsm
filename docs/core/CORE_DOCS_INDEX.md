# 核心文档索引（docs/core）

## 说明

- 核心文档 = 全局重要、长期维护的参考文档。阶段性报告、功能调试手册不在此列。
- 核心文档实体统一存放在 `docs/core/`，后续开发前从此索引定位。
- 最后更新：2026-07-27（1a 阶段设备资产联动+业务规则全部完成，38 测试用例）

---

## A 类：项目管理文档

1. **ITSM 重构项目需求设计文档**（PB 源码全面分析 + 优化方案 + 重构路线图）
   - `docs/core/ITSM重构项目需求设计文档.md`

2. **项目整体实施计划**（后端/数据库迁移/前端/部署/里程碑）
   - `docs/core/项目整体实施计划.md`

3. **系统功能对比分析与扩展规划**（已有功能映射 + Tier-1/2/3 优先级）
   - `docs/core/系统功能对比分析与扩展规划.md`

4. **前端开发方案**（Vue 3 + Element Plus，F1/F2/F3 阶段计划 + P0 增强清单）
   - `docs/superpowers/plans/2026-05-08-frontend-vue3-setup.md`
   - `docs/superpowers/specs/2026-05-14-F2业务主链前端权威设计文档.md`
   - 状态：F1 完成，P0 增强已实施（2026-05-13）

4. **全阶段模型字段核对报告**（阶段1-5全部138个模型逐表核对，已包含阶段1内容）
   - `docs/core/全阶段模型字段核对报告.md`

5. **变更日志**（全部版本变更记录，Keep a Changelog 格式）
   - `docs/core/CHANGELOG.md`
   - 最后更新：2026-05-13（v0.9.0）

---

## B 类：技术参考文档

6. **API 接口文档**（22个蓝图 ~250 端点，含结算/退货/执行看板等 43 采购端点）
   - `docs/core/API接口文档.md`
7. **数据库 ER 关系文档**（144个模型跨域关联 + Mermaid ER 图）
   - `docs/core/数据库ER关系文档.md`
8. **数据库字典（PostgreSQL 当前版）**（information_schema 导出，145 表完整字段/类型/注释，含 TPC14_DT, 2026-06-08 v1.1 列宽修正）
   - `docs/core/数据库字典_PostgreSQL当前版.md`
   - ⚠️ 旧版 `数据库字典_精简后_最终版.md` 为 Oracle 迁移基线，已归档为历史参考
9. **数据库变更追踪**（迁移后→P0→F2验收：新增12表+列宽修正11处）
   - `docs/core/数据库变更追踪_迁移后.md`
10. **客户主数据字段规范**（生命周期/来源类型/设备统计/行政区域匹配 + EidTrack 约定）
    - `docs/core/客户主数据字段规范.md`
11. **实施单资产同步开发规范**（维护单关闭时资产同步 + EidTrack 生成规则）
    - `docs/core/实施单资产同步开发规范.md`
12. **多点登录功能技术实现方案**（技术架构 + 数据模型 + 核心流程）
    - `docs/core/多点登录功能技术实现方案.md`
13. **PB 模块映射清单**（25 PB 模块 → Python 模块映射）
    - `docs/core/PB_TO_PYTHON_MODULE_MAPPING.csv`
14. **PB SQL 映射清单**（关键 SQL 语句迁移映射）
    - `docs/core/PB_TO_PYTHON_SQL_MAPPING.csv`
15. **测试策略文档**（24 采购测试通过，命名约定、质量门禁）
    - `docs/core/测试策略文档.md`
16. **采购结算单与退货功能设计方案**（2026-05-26，技术设计文档）
    - `docs/core/采购结算单与退货功能设计方案.md`（← `CJdocs/myitsm/` 链接）
17. **采购结算与退货功能代码修改汇总**（2026-05-26，实施总结）
    - `docs/core/采购结算与退货功能代码修改汇总.md`
18. **采购结算与退货功能操作手册**（2026-05-27，用户手册）
    - `docs/core/采购结算与退货功能操作手册.md`
19. **采购-仓库-质检跨模块流程衔接设计**（2026-05-27，技术设计文档）
    - `docs/core/采购-仓库-质检跨模块流程衔接设计.md`
20. **仓库模块重构方案**（2026-05-27，技术设计 spec）
    - `docs/superpowers/specs/2026-05-27-warehouse-module-plan.md`
21. **仓库模块实施计划**（2026-05-27，代码改动 + 迁移脚本 + 执行顺序）
    - `docs/superpowers/plans/2026-05-27-warehouse-module-impl.md`
22. **仓库模块实施进度与后续计划**（2026-05-28，P0/P1/P1.5/P2 验收状态）
    - `docs/core/仓库模块实施进度与后续计划.md`
23. **仓库模块操作手册**（2026-05-28，入库/出库/库存/盘点/报表操作指南）
    - `docs/core/仓库模块操作手册.md`
24. **仓库模块出入库联动设计**
    - `docs/superpowers/specs/2026-05-30-warehouse-full-design.md`
25. **后续开发计划：仓库管理与业务主链联动**
    - `docs/core/后续开发计划_仓库与业务主链.md`
26. ⚠️ ~~MES/QC/仓库联动技术文档 v1~~（已被 #29 v2 取代）
27. **上门服务与配件收费优化方案**（A→D 阶段完整方案 + 实施路线 + 验收）
    - `docs/myitsm/上门服务与配件收费优化方案.md`
    - `docs/myitsm/上门服务与配件收费优化方案_验收手册.md`
28. **日常维护单据状态管理优化方案**（关单即落地 + 状态机扩展 + 11 项联动清单 + 1a/1b 实施路线）
    - `docs/myitsm/日常维护单据状态管理优化方案.md`
    - `docs/core/1a阶段实施计划.md`（2026-07-27 全部完成，设备资产联动+业务规则，27 任务 D1-D8/C1-C9/V1-V3 详细设计，对齐 EAM/FSM 六层模型 BM_S 8 档+Entitlement 6 级优先级，38 测试用例）
    - 状态：✅ 1a 阶段全部完成（2026-07-27，分支 `feature/1a-asset-entitlement`）
29. **故障代码体系优化技术文档**（tit04_archivecode 三级树形字典 + 配件关联映射）
    - `docs/myitsm/故障代码体系优化技术文档.md`
    - `docs/core/MES_QC_Warehouse_Technical_Document.md`
27. ⚠️ ~~MES/QC/仓库联动操作手册 v1~~（已被 #30 v2 取代，验收步骤以 v2 为准）
    - `docs/core/MES_QC_Warehouse_Operation_Manual.md`
28. **文档体系覆盖审计报告**（2026-06-07，MES/QC/仓库文档 vs 代码 vs 前端覆盖检查）
    - `docs/core/DOCUMENTATION_COVERAGE_AUDIT_20260607.md`
29. **MES/QC/仓库联动业务流程与技术实现 v2**（2026-06-09，4主线+2子流程+IQC/IPQC/FQC边界，含生产工单QC_PENDING状态机）
    - `docs/core/MES_QC_Warehouse_业务流程与技术实现_v2.md`
30. **MES/QC/仓库联动验收操作手册 v2**（2026-06-09，4模式+3QC类型验收步骤、状态机验收、数据一致性验收、验收检查清单）
    - `docs/core/MES_QC_Warehouse_验收操作手册_v2.md`

31. **生产质检与物料消耗优化实施文档**（2026-06-12，FQC 行级判定+更换+反审核+TMS04 扩展+补料 API，五阶段代码已完成）
    - `docs/core/生产质检与物料消耗优化实施文档.md`
    - 状态：五阶段代码完成，待功能测试

32. **FQC 优化与补料方案统一实施计划**（2026-06-12，三阶段路线图，Phase 0–3 已实现）
    - `docs/core/FQC优化与补料方案统一实施计划.md`
    - 状态：Phase 0–3 已实现，前端成本汇总页待后续

33. **预计划设备来源与 EID 绑定专项设计**（2026-06-30，TWH11/TMM43_EID 联动分析、list_available_eids API、EID 绑定模式讨论、销售实施全链路规划）
    - `docs/core/预计划设备来源与EID绑定专项设计.md`
    - `docs/core/预计划设备来源与EID绑定_前端操作验收手册.md`（2026-07-02，前端操作验收手册，15 项检查清单）
    - 状态：✅ 全部完成（方案 A/B 全链路 + 11a-g + 方案 A 专属功能，212 passed）

34. **PB 预计划 plantyp=10 磁卡号变更业务流程分析**（2026-07-02，基于 PB 源码 + Oracle 存储过程源码 + 数据库数据三方交叉验证，含 USP_PLAN_IMPLE/USP_PLAN_CONFRIM/USP_ITSM_TRANS_IN/USP_TRANS_IN_CONFRIM 完整分析，BG/CK/BQ 三种子类型真实来源辨析）
    - `docs/core/PB预计划plantyp10磁卡号变更业务流程分析.md`
    - 状态：✅ 定稿（重构对齐基线）

35. **客户状态与磁卡号变更优化设计**（2026-07-02 升级为核心文档，客户生命周期 TEMP→PENDING→ACTIVE→INVALID 四态机 + 磁卡号变更 CK/BQ/BG 业务优化 + PB SP 权威逻辑还原）
    - `docs/core/客户状态与磁卡号变更优化设计.md`
    - 状态：✅ 定稿（2026-07-02 对齐 PB USP_PLAN_IMPLE 硬编码 CK，更新 §2.4/§3/§5.2/§11.5）

36. **预计划出库流程优化设计**（2026-07-06，is_outflag 三态语义 N/A/0/1 + pos_from='00' 出库判定 + 出库入口迁实施模块 + 方案B 批量出库）
    - `docs/core/预计划出库流程优化设计.md`
    - 状态：✅ P0-P3 全部完成（三态+门槛+入口迁移+批量出库）

37. **预计划 plantyp 下游单据与单号前缀规则**（2026-07-10，5 种 plantyp 的权威参考：系统字典定义 → 下游 ITSM 单据路由 → 单号前缀规则 → PB 原版对照 → IdMaster 号段清单，含 CG/ST→GB、R→RC 修正记录）
    - `docs/core/预计划plantyp下游单据与单号前缀规则.md`
    - 状态：✅ 定稿（2026-07-10 完成命名统一 + 前缀修正 + 系统字典更新）

38. **ITSM 单据主子表与业务操作现状分析**（2026-07-10，初始版。2026-07-11 更新：修正状态机描述 + P0 PUT 端点补齐 + 前端流转按钮 + 回收明细 DELETE）
    - `docs/core/ITSM单据主子表与业务操作现状分析.md`
    - 状态：✅ P0-P3 全部完成

40. **ITSM 详情页 UI 优化统一设计方案**（2026-07-11，整合 Windsurf 规划与讨论共识：PB 五区域模式 + 行业 ITSM 对标 + 6 项前置决策 + 7 类单据 Tab 矩阵 + 收费自动判断 + 通用组件设计 + 实施路线 P0-P4）

41. **数据流与代码链路详解 — 以通讯方式为例**（2026-07-13，教学文档：以 MDA33257 日常维护单为例，逐层追踪"通讯方式"从 PostgreSQL → ORM → Service 字典翻译 → API → 浏览器渲染的完整 8 层代码链路，含编码翻译模式总结与同类字段速查表）
    - `docs/core/数据流与代码链路详解_以通讯方式为例.md`
    - 状态：✅ 定稿
    - `docs/core/ITSM详情页UI优化统一设计方案.md`
    - 状态：✅ 定稿，P0 实施基线

39. **PB Oracle 数据库对象导出清单**（2026-07-11，从 PB 原 Oracle 库 CCGL_TEST 全量导出 286 个数据库对象源码：49 存储过程 + 22 函数 + 21 视图 + 15 序列 + 160 索引 + 12 触发器 + 1 包 + 5 类型，存放 `PBsrc/pb_oracle_*/`，含关键 SP/函数/视图/触发器业务作用与重构对应关系映射）
    - `docs/core/PB_Oracle_数据库对象导出清单.md`
    - 状态：✅ 定稿（PB→Python 重构的数据库侧权威参考）

42. **区域人员管理与自动派单技术方案**（2026-07-14，PB u_mc_area/d_mc_area_list/d_mc_area_form/d_mc_areausers 功能重构 + UserArea 模型修复 + Area CRUD + 自动派单 store_id→area_cd→usercd 链路 + 派工 Tab maintenance_type 清理）
    - `docs/core/区域人员管理与自动派单技术方案.md`
    - 状态：✅  方案定稿，已实施

43. **派工与通知优化技术方案**（2026-07-15，6个UI/校验问题修复 + 派单规则引擎 tit30_dispatch_rule + tmc12_groups.leader_cd 组长 + 派工创建自动建Notification + 派工Tab编辑通知入口 + 维护单列表"派给我/本区域"Tab + 对齐PB of_newfetion/w_r_itsm_fetion 飞信流程）
    - `docs/core/派工与通知优化技术方案.md`
    - 状态：✅  方案定稿，已实施

44. **上门服务与配件收费优化方案**（2026-07-19，PB 三 Tab 业务逻辑分析 + 重构现状对比 + 优化设计 + 实施路线图 A/B/C/D 四阶段 + 18 项待确认事项全部已确认 + 落地优先级与状态总览）
    - `docs/myitsm/上门服务与配件收费优化方案.md`
    - 状态：🟡 阶段 A/C 部分落地（四要素字段+拼句+CLOSURE_REASON 字典+PAY_SVC 字典+工程师虚拟仓治理已生成迁移），A3 前端/B2-B4/C1-C2/C6-C7/D1-D2 待落地
    - 当前处理事项：按 §8.1 落地顺序推进 A 阶段剩余（A1 gzdm/gzdl/gzxl/device_id/accessories_id 字段 + A3 前端离店弹窗 + A4 测试）

---

## C 类：数据迁移与治理文档（历史基线）

> 以下为迁移时（2026-05-08）的基线文档，表结构与字段类型为迁移时状态。当前权威参考：`数据库ER关系文档.md`。

15. **数据库字典**（Oracle 迁移基线，130 表/Oracle 类型，P0 字段已补）
    - `docs/core/数据库字典_精简后_最终版.md`
    - 状态：⚠️ 历史基线，以 ER 文档为准

16. **数据迁移执行方案 v2**（迁移过程记录，表分类为迁移时状态）
    - `docs/core/数据迁移执行方案_v2.md`
    - 状态：✅ 已执行（99.6%）

17. **数据迁移问题解决报告**（7 大问题修复记录）
    - `docs/core/数据迁移问题解决报告.md`

18. **P0 数据治理记录**（批量修复 + 自动纠正机制 + 回滚方案 + 已知待处理）
    - `docs/core/P0数据治理记录.md`
    - 状态：✅ 已执行

18. **数据迁移实施计划**（writing-plans 生成）
    - `docs/superpowers/plans/2026-05-08-ortopbitsmdb-to-myitsm-migration.md`

19. **迁移工具代码**
    - `app/migration/`（config / connector / field_mapper / batch_runner）
    - `migrate_data.py`（CLI 入口）
    - `tests/test_migration_*.py`（3 个测试文件）

---

## D 类：交付与验收文档

20. **迁移验收清单（DoD）**
    - `docs/core/PB_TO_PYTHON_DOD_CHECKLIST.md`

21. **发布与回滚清单**
    - `docs/core/PB_TO_PYTHON_RELEASE_ROLLBACK_CHECKLIST.md`

22. **PB→Python 重构执行模版**（通用方法论）
    - `docs/core/PB_TO_PYTHON_MIGRATION_TEMPLATE.md`

---

## E 类：历史参考（非核心，仅供追溯）

以下文档为阶段性产物或已过时，不纳入核心体系，仅供历史追溯：

- `docs/core/阶段1_模型字段核对报告.md` — 已被 #4 全阶段报告包含
- `docs/core/PB_TO_PYTHON_OPTIMIZATION_REQUIREMENTS.md` — 设计阶段方案（Oracle DDL，与实际实现差异大）
- `docs/core/多点登录功能故障排查手册.md` — 功能调试文档
- `docs/core/文档体系审查报告.md` — 一次性审查报告
- `docs/core/采购需求审核数量问题技术分析报告.md` — 调试经验总结（el-input-number :max 陷阱）
- `docs/archive/` — 旧重构（2026-03-11）全部资料

---

## 项目目录结构

```
myitsm/
├── AGENTS.md                  # 项目规则与约定
├── README.md                  # 开发环境搭建指南
├── app/                       # Flask 后端代码
│   ├── api/                   # 蓝图层（20个模块 205 端点）
│   ├── models/                # SQLAlchemy 模型（144个）
│   ├── services/              # 业务逻辑层
│   ├── repositories/          # 数据访问层
│   ├── schemas/               # Pydantic 校验
│   ├── migration/             # 数据迁移工具
│   └── extensions/            # Flask 扩展
├── frontend/                  # Vue 3 + Element Plus 前端
├── tests/                     # 测试用例（148+）
├── migrations/                # Alembic 数据库迁移
├── docs/
│   ├── core/                  # 核心文档（本索引）
│   ├── myitsm/                # ITSM 模块专项文档（优化方案/验收手册）
│   ├── superpowers/plans/     # 实施计划
│   ├── superpowers/specs/     # 头脑风暴设计文档
│   └── archive/               # 归档文档
├── scripts/                   # 运维脚本
├── PBsrc/                     # PB 原始源码
├── pyproject.toml
└── wsgi.py
```

## 后续约定

- 新增核心文档 → 写入 `docs/core/`，同步更新本索引
- 功能调试文档 → 不纳入核心索引，功能稳定后可归档
- 阶段性报告被新报告覆盖 → 移入 E 类历史参考
