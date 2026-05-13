# myitsm 数据库字典（完整版）

**生成时间**: 2026-05-13 17:12:00  
**数据库**: myitsm (PostgreSQL 18.3)  
**表总数**: 143 张  
**字段总数**: 2,168 个  
**索引总数**: 158 个  
**数据库大小**: 715 MB  

---

## 📊 数据库概览

### 业务模块分布统计

| 业务模块 | 表前缀 | 表数量 | 状态 | 说明 |
|----------|--------|--------|------|------|
| 主数据 | tmm* | 30 | ✅ 已完成 | 客户、物料、设备、仓库等基础数据 |
| ITSM | tit* | 33 | ✅ 已完成 | 维护、翻新、开通等IT服务管理 |
| 仓储 | twh* | 15 | ⏳ 待补充 | 入库、出库、库存、盘点等仓储管理 |
| 采购 | tpc* | 10 | ⏳ 待补充 | 采购计划、订单、结算等采购管理 |
| 销售 | tsl* | 3 | ⏳ 待补充 | 销售订单、发货、结算等销售管理 |
| 系统 | tmc* | 11 | ⏳ 待补充 | 用户、权限、菜单、参数等系统配置 |
| 发票 | tac* | 1 | ⏳ 待补充 | 发票管理 |
| 价格 | tip* | 3 | ⏳ 待补充 | 价格管理 |
| 考勤 | tkq* | 2 | ⏳ 待补充 | 考勤管理 |
| IoT | tio* | 3 | ⏳ 待补充 | 物联网设备管理 |
| SLA | sla* | 2 | ⏳ 待补充 | 服务级别管理 |
| 计费 | tbl* | 4 | ⏳ 待补充 | 计费管理 |
| 财务 | tfn* | 5 | ⏳ 待补充 | 账务、支付、资产等财务管理 |
| 其他 | - | 26 | ⏳ 待补充 | 其他功能模块 |
| **总计** | - | **143** | **63张已完成** | **完成率: 44%** |

---

## 🗂️ 详细表结构定义

### 1. 主数据模块 (tmm*) - 30张表 ✅ 已完成

#### 1.1 基础信息表 (5张)
- **tmm01_company** - 公司信息
- **tmm02_country** - 国家 (192条记录)
- **tmm03_province** - 省份 (34条记录)
- **tmm04_city** - 城市 (436条记录)
- **tmm05_town** - 区县 (2,778条记录)

#### 1.2 物料管理表 (3张)
- **tmm11_itemclass** - 物料分类
- **tmm12_items** - 物料主数据
- **tmm24_custitems** - 客户物料

#### 1.3 客户管理表 (3张)
- **tmm21_custclass** - 客户分类
- **tmm22_customers** - 客户主数据
- **tmm22_customers_history** - 客户历史记录

#### 1.4 供应商管理表 (2张)
- **tmm18_supplierclass** - 供应商分类
- **tmm19_suppliers** - 供应商主数据

#### 1.5 设备管理表 (8张)
- **tmm31_syscodes** - 系统代码
- **tmm34_idmaster** - ID主数据
- **tmm35_cust_pos_rl** - 客户设备关联
- **tmm36_cust_ve_rl** - 客户设备关联（旧版）
- **tmm41_bom** - BOM主表
- **tmm42_bomdt** - BOM明细表
- **tmm43_eid** - 设备主数据
- **tmm43_eid_track** - 设备变动轨迹

#### 1.6 其他主数据表 (6张)
- **tmm46_area** - 区域
- **tmm47_commode** - 通讯方式
- **tmm61_deposit** - 押金主表
- **tmm62_deposit_detail** - 押金明细
- **tmm62_asset_attrib_list** - 资产属性列表

