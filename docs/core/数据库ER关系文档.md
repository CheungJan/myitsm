# 数据库 ER 关系文档

**版本**: v2.1  
**更新日期**: 2026-05-08  
**模型总数**: 138个业务模型（BaseModel 为公共基类，不计入）  
**本次更新**: 资产盘点/POS变更模型已补全 Repository+Service+API 三层

> **v2.0 变更说明**：修正所有表名为实际 `__tablename__` 值，与 Oracle 数据库字典保持一致；
> 新增"Oracle 遗留表评估"章节，标注重构后不再需要的表。

---

## 一、全局设计原则

### 1.1 公共基类

所有业务模型继承 `BaseModel`（`app/models/base.py`），提供：
- `created_at` — 创建时间（自动赋值）
- `updated_at` — 更新时间（自动更新）
- `opercd` — 操作人代码

### 1.2 主键策略

- **等价迁移表**：保留 Oracle 原始业务主键（如 `custcd`、`maintenance_id`）
- **新增扩展表**：使用代理主键（自增 Integer）
- **原复合主键**：改为代理主键 + 唯一约束

### 1.3 外键约定

- 模型层通过 `db.ForeignKey` 声明关联关系
- 通过 `db.relationship` + `back_populates` 实现双向导航
- 级联删除仅在明细表上使用

---

## 二、业务域 ER 关系（按实际表名）

### 2.1 系统管理域（9个模型，system.py）

```
TMC01_MENUS (Menu)
  ├── TMC02_MENUSDT (MenuDetail) — 菜单明细
  └── TMC03_USERMENUS (UserMenu) — 用户菜单权限

TMC11_DEPARTMENTS (Department) — 部门

TMC12_GROUPS (Group) — 用户组
  └── TMC21_USERGROUP (UserGroup) — 用户-组关联
  └── TMC31_GROUPRIGHT (GroupRight) — 组权限

TMC13_USERS (User) — 系统用户
  └── TMC22_USERBUSITYP (UserBusiTyp) — 用户业务类型

TMC41_ACCLOG (AccLog) — 访问日志
TMC71_SYSPARM (SysParm) — 系统参数
```

| 模型 | 实际表名 | 主键 | 说明 |
|------|---------|------|------|
| Menu | tmc01_menus | menucd | 系统菜单 |
| MenuDetail | tmc02_menusdt | id | 菜单明细 |
| UserMenu | tmc03_usermenus | id | 用户菜单权限 |
| Department | tmc11_departments | deptcd | 部门 |
| Group | tmc12_groups | groupcd | 用户组 |
| User | tmc13_users | usercd | 系统用户 |
| UserGroup | tmc21_usergroup | id | 用户-组关联 |
| UserBusiTyp | tmc22_userbusityp | id | 用户业务类型 |
| GroupRight | tmc31_groupright | id | 组权限 |
| AccLog | tmc41_acclog | id | 访问日志 |
| SysParm | tmc71_sysparm | parmcd | 系统参数 |

---

### 2.2 主数据域（13个模型，master.py）

```
TMM01_COMPANY (Company) — 公司

TMM22_CUSTOMERS (Customer)
  ├── TMM35_CUST_POS_RL (CustPosRl) — 客户-设备关联
  └── TMM22_CUSTOMERS_HISTORY (CustomerHistory) — 磁卡号变更历史

TMM12_ITEMS (Item) — 物料
  └── TMM11_ITEMCLASS (ItemClass) — 物料分类

TMM19_SUPPLIERS (Supplier) — 供应商
  └── TMM18_SUPPLIERCLASS (SupplierClass) — 供应商分类

TMM21_CUSTCLASS (CustClass) — 客户分类
TMM31_SYSCODES (SysCode) — 系统编码
TMM34_IDMASTER (IdMaster) — ID生成器
TMM46_AREA (Area) — 区域
TMM47_COMMODE (ComMode) — 通讯方式
```

| 模型 | 实际表名 | 主键 | 说明 |
|------|---------|------|------|
| Company | tmm01_company | companycd | 公司主数据 |
| ItemClass | tmm11_itemclass | classcd | 物料分类 |
| Item | tmm12_items | itemcd | 物料/商品 |
| SupplierClass | tmm18_supplierclass | classcd | 供应商分类 |
| Supplier | tmm19_suppliers | suppcd | 供应商 |
| CustClass | tmm21_custclass | classcd | 客户分类 |
| Customer | tmm22_customers | cust_cd | 客户/门店主表 |
| CustomerHistory | tmm22_customers_history | id | 磁卡号变更历史（P0优化） |
| SysCode | tmm31_syscodes | codetyp+codecd | 系统编码字典 |
| IdMaster | tmm34_idmaster | id | ID 流水号生成器 |
| CustPosRl | tmm35_cust_pos_rl | id | 客户-设备关联（资产台账） |
| Area | tmm46_area | areacd | 区域 |
| ComMode | tmm47_commode | commodecd | 通讯方式 |

