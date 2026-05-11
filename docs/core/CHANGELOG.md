# 变更日志

所有重要变更均记录在此文件中。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [v0.8.1] — 2026-05-11 — 系统参数清理

- 标记 5 个零售遗留字段为废弃（costtype/centralwarehouse/poinvaliddays/soinvaliddays/shopbilltype）
- 新增 3 个 ITSM 全局参数（jwt_expiration_seconds/log_retention_days/max_upload_size_mb）
- ParamsList.vue 改为 3 分组表单（认证安全/系统运维/路径配置），6 字段
- allowmultilogon 接入登录流程，登出 API + token 活跃管理
- SysCode 模型加 memo 字段，tit03→tmm31 字典合并完成

---

## [v0.8.0] — 2026-05-10 — F1 前端地基完成 + 字典表合并 + 数据修复

### 新增
- **行政区域表迁移**：新增 tmm02_country(192)/tmm03_province(34)/tmm04_city(436)/tmm05_town(2778)
- **客户行政区域回填**：11,022条 country_cd=191/prvn_cd=09，按分类名+地址匹配 city_cd
- **预计划关联**：6927条 source_type=PREPLAN，preplan_id 通过磁卡号关联 plan_cust
- **物料分类树**：ItemList.vue CTE递归树+表格联动，CRUD+搜索互斥
- **客户管理重写**：52字段全展示，9分组折叠编辑，6码表下拉，详情/编辑对等
- **EID设备管理**：复用物料分类树(含EID角标)，7码表下拉，变更历史(type=i/u/d)
- **前端类型安全**：master.ts 严格interface，分组码表映射(codeMaps)

### 变更
- **tit03_syscodes→tmm31_syscodes**：75条ITSM字典迁入，ItsmSysCode模型移除
- **新增31条业务码表**：CS/SRC/ES/ET/NO/IU/OD/SS/PS/QS
- **itemclass parent_cd修复**：从ortopbitsmdb同步186条
- **SysCode模型加memo字段**

### 数据修复
- 客户状态/来源初始化(11020条ACTIVE+MANUAL)
- 物料分类parent_cd回填(186条)
- 行政区域回填(按分类名+地址匹配)
- 预计划来源识别(PREPLAN 6927条)

### 文档
- 新增 客户主数据字段规范.md
- 更新 前端vue3-setup.md(实施记录)、迁移计划(Phase7补充)、CORE_DOCS_INDEX

---

## [v0.7.0] — 2026-05-08 — 数据迁移完成 + 模块补全