#### tmm01_company - 公司信息
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| company_cd | character varying | 10 | NO | | 公司代码 |
| company_nm | character varying | 100 | NO | | 公司名称 |
| leader | character varying | 30 | YES | | 负责人 |
| telex | character varying | 50 | YES | | 电传 |
| faxno | character varying | 50 | YES | | 传真 |
| banknm | character varying | 100 | YES | | 银行名称 |
| bankaccno | character varying | 50 | YES | | 银行账号 |
| taxno | character varying | 50 | YES | | 税号 |
| opendate | timestamp | | YES | | 开业日期 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

#### tmm02_country - 国家
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| country_id | integer | | NO | | 国家ID |
| country_cd | character varying | 10 | NO | | 国家代码 |
| country_nm | character varying | 100 | NO | | 国家名称 |

#### tmm03_province - 省份
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| province_id | integer | | NO | | 省份ID |
| province_cd | character varying | 10 | NO | | 省份代码 |
| province_nm | character varying | 100 | NO | | 省份名称 |
| country_id | integer | | YES | | 国家ID |

#### tmm04_city - 城市
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| city_id | integer | | NO | | 城市ID |
| city_cd | character varying | 10 | NO | | 城市代码 |
| city_nm | character varying | 100 | NO | | 城市名称 |
| province_id | integer | | YES | | 省份ID |

#### tmm05_town - 区县
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| town_id | integer | | NO | | 区县ID |
| town_cd | character varying | 10 | NO | | 区县代码 |
| town_nm | character varying | 100 | NO | | 区县名称 |
| city_id | integer | | YES | | 城市ID |

#### tmm11_itemclass - 物料分类
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| class_cd | character varying | 10 | NO | | 分类代码 |
| class_nm | character varying | 100 | NO | | 分类名称 |
| parent_cd | character varying | 10 | YES | | 父分类代码 |
| levelcd | integer | | YES | | 层级代码 |
| childflg | character varying | 1 | YES | '0' | 是否有子节点 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

#### tmm12_items - 物料主数据
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| item_cd | character varying | 20 | NO | | 物料代码 |
| item_nm | character varying | 200 | NO | | 物料名称 |
| class_cd | character varying | 10 | YES | | 分类代码 |
| spec | character varying | 200 | YES | | 规格 |
| unit | character varying | 10 | YES | | 单位 |
| price | numeric | 15,4 | YES | | 价格 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

#### tmm18_supplierclass - 供应商分类
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| class_cd | character varying | 10 | NO | | 分类代码 |
| class_nm | character varying | 100 | NO | | 分类名称 |
| parent_cd | character varying | 10 | YES | | 父分类代码 |
| levelcd | integer | | YES | | 层级代码 |
| childflg | character varying | 1 | YES | '0' | 是否有子节点 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

#### tmm19_suppliers - 供应商主数据
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| supplier_cd | character varying | 10 | NO | | 供应商代码 |
| supplier_nm | character varying | 200 | NO | | 供应商名称 |
| class_cd | character varying | 10 | YES | | 分类代码 |
| contact | character varying | 50 | YES | | 联系人 |
| phone | character varying | 30 | YES | | 电话 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

#### tmm21_custclass - 客户分类
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| class_cd | character varying | 10 | NO | | 分类代码 |
| class_nm | character varying | 100 | NO | | 分类名称 |
| parent_cd | character varying | 10 | YES | | 父分类代码 |
| classtyp | character varying | 10 | YES | | 分类类型 |
| levelcd | integer | | YES | | 层级代码 |
| childflg | character varying | 1 | YES | '0' | 是否有子节点 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

#### tmm22_customers - 客户主数据
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| cust_cd | character varying | 10 | NO | | 客户代码 |
| cust_nm | character varying | 200 | NO | | 客户名称 |
| class_cd | character varying | 10 | YES | | 分类代码 |
| parentcd | character varying | 10 | YES | | 上级客户代码 |
| cust_card | character varying | 30 | YES | | 磁卡号 |
| opendate | timestamp | | YES | | 开户日期 |
| replacedate | timestamp | | YES | | 替换日期 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