---

### 2.3 ITSM 核心域（30个模型，itsm.py + sales.py）

#### 核心主子表关系

```
TIT10_MAINTENANCEDAY (MaintenanceDaily) — 日常维护单
  ├── TIT10_POS_DETAIL (PosDetail) — 维护单配件明细
  ├── TIT10_MAIN_TRACK (MaintenanceDailyTrack) — 状态轨迹
  ├── TIT10_MAINTENANCE_LIABILITY — 豁免信息
  ├── TIT23_MAINTENANCE_D2D — 上门服务（公用）
  └── TIT25_ACCESSORIES_UPDATE — 配件更新

TIT13_MAINTENANCE_OPEN (MaintenanceOpen) — 新机开通单
  └── TIT14_EQUIPMENT_OPEN (EquipmentOpen)

TIT15_MAINTENANCE_RENOVATE (MaintenanceRenovate) — 旧机翻新单
  └── TIT15_EQUIPMENT_RENOVATE (EquipmentRenovate)

TIT16_DEVICE_CHANGE (DeviceChange) — 设备变更单
  └── TMM22_CUSTOMERS_HISTORY — 磁卡号变更记录

TIT17_MAINTENANCE (Maintenance) — 日常保养单
  ├── TIT17_CUST_POS_DAILY (CustPosDaily)
  └── TIT17_MAINTENANCE_PLAN (MaintenancePlan)

TIT18_STORE_CLOSE (StoreClose) — 门店关闭
TIT20_RECYCLE_TASK → TIT20_RECYCLE_TASK_DTL — 回收任务（P0优化新增）
TIT28_FREE_REPLACE → TIT28_FREE_REPLACE_DT — 免费更换
TIT29_NOCLOSE_TRACK — 未关单跟踪

PLAN_CUST (PlanCust) — 预计划
```

#### 主表（共享 MaintenanceState 状态机）

| 模型 | 实际表名 | 主键 |
|------|---------|------|
| MaintenanceDaily | tit10_maintenanceday | maintenance_id |
| MaintenanceOpen | tit13_maintenance_open | new_opening_id |
| MaintenanceRenovate | tit15_maintenance_renovate | renovate_id |
| DeviceChange | tit16_device_change | change_id |
| Maintenance | tit17_maintenance | maintenance_id |
| StoreClose | tit18_store_close | store_close_id |
| RecycleTask | tit20_recycle_task | recycle_id |

#### 子表/明细表

| 模型 | 实际表名 | 关联主表 |
|------|---------|---------|
| PosDetail | tit10_pos_detail | MaintenanceDaily |
| MaintenanceDailyTrack | tit10_main_track | MaintenanceDaily |
| MaintenanceLiability | tit10_maintenance_liability | MaintenanceDaily |
| EquipmentOpen | tit14_equipment_open | MaintenanceOpen |
| EquipmentRenovate | tit15_equipment_renovate | MaintenanceRenovate |
| CustPosDaily | tit17_cust_pos_daily | Maintenance |
| MaintenancePlan | tit17_maintenance_plan | Maintenance |
| RecycleTaskDtl | tit20_recycle_task_dtl | RecycleTask |
| FreeReplaceDt | tit28_free_replace_dt | FreeReplace |

#### 公用附表（跨业务单据复用）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| MaintenanceD2D | tit23_maintenance_d2d | 上门服务记录 |
| MaintenanceRV | tit24_maintenance_rv | 客户回访记录 |
| AccessoriesUpdate | tit25_accessories_update | 配件更新记录 |
| MaintenanceDispatch | tit21_maintenance_dispatch | 工单分派记录 |
| PayList | tit26_paylist | 收费记录 |
| CloseBills | tit27_close_bills | 关单记录 |