**PR**: [#7](https://github.com/CheungJan/myitsm/pull/7) / [#8](https://github.com/CheungJan/myitsm/pull/8)

### 新增
- **数据迁移工具**：双PG连接器 + 动态字段映射 + 5批执行引擎 + CLI入口（`app/migration/`）
- **逐表校验测试**：14 个参数化行数对比测试
- **资产盘点模块**：AssetCheckAccept Repository + Service + API（6端点）
- **POS设备变更模块**：PosChange Repository + Service + API（4端点）

### 数据迁移结果
- 86 表完全匹配，总体完整率 **99.6%**（3,339,020/3,353,080 行）
- 7 大问题全部修复（OFFSET不一致、CHAR空格、NOT NULL默认值、id FK断裂等）

### 文档
- 新增 数据迁移执行方案 v2、数据迁移问题解决报告、Oracle核查导出指南
- 更新 项目整体实施计划 v1.3、API接口文档 v1.2、系统功能分析 v1.3、文档体系审查报告、数据库ER关系文档 v2.1

---

## [v0.6.0] — 2026-05-07 — 阶段6 事务查询与报表模块

### 新增
- **全模块单据统一查询**：跨 9 种单据类型 UNION ALL 联合查询，支持按类型/门店/状态/日期/关键字筛选
- **错账更正（红蓝单冲销）**：原单标记冲销（redflg）+ 审计日志记录
- **进销存汇总**：按物料+仓库聚合期初/入库/出库/期末
- **库存报表**（3端点）：库存快照 + 库存预警清单 + 库存变动流水
- **EID 追踪报表**（2端点）：EID 全生命周期追踪 + 单个 EID 变更追溯明细
- **销售报表**（2端点）：销售状态汇总统计 + 未结单据清单
- **BOM 结构树报表**

### 文件
- `app/api/transactions.py` — 事务查询蓝图（4端点）
- `app/api/reports.py` — 报表蓝图（8端点）
- `app/services/transaction_service.py` / `report_service.py`
- `app/repositories/transaction_repository.py` / `report_repository.py`
- `app/schemas/transaction.py` / `report.py`

---

## [v0.5.0] — 2026-04-27 — 阶段5 Tier-2/3 完整实现

**PR**: [#6](https://github.com/CheungJan/myitsm/pull/6)

### 新增
- **结算管理 (G4)**：结算规则/账单/账单明细/结算批次，4个模型 + 12个 API 端点
- **财务应收应付 (G5)**：会计科目/应收/应付/收付款/设备折旧，5个模型 + 15个端点
- **客户自助服务门户 (G9)**：门户用户/自助报修/服务评价，3个模型 + 9个端点
- **MES 生产制造 (G7)**：生产工单/工序定义/工单工序/物料消耗，4个模型 + 10个端点
- **IoT 数据监控 (G8)**：设备接入/数据采集/报警规则/报警记录，4个模型 + 10个端点
- 项目整体实施计划文档 (`docs/core/项目整体实施计划.md`)
- 系统功能对比分析与扩展规划文档
- 全阶段模型字段核对报告

### 修复
- Portal 用户密码改为服务端哈希存储（原为明文）
- 所有 create/update 端点统一传播 `g.current_user` 至 `opercd` 审计字段
- Depreciation eid 唯一约束
- AlertLog acknowledge 自动填充 ack_user
- RepairRequest.submit_time / ServiceRating.rating_time 创建时自动赋值

### 变更
- 项目文件结构重组：PB 源码统一至 `PBsrc/`，旧重构代码移至 `_backup/`
- 旧重构文档归档至 `docs/archive/`
- AGENTS.md / CORE_DOCS_INDEX.md 全面更新

---

## [v0.4.0] — 2026-04-26 — 阶段4 辅助模块 + Tier-1 扩展

**PR**: [#5](https://github.com/CheungJan/myitsm/pull/5)

### 新增
- **考勤管理**：TKQ01/TKQ02，2个模型 + 3个端点
- **库存预警**：TIV01/TIV02，2个模型 + 4个端点
- **价格管理**：TIP01/TIP03，2个模型 + 4个端点
- **押金管理**：TMM61 系列5个模型 + 9个端点
- **合同管理 (Tier-1)**：THT01，8个端点
- **发票管理 (Tier-1)**：TAC01，8个端点
- **通知系统 (Tier-1)**：TNTF01/TNTF02，2个模型 + 7个端点（替代原飞信方案）

### 修复
- update 端点统一使用 `exclude_unset` 替代 `exclude_none`
- 7个 update 端点补充 `opercd` 更新
- `update_time` 不存在属性移除（`updated_at` 自动更新）
- `test_update_price` 错误端点修正

---

## [v0.3.0] — 2026-04-25 — 阶段3 仓储/采购/销售/SLA

**PR**: [#4](https://github.com/CheungJan/myitsm/pull/4)

### 新增
- **仓储管理**：15个模型（仓库/库区/库位/入库/出库/余额/流水/盘点/调拨）+ 13个端点
- **采购管理**：10个模型（计划/登记/单据/退货/供应商评价/合同）+ 13个端点
- **销售管理**：4个模型（预计划/单据/延期）+ 11个端点
- **SLA 服务级别管理 (Tier-1)**：2个模型（SLA定义/工单监控）+ 8个端点
- 入库审核自动增加库存余额、出库审核自动扣减库存余额

### 修复
- `usseflg` 字段拼写错误修正
- SLA 统计 `avg_response` 缺少 `sla_id` 过滤

---

## [v0.2.0] — 2026-04-24 — 阶段2 ITSM 核心迁移

**PR**: [#3](https://github.com/CheungJan/myitsm/pull/3)

### 新增
- **ITSM 字典表**：6个模型（故障类型/服务类型/优先级/状态定义/变更类型/设备类型）
- **日常维护单 (TIT10)**：MaintenanceDaily + PosDetail + MainTrack，5个端点
- **新机开通 (TIT13-14)**：MaintenanceOpen + EquipmentOpen，4个端点
- **旧机翻新 (TIT15)**：MaintenanceRenovate + EquipmentRenovate，4个端点
- **设备变更 (TIT16)**：DeviceChange，4个端点
- **门店关闭 (TIT18)**：StoreClose，4个端点
- **日常保养 (TIT17)**：Maintenance + CustPosDaily
- **免费更换 (TIT19)**：FreeReplace
- **回收任务 (TIT20, P0-1/优化4.2)**：RecycleTask + RecycleTaskDtl，7个端点（取机/回收从日常维护剥离为独立业务）
- **公用附表 (TIT23-27)**：D2D/RV/AccessoriesUpdate/Dispatch/CloseBill，10个端点
- **统一状态机**：`MaintenanceState`（NEW→ASSIGNED→IN_PROGRESS→COMPLETED→CLOSED）
- **P0-4 优化**：DeviceChange CK 变更完成时自动保存磁卡号历史到 CustomerHistory

### 修复
- `_do_transition` 补充 `update_time`/`updator` 审计字段更新
- `db.session.commit()` 移至各 Service 的 transition 方法确保事务原子性
- HTTP 状态码统一（审核/流转成功返回 200 而非 201）
- 状态机 fallback 问题修正
- CustomerHistory 字段映射修正

---

## [v0.1.0] — 2026-04-23 — 阶段1 基础架构

**PR**: [#2](https://github.com/CheungJan/myitsm/pull/2)

### 新增
- **Flask 应用工厂**：`create_app()`，支持 development/testing/production 配置切换
- **JWT 认证**：`login_required` 装饰器 + Bearer Token 验证
- **统一响应**：`success_response()` / `error_response()`，含 request_id 追踪
- **系统管理（11个模型）**：User/Menu/Role/UserGroup/UserGroupMember/UserRole/RoleMenu/Department/SysParm/CodeTable/AuditLog
- **主数据（13个模型）**：Customer/Store/Product/ProductPrice/PosModel/CustPosRl/CustomerHistory/CustomersHistory/Area/Engineer/Supplier/Equipment/EquipmentType
- **API 蓝图**：health(1) + auth(2) + system(8) = 11个端点
- **CI 流水线**：GitHub Actions 质量门禁（black/isort/ruff/mypy/pytest/bandit）
- **BaseModel 基类**：TimestampMixin（created_at/updated_at/opercd）
- `.env.example` 环境变量模板
- `pyproject.toml` 项目配置

---

## [v0.0.1] — 2026-04-22 — 需求文档

**PR**: [#1](https://github.com/CheungJan/myitsm/pull/1)

### 新增
- ITSM 重构项目需求设计文档（PB 源码全面分析 + 25个 PBL 模块梳理 + 4项优化方案 + 5阶段重构路线图）
- 数据库字典精简版
- PB→Python SQL 映射表
- AGENTS.md 项目规则
- CORE_DOCS_INDEX.md 文档索引