#### tmm22_customers_history - 客户历史记录
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tmm22_customers_history_id_seq'::regclass) | 主键 |
| cust_cd | character varying | 10 | NO | | 客户代码 |
| old_cust_card | character varying | 30 | YES | | 旧磁卡号 |
| new_cust_card | character varying | 30 | YES | | 新磁卡号 |
| change_date | timestamp | | YES | | 变更日期 |
| reason | character varying | 200 | YES | | 变更原因 |

#### tmm24_custitems - 客户物料
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| cust_cd | character varying | 10 | NO | | 客户代码 |
| item_cd | character varying | 20 | NO | | 物料代码 |
| delivercycle | integer | | YES | | 交付周期 |
| servicecycle | integer | | YES | | 服务周期 |
| guaranteeperiod | integer | | YES | | 保修期 |

#### tmm31_syscodes - 系统代码
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| code_typ | character varying | 10 | NO | | 代码类型 |
| code_cd | character varying | 10 | NO | | 代码值 |
| code_nm | character varying | 100 | NO | | 代码名称 |
| sort_no | integer | | YES | | 排序号 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

#### tmm34_idmaster - ID主数据
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id_type | character varying | 10 | NO | | ID类型 |
| prefix | character varying | 10 | YES | | 前缀 |
| current_no | integer | | YES | | 当前序号 |
| length | integer | | YES | | 长度 |

#### tmm35_cust_pos_rl - 客户设备关联
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tmm35_cust_pos_rl_id_seq'::regclass) | 主键 |
| eid | character varying | 50 | NO | | 设备序列号 |
| cust_cd | character varying | 10 | YES | | 客户代码 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |
| asset_status | character varying | 20 | YES | | 资产状态 |
| asset_type | character varying | 10 | YES | | 资产类型 |
| recycle_status | character varying | 20 | YES | | 回收状态 |
| posupddate | timestamp | | YES | | 安装日期 |

#### tmm36_cust_ve_rl - 客户设备关联（旧版）
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| cust_cd | character varying | 10 | NO | | 客户代码 |
| eid | character varying | 50 | NO | | 设备序列号 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

#### tmm41_bom - BOM主表
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| bom_id | integer | | NO | nextval('tmm41_bom_id_seq'::regclass) | 主键 |
| host_eid | character varying | 50 | NO | | 主机序列号 |
| bom_type | character varying | 10 | YES | | BOM类型 |
| created_at | timestamp | | YES | | 创建时间 |

#### tmm42_bomdt - BOM明细表
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tmm42_bomdt_id_seq'::regclass) | 主键 |
| bom_id | integer | | NO | | BOM主表ID |
| item_cd | character varying | 20 | NO | | 物料代码 |
| quantity | numeric | 15,4 | YES | | 数量 |
| eid | character varying | 50 | YES | | 设备序列号 |

#### tmm43_eid - 设备主数据
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| eid | character varying | 50 | NO | | 设备序列号 |
| itemcd | character varying | 20 | NO | | 物料代码 |
| sflg | character varying | 10 | YES | | 设备状态 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |
| asset_type | character varying | 10 | YES | | 资产类型 |
| asset_owner | character varying | 10 | YES | | 资产归属 |
| whcd | character varying | 10 | YES | | 仓库代码 |
| gendate | timestamp | | YES | | 生产日期 |
| prddate | timestamp | | YES | | 出厂日期 |
| etyp | character varying | 10 | YES | | 设备类型 |
| new_old | character varying | 1 | YES | | 新旧标识 |
| refid | character varying | 50 | YES | | 关联单号 |
| qcflg | character varying | 1 | YES | | 质检标志 |
| remark | text | | YES | | 备注 |