#### 字典表

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| TimepointArea | tit01_timepoint_area | 响应时间等级 |
| LiabilityReg | tit02_liabilityreg | 免责条例 |
| LiabilityRegDt | tit02_liabilityregdt | 免责条例明细 |
| ItsmSysCode | tit03_syscodes | ITSM 字典 |
| ArchiveCode | tit04_archivecode | 归档字典 |
| RepairInfo | tit05_repairinfo | 返修范围 |
| UserArea | tit06_userarea | 区域人员 |
| MaintenanceAttc | tit11_maintenance_attc | 维护单附表 |
| MaintenanceArchive | tit12_maintenance_archive | 归档表 |
| OnChooseDt | tit19_on_choosedt | 配件选取明细 |
| NoCloseTrack | tit29_noclose_track | 未关单跟踪 |

---

### 2.4 仓储域（14个模型，warehouse.py）

```
TWH01_WAREHOUSE (Warehouse)
  ├── TWH13_IN (StockIn) → TWH14_CHECKINDT (StockInDetail)
  ├── TWH15_OUT (StockOut) → TWH16_OUTDTEID / TWH16_OUTDTPRD
  ├── TWH17_OVERLOST (OverLost) → TWH18_OVERLOSTDT / TWH18_OVERLOSTEID
  ├── TWH11_DETAIL (StockDetail) → TWH12_DETAILDT (StockDetailDt)
  ├── TWH19_ASSET_C_A → TWH20_ASSET_C_A_DTL (资产盘点)
  └── TWH21_POS_CHANGE → TWH22_POS_CHANGE_DT (POS变更)
```

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| Warehouse | twh01_warehouse | 仓库主数据 |
| StockDetail | twh11_detail | 库存明细 |
| StockDetailDt | twh12_detaildt | 库存流水 |
| StockIn | twh13_in | 入库单（8种类型统一） |
| StockInDetail | twh14_checkindt | 入库明细 |
| StockOut | twh15_out | 出库单 |
| StockOutDetailEid | twh16_outdteid | 出库设备明细 |
| StockOutDetailPrd | twh16_outdtprd | 出库产品明细 |
| OverLost | twh17_overlost | 盘盈盘亏 |
| OverLostDt | twh18_overlostdt | 盘盈盘亏明细 |
| OverLostEid | twh18_overlosteid | 盘盈盘亏设备 |
| AssetCheckAccept | twh19_asset_c_a | 资产盘点 ✅ (repo+service+api) |
| AssetCheckAcceptDtl | twh20_asset_c_a_dtl | 盘点明细 ✅ |
| PosChange | twh21_pos_change | POS设备变更 ✅ (repo+service+api) |
| PosChangeDt | twh22_pos_change_dt | POS变更明细 ✅ |

---

### 2.5 采购域（10个模型，procurement.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| PurchasePlan | tpc01_pcplan | 采购计划 |
| PurchasePlanDt | tpc02_pcplandt | 计划明细 |
| PurchasePlanStatus | tpc03_pcplanstatus | 计划状态 |
| PurchaseRegister | tpc12_register | 采购登记 |
| PurchaseRegisterDt | tpc13_registerdt | 登记明细 |
| PurchaseBill | tpc14_pcbill | 采购单据 |
| ReturnPurchaseBill | tpc16_rpcbill | 退货单 |
| ReturnPurchaseBillDt | tpc17_rpcbilldt | 退货明细 |
| SupplierAppraisal | tpc20_suppappraisal | 供应商评价 |
| SupplierAppraisalDt | tpc21_suppappraisaldt | 评价明细 |

---

### 2.6 销售域（4个模型，sales.py + itsm.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| PlanCust | plan_cust | 预计划 |
| SalesBill | tsl10_slbill | 销售单据 |
| SalesExtend | tsl01_extend | 销售延期 |
| SalesExtendDt | tsl02_extenddt | 延期明细 |

---

### 2.7 辅助管理域

#### 考勤（2个，attendance.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| Attendance | tkq01_attendance | 考勤记录 |
| AttendanceCount | tkq02_attendancecount | 考勤月度汇总 |

#### 库存预警 + 价格（4个，inventory.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| Price | tip01_price | 价格规则 |
| AdjustPrice | tip03_adjprice | 调价记录 |
| InventoryLimit | tiv01_invlimit | 库存预警规则 |
| InventoryLimitHistory | tiv02_invlimit_hi | 库存预警历史 |