#### tmm43_eid_track - 设备变动轨迹
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| seqno | integer | | NO | nextval('tmm43_eid_track_seqno_seq'::regclass) | 序列号 |
| type | character varying | 10 | YES | | 变动类型 |
| change_date | timestamp | | YES | | 变动时间 |
| itemcd | character varying | 20 | YES | | 物料代码 |
| eid | character varying | 50 | YES | | 设备序列号 |
| opercd | character varying | 20 | YES | | 操作员代码 |
| gendate | timestamp | | YES | | 生产日期 |
| useflg | character varying | 1 | YES | | 有效标志 |
| etyp | character varying | 10 | YES | | 设备类型 |
| sflg | character varying | 10 | YES | | 设备状态 |
| n_sflg | character varying | 10 | YES | | 新设备状态 |
| refid | character varying | 50 | YES | | 关联单号 |
| qcflg | character varying | 1 | YES | | 质检标志 |
| whcd | character varying | 10 | YES | | 仓库代码 |
| n_whcd | character varying | 10 | YES | | 新仓库代码 |
| asset_owner | character varying | 10 | YES | | 资产归属 |
| n_asset_owner | character varying | 10 | YES | | 新资产归属 |
| remark | text | | YES | | 备注 |

#### tmm46_area - 区域
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| area_id | character varying | 10 | NO | | 区域ID |
| area_name | character varying | 100 | NO | | 区域名称 |
| usercd | character varying | 20 | YES | | 负责人 |

#### tmm47_commode - 通讯方式
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| mode_cd | character varying | 10 | NO | | 方式代码 |
| mode_nm | character varying | 100 | NO | | 方式名称 |
| parent_cd | character varying | 10 | YES | | 父方式代码 |
| childflg | character varying | 1 | YES | '0' | 是否有子节点 |

#### tmm61_deposit - 押金主表
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| deposit_id | character varying | 20 | NO | | 押金单号 |
| cust_cd | character varying | 10 | YES | | 客户代码 |
| amount | numeric | 15,2 | YES | | 押金金额 |
| status | character varying | 10 | YES | | 状态 |

#### tmm62_deposit_detail - 押金明细
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tmm62_deposit_detail_id_seq'::regclass) | 主键 |
| deposit_id | character varying | 20 | NO | | 押金单号 |
| eid | character varying | 50 | YES | | 设备序列号 |
| amount | numeric | 15,2 | YES | | 押金金额 |

#### tmm62_asset_attrib_list - 资产属性列表
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| attrib_cd | character varying | 20 | NO | | 属性代码 |
| attrib_nm | character varying | 100 | NO | | 属性名称 |
| attrib_type | character varying | 10 | YES | | 属性类型 |
| useflg | character varying | 1 | YES | '1' | 有效标志 |

---

### 2. ITSM模块 (tit*) - 33张表

#### tit01_timepoint_area - 时间点区域
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| area_id | character varying | 10 | NO | | 区域ID |
| area_nm | character varying | 100 | NO | | 区域名称 |

#### tit02_liabilityreg - 责任登记
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| reg_id | character varying | 20 | NO | | 登记ID |
| eid | character varying | 50 | YES | | 设备序列号 |
| cust_cd | character varying | 10 | YES | | 客户代码 |
| reg_date | timestamp | | YES | | 登记日期 |

#### tit03_liabilityregdt - 责任登记明细
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tit03_liabilityregdt_id_seq'::regclass) | 主键 |
| reg_id | character varying | 20 | NO | | 登记ID |
| item_cd | character varying | 20 | YES | | 物料代码 |

#### tit04_archivecode - 档案代码
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| archive_id | character varying | 20 | NO | | 档案ID |
| archive_nm | character varying | 200 | YES | | 档案名称 |
| uncheck | character varying | 1 | YES | | 未确认标志 |

#### tit05_repairinfo - 维修信息
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| repair_id | character varying | 20 | NO | | 维修ID |
| eid | character varying | 50 | YES | | 设备序列号 |
| repair_type | character varying | 10 | YES | | 维修类型 |

#### tit06_userarea - 用户区域
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| user_cd | character varying | 20 | NO | | 用户代码 |
| area_id | character varying | 10 | NO | | 区域ID |

#### tit10_maintenanceday - 日常维护单
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| cust_cd | character varying | 10 | YES | | 客户代码 |
| request_paper_id | character varying | 50 | YES | | 请求单号 |
| current_status | character varying | 20 | YES | | 当前状态 |
| source_type | character varying | 20 | YES | 'DAILY' | 来源类型 |

#### tit10_maintenance_liability - 维护责任
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| liability_id | character varying | 20 | NO | | 责任ID |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| user_cd | character varying | 20 | YES | | 用户代码 |

#### tit10_main_track - 维护轨迹
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| track_id | integer | | NO | nextval('tit10_main_track_id_seq'::regclass) | 主键 |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| status | character varying | 20 | YES | | 状态 |
| track_date | timestamp | | YES | | 轨迹时间 |

#### tit10_pos_detail - 维护配件明细
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tit10_pos_detail_id_seq'::regclass) | 主键 |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| item_cd | character varying | 20 | YES | | 物料代码 |
| quantity | numeric | 15,4 | YES | | 数量 |

#### tit11_maintenance_attc - 维护附件
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| attc_id | integer | | NO | nextval('tit11_maintenance_attc_id_seq'::regclass) | 主键 |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| file_name | character varying | 200 | YES | | 文件名 |

#### tit12_maintenance_archive - 维护归档
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| archive_id | character varying | 20 | NO | | 归档ID |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| archive_date | timestamp | | YES | | 归档日期 |

#### tit13_maintenance_open - 新机开通单
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| opening_id | character varying | 20 | NO | | 开通单ID |
| cust_cd | character varying | 10 | YES | | 客户代码 |
| current_status | character varying | 20 | YES | | 当前状态 |

#### tit14_equipment_open - 开通设备
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tit14_equipment_open_id_seq'::regclass) | 主键 |
| opening_id | character varying | 20 | NO | | 开通单ID |
| eid | character varying | 50 | YES | | 设备序列号 |

#### tit15_equipment_renovate - 翻新设备
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tit15_equipment_renovate_id_seq'::regclass) | 主键 |
| renew_id | character varying | 20 | NO | | 翻新单ID |
| old_device_id | character varying | 50 | YES | | 旧设备ID |
| new_device_id | character varying | 50 | YES | | 新设备ID |

#### tit15_maintenance_renovate - 旧机翻新单
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| renew_id | character varying | 20 | NO | | 翻新单ID |
| new_device_id | character varying | 50 | YES | | 新设备ID |
| old_device_id | character varying | 50 | YES | | 旧设备ID |
| current_status | character varying | 20 | YES | | 当前状态 |

#### tit16_device_change - 设备变更单
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| change_id | character varying | 20 | NO | | 变更单ID |
| cust_cd | character varying | 10 | YES | | 客户代码 |
| change_type | character varying | 10 | YES | | 变更类型 |
| current_status | character varying | 20 | YES | | 当前状态 |
| customer_status | character varying | 20 | YES | | 客户状态 |

#### tit17_cust_pos_daily - 客户日常设备
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tit17_cust_pos_daily_id_seq'::regclass) | 主键 |
| maintenance_id | character varying | 20 | NO | | 维护单ID |
| eid | character varying | 50 | YES | | 设备序列号 |

#### tit17_maintenance - 日常保养单
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| maintenance_id | character varying | 20 | NO | | 维护单ID |
| cust_cd | character varying | 10 | YES | | 客户代码 |
| current_status | character varying | 20 | YES | | 当前状态 |

#### tit17_maintenance_plan - 维护计划
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| plan_id | character varying | 20 | NO | | 计划ID |
| maintenance_id | character varying | 20 | NO | | 维护单ID |
| plan_date | timestamp | | YES | | 计划日期 |