#### 押金（5个，deposit.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| Deposit | tmm61_deposit | 押金主表 |
| DepositDetail | tmm61_deposit_dtl | 押金变更明细 |
| DepositIO | tmm61_deposit_io | 押金出入记录 |
| DepositList | tmm61_deposit_list | 押金清单 |
| DepositPosModel | tmm61_deposit_posmodel | 型号押金标准 |

#### 合同 + 发票（2个，auxiliary.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| Contract | tht01_htgl | 合同管理 |
| Invoice | tac01_fpsk | 发票收款 |

---

### 2.8 Tier-1 扩展域

#### SLA 服务级别（2个，sla.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| SlaDefinition | sla_definition | SLA 定义 |
| SlaTicket | sla_ticket | SLA 工单监控 |

#### 通知系统（2个，notification.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| NotificationTemplate | tntf01_template | 通知模板 |
| Notification | tntf02_notification | 通知记录 |

---

### 2.9 Tier-2 扩展域

#### 结算（4个，billing.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| BillingRule | tbl01_billing_rule | 结算规则 |
| Bill | tbl02_bill | 账单主表 |
| BillDetail | tbl03_bill_detail | 账单明细 |
| BillingBatch | tbl04_billing_batch | 结算批次 |

#### 财务（5个，finance.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| Account | tfn01_account | 会计科目 |
| Receivable | tfn02_receivable | 应收 |
| Payable | tfn03_payable | 应付 |
| Payment | tfn04_payment | 收付款 |
| Depreciation | tfn05_depreciation | 设备折旧 |

#### 门户（3个，portal.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| PortalUser | tpt01_portal_user | 门户用户 |
| RepairRequest | tpt02_repair_request | 自助报修 |
| ServiceRating | tpt03_service_rating | 服务评价 |

---

### 2.10 Tier-3 扩展域

#### MES 制造（4个，mes.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| WorkOrder | tms01_work_order | 生产工单 |
| ProcessDef | tms02_process_def | 工序定义 |
| WorkProcess | tms03_work_process | 工单工序 |
| MaterialConsume | tms04_material_consume | 物料消耗 |

#### IoT 监控（4个，iot.py）

| 模型 | 实际表名 | 说明 |
|------|---------|------|
| DeviceConn | tio01_device_conn | 设备接入 |
| DeviceData | tio02_device_data | 设备数据 |
| AlertRule | tio03_alert_rule | 报警规则 |
| AlertLog | tio04_alert_log | 报警记录 |

---

## 三、跨域关键关联

| 源域 | 目标域 | 关联路径 | 说明 |
|------|--------|---------|------|
| ITSM | 主数据 | maintenance.custcd → tmm22_customers.cust_cd | 工单关联客户 |
| ITSM | 主数据 | device_change → tmm22_customers_history | 设备变更→磁卡号历史 |
| ITSM | 主数据 | cust_pos_rl.cust_cd → tmm22_customers.cust_cd | 设备关联客户 |
| 仓储 | 主数据 | stock_in/out.itemcd → tmm12_items.itemcd | 出入库关联物料 |
| 仓储 | 主数据 | stock_in/out.suppcd → tmm19_suppliers.suppcd | 出入库关联供应商 |
| 采购 | 主数据 | register.suppcd → tmm19_suppliers.suppcd | 采购关联供应商 |
| 销售 | 主数据 | plan_cust.custcd → tmm22_customers.cust_cd | 预计划关联客户 |
| 押金 | 主数据 | deposit_list.custcd → tmm22_customers.cust_cd | 押金关联客户 |
| SLA | ITSM | sla_ticket.maintenance_id → 各主表 | SLA 监控关联工单 |
| 门户 | ITSM | repair_request → tit10_maintenanceday | 自助报修转工单 |

---

## 四、Oracle 遗留表评估（33张无模型表）

以下为 `数据库字典_精简后_最终版.md` 中存在但当前无 Python 模型的表。
按重构后实际需要分为四类，**避免过度恢复不需要的表**。

### 4.1 已被替代/淘汰（不需要建模，共7张）