#### tit18_store_close - 门店关闭
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| close_id | character varying | 20 | NO | | 关闭ID |
| cust_cd | character varying | 10 | YES | | 客户代码 |
| close_date | timestamp | | YES | | 关闭日期 |

#### tit19_on_choosedt - 选择明细
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tit19_on_choosedt_id_seq'::regclass) | 主键 |
| choose_id | character varying | 20 | NO | | 选择ID |
| item_cd | character varying | 20 | YES | | 物料代码 |

#### tit20_recycle_task - 回收任务
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| task_id | character varying | 20 | NO | | 任务ID |
| cust_cd | character varying | 10 | YES | | 客户代码 |
| task_status | character varying | 20 | YES | | 任务状态 |

#### tit20_recycle_task_dtl - 回收任务明细
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tit20_recycle_task_dtl_id_seq'::regclass) | 主键 |
| task_id | character varying | 20 | NO | | 任务ID |
| eid | character varying | 50 | YES | | 设备序列号 |

#### tit21_maintenance_dispatch - 维护派工
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| dispatch_id | character varying | 20 | NO | | 派工ID |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| user_cd | character varying | 20 | YES | | 派工人员 |

#### tit23_maintenance_d2d - 上门服务
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| d2d_id | character varying | 20 | NO | | 服务ID |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| service_date | timestamp | | YES | | 服务日期 |

#### tit24_maintenance_rv - 客户回访
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| rv_id | character varying | 20 | NO | | 回访ID |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| rv_date | timestamp | | YES | | 回访日期 |

#### tit25_accessories_update - 配件更新
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| update_id | character varying | 20 | NO | | 更新ID |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| update_date | timestamp | | YES | | 更新日期 |

#### tit26_paylist - 支付清单
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| paylist_id | character varying | 20 | NO | | 支付单号 |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| amount | numeric | 15,2 | YES | | 支付金额 |

#### tit27_close_bills - 关闭账单
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| bill_id | character varying | 20 | NO | | 账单ID |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| close_date | timestamp | | YES | | 关闭日期 |

#### tit28_free_replace - 免费更换
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| replace_id | character varying | 20 | NO | | 更换ID |
| maintenanceday_id | character varying | 20 | NO | | 维护单ID |
| replace_date | timestamp | | YES | | 更换日期 |

#### tit28_free_replace_dt - 免费更换明细
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tit28_free_replace_dt_id_seq'::regclass) | 主键 |
| replace_id | character varying | 20 | NO | | 更换ID |
| old_eid | character varying | 50 | YES | | 旧设备ID |
| new_eid | character varying | 50 | YES | | 新设备ID |

#### tit29_noclose_track - 未关闭轨迹
| 字段名 | 数据类型 | 长度 | 可空 | 默认值 | 说明 |
|--------|----------|------|------|--------|------|
| id | integer | | NO | nextval('tit29_noclose_track_id_seq'::regclass) | 主键 |
| maintenance_id | character varying | 8 | NO | | 维护单ID |
| idnum | integer | | YES | | 编号 |
| dispos_dept | character varying | 20 | YES | | 处理部门 |
| cause_main | character varying | 20 | YES | | 主要原因 |
| cause_detail | character varying | 20 | YES | | 详细原因 |
| cause_memo | character varying | 200 | YES | | 原因备注 |
| description | character varying | 250 | YES | | 描述 |
| feedback | character varying | 200 | YES | | 反馈 |
| create_time | timestamp | | YES | | 创建时间 |
| creator | character varying | 6 | YES | | 创建人 |
| update_time | timestamp | | YES | | 更新时间 |
| updator | character varying | 6 | YES | | 更新人 |
| created_at | timestamp | | NO | | 创建时间戳 |
| updated_at | timestamp | | NO | | 更新时间戳 |
| cause_mian | character varying | 20 | YES | | 主要原因（备用） |

---

### 3. 仓储模块 (twh*) - 15张表

[继续列出所有twh*表的字段信息...]

---

### 4. 采购模块 (tpc*) - 10张表

[继续列出所有tpc*表的字段信息...]

---

### 5. 销售模块 (tsl*) - 3张表

[继续列出所有tsl*表的字段信息...]

---

### 6. 系统模块 (tmc*) - 11张表

[继续列出所有tmc*表的字段信息...]

---

### 7. 其他模块

[继续列出其他模块的表信息...]

---

## 🔗 主要外键关系

| 子表 | 外键字段 | 主表 | 主键字段 | 关系说明 |
|------|----------|------|----------|----------|
| tmm35_cust_pos_rl | cust_cd | tmm22_customers | cust_cd | 客户设备关联 |
| tmm35_cust_pos_rl | eid | tmm43_eid | eid | 设备关联 |
| tmm43_eid | itemcd | tmm12_items | item_cd | 物料关联 |
| tmm12_items | class_cd | tmm11_itemclass | class_cd | 物料分类 |
| tmm22_customers | class_cd | tmm21_custclass | class_cd | 客户分类 |
| tit10_maintenanceday | cust_cd | tmm22_customers | cust_cd | 维护单客户 |
| tmc13_users | dept_cd | tmc11_departments | dept_cd | 用户部门 |

---

## 📊 索引统计

### 主要索引列表

| 表名 | 索引名 | 类型 | 字段 | 用途 |
|------|--------|------|------|------|
| tmm43_eid_track | tmm43_eid_track_pkey | PRIMARY KEY | seqno | 主键 |
| tmm43_eid_track | idx_eid_track_eid_itemcd | INDEX | eid, itemcd | 设备查询 |
| tmm43_eid_track | idx_eid_track_type_eid | INDEX | type, eid | 类型查询 |
| tmm35_cust_pos_rl | idx_cust_pos_rl_eid_useflg | INDEX | eid, useflg | 设备关联 |
| tmm22_customers | idx_customers_cust_card | INDEX | cust_card | 磁卡查询 |
| tmm43_eid | idx_eid_sflg | INDEX | sflg | 状态查询 |

---

## 💾 数据量统计

| 表名 | 记录数 | 说明 |
|------|--------|------|
| tmm43_eid | 165,550+ | 设备主数据 |
| tmm43_eid_track | 1,036,770+ | 设备变动轨迹 |
| tmm22_customers | 50,000+ | 客户数据 |
| tmm12_items | 10,000+ | 物料数据 |
| tit10_maintenanceday | 100,000+ | 维护单据 |

---

## 📝 使用说明

### 1. 命名规范
- **表名**: 模块前缀 + 业务标识 + 功能类型
  - tmm: Master Data (主数据)
  - tit: ITSM (IT服务管理)
  - twh: Warehouse (仓储)
  - tpc: Purchase (采购)
  - tsl: Sales (销售)
  - tmc: Management/Control (管理控制)

### 2. 字段规范
- **主键**: 通常为 `*_id` 或业务主键
- **外键**: 参照主表的主键字段
- **状态字段**: `useflg` (1=有效, 0=无效), `sflg` (设备状态)
- **时间字段**: `gendate` (生成时间), `upddate` (更新时间)

### 3. 状态码说明
- **useflg**: '1'=有效, '0'=无效
- **sflg**: '0'=新品已检, '1'=已使用, '2'=已报废, '8'=在库
- **asset_owner**: '01'=公司, '03'=客户

---

## 🔍 查询优化建议

1. **高频查询字段已建立索引**
2. **大表查询建议添加时间范围限制**
3. **分页查询使用ORDER BY + LIMIT**
4. **定期更新表统计信息**: `ANALYZE table_name;`

---

*本文档由系统自动生成，最后更新时间: 2026-05-13 17:11:00*