| Oracle 表 | 原用途 | 替代方案 | 不建模原因 |
|-----------|--------|---------|-----------|
| SYS_USER | 零售系统用户 | TMC13_USERS | 旧系统独立用户表，已合并到 TMC13 |
| SYS_ROLE_USER | 零售角色关联 | TMC21_USERGROUP + TMC31_GROUPRIGHT | 已合并到统一权限体系 |
| TIT22_FETION_SEND | 飞信发送记录 | TNTF02_NOTIFICATION | 飞信已于2021年停用，由通知系统替代 |
| TMC42_CONNECTINFO | PB连接信息 | Flask 会话管理 | PB 专属的 C/S 连接管理，B/S 架构不需要 |
| TMC43_LOGS | PB操作日志 | TMC41_ACCLOG | 旧日志表，统一到访问日志 |
| TMC44_SYSLOCK | PB并发锁 | 数据库行级锁 | PB 专属的表级锁机制，PostgreSQL 自带行锁 |
| TMC51_VERCTRL | PB版本控制 | Git + Flask-Migrate | PB 客户端版本管理，B/S 架构不需要 |

### 4.2 地理参考数据（可按需导入，暂不建模，共4张）

| Oracle 表 | 原用途 | 说明 |
|-----------|--------|------|
| TMM02_COUNTRY | 国家字典 | 标准地理参考数据，可作为 CSV 导入或在线接口 |
| TMM03_PROVINCE | 省份字典 | 同上 |
| TMM04_CITY | 城市字典 | 同上 |
| TMM05_TOWN | 乡镇字典 | 同上 |

### 4.3 ~~建议后续建模~~ → 已完成建模（业务必须，共14张）

> **已全部建模完成**。这14张表均为业务核心所需（设备管理、BOM、质检、库存明细等），不应推迟。

| Oracle 表 | 字段数 | 用途 | Python 模型 | 所在文件 |
|-----------|--------|------|-------------|---------|
| TMM43_EID | 17 | 设备 SN 码主表 | Eid | master.py |
| TMM43_EID_TRACK | 31 | 设备 SN 变更追踪 | EidTrack | master.py |
| TMM41_BOM | 6 | BOM 清单主表 | Bom | master.py |
| TMM42_BOMDT | 7 | BOM 明细 | BomDt | master.py |
| TMM24_CUSTITEMS | 13 | 客户-物品关联 | CustItems | master.py |
| TMM36_CUST_VE_RL | 17 | 客户-车辆关联 | CustVeRl | master.py |
| TMM62_ASSET_ATTRIB_LIST | 7 | 资产属性清单 | AssetAttribList | master.py |
| TQC10_RESULT | 13 | 质检结果主表 | QcResult | warehouse.py |
| TQC11_RESULTDT | 16 | 质检结果明细 | QcResultDt | warehouse.py |
| TQC11_RESULTEID | 18 | 质检设备结果 | QcResultEid | warehouse.py |
| TMP14_CHECKINDT | 9 | 采购验收明细 | PurchaseCheckInDt | procurement.py |
| TTX01_TXKMG | 8 | 调拨科目管理 | TransferAccount | warehouse.py |
| TIV11_DETAIL | 7 | 库存明细（预警模块） | InventoryDetail | inventory.py |
| TIV12_DETAILDT | 12 | 库存明细流水（预警模块） | InventoryDetailDt | inventory.py |

### 4.4 可选/业务价值较低（共8张）

| Oracle 表 | 字段数 | 原用途 | 说明 |
|-----------|--------|--------|------|
| TMM48_FIXEDASSET | 9 | 固定资产 | 简单台账，可用 CustPosRl 替代部分功能 |
| TMM40_LABEL | 6 | 标签管理 | PB 打印标签，B/S 暂无直接需求 |
| TMM45_SUPPAPPRAISAL | 7 | 供应商考核主表 | 已有 TPC20/21，可能重复 |
| TMM49_G3NO | 8 | 3G 号码管理 | 3G 技术过时，仅历史数据参考 |
| TMM50_MFLOG | 6 | 制造流转日志 | PB 专属流转标记 |
| TMM52_POSSTATUS | 9 | POS 状态码表 | 可用 TMM31_SYSCODES 编码表替代 |
| TMM33_MESSAGE | 8 | 系统消息 | 已有 TNTF01/02 通知系统替代 |

---

## 五、统计汇总

| 类别 | 数量 |
|------|------|
| 当前已实现的业务模型 | 138（含14张新增业务必须表） |
| Oracle 等价迁移表（已完全匹配） | 69 |
| Oracle 等价迁移表（有字段缺失，已补全） | 28（共155+10字段已恢复） |
| 4.3节业务必须表（已建模） | 14 |
| 重构新增表（优化方案+Tier扩展） | 27 |
| Oracle 遗留表（已替代/淘汰，不建模） | 7 |
| Oracle 遗留表（地理参考，暂不建模） | 4 |
| Oracle 遗留表（可选/低价值） | 8 |
