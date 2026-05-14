# 完整数据库字典（myitsm）

> 生成时间：2026-05-13 | 数据库：myitsm | PostgreSQL 18.3 (Homebrew) | 存储：715 MB
> 🟢=自动生成（information_schema）| 🟡=手动维护 | 🔗=引用ER文档
> 配套：`数据库ER关系文档.md`（ER关联）| `数据库变更追踪_迁移后.md`（变更历史）

---

## A. 概览

| 指标 | 值 |
|------|----|
| 业务表总数 | 142 |
| 非主键索引 | 16 |
| 数据库大小 | 715 MB |

### 模块分布

| 模块 | 表数 | 说明 |
|------|------|------|
| 系统管理 (tmc) | 11 | 用户/部门/菜单/权限/参数 |
| 主数据 (tmm) | 25 | 客户/物料/设备/供应商/区域（不含押金） |
| ITSM 核心 (tit) | 33 | 维护/翻新/开通/归档/变更 |
| 仓储 (twh) | 15 | 入库/出库/库存/调拨 |
| 采购 (tpc) | 10 | 采购计划/订单 |
| 销售 (tsl) | 3 | 销售/延期 |
| 财务 (tfn) | 5 | 账务/支付 |
| 财务 (tac/tht) | 1 | 合同/发票 |
| 考勤 (tkq) | 2 | 考勤 |
| 库存预警 (tiv) | 4 | 预警规则/库存明细 |
| 结算 (tbl) | 4 | 结算规则/账单 |
| 通知 (tntf) | 2 | 通知模板/记录 |
| SLA (sla) | 2 | 服务级别 |
| 门户 (tpt) | 3 | 自助报修/评价 |
| IoT (tio) | 4 | 设备接入/监控 |
| MES (tms) | 4 | 生产工单/工序 |
| 押金 (tmm61) | 5 | 押金管理 |
| 质检 (tqc) | 3 | 质检结果 |
| 调拨 (ttx) | 1 | 调拨科目 |
| 价格 (tip) | 2 | 价格规则 |
| 预计划 (plan) | 1 | 预计划客户 |
| 采购验收 (tmp) | 1 | 采购验收明细 |
| **合计** | **141** | |

---

## B. 表详情（按模块分组）

> 🟢 字段名/类型/约束/注释 = PG自动 | 🟡 业务描述 = 手动维护

### 系统管理 (tmc) — 11 张表
> 用户/部门/菜单/权限/参数

#### 1. tmc01_menus

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | menu_cd | VARCHAR(20) | PK NOT NULL | 菜单编码 |
| 2 | menu_nm | VARCHAR(100) | NOT NULL | 菜单名称 |
| 3 | parent_cd | VARCHAR(20) |  | 上级菜单编码 |
| 4 | menu_order | INTEGER |  | 排序号 |
| 5 | status | VARCHAR(1) |  | 状态 |
| 6 | created_at | TIMESTAMP | NOT NULL |  |
| 7 | updated_at | TIMESTAMP | NOT NULL |  |
| 8 | levelcd | VARCHAR(1) |  | 菜单层级 |
| 9 | parent | VARCHAR(6) |  | 父级菜单（Oracle原字段） |
| 10 | picname | VARCHAR(30) |  | 图标名称 |
| 11 | ordno | INTEGER |  | 排序号（Oracle原字段） |
| 12 | openflg | VARCHAR(1) |  | 开放标志 |
| 13 | childflg | VARCHAR(1) |  | 子节点标志 |
| 14 | useflg | VARCHAR(1) |  | 有效标志 |

#### 2. tmc02_menusdt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | menu_cd | VARCHAR(20) | NOT NULL |  |
| 3 | func_cd | VARCHAR(50) |  | 功能编码 |
| 4 | func_nm | VARCHAR(100) |  | 功能名称 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |
| 7 | useflg | VARCHAR(1) |  | 有效标志 |

#### 3. tmc03_usermenus

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | user_cd | VARCHAR(20) | NOT NULL |  |
| 3 | menu_cd | VARCHAR(20) | NOT NULL |  |
| 4 | created_at | TIMESTAMP | NOT NULL |  |
| 5 | updated_at | TIMESTAMP | NOT NULL |  |
| 6 | ordno | INTEGER |  | 排序号 |
| 7 | useflg | VARCHAR(1) |  | 有效标志 |

#### 4. tmc11_departments

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | dept_cd | VARCHAR(20) | PK NOT NULL | 部门编码 |
| 2 | dept_nm | VARCHAR(50) | NOT NULL | 部门名称 |
| 3 | parent_cd | VARCHAR(20) |  | 上级部门编码 |
| 4 | status | VARCHAR(1) |  | 状态 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |
| 7 | levelcd | VARCHAR(1) |  | 部门层级 |
| 8 | parent | VARCHAR(6) |  | 上级部门（Oracle原字段） |
| 9 | leader | VARCHAR(6) |  | 部门领导 |
| 10 | childflg | VARCHAR(1) |  | 子节点标志 |
| 11 | useflg | VARCHAR(1) |  | 有效标志 |

#### 5. tmc12_groups

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | group_cd | VARCHAR(20) | PK NOT NULL | 组编码 |
| 2 | group_nm | VARCHAR(50) | NOT NULL | 组名称 |
| 3 | status | VARCHAR(1) |  | 状态 |
| 4 | created_at | TIMESTAMP | NOT NULL |  |
| 5 | updated_at | TIMESTAMP | NOT NULL |  |
| 6 | useflg | VARCHAR(1) |  | 有效标志 |

#### 6. tmc13_users

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | user_cd | VARCHAR(20) | PK NOT NULL | 用户编码 |
| 2 | user_nm | VARCHAR(50) | NOT NULL | 用户名称 |
| 3 | password | VARCHAR(128) | NOT NULL | 密码 |
| 4 | status | VARCHAR(1) |  | 状态（1有效/0无效） |
| 5 | dept_cd | VARCHAR(20) |  | 部门 |
| 6 | phone | VARCHAR(30) |  | 电话 |
| 7 | email | VARCHAR(100) |  | 邮箱 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |
| 10 | passwd | VARCHAR(128) |  | 原始密码（数据迁移用） |
| 11 | credamt | NUMERIC(12,2) |  | 信用额度 |
| 12 | useflg | VARCHAR(1) |  | 有效标志 |

#### 7. tmc21_usergroup

**索引**: `uq_usergroup` (user_cd, group_cd)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | user_cd | VARCHAR(20) | NOT NULL |  |
| 3 | group_cd | VARCHAR(20) | NOT NULL |  |
| 4 | created_at | TIMESTAMP | NOT NULL |  |
| 5 | updated_at | TIMESTAMP | NOT NULL |  |

#### 8. tmc22_userbusityp

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | user_cd | VARCHAR(20) | NOT NULL |  |
| 3 | busi_typ | VARCHAR(10) | NOT NULL | 业务类型 |
| 4 | created_at | TIMESTAMP | NOT NULL |  |
| 5 | updated_at | TIMESTAMP | NOT NULL |  |

#### 9. tmc31_groupright

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | group_cd | VARCHAR(20) | NOT NULL |  |
| 3 | menu_cd | VARCHAR(20) | NOT NULL | 菜单编码 |
| 4 | func_cd | VARCHAR(50) |  | 功能编码 |
| 5 | right_flg | VARCHAR(1) |  | 权限标志 |
| 6 | created_at | TIMESTAMP | NOT NULL |  |
| 7 | updated_at | TIMESTAMP | NOT NULL |  |
| 8 | scale | VARCHAR(1) |  | 权限范围 |
| 9 | useflg | VARCHAR(1) |  | 有效标志 |

#### 10. tmc41_acclog

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | user_cd | VARCHAR(20) |  | 用户编码 |
| 3 | action | VARCHAR(50) |  | 操作类型 |
| 4 | detail | text |  | 操作明细 |
| 5 | ip_addr | VARCHAR(50) |  | IP地址 |
| 6 | created_at | TIMESTAMP | NOT NULL |  |
| 7 | updated_at | TIMESTAMP | NOT NULL |  |
| 8 | startdate | TIMESTAMP |  | 开始日期 |

#### 11. tmc71_sysparm

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | parm_cd | VARCHAR(50) | PK NOT NULL | 参数编码 |
| 2 | parm_nm | VARCHAR(100) |  | 参数名称 |
| 3 | parm_val | VARCHAR(500) |  | 参数值 |
| 4 | parm_desc | VARCHAR(200) |  | 参数说明 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |
| 7 | pk | VARCHAR(50) |  | 参数主键 |
| 8 | costtype | VARCHAR(1) |  | 成本类型 |
| 9 | autobackpath | VARCHAR(200) |  | 自动备份路径 |
| 10 | invoicesharepath | VARCHAR(200) |  | 发票共享路径 |
| 11 | poinvaliddays | INTEGER |  | 采购失效天数 |
| 12 | soinvaliddays | INTEGER |  | 销售失效天数 |
| 13 | allowmultilogon | VARCHAR(1) |  | 允许多点登录 |
| 14 | shopbilltype | VARCHAR(1) |  | 店铺单据类型 |
| 15 | centralwarehouse | VARCHAR(4) |  | 中心仓库编码 |
| 16 | jwt_expiration_seconds | INTEGER |  | JWT超时(秒) |
| 17 | log_retention_days | INTEGER |  | 日志保留天数 |
| 18 | max_upload_size_mb | INTEGER |  | 上传大小限制(MB) |


### 主数据 (tmm) — 25 张表
> 客户/物料/设备/供应商/区域（不含押金）

#### 1. tmm01_company

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | comp_cd | VARCHAR(20) | PK NOT NULL | 公司编码 |
| 2 | comp_nm | VARCHAR(100) | NOT NULL | 公司名称 |
| 3 | address | VARCHAR(200) |  | 地址 |
| 4 | phone | VARCHAR(30) |  | 电话 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |
| 7 | leader | VARCHAR(10) |  | 负责人 |
| 8 | telex | VARCHAR(20) |  | 电传号 |
| 9 | faxno | VARCHAR(20) |  | 传真 |
| 10 | banknm | VARCHAR(30) |  | 开户银行 |
| 11 | bankaccno | VARCHAR(20) |  | 银行账号 |
| 12 | taxno | VARCHAR(18) |  | 税号 |
| 13 | opendate | TIMESTAMP |  | 开业日期 |
| 14 | useflg | VARCHAR(1) |  | 有效标志 |
| 15 | mailcd | VARCHAR(6) |  | 邮编 |
| 16 | produce | INTEGER |  | 生产标志 |
| 17 | maintenance | INTEGER |  | 维护标志 |

#### 2. tmm02_country

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | country_cd | VARCHAR(3) | PK NOT NULL | 国家代码 |
| 2 | country_nm | VARCHAR(50) | NOT NULL | 国家名称 |
| 3 | useflg | VARCHAR(1) |  | 有效标志 |
| 4 | created_at | TIMESTAMP | NOT NULL |  |
| 5 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tmm03_province

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | prvn_cd | VARCHAR(2) | PK NOT NULL | 省份代码 |
| 2 | prvn_nm | VARCHAR(50) | NOT NULL | 省份名称 |
| 3 | country_cd | VARCHAR(3) |  | 国家代码 |
| 4 | useflg | VARCHAR(1) |  | 有效标志 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. tmm04_city

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | city_cd | VARCHAR(4) | PK NOT NULL | 城市代码 |
| 2 | city_nm | VARCHAR(50) | NOT NULL | 城市名称 |
| 3 | prvn_cd | VARCHAR(2) |  | 省份代码 |
| 4 | useflg | VARCHAR(1) |  | 有效标志 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |

#### 5. tmm05_town

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | town_cd | VARCHAR(4) | PK NOT NULL | 区县代码 |
| 2 | town_nm | VARCHAR(50) | NOT NULL | 区县名称 |
| 3 | city_cd | VARCHAR(4) |  | 城市代码 |
| 4 | useflg | VARCHAR(1) |  | 有效标志 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |

#### 6. tmm11_itemclass

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | class_cd | VARCHAR(20) | PK NOT NULL | 分类编码 |
| 2 | class_nm | VARCHAR(50) | NOT NULL | 分类名称 |
| 3 | parent_cd | VARCHAR(20) |  | 上级分类 |
| 4 | created_at | TIMESTAMP | NOT NULL |  |
| 5 | updated_at | TIMESTAMP | NOT NULL |  |
| 6 | classtyp | VARCHAR(1) |  | 分类类型 |
| 7 | childflg | VARCHAR(1) |  | 子节点标志 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |
| 9 | opercd | VARCHAR(6) |  |  |
| 10 | gendate | TIMESTAMP |  |  |
| 11 | upddate | TIMESTAMP |  |  |

#### 7. tmm12_items

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | item_cd | VARCHAR(20) | PK NOT NULL | 物料编码 |
| 2 | item_nm | VARCHAR(100) | NOT NULL | 物料名称 |
| 3 | class_cd | VARCHAR(20) |  | 分类编码 |
| 4 | spec | VARCHAR(100) |  | 规格型号 |
| 5 | unit | VARCHAR(10) |  | 单位 |
| 6 | useflg | VARCHAR(1) |  | 有效标志 |
| 7 | created_at | TIMESTAMP | NOT NULL |  |
| 8 | updated_at | TIMESTAMP | NOT NULL |  |
| 9 | itemanm | VARCHAR(40) |  | 物料别名 |
| 10 | itembrcd | VARCHAR(30) |  | 物料条码 |
| 11 | itemsize | VARCHAR(30) |  | 规格尺寸 |
| 12 | countrycd | VARCHAR(3) |  | 产地国家 |
| 13 | provincecd | VARCHAR(2) |  | 省份 |
| 14 | citycd | VARCHAR(4) |  | 城市 |
| 15 | wunit | VARCHAR(4) |  | 计量单位 |
| 16 | pcrep | VARCHAR(6) |  | 采购负责人 |
| 17 | keeper | VARCHAR(6) |  | 库管员 |
| 18 | upperlimit | INTEGER |  | 库存上限 |
| 19 | lowerlimit | INTEGER |  | 库存下限 |
| 20 | minorder | INTEGER |  | 最小订购量 |
| 21 | newperiod | INTEGER |  | 新品周期(天) |
| 22 | oldperiod | INTEGER |  | 旧品周期(天) |
| 23 | backup | VARCHAR(200) |  | 备注 |
| 24 | typflg | VARCHAR(1) |  | 物料类型标志 |
| 25 | purchasetyp | VARCHAR(1) |  | 采购类型 |
| 26 | consume | VARCHAR(1) |  | 消耗标志 |

#### 8. tmm18_supplierclass

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | class_cd | VARCHAR(20) | PK NOT NULL | 分类编码 |
| 2 | class_nm | VARCHAR(50) | NOT NULL | 分类名称 |
| 3 | created_at | TIMESTAMP | NOT NULL |  |
| 4 | updated_at | TIMESTAMP | NOT NULL |  |
| 5 | classtyp | VARCHAR(1) |  | 分类类型 |
| 6 | parent | VARCHAR(20) |  | 上级分类 |
| 7 | childflg | VARCHAR(1) |  | 子节点标志 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |

#### 9. tmm19_suppliers

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | supp_cd | VARCHAR(20) | PK NOT NULL | 供应商编码 |
| 2 | supp_nm | VARCHAR(100) | NOT NULL | 供应商名称 |
| 3 | class_cd | VARCHAR(20) |  | 分类编码 |
| 4 | address | VARCHAR(200) |  | 地址 |
| 5 | phone | VARCHAR(30) |  | 电话 |
| 6 | contactor | VARCHAR(50) |  | 联系人 |
| 7 | useflg | VARCHAR(1) |  | 有效标志 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |
| 10 | custcd | VARCHAR(8) |  | 关联客户编码 |
| 11 | custnm | VARCHAR(60) |  | 供应商全称 |
| 12 | custanm | VARCHAR(20) |  | 供应商别名 |
| 13 | custbrcd | VARCHAR(20) |  | 供应商条码 |
| 14 | scale | VARCHAR(1) |  | 规模等级 |
| 15 | zipcd | VARCHAR(6) |  | 邮编 |
| 16 | phoneno | VARCHAR(20) |  | 座机电话 |
| 17 | faxno | VARCHAR(20) |  | 传真 |
| 18 | taxno | VARCHAR(18) |  | 税号 |
| 19 | banknm | VARCHAR(40) |  | 开户银行 |
| 20 | bankaccno | VARCHAR(50) |  | 银行账号 |
| 21 | pcrep | VARCHAR(6) |  | 采购联系人 |
| 22 | suppinfo | VARCHAR(1) |  | 供应商状态 |
| 23 | agreements | VARCHAR(1) |  | 协议标志 |

#### 10. tmm21_custclass

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | class_cd | VARCHAR(20) | PK NOT NULL | 分类编码 |
| 2 | class_nm | VARCHAR(50) | NOT NULL | 分类名称 |
| 3 | parent_cd | VARCHAR(20) |  | 上级分类 |
| 4 | created_at | TIMESTAMP | NOT NULL |  |
| 5 | updated_at | TIMESTAMP | NOT NULL |  |
| 6 | classtyp | VARCHAR(1) |  | 分类类型 |
| 7 | childflg | VARCHAR(1) |  | 子节点标志 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |

#### 11. tmm22_customers

**索引**: `tmm22_customers_cust_card_key` (cust_card)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | cust_cd | VARCHAR(20) | PK NOT NULL | 客户编码 |
| 2 | cust_nm | VARCHAR(100) | NOT NULL | 客户名称 |
| 3 | cust_card | VARCHAR(30) |  | 磁卡号 |
| 4 | class_cd | VARCHAR(20) |  | 客户分类 |
| 5 | area_cd | VARCHAR(20) |  | 区域编码 |
| 6 | address | VARCHAR(200) |  | 地址 |
| 7 | phone_no | VARCHAR(30) |  | 电话 |
| 8 | contactor | VARCHAR(50) |  | 联系人 |
| 9 | busi_typ | VARCHAR(10) |  | 业务类型 |
| 10 | useflg | VARCHAR(1) |  | 有效标志 |
| 11 | customer_status | VARCHAR(10) |  | 生命周期状态（TEMP/PENDING/ACTIVE/INVALID） |
| 12 | ppt_code | VARCHAR(20) |  | 品牌编码 |
| 13 | zf_type | VARCHAR(10) |  | 支付方式 |
| 14 | comm_mode | VARCHAR(20) |  | 通讯方式 |
| 15 | store_cd | VARCHAR(30) |  | 门店编码 |
| 16 | created_at | TIMESTAMP | NOT NULL |  |
| 17 | updated_at | TIMESTAMP | NOT NULL |  |
| 18 | cust_anm | VARCHAR(40) |  | 客户别名 |
| 19 | cust_brcd | VARCHAR(20) |  | 客户条码 |
| 20 | zipcd | VARCHAR(6) |  | 邮编 |
| 21 | faxno | VARCHAR(20) |  | 传真 |
| 22 | taxno | VARCHAR(18) |  | 税号 |
| 23 | banknm | VARCHAR(40) |  | 开户银行 |
| 24 | bankaccno | VARCHAR(50) |  | 银行账号 |
| 25 | parentcd | VARCHAR(8) |  | 上级客户编码 |
| 26 | backup | VARCHAR(200) |  | 备注 |
| 27 | location | VARCHAR(1) |  | 位置标志 |
| 28 | area | INTEGER |  | 区域编号 |
| 29 | pos_n | INTEGER |  | POS数量 |
| 30 | opersystem | VARCHAR(128) |  | POS操作系统 |
| 31 | data_base | VARCHAR(128) |  | POS数据库版本 |
| 32 | soft_edition | VARCHAR(128) |  | POS软件版本 |
| 33 | s_status | VARCHAR(1) |  | 状态标志 |
| 34 | ad_video | VARCHAR(1) |  | 广告机标志 |
| 35 | card3g | VARCHAR(30) |  | 3G卡号 |
| 36 | adr3g | VARCHAR(20) |  | 3G地址 |
| 37 | systemcode | VARCHAR(50) |  | 内核版本 |
| 38 | custrnm | VARCHAR(80) |  | 客户全称 |
| 39 | opendate | TIMESTAMP |  | 首次开通日期 |
| 40 | replacedate | TIMESTAMP |  | 最近更换日期 |
| 41 | levels | VARCHAR(2) |  | 客户等级 |
| 42 | ordertype | VARCHAR(10) |  | 要货方式 |
| 43 | jl_contactor | VARCHAR(10) |  | 经理联系人 |
| 44 | jl_phoneno | VARCHAR(60) |  | 经理电话 |
| 45 | posstatus | VARCHAR(2) |  | POS运行状态 |
| 46 | posstatus1 | VARCHAR(2) |  | POS状态1 |
| 47 | is_contract | VARCHAR(2) |  | 合同标志 |
| 48 | yj_money | NUMERIC(12,2) |  | 押金金额 |
| 49 | source_type | VARCHAR(20) |  | 来源类型（PREPLAN/MANUAL/IMPORT/API） |
| 50 | verified_at | TIMESTAMP |  | 转正时间 |
| 51 | preplan_id | VARCHAR(50) |  | 关联预计划号 |
| 52 | valid_until | TIMESTAMP |  | 临时客户有效期 |
| 53 | country_cd | VARCHAR(3) |  | 国家代码 |
| 54 | prvn_cd | VARCHAR(2) |  | 省份代码 |
| 55 | city_cd | VARCHAR(4) |  | 城市代码 |
| 56 | town_cd | VARCHAR(4) |  | 区县代码 |

#### 12. tmm22_customers_history

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | cust_cd | VARCHAR(20) | NOT NULL | 客户编码 |
| 3 | change_type | VARCHAR(10) | NOT NULL | 变更类型（CK=磁卡号） |
| 4 | old_value | VARCHAR(200) |  | 变更前值 |
| 5 | new_value | VARCHAR(200) |  | 变更后值 |
| 6 | oper_cd | VARCHAR(20) |  | 操作员 |
| 7 | oper_date | TIMESTAMP |  | 操作时间 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |
| 10 | change_reason | VARCHAR(200) |  | 变更原因 |
| 11 | device_change_id | VARCHAR(20) |  | 关联变更单号 |

#### 13. tmm24_custitems

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | itemcd | VARCHAR(6) | PK NOT NULL | 物料编码 |
| 2 | custcd | VARCHAR(8) | PK NOT NULL | 客户编码 |
| 3 | dfltflg | VARCHAR(1) |  | 默认标志 |
| 4 | opercd | VARCHAR(6) |  | 操作员 |
| 5 | gendate | TIMESTAMP |  | 创建日期 |
| 6 | upddate | TIMESTAMP |  | 更新日期 |
| 7 | useflg | VARCHAR(1) |  | 有效标志 |
| 8 | delivercycle | numeric |  | 配送周期 |
| 9 | servicecycle | numeric |  | 服务周期 |
| 10 | guaranteeperiod | numeric |  | 保修期 |
| 11 | backup | VARCHAR(200) |  | 备注 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 14. tmm31_syscodes

**索引**: `uq_syscode` (code_typ, code_cd)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | code_typ | VARCHAR(10) | NOT NULL | 编码类型 |
| 3 | code_cd | VARCHAR(20) | NOT NULL | 编码值 |
| 4 | code_nm | VARCHAR(50) |  | 编码名称 |
| 5 | useflg | VARCHAR(1) |  | 有效标志 |
| 6 | sort_no | INTEGER |  | 排序号 |
| 7 | created_at | TIMESTAMP | NOT NULL |  |
| 8 | updated_at | TIMESTAMP | NOT NULL |  |
| 9 | sysflg | VARCHAR(1) |  | 系统标志 |
| 10 | memo | VARCHAR(60) |  | 说明 |

#### 15. tmm34_idmaster

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id_type | VARCHAR(20) | PK NOT NULL | 编号类型 |
| 2 | prefix | VARCHAR(10) |  | 前缀 |
| 3 | current_no | INTEGER |  | 当前编号 |
| 4 | step | INTEGER |  | 步长 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |
| 7 | idtyp | VARCHAR(2) |  | ID类型 |
| 8 | idtypnm | VARCHAR(20) |  | 类型名称 |
| 9 | curbillid | VARCHAR(30) |  | 当前流水号 |
| 10 | maxbillid | VARCHAR(30) |  | 最大流水号 |
| 11 | loops | VARCHAR(1) |  | 循环标志 |
| 12 | useflg | VARCHAR(1) |  | 有效标志（IdMaster） |

#### 16. tmm35_cust_pos_rl

**索引**: `idx_cust_pos_rl_eid_useflg` (eid, useflg)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | cust_cd | VARCHAR(20) | NOT NULL | 客户编码 |
| 3 | pos_cd | VARCHAR(30) |  | POS编码 |
| 4 | item_cd | VARCHAR(20) |  | 物料编码 |
| 5 | eid | VARCHAR(50) |  | 设备序列号 |
| 6 | useflg | VARCHAR(1) |  | 有效标志 |
| 7 | created_at | TIMESTAMP | NOT NULL |  |
| 8 | updated_at | TIMESTAMP | NOT NULL |  |
| 9 | sysinfo | VARCHAR(30) |  | 系统信息 |
| 10 | softinfo | VARCHAR(30) |  | 软件信息 |
| 11 | posupddate | TIMESTAMP |  | POS更新日期 |
| 12 | posinfo | VARCHAR(30) |  | POS信息 |
| 13 | pos_area | VARCHAR(2) |  | 区域 |
| 14 | status | VARCHAR(1) |  | 设备状态 |
| 15 | typflg | VARCHAR(2) |  | 类型标志 |
| 16 | maintenancedate | TIMESTAMP |  | 维护日期 |
| 17 | maintenancetyp | VARCHAR(6) |  | 维护类型 |
| 18 | maintenanceno | VARCHAR(10) |  | 维护单号 |
| 19 | asset_status | VARCHAR(10) |  | 资产状态（ACTIVE/RETURNED/SCRAPPED） |
| 20 | created_from | VARCHAR(20) |  | 来源追溯 |
| 21 | source_id | VARCHAR(20) |  | 来源单号 |
| 22 | warranty_expire | TIMESTAMP |  | 保修到期日 |

#### 17. tmm36_cust_ve_rl

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | custcd | VARCHAR(8) | PK NOT NULL | 客户编码 |
| 2 | eid | VARCHAR(13) | PK NOT NULL | 设备序列号 |
| 3 | itemcd | VARCHAR(6) | PK NOT NULL | 物料编码 |
| 4 | startdate | TIMESTAMP |  | 开始日期 |
| 5 | sysinfo | VARCHAR(30) |  | 系统信息 |
| 6 | softinfo | VARCHAR(30) |  | 软件信息 |
| 7 | posupddate | TIMESTAMP |  | POS更新日期 |
| 8 | posinfo | VARCHAR(30) |  | POS信息 |
| 9 | area | VARCHAR(2) |  | 区域 |
| 10 | status | VARCHAR(1) |  | 状态 |
| 11 | typflg | VARCHAR(2) |  | 类型标志 |
| 12 | maintenancedate | VARCHAR(6) |  | 维护日期 |
| 13 | maintenancetyp | TIMESTAMP |  | 维护类型 |
| 14 | opercd | VARCHAR(6) |  | 操作员 |
| 15 | gendate | TIMESTAMP |  | 创建日期 |
| 16 | upddate | TIMESTAMP |  | 更新日期 |
| 17 | useflg | VARCHAR(1) |  | 有效标志 |
| 18 | created_at | TIMESTAMP | NOT NULL |  |
| 19 | updated_at | TIMESTAMP | NOT NULL |  |

#### 18. tmm41_bom

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | bomcd | VARCHAR(6) | PK NOT NULL | BOM编码 |
| 2 | bomnm | VARCHAR(50) |  | BOM名称 |
| 3 | opercd | VARCHAR(6) |  | 操作员 |
| 4 | gendate | TIMESTAMP |  | 创建日期 |
| 5 | upddate | TIMESTAMP |  | 更新日期 |
| 6 | useflg | VARCHAR(1) |  | 有效标志 |
| 7 | created_at | TIMESTAMP | NOT NULL |  |
| 8 | updated_at | TIMESTAMP | NOT NULL |  |

#### 19. tmm42_bomdt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | bomcd | VARCHAR(6) | PK NOT NULL | BOM编码 |
| 2 | itemcd | VARCHAR(6) | PK NOT NULL | 物料编码 |
| 3 | bomqty | NUMERIC(12,0) |  | BOM数量 |
| 4 | opercd | VARCHAR(6) |  | 操作员 |
| 5 | gendate | TIMESTAMP |  | 创建日期 |
| 6 | upddate | TIMESTAMP |  | 更新日期 |
| 7 | itemtyp | VARCHAR(1) |  | 物料类型 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |

#### 20. tmm43_eid

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | itemcd | VARCHAR(6) | PK NOT NULL | 物料编码 |
| 2 | eid | VARCHAR(13) | PK NOT NULL | 设备序列号 |
| 3 | opercd | VARCHAR(6) |  | 操作员 |
| 4 | gendate | TIMESTAMP |  | 创建日期 |
| 5 | useflg | VARCHAR(1) |  | 有效标志 |
| 6 | etyp | VARCHAR(1) |  | 设备类型 |
| 7 | sflg | VARCHAR(1) |  | 状态标志 |
| 8 | refid | VARCHAR(8) |  | 关联单号 |
| 9 | qcflg | VARCHAR(2) |  | 质检标志 |
| 10 | whcd | VARCHAR(2) |  | 仓库编码 |
| 11 | prddate | TIMESTAMP |  | 生产日期 |
| 12 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 13 | new_old | VARCHAR(1) |  | 新旧标志 |
| 14 | remark | VARCHAR(200) |  | 备注 |
| 15 | manuf_seq | VARCHAR(100) |  | 制造序列号 |
| 16 | old_degree | numeric |  | 旧化程度 |
| 17 | isunit | VARCHAR(1) |  | 是否整机 |
| 18 | created_at | TIMESTAMP | NOT NULL |  |
| 19 | updated_at | TIMESTAMP | NOT NULL |  |
| 20 | asset_type | VARCHAR(10) |  |  |
| 21 | recyclable | BOOLEAN |  |  |
| 22 | recycle_status | VARCHAR(10) |  |  |
| 23 | asset_owner | VARCHAR(20) |  |  |
| 24 | install_date | TIMESTAMP |  |  |

#### 21. tmm43_eid_track

**索引**: `idx_eid_track_eid_itemcd` (eid, itemcd), `idx_eid_track_type_eid` (type, eid)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | seqno | INTEGER | PK NOT NULL | 序号 |
| 2 | type | VARCHAR(1) |  | 变更类型 |
| 3 | change_date | TIMESTAMP |  | 变更日期 |
| 4 | itemcd | VARCHAR(6) |  | 物料编码 |
| 5 | eid | VARCHAR(13) |  | 设备序列号 |
| 6 | opercd | VARCHAR(6) |  | 操作员 |
| 7 | gendate | TIMESTAMP |  | 创建日期 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |
| 9 | etyp | VARCHAR(1) |  | 设备类型 |
| 10 | sflg | VARCHAR(1) |  | 状态标志 |
| 11 | refid | VARCHAR(8) |  | 关联单号 |
| 12 | qcflg | VARCHAR(2) |  | 质检标志 |
| 13 | whcd | VARCHAR(2) |  | 仓库编码 |
| 14 | prddate | TIMESTAMP |  | 生产日期 |
| 15 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 16 | new_old | VARCHAR(1) |  | 新旧标志 |
| 17 | n_sflg | VARCHAR(1) |  | 新状态标志 |
| 18 | n_refid | VARCHAR(8) |  | 新关联单号 |
| 19 | n_qcflg | VARCHAR(2) |  | 新质检标志 |
| 20 | n_whcd | VARCHAR(2) |  | 新仓库编码 |
| 21 | n_prddate | TIMESTAMP |  | 新生产日期 |
| 22 | n_itemtyp | VARCHAR(2) |  | 新物料类型 |
| 23 | n_new_old | VARCHAR(1) |  | 新新旧标志 |
| 24 | n_itemcd | VARCHAR(6) |  | 新物料编码 |
| 25 | n_etyp | VARCHAR(1) |  | 新设备类型 |
| 26 | remark | VARCHAR(200) |  | 备注 |
| 27 | n_remark | VARCHAR(200) |  | 新备注 |
| 28 | manuf_seq | VARCHAR(100) |  | 制造序列号 |
| 29 | n_manf_seq | VARCHAR(100) |  | 新制造序列号 |
| 30 | old_degree | numeric |  | 旧化程度 |
| 31 | n_old_degree | numeric |  | 新旧化程度 |
| 32 | created_at | TIMESTAMP | NOT NULL |  |
| 33 | updated_at | TIMESTAMP | NOT NULL |  |
| 34 | install_date | TIMESTAMP |  |  |
| 35 | n_install_date | TIMESTAMP |  |  |
| 36 | cust_cd | VARCHAR(20) |  |  |
| 37 | n_cust_cd | VARCHAR(20) |  |  |
| 38 | asset_type | VARCHAR(10) |  |  |
| 39 | n_asset_type | VARCHAR(10) |  |  |
| 40 | recyclable | VARCHAR(1) |  |  |
| 41 | n_recyclable | VARCHAR(1) |  |  |
| 42 | recycle_status | VARCHAR(10) |  |  |
| 43 | n_recycle_status | VARCHAR(10) |  |  |
| 44 | asset_owner | VARCHAR(20) |  |  |
| 45 | n_asset_owner | VARCHAR(20) |  |  |

#### 22. tmm44_pos_r_eid

**索引**: `idx_pos_r_eid_eid` (eid), `idx_pos_r_eid_useflg` (useflg, eid)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | posid | VARCHAR(50) |  |  |
| 3 | eid | VARCHAR(50) |  |  |
| 4 | useflg | VARCHAR(1) |  |  |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |
| 7 | itemcd | VARCHAR(10) |  |  |
| 8 | opercd | VARCHAR(6) |  |  |
| 9 | gendate | TIMESTAMP |  |  |
| 10 | upddate | TIMESTAMP |  |  |

#### 23. tmm46_area

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | area_cd | VARCHAR(20) | PK NOT NULL | 区域编码 |
| 2 | area_nm | VARCHAR(50) | NOT NULL | 区域名称 |
| 3 | parent_cd | VARCHAR(20) |  | 上级区域 |
| 4 | useflg | VARCHAR(1) |  | 有效标志 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |
| 7 | area_id | INTEGER |  | 区域ID |
| 8 | name | VARCHAR(50) |  | 区域全称 |
| 9 | usercd | VARCHAR(6) |  | 负责人编码 |

#### 24. tmm47_commode

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | cmm_cd | VARCHAR(20) | PK NOT NULL | 通讯方式编码 |
| 2 | cmm_nm | VARCHAR(50) | NOT NULL | 通讯方式名称 |
| 3 | cmm_type | VARCHAR(10) |  | 类型 |
| 4 | useflg | VARCHAR(1) |  | 有效标志 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |
| 7 | parent | VARCHAR(20) |  | 上级编码 |
| 8 | childflg | VARCHAR(1) |  | 子节点标志 |

#### 25. tmm62_asset_attrib_list

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | itemcd | VARCHAR(10) | PK NOT NULL | 物料编码 |
| 2 | eid | VARCHAR(30) | PK NOT NULL | 设备序列号 |
| 3 | c_type | VARCHAR(10) |  | 分类类型 |
| 4 | updatetime | TIMESTAMP |  | 更新时间 |
| 5 | c_address | VARCHAR(200) |  | 地址 |
| 6 | remark | VARCHAR(200) |  | 备注 |
| 7 | asset_type | VARCHAR(10) |  | 资产类型 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |


### ITSM 核心 (tit) — 33 张表
> 维护/翻新/开通/归档/变更

#### 1. tit01_timepoint_area

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | levels | VARCHAR(2) | PK NOT NULL | 响应等级 |
| 2 | explain | VARCHAR(20) |  | 说明 |
| 3 | timepoint | TIMESTAMP |  | 时间点 |
| 4 | before_tm | NUMERIC(5,2) |  | 时间点前（小时） |
| 5 | after_tm | NUMERIC(5,2) |  | 时间点后（小时） |
| 6 | useflg | VARCHAR(1) |  | 有效标志 |
| 7 | created_at | TIMESTAMP | NOT NULL |  |
| 8 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tit02_liabilityreg

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | liab_cd | VARCHAR(4) | PK NOT NULL | 科目编码 |
| 2 | liab_nm | VARCHAR(20) |  | 科目名称 |
| 3 | describe | VARCHAR(200) |  | 描述 |
| 4 | liab_type | VARCHAR(1) |  | 分类 |
| 5 | parent | VARCHAR(4) |  | 上级编码 |
| 6 | child_flg | VARCHAR(1) |  | 子类别标志 |
| 7 | useflg | VARCHAR(1) |  | 有效标志 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tit02_liabilityregdt

**索引**: `uq_liabilityregdt` (lbdt_cd, liab_cd)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | lbdt_cd | VARCHAR(8) | NOT NULL | 明细编码 |
| 3 | liab_cd | VARCHAR(8) | NOT NULL | 科目编码 |
| 4 | define | VARCHAR(200) |  | 明细定义 |
| 5 | useflg | VARCHAR(1) |  | 有效标志 |
| 6 | created_at | TIMESTAMP | NOT NULL |  |
| 7 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. tit04_archivecode

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | arch_cd | VARCHAR(10) | PK NOT NULL | 科目编码 |
| 2 | arch_nm | VARCHAR(60) |  | 科目名称 |
| 3 | describe | VARCHAR(200) |  | 描述 |
| 4 | arch_type | VARCHAR(1) |  | 分类 |
| 5 | parent | VARCHAR(10) |  | 上级编码 |
| 6 | child_flg | VARCHAR(1) |  | 子类别标志 |
| 7 | max_level | INTEGER |  | 最大级次 |
| 8 | arch_group | VARCHAR(1) |  | 故障分组 |
| 9 | fault_type | VARCHAR(10) |  | 故障类型 |
| 10 | useflg | VARCHAR(1) |  | 有效标志 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |
| 13 | uncheck | VARCHAR(1) |  | 未审核标志 |

#### 5. tit05_repairinfo

**索引**: `uq_repairinfo` (rep_type, obj_cd)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | rep_type | VARCHAR(2) | NOT NULL | 类型（01客户/02配件） |
| 3 | obj_cd | VARCHAR(8) | NOT NULL | 对象编号 |
| 4 | useflg | VARCHAR(1) |  | 有效标志 |
| 5 | created_at | TIMESTAMP | NOT NULL |  |
| 6 | updated_at | TIMESTAMP | NOT NULL |  |

#### 6. tit06_userarea

**索引**: `uq_userarea` (area_id, user_cd)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | area_id | INTEGER | NOT NULL | 区域ID |
| 3 | user_cd | VARCHAR(6) | NOT NULL | 人员编号 |
| 4 | created_at | TIMESTAMP | NOT NULL |  |
| 5 | updated_at | TIMESTAMP | NOT NULL |  |

#### 7. tit10_main_track

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维护单ID |
| 3 | dep_cd | VARCHAR(8) |  | 部门编码 |
| 4 | memo | VARCHAR(255) |  | 备注 |
| 5 | updatetime | TIMESTAMP |  | 更新时间 |
| 6 | from_status | VARCHAR(2) |  | 原状态 |
| 7 | to_status | VARCHAR(2) |  | 目标状态 |
| 8 | oper_cd | VARCHAR(20) |  | 操作员 |
| 9 | created_at | TIMESTAMP | NOT NULL |  |
| 10 | updated_at | TIMESTAMP | NOT NULL |  |

#### 8. tit10_maintenance_liability

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维护单ID |
| 3 | exceptions_cd | VARCHAR(10) |  | 免责条款编码 |
| 4 | exceptions_nm | VARCHAR(200) |  | 条款名称 |
| 5 | dept_nm | VARCHAR(20) |  | 审核部门 |
| 6 | assess_flg | VARCHAR(1) |  | 是否考核 |
| 7 | exempt_flg | VARCHAR(1) |  | 是否豁免 |
| 8 | type | VARCHAR(1) |  | 类型（1未完成/2未达标） |
| 9 | is_finish | VARCHAR(1) |  | 处理状态（0未处理/1已分配/2已处理/3已审核） |
| 10 | useflg | VARCHAR(1) |  | 有效标记 |
| 11 | set_from | VARCHAR(10) |  | 来源 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 9. tit10_maintenanceday

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | maintenance_id | VARCHAR(8) | PK NOT NULL | 维护单号 |
| 2 | company_id | VARCHAR(8) |  | 所属区域公司ID |
| 3 | store_id | VARCHAR(8) |  | 门店ID |
| 4 | temp_contract | VARCHAR(60) |  | 临时联系电话 |
| 5 | fault_type | VARCHAR(8) |  | 故障类型 |
| 6 | servrity | VARCHAR(1) |  | 严重程度 |
| 7 | emergency_level | VARCHAR(1) |  | 紧急程度 |
| 8 | priority | VARCHAR(1) |  | 优先级 |
| 9 | requester | VARCHAR(6) |  | 请求人员 |
| 10 | request_time | TIMESTAMP |  | 请求时间 |
| 11 | expected_completion_time | TIMESTAMP |  | 合同要求完成时间 |
| 12 | deliver_no | VARCHAR(8) |  | 送货单号 |
| 13 | short_description | VARCHAR(80) |  | 故障简述 |
| 14 | detail_description | VARCHAR(200) |  | 详细描述 |
| 15 | device_id | VARCHAR(13) |  | 故障设备编号 |
| 16 | current_status | VARCHAR(2) |  | 当前状态 |
| 17 | is_success | VARCHAR(1) |  | 成功标志 |
| 18 | is_old | VARCHAR(1) |  | 是否补单 |
| 19 | faultcode | VARCHAR(80) |  | 故障编码 |
| 20 | create_time | TIMESTAMP |  | 创建时间 |
| 21 | creator | VARCHAR(6) |  | 创建人 |
| 22 | update_time | TIMESTAMP |  | 更新时间 |
| 23 | updator | VARCHAR(6) |  | 更新人 |
| 24 | firstor | VARCHAR(6) |  | 第一次上门工程师ID |
| 25 | first_time | TIMESTAMP |  | 第一次上门时间 |
| 26 | leave_time | TIMESTAMP |  | 第一次离店时间 |
| 27 | close_time | TIMESTAMP |  | 关单时间 |
| 28 | revisit_time | TIMESTAMP |  | 回访时间 |
| 29 | is_archive | VARCHAR(1) |  | 是否归档 |
| 30 | view_type | VARCHAR(1) |  | 视频操作类型 |
| 31 | memo | VARCHAR(200) |  | 异常状态备注 |
| 32 | requst_typ | VARCHAR(10) |  | 请求类型 |
| 33 | requset_paper_id | VARCHAR(10) |  | 请求单号 |
| 34 | source_type | VARCHAR(10) |  | 来源类型（DAILY=日常维护/RECYCLE=取机回收） |
| 35 | created_at | TIMESTAMP | NOT NULL |  |
| 36 | updated_at | TIMESTAMP | NOT NULL |  |

#### 10. tit10_pos_detail

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | bill_id | VARCHAR(8) | NOT NULL | 单据编号 |
| 3 | sm_id | INTEGER |  | SM表ID |
| 4 | noflg | VARCHAR(1) |  | 新旧设备标记 |
| 5 | device_id | VARCHAR(13) |  | 整机ID |
| 6 | item_cd | VARCHAR(6) |  | 配件类型 |
| 7 | accessories_id | VARCHAR(13) |  | 配件编号 |
| 8 | status | VARCHAR(1) |  | 状态 |
| 9 | created_at | TIMESTAMP | NOT NULL |  |
| 10 | updated_at | TIMESTAMP | NOT NULL |  |
| 11 | create_time | TIMESTAMP |  | 创建时间 |
| 12 | creator | VARCHAR(6) |  | 创建人 |

#### 11. tit11_maintenance_attc

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维护单ID |
| 3 | business_operation_id | INTEGER |  | 业务流水操作表ID |
| 4 | attc_id | VARCHAR(8) |  | 附件ID |
| 5 | attc_nm | VARCHAR(40) |  | 附件名称 |
| 6 | create_time | TIMESTAMP |  | 创建时间 |
| 7 | creator | VARCHAR(6) |  | 创建人 |
| 8 | update_time | TIMESTAMP |  | 更新时间 |
| 9 | updator | VARCHAR(6) |  | 更新人 |
| 10 | created_at | TIMESTAMP | NOT NULL |  |
| 11 | updated_at | TIMESTAMP | NOT NULL |  |
| 12 | attc | bytea |  | 附件内容 |

#### 12. tit12_maintenance_archive

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维护单ID |
| 3 | business_operation_id | INTEGER |  | 业务流水操作表ID |
| 4 | fault_cd | VARCHAR(10) |  | 故障编码 |
| 5 | fault_cd_audit | VARCHAR(10) |  | 故障编码（审核后） |
| 6 | fault_type | VARCHAR(10) |  | 故障大类 |
| 7 | fault_detail_type | VARCHAR(10) |  | 故障小类 |
| 8 | description | VARCHAR(200) |  | 描述 |
| 9 | useflg | VARCHAR(1) |  | 有效标记 |
| 10 | is_audit | VARCHAR(1) |  | 审核标记 |
| 11 | create_time | TIMESTAMP |  | 创建时间 |
| 12 | creator | VARCHAR(6) |  | 创建人 |
| 13 | update_time | TIMESTAMP |  | 更新时间 |
| 14 | updator | VARCHAR(6) |  | 更新人 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |

#### 13. tit13_maintenance_open

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | new_opening_id | VARCHAR(8) | PK NOT NULL | 新机开通表ID |
| 2 | company_id | VARCHAR(8) |  | 所属区域公司ID |
| 3 | store_id | VARCHAR(8) |  | 门店ID |
| 4 | request_time | TIMESTAMP |  | 请求时间 |
| 5 | requset_paper_id | VARCHAR(8) |  | 仓储请求单ID |
| 6 | device_id | VARCHAR(13) |  | 整机编号 |
| 7 | count | INTEGER |  | 开通数量 |
| 8 | expected_completion_time | TIMESTAMP |  | 合同要求完成时间 |
| 9 | deliver_no | VARCHAR(8) |  | 送货单号 |
| 10 | short_description | VARCHAR(80) |  | 简述 |
| 11 | detail_description | VARCHAR(200) |  | 详细描述 |
| 12 | current_status | VARCHAR(2) |  | 当前状态 |
| 13 | is_success | VARCHAR(1) |  | 成功标志 |
| 14 | is_old | VARCHAR(1) |  | 是否补单 |
| 15 | create_time | TIMESTAMP |  | 创建时间 |
| 16 | creator | VARCHAR(6) |  | 创建人 |
| 17 | update_time | TIMESTAMP |  | 更新时间 |
| 18 | updator | VARCHAR(6) |  | 更新人 |
| 19 | firstor | VARCHAR(6) |  | 第一次上门工程师ID |
| 20 | first_time | TIMESTAMP |  | 第一次上门时间 |
| 21 | leave_time | TIMESTAMP |  | 第一次离店时间 |
| 22 | close_time | TIMESTAMP |  | 关单时间 |
| 23 | revisit_time | TIMESTAMP |  | 回访时间 |
| 24 | from_custcard | VARCHAR(20) |  | 来源磁卡号 |
| 25 | from_custcd | VARCHAR(8) |  | 来源客户编码 |
| 26 | created_at | TIMESTAMP | NOT NULL |  |
| 27 | updated_at | TIMESTAMP | NOT NULL |  |

#### 14. tit14_equipment_open

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | new_opening_id | VARCHAR(8) | NOT NULL | 新机开通ID |
| 3 | business_operation_id | INTEGER |  | 业务流水操作表ID |
| 4 | device_id | VARCHAR(13) |  | 整机ID |
| 5 | price | NUMERIC(5,3) |  | 价格 |
| 6 | delivery_id | VARCHAR(8) |  | 送货单号 |
| 7 | is_finish | VARCHAR(1) |  | 是否完成 |
| 8 | is_change | VARCHAR(1) |  | 是否换机 |
| 9 | change_eid | VARCHAR(50) |  | 换机设备号 |
| 10 | from_custcard | VARCHAR(20) |  | 来源磁卡号 |
| 11 | from_posid | VARCHAR(13) |  | 来源POS编号 |
| 12 | from_custcd | VARCHAR(8) |  | 来源客户编码 |
| 13 | create_time | TIMESTAMP |  | 创建时间 |
| 14 | creator | VARCHAR(6) |  | 创建人 |
| 15 | update_time | TIMESTAMP |  | 更新时间 |
| 16 | updator | VARCHAR(6) |  | 更新人 |
| 17 | created_at | TIMESTAMP | NOT NULL |  |
| 18 | updated_at | TIMESTAMP | NOT NULL |  |

#### 15. tit15_equipment_renovate

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | renovate_id | VARCHAR(8) | NOT NULL | 旧机翻新ID |
| 3 | business_operation_id | INTEGER |  | 业务流水操作表ID |
| 4 | device_id | VARCHAR(13) |  | 旧机ID |
| 5 | new_device_id | VARCHAR(13) |  | 新机ID |
| 6 | price | NUMERIC(5,3) |  | 价格 |
| 7 | delivery_id | VARCHAR(8) |  | 送货单号 |
| 8 | is_finish | VARCHAR(1) |  | 是否完成 |
| 9 | is_change | VARCHAR(1) |  | 是否换机 |
| 10 | change_eid | VARCHAR(50) |  | 换机设备号 |
| 11 | create_time | TIMESTAMP |  | 创建时间 |
| 12 | creator | VARCHAR(6) |  | 创建人 |
| 13 | update_time | TIMESTAMP |  | 更新时间 |
| 14 | updator | VARCHAR(6) |  | 更新人 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |

#### 16. tit15_maintenance_renovate

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | renew_id | VARCHAR(8) | PK NOT NULL | 旧机翻新表ID |
| 2 | company_id | VARCHAR(8) |  | 所属区域公司ID |
| 3 | store_id | VARCHAR(8) |  | 门店ID |
| 4 | request_time | TIMESTAMP |  | 请求时间 |
| 5 | requset_paper_id | VARCHAR(8) |  | 仓储请求单ID |
| 6 | old_device_id | VARCHAR(13) |  | 旧设备编号 |
| 7 | new_device_id | VARCHAR(13) |  | 换新设备编号 |
| 8 | count | INTEGER |  | 变更数量 |
| 9 | expected_completion_time | TIMESTAMP |  | 合同要求完成时间 |
| 10 | deliver_no | VARCHAR(8) |  | 送货单号 |
| 11 | short_description | VARCHAR(80) |  | 简述 |
| 12 | detail_description | VARCHAR(200) |  | 详细描述 |
| 13 | current_status | VARCHAR(2) |  | 当前状态 |
| 14 | is_success | VARCHAR(1) |  | 成功标志 |
| 15 | is_old | VARCHAR(1) |  | 是否补单 |
| 16 | create_time | TIMESTAMP |  | 创建时间 |
| 17 | creator | VARCHAR(6) |  | 创建人 |
| 18 | update_time | TIMESTAMP |  | 更新时间 |
| 19 | updator | VARCHAR(6) |  | 更新人 |
| 20 | firstor | VARCHAR(6) |  | 第一次上门工程师ID |
| 21 | first_time | TIMESTAMP |  | 第一次上门时间 |
| 22 | leave_time | TIMESTAMP |  | 第一次离店时间 |
| 23 | close_time | TIMESTAMP |  | 关单时间 |
| 24 | revisit_time | TIMESTAMP |  | 回访时间 |
| 25 | is_back | VARCHAR(1) |  | 设备是否返回（Y/N） |
| 26 | created_at | TIMESTAMP | NOT NULL |  |
| 27 | updated_at | TIMESTAMP | NOT NULL |  |

#### 17. tit16_device_change

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | device_change_id | VARCHAR(8) | PK NOT NULL | 变更单ID |
| 2 | store_id | VARCHAR(8) |  | 门店ID |
| 3 | requset_paper_id | VARCHAR(8) |  | 变更请求单ID |
| 4 | change_type | VARCHAR(8) |  | 变更类型（CK/BQ/BG） |
| 5 | device_id | VARCHAR(13) |  | 整机ID |
| 6 | new_contactor | VARCHAR(10) |  | 变更后联系人 |
| 7 | new_tel | VARCHAR(60) |  | 变更后电话 |
| 8 | new_address | VARCHAR(200) |  | 变更后地址 |
| 9 | new_store_card | VARCHAR(20) |  | 变更后门店磁卡号 |
| 10 | new_store_id | VARCHAR(8) |  | 变更后门店ID |
| 11 | is_store_inside_change | VARCHAR(1) |  | 是否店内移机（Y/N） |
| 12 | request_time | TIMESTAMP |  | 请求时间 |
| 13 | expected_completion_time | TIMESTAMP |  | 合同要求完成时间 |
| 14 | short_description | VARCHAR(80) |  | 简述 |
| 15 | detail_description | VARCHAR(200) |  | 详细描述 |
| 16 | current_status | VARCHAR(2) |  | 当前状态 |
| 17 | is_success | VARCHAR(1) |  | 成功标志 |
| 18 | is_old | VARCHAR(1) |  | 是否补单 |
| 19 | create_time | TIMESTAMP |  | 创建时间 |
| 20 | creator | VARCHAR(6) |  | 创建人 |
| 21 | update_time | TIMESTAMP |  | 更新时间 |
| 22 | updator | VARCHAR(6) |  | 更新人 |
| 23 | firstor | VARCHAR(6) |  | 第一次上门工程师ID |
| 24 | first_time | TIMESTAMP |  | 第一次上门时间 |
| 25 | leave_time | TIMESTAMP |  | 第一次离店时间 |
| 26 | close_time | TIMESTAMP |  | 关单时间 |
| 27 | revisit_time | TIMESTAMP |  | 回访时间 |
| 28 | created_at | TIMESTAMP | NOT NULL |  |
| 29 | updated_at | TIMESTAMP | NOT NULL |  |

#### 18. tit17_cust_pos_daily

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | daily_maintenance_id | VARCHAR(8) | NOT NULL | 保养单号 |
| 3 | business_operation_id | INTEGER |  | 业务操作流水ID |
| 4 | cust_cd | VARCHAR(8) |  | 客户代码 |
| 5 | eid | VARCHAR(13) |  | 设备序列号 |
| 6 | item_cd | VARCHAR(6) |  | 机型 |
| 7 | startdate | TIMESTAMP |  | 开通日期 |
| 8 | sysinfo | VARCHAR(30) |  | 系统程序 |
| 9 | softinfo | VARCHAR(30) |  | 软件配置 |
| 10 | posupddate | TIMESTAMP |  | 设备更新时间 |
| 11 | posinfo | VARCHAR(30) |  | POS版本 |
| 12 | area | VARCHAR(2) |  | 划区 |
| 13 | status | VARCHAR(1) |  | 设备状态（1在用/0备机） |
| 14 | typ_flg | VARCHAR(2) |  | 类型（1.POS机/2.视频机） |
| 15 | maintenancedate | TIMESTAMP |  | 保养时间 |
| 16 | maintenancetyp | VARCHAR(6) |  | 保养状态（1已保养/0未保养） |
| 17 | request_enginner_id | VARCHAR(6) |  | 操作工程师 |
| 18 | request_time | TIMESTAMP |  | 请求时间 |
| 19 | short_description | VARCHAR(80) |  | 简述 |
| 20 | detail_description | VARCHAR(200) |  | 详细描述 |
| 21 | create_time | TIMESTAMP |  | 创建时间 |
| 22 | creator | VARCHAR(6) |  | 创建人 |
| 23 | update_time | TIMESTAMP |  | 更新时间 |
| 24 | updator | VARCHAR(6) |  | 更新人 |
| 25 | useflg | VARCHAR(1) |  | 有效标志 |
| 26 | created_at | TIMESTAMP | NOT NULL |  |
| 27 | updated_at | TIMESTAMP | NOT NULL |  |

#### 19. tit17_maintenance

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | daily_maintenance_id | VARCHAR(8) | PK NOT NULL | 日常保养维护单ID |
| 2 | store_id | VARCHAR(8) |  | 门店ID |
| 3 | has_video_device | VARCHAR(1) |  | 是否有视频 |
| 4 | video_device_status | VARCHAR(20) |  | 视频状态 |
| 5 | video_device_error_des | VARCHAR(200) |  | 视频故障描述 |
| 6 | request_enginner_id | VARCHAR(6) |  | 请求工程师ID |
| 7 | request_time | TIMESTAMP |  | 请求时间 |
| 8 | short_description | VARCHAR(80) |  | 简述 |
| 9 | detail_description | VARCHAR(200) |  | 详细描述 |
| 10 | current_status | VARCHAR(2) |  | 当前状态 |
| 11 | is_success | VARCHAR(1) |  | 成功标志 |
| 12 | is_old | VARCHAR(1) |  | 是否补单 |
| 13 | create_time | TIMESTAMP |  | 创建时间 |
| 14 | creator | VARCHAR(6) |  | 创建人 |
| 15 | update_time | TIMESTAMP |  | 更新时间 |
| 16 | updator | VARCHAR(6) |  | 更新人 |
| 17 | firstor | VARCHAR(6) |  | 第一次上门工程师ID |
| 18 | first_time | TIMESTAMP |  | 第一次上门时间 |
| 19 | leave_time | TIMESTAMP |  | 第一次离店时间 |
| 20 | close_time | TIMESTAMP |  | 关单时间 |
| 21 | revisit_time | TIMESTAMP |  | 回访时间 |
| 22 | created_at | TIMESTAMP | NOT NULL |  |
| 23 | updated_at | TIMESTAMP | NOT NULL |  |

#### 20. tit17_maintenance_plan

**索引**: `uq_maintenance_plan` (plan_y, plan_yymm, area_id)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | plan_y | VARCHAR(4) | NOT NULL | 计划年 |
| 3 | plan_yymm | VARCHAR(6) | NOT NULL | 计划年月 |
| 4 | area_id | INTEGER | NOT NULL | 区域 |
| 5 | plan_qty | INTEGER |  | 计划量 |
| 6 | create_time | TIMESTAMP |  | 创建日期 |
| 7 | creator | VARCHAR(6) |  | 创建人 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |

#### 21. tit18_store_close

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | store_close_id | VARCHAR(8) | PK NOT NULL | 门店关闭单ID |
| 2 | store_id | VARCHAR(8) |  | 门店ID |
| 3 | request_time | TIMESTAMP |  | 请求时间 |
| 4 | requset_paper_id | VARCHAR(8) |  | 请求单号 |
| 5 | close_type | VARCHAR(2) |  | 关闭类型 |
| 6 | temp_close_date_begin | TIMESTAMP |  | 临时关闭开始时间 |
| 7 | temp_close_date_end | TIMESTAMP |  | 临时关闭结束时间 |
| 8 | expected_completion_time | TIMESTAMP |  | 要求完成时间 |
| 9 | short_description | VARCHAR(80) |  | 简述 |
| 10 | detail_description | VARCHAR(200) |  | 详细描述 |
| 11 | current_status | VARCHAR(2) |  | 当前状态 |
| 12 | is_success | VARCHAR(1) |  | 成功标志 |
| 13 | is_old | VARCHAR(1) |  | 是否补单 |
| 14 | create_time | TIMESTAMP |  | 创建时间 |
| 15 | creator | VARCHAR(6) |  | 创建人 |
| 16 | update_time | TIMESTAMP |  | 更新时间 |
| 17 | updator | VARCHAR(6) |  | 更新人 |
| 18 | firstor | VARCHAR(6) |  | 第一次上门工程师ID |
| 19 | first_time | TIMESTAMP |  | 第一次上门时间 |
| 20 | leave_time | TIMESTAMP |  | 第一次离店时间 |
| 21 | close_time | TIMESTAMP |  | 关单时间 |
| 22 | revisit_time | TIMESTAMP |  | 回访时间 |
| 23 | created_at | TIMESTAMP | NOT NULL |  |
| 24 | updated_at | TIMESTAMP | NOT NULL |  |

#### 22. tit19_on_choosedt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | bill_id | VARCHAR(8) | NOT NULL | 单据编号 |
| 3 | business_id | INTEGER |  | 设备操作流水 |
| 4 | oldflg | VARCHAR(1) |  | 新旧设备标记 |
| 5 | device_id | VARCHAR(13) |  | 整机ID |
| 6 | item_cd | VARCHAR(6) |  | 配件类型 |
| 7 | accessories_id | VARCHAR(13) |  | 配件编号 |
| 8 | chooseflg | VARCHAR(1) |  | 选取标记 |
| 9 | updateflg | VARCHAR(1) |  | 是否提交 |
| 10 | create_time | TIMESTAMP |  | 创建时间 |
| 11 | creator | VARCHAR(6) |  | 创建人 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 23. tit20_recycle_task

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | recycle_id | VARCHAR(12) | PK NOT NULL | 回收任务ID |
| 2 | recycle_type | VARCHAR(2) |  | 回收类型 |
| 3 | plan_no | VARCHAR(10) |  | 来源预计划单号 |
| 4 | maintenance_id | VARCHAR(8) |  | 关联维护单号 |
| 5 | cust_cd | VARCHAR(8) | NOT NULL | 门店代码 |
| 6 | task_status | VARCHAR(2) |  | 任务状态 |
| 7 | asset_count | INTEGER |  | 应回收资产数量 |
| 8 | asset_list | VARCHAR(500) |  | 资产清单JSON |
| 9 | assigned_to | VARCHAR(6) |  | 分配人员 |
| 10 | assigned_date | TIMESTAMP |  | 分配日期 |
| 11 | completed_date | TIMESTAMP |  | 完成日期 |
| 12 | actual_count | INTEGER |  | 实际回收数量 |
| 13 | disposition | VARCHAR(2) |  | 处置方式 |
| 14 | target_warehouse | VARCHAR(10) |  | 目标仓库 |
| 15 | useflg | VARCHAR(1) |  | 有效标志 |
| 16 | remark | VARCHAR(200) |  | 备注 |
| 17 | create_time | TIMESTAMP |  | 创建时间 |
| 18 | creator | VARCHAR(6) |  | 创建人 |
| 19 | update_time | TIMESTAMP |  | 更新时间 |
| 20 | updator | VARCHAR(6) |  | 更新人 |
| 21 | created_at | TIMESTAMP | NOT NULL |  |
| 22 | updated_at | TIMESTAMP | NOT NULL |  |

#### 24. tit20_recycle_task_dtl

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | recycle_id | VARCHAR(12) | PK NOT NULL | 回收任务ID |
| 2 | asset_id | VARCHAR(20) | PK NOT NULL | 资产ID |
| 3 | asset_type | VARCHAR(10) |  | 资产类型 |
| 4 | expected_status | VARCHAR(10) |  | 预期状态 |
| 5 | actual_status | VARCHAR(10) |  | 实际状态 |
| 6 | recovered_date | TIMESTAMP |  | 回收日期 |
| 7 | warehouse_cd | VARCHAR(10) |  | 入库仓库 |
| 8 | remark | VARCHAR(200) |  | 备注 |
| 9 | created_at | TIMESTAMP | NOT NULL |  |
| 10 | updated_at | TIMESTAMP | NOT NULL |  |

#### 25. tit21_maintenance_dispatch

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维护单ID |
| 3 | business_operation_id | INTEGER |  | 业务操作流水表ID |
| 4 | maintenance_type | VARCHAR(2) |  | 维护类型 |
| 5 | operator | VARCHAR(6) |  | 操作人 |
| 6 | accpectd_group | VARCHAR(2) |  | 分派组 |
| 7 | accpectder | VARCHAR(6) |  | 分派人 |
| 8 | dispatch_time | TIMESTAMP |  | 分派时间 |
| 9 | create_time | TIMESTAMP |  | 创建时间 |
| 10 | creator | VARCHAR(6) |  | 创建人 |
| 11 | update_time | TIMESTAMP |  | 更新时间 |
| 12 | updator | VARCHAR(6) |  | 更新人 |
| 13 | created_at | TIMESTAMP | NOT NULL |  |
| 14 | updated_at | TIMESTAMP | NOT NULL |  |

#### 26. tit23_maintenance_d2d

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维护单ID（跨单据复用） |
| 3 | business_operation_id | INTEGER |  | 业务操作流水表ID |
| 4 | d2d_engineer | VARCHAR(6) |  | 上门工程师 |
| 5 | arrive_time | TIMESTAMP |  | 到达时间 |
| 6 | leave_time | TIMESTAMP |  | 离店时间 |
| 7 | jjbz | VARCHAR(1) |  | 解决标志 |
| 8 | d2d_descripiton | VARCHAR(200) |  | 处理过程描述 |
| 9 | d2d_phone | VARCHAR(60) |  | 电话 |
| 10 | old_business_id | INTEGER |  | 原操作流水ID |
| 11 | d2d_group | INTEGER |  | 分组 |
| 12 | d2d_type | VARCHAR(1) |  | 类型（1到店/2离店/3催单/4记录） |
| 13 | create_time | TIMESTAMP |  | 创建时间 |
| 14 | creator | VARCHAR(6) |  | 创建人 |
| 15 | update_time | TIMESTAMP |  | 更新时间 |
| 16 | updator | VARCHAR(6) |  | 更新人 |
| 17 | useflg | VARCHAR(1) |  | 有效标志 |
| 18 | posstatus | VARCHAR(2) |  | POS状态 |
| 19 | posstatus1 | VARCHAR(2) |  | POS状态1 |
| 20 | created_at | TIMESTAMP | NOT NULL |  |
| 21 | updated_at | TIMESTAMP | NOT NULL |  |

#### 27. tit24_maintenance_rv

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维护单ID |
| 3 | business_operation_id | INTEGER |  | 业务操作流水表ID |
| 4 | rv_time | TIMESTAMP |  | 回访时间 |
| 5 | rv_operator | VARCHAR(20) |  | 回访人员 |
| 6 | feedback | VARCHAR(200) |  | 客户反馈 |
| 7 | satisfaction | VARCHAR(1) |  | 满意度 |
| 8 | create_time | TIMESTAMP |  | 创建时间 |
| 9 | creator | VARCHAR(6) |  | 创建人 |
| 10 | update_time | TIMESTAMP |  | 更新时间 |
| 11 | updator | VARCHAR(6) |  | 更新人 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 28. tit25_accessories_update

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维修单ID |
| 3 | business_operation_id | INTEGER |  | 业务流水操作表ID |
| 4 | store_id | VARCHAR(8) |  | 门店ID |
| 5 | device_id | VARCHAR(13) |  | 整机ID |
| 6 | old_accessories_id | VARCHAR(13) |  | 旧配件ID |
| 7 | accessories_type | VARCHAR(60) |  | 配件类型名称 |
| 8 | new_accessories_id | VARCHAR(13) |  | 新配件ID |
| 9 | is_new | VARCHAR(1) |  | 新配件是否为新品 |
| 10 | description | VARCHAR(200) |  | 过程描述 |
| 11 | price | NUMERIC(10,3) |  | 价格 |
| 12 | engineer_id | VARCHAR(6) |  | 工程师ID |
| 13 | in_wh | VARCHAR(1) |  | 是否入库 |
| 14 | invflg | VARCHAR(1) |  | 是否开票 |
| 15 | receipt_id | VARCHAR(8) |  | 收据号 |
| 16 | delivery_id | VARCHAR(8) |  | 送货单号 |
| 17 | create_time | TIMESTAMP |  | 创建时间 |
| 18 | creator | VARCHAR(6) |  | 创建人 |
| 19 | update_time | TIMESTAMP |  | 更新时间 |
| 20 | updator | VARCHAR(6) |  | 更新人 |
| 21 | auditflg | VARCHAR(1) |  | 提交标志 |
| 22 | posflg | VARCHAR(1) |  | 更换整机标志 |
| 23 | c_type | VARCHAR(1) |  | 操作类型（1维修/2购买） |
| 24 | created_at | TIMESTAMP | NOT NULL |  |
| 25 | updated_at | TIMESTAMP | NOT NULL |  |

#### 29. tit26_paylist

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维修单ID |
| 3 | business_operation_id | INTEGER |  | 业务流水操作表ID |
| 4 | store_id | VARCHAR(8) |  | 门店ID |
| 5 | engineer_id | VARCHAR(6) |  | 工程师ID |
| 6 | receipt_id | VARCHAR(8) |  | 收据号 |
| 7 | delivery_id | VARCHAR(8) |  | 送货单号 |
| 8 | paytype | VARCHAR(30) |  | 收费类型 |
| 9 | payje | NUMERIC(8,3) |  | 收款金额 |
| 10 | memo | VARCHAR(250) |  | 备注 |
| 11 | paydate | TIMESTAMP |  | 收款日期 |
| 12 | useflg | VARCHAR(1) |  | 有效标记 |
| 13 | create_time | TIMESTAMP |  | 创建时间 |
| 14 | creator | VARCHAR(6) |  | 创建人 |
| 15 | update_time | TIMESTAMP |  | 更新时间 |
| 16 | updator | VARCHAR(6) |  | 更新人 |
| 17 | created_at | TIMESTAMP | NOT NULL |  |
| 18 | updated_at | TIMESTAMP | NOT NULL |  |

#### 30. tit27_close_bills

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 任务单ID |
| 3 | business_operation_id | INTEGER |  | 业务操作流水表ID |
| 4 | close_time | TIMESTAMP |  | 关单时间 |
| 5 | close_type | VARCHAR(2) |  | 关单类型 |
| 6 | description | VARCHAR(200) |  | 描述 |
| 7 | is_old | VARCHAR(1) |  | 是否补关单 |
| 8 | is_archive | VARCHAR(1) |  | 是否归档 |
| 9 | create_time | TIMESTAMP |  | 创建时间 |
| 10 | creator | VARCHAR(6) |  | 创建人 |
| 11 | update_time | TIMESTAMP |  | 更新时间 |
| 12 | updator | VARCHAR(6) |  | 更新人 |
| 13 | created_at | TIMESTAMP | NOT NULL |  |
| 14 | updated_at | TIMESTAMP | NOT NULL |  |

#### 31. tit28_free_replace

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | renew_id | VARCHAR(8) | PK NOT NULL | 免费更换表ID |
| 2 | company_id | VARCHAR(8) |  | 所属区域公司ID |
| 3 | store_id | VARCHAR(8) |  | 门店ID |
| 4 | request_time | TIMESTAMP |  | 请求时间 |
| 5 | requset_paper_id | VARCHAR(8) |  | 请求ID |
| 6 | old_device_id | VARCHAR(13) |  | 旧设备编号 |
| 7 | new_device_id | VARCHAR(13) |  | 换新设备编号 |
| 8 | deliver_no | VARCHAR(8) |  | 送货单号 |
| 9 | count | INTEGER |  | 变更数量 |
| 10 | expected_completion_time | TIMESTAMP |  | 合同要求完成时间 |
| 11 | short_description | VARCHAR(80) |  | 简述 |
| 12 | detail_description | VARCHAR(200) |  | 详细描述 |
| 13 | current_status | VARCHAR(2) |  | 当前状态 |
| 14 | is_success | VARCHAR(1) |  | 成功标志 |
| 15 | is_old | VARCHAR(1) |  | 是否补单 |
| 16 | is_back | VARCHAR(1) |  | 设备是否返回（Y/N） |
| 17 | create_time | TIMESTAMP |  | 创建时间 |
| 18 | creator | VARCHAR(6) |  | 创建人 |
| 19 | update_time | TIMESTAMP |  | 更新时间 |
| 20 | updator | VARCHAR(6) |  | 更新人 |
| 21 | firstor | VARCHAR(6) |  | 第一次上门工程师ID |
| 22 | first_time | TIMESTAMP |  | 第一次上门时间 |
| 23 | leave_time | TIMESTAMP |  | 第一次离店时间 |
| 24 | close_time | TIMESTAMP |  | 关单时间 |
| 25 | revisit_time | TIMESTAMP |  | 回访时间 |
| 26 | created_at | TIMESTAMP | NOT NULL |  |
| 27 | updated_at | TIMESTAMP | NOT NULL |  |

#### 32. tit28_free_replace_dt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | renovate_id | VARCHAR(8) | NOT NULL | 免费更换ID |
| 3 | business_operation_id | INTEGER |  | 业务流水操作表ID |
| 4 | device_id | VARCHAR(13) |  | 旧机ID |
| 5 | new_device_id | VARCHAR(13) |  | 新机ID |
| 6 | delivery_id | VARCHAR(8) |  | 送货单号 |
| 7 | is_finish | VARCHAR(1) |  | 是否完成 |
| 8 | create_time | TIMESTAMP |  | 创建时间 |
| 9 | creator | VARCHAR(6) |  | 创建人 |
| 10 | update_time | TIMESTAMP |  | 更新时间 |
| 11 | updator | VARCHAR(6) |  | 更新人 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 33. tit29_noclose_track

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | maintenance_id | VARCHAR(8) | NOT NULL | 维护单号 |
| 3 | idnum | INTEGER |  | 编号 |
| 4 | dispos_dept | VARCHAR(20) |  | 处理部门 |
| 5 | cause_main | VARCHAR(20) |  | 原因大类 |
| 6 | cause_detail | VARCHAR(20) |  | 原因小类 |
| 7 | cause_memo | VARCHAR(200) |  | 原因说明 |
| 8 | description | VARCHAR(250) |  | 详情 |
| 9 | feedback | VARCHAR(200) |  | 部门反馈 |
| 10 | create_time | TIMESTAMP |  | 创建时间 |
| 11 | creator | VARCHAR(6) |  | 创建人 |
| 12 | update_time | TIMESTAMP |  | 更新时间 |
| 13 | updator | VARCHAR(6) |  | 更新人 |
| 14 | created_at | TIMESTAMP | NOT NULL |  |
| 15 | updated_at | TIMESTAMP | NOT NULL |  |
| 16 | cause_mian | VARCHAR(20) |  | 原因大类（Oracle原字段名） |


### 仓储 (twh) — 15 张表
> 入库/出库/库存/调拨

#### 1. twh01_warehouse

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | whcd | VARCHAR(2) | PK NOT NULL | 仓库编码 |
| 2 | whnm | VARCHAR(60) |  | 仓库名称 |
| 3 | whtyp | VARCHAR(2) |  | 仓库类型 |
| 4 | address | VARCHAR(60) |  | 地址 |
| 5 | phoneno | VARCHAR(15) |  | 电话 |
| 6 | fax | VARCHAR(15) |  | 传真 |
| 7 | leader | VARCHAR(6) |  | 负责人 |
| 8 | defaultflg | VARCHAR(1) |  | 默认仓库标志 |
| 9 | remoteflg | VARCHAR(1) |  | 远程仓库标志 |
| 10 | opercd | VARCHAR(6) |  | 操作员 |
| 11 | gendate | TIMESTAMP |  | 创建日期 |
| 12 | upddate | TIMESTAMP |  | 更新日期 |
| 13 | useflg | VARCHAR(1) |  | 有效标志 |
| 14 | whtransflg | VARCHAR(1) |  | 仓储流转标志 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. twh11_detail

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | seqno | INTEGER | PK NOT NULL | 序号 |
| 2 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 3 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 4 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 5 | prddate | TIMESTAMP |  | 生产日期 |
| 6 | itemqty | INTEGER |  | 库存数量 |
| 7 | opercd | VARCHAR(6) |  | 操作员 |
| 8 | gendate | TIMESTAMP |  | 创建日期 |
| 9 | upddate | TIMESTAMP |  | 更新日期 |
| 10 | useflg | VARCHAR(1) |  | 有效标志 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. twh12_detaildt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | seqno | INTEGER | PK NOT NULL | 序号 |
| 2 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 3 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 4 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 5 | prddate | TIMESTAMP |  | 生产日期 |
| 6 | billid | VARCHAR(8) |  | 单据号 |
| 7 | invdate | TIMESTAMP |  | 库存日期 |
| 8 | invtyp | VARCHAR(1) |  | 出入库类型 |
| 9 | itemqty | INTEGER |  | 变动数量 |
| 10 | storeqty | INTEGER |  | 库存余量 |
| 11 | opercd | VARCHAR(6) |  | 操作员 |
| 12 | gendate | TIMESTAMP |  | 创建日期 |
| 13 | useflg | VARCHAR(1) |  | 有效标志 |
| 14 | iotyp | VARCHAR(1) |  | 出入类型（I入/O出） |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. twh13_in

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | inbillid | VARCHAR(8) | PK NOT NULL | 入库单号 |
| 2 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 3 | indate | TIMESTAMP |  | 入库日期 |
| 4 | invtyp | VARCHAR(1) | NOT NULL | 入库类型 |
| 5 | refbillid | VARCHAR(8) |  | 关联单据号 |
| 6 | ptimes | INTEGER |  | 打印次数 |
| 7 | memo | VARCHAR(255) |  | 备注 |
| 8 | opercd | VARCHAR(6) |  | 操作员 |
| 9 | gendate | TIMESTAMP |  | 创建日期 |
| 10 | auditflg | VARCHAR(1) |  | 审核标志 |
| 11 | auditman | VARCHAR(6) |  | 审核人 |
| 12 | auditdate | TIMESTAMP |  | 审核日期 |
| 13 | useflg | VARCHAR(1) |  | 有效标志 |
| 14 | optyp | VARCHAR(1) |  | 操作类型 |
| 15 | suppcd | VARCHAR(8) |  | 供应商编码 |
| 16 | created_at | TIMESTAMP | NOT NULL |  |
| 17 | updated_at | TIMESTAMP | NOT NULL |  |

#### 5. twh14_checkindt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | inbillid | VARCHAR(8) | NOT NULL | 入库单号 |
| 3 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 4 | lineno | INTEGER | NOT NULL | 行号 |
| 5 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 6 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 7 | prddate | TIMESTAMP |  | 生产日期 |
| 8 | batchid | VARCHAR(50) |  | 批次号 |
| 9 | inqty | INTEGER |  | 入库数量 |
| 10 | reflineno | INTEGER |  | 关联行号 |
| 11 | s_money | NUMERIC(10,2) |  | 金额 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 6. twh15_out

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | outbillid | VARCHAR(8) | PK NOT NULL | 出库单号 |
| 2 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 3 | outdate | TIMESTAMP |  | 出库日期 |
| 4 | invtyp | VARCHAR(1) | NOT NULL | 出库类型 |
| 5 | ptimes | INTEGER |  | 打印次数 |
| 6 | memo | VARCHAR(255) |  | 备注 |
| 7 | opercd | VARCHAR(6) |  | 操作员 |
| 8 | gendate | TIMESTAMP |  | 创建日期 |
| 9 | auditflg | VARCHAR(1) |  | 审核标志 |
| 10 | auditman | VARCHAR(6) |  | 审核人 |
| 11 | auditdate | TIMESTAMP |  | 审核日期 |
| 12 | optyp | VARCHAR(2) |  | 操作类型 |
| 13 | useflg | VARCHAR(1) |  | 有效标志 |
| 14 | targetwhcd | VARCHAR(2) |  | 目标仓库（调拨） |
| 15 | suppcd | VARCHAR(8) |  | 供应商编码（退货） |
| 16 | created_at | TIMESTAMP | NOT NULL |  |
| 17 | updated_at | TIMESTAMP | NOT NULL |  |

#### 7. twh16_outdteid

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 3 | outbillid | VARCHAR(8) | NOT NULL | 出库单号 |
| 4 | lineno | INTEGER | NOT NULL | 行号 |
| 5 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 6 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 7 | prddate | TIMESTAMP |  | 生产日期 |
| 8 | eid | VARCHAR(13) |  | 设备唯一标识 |
| 9 | outqty | INTEGER |  | 出库数量 |
| 10 | qcqty | INTEGER |  | 质检数量 |
| 11 | reflineno | INTEGER |  | 关联行号 |
| 12 | s_money | NUMERIC(10,2) |  | 金额 |
| 13 | created_at | TIMESTAMP | NOT NULL |  |
| 14 | updated_at | TIMESTAMP | NOT NULL |  |

#### 8. twh16_outdtprd

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 3 | outbillid | VARCHAR(8) | NOT NULL | 出库单号 |
| 4 | lineno | INTEGER | NOT NULL | 行号 |
| 5 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 6 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 7 | prddate | TIMESTAMP |  | 生产日期 |
| 8 | outqty | INTEGER |  | 出库数量 |
| 9 | qcqty | INTEGER |  | 质检数量 |
| 10 | reflineno | INTEGER |  | 关联行号 |
| 11 | s_money | NUMERIC(10,2) |  | 金额 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 9. twh17_overlost

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | olbillid | VARCHAR(8) | PK NOT NULL | 盘点单号 |
| 2 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 3 | oltyp | VARCHAR(2) |  | 盘点类型 |
| 4 | oldate | TIMESTAMP |  | 盘点日期 |
| 5 | cfdate | TIMESTAMP |  | 确认日期 |
| 6 | memo | VARCHAR(60) |  | 备注 |
| 7 | opercd | VARCHAR(6) |  | 操作员 |
| 8 | gendate | TIMESTAMP |  | 创建日期 |
| 9 | useflg | VARCHAR(1) |  | 有效标志 |
| 10 | cfercd | VARCHAR(6) |  | 确认人 |
| 11 | optyp | VARCHAR(2) |  | 操作类型 |
| 12 | olreason | VARCHAR(100) |  | 盘点原因 |
| 13 | olsign | VARCHAR(1) |  | 盘盈盘亏标志（+盈/-亏） |
| 14 | auditflg | VARCHAR(1) |  | 审核标志 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |

#### 10. twh18_overlostdt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 3 | olbillid | VARCHAR(8) | NOT NULL | 盘点单号 |
| 4 | lineno | INTEGER | NOT NULL | 行号 |
| 5 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 6 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 7 | olqty | NUMERIC(12,4) |  | 盘点差异数量 |
| 8 | prddate | TIMESTAMP |  | 生产日期 |
| 9 | memo | VARCHAR(255) |  | 备注 |
| 10 | created_at | TIMESTAMP | NOT NULL |  |
| 11 | updated_at | TIMESTAMP | NOT NULL |  |

#### 11. twh18_overlosteid

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | whcd | VARCHAR(2) | NOT NULL | 仓库编码 |
| 3 | olbillid | VARCHAR(8) | NOT NULL | 盘点单号 |
| 4 | lineno | INTEGER | NOT NULL | 行号 |
| 5 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 6 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 7 | olqty | NUMERIC(12,4) |  | 差异数量 |
| 8 | prddate | TIMESTAMP |  | 生产日期 |
| 9 | memo | VARCHAR(255) |  | 备注 |
| 10 | eid | VARCHAR(13) |  | 设备唯一标识 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |

#### 12. twh19_asset_c_a

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | opbillid | VARCHAR(8) | PK NOT NULL | 盘点单号 |
| 2 | slbillid | VARCHAR(8) |  | 关联销售单号 |
| 3 | custcd | VARCHAR(8) | NOT NULL | 客户编码 |
| 4 | impdate | VARCHAR(6) |  | 实施日期 |
| 5 | traindate | VARCHAR(6) |  | 培训日期 |
| 6 | busityp | VARCHAR(2) |  | 业务类型 |
| 7 | sltyp | VARCHAR(2) |  | 销售类型 |
| 8 | itemcd | VARCHAR(6) |  | 物料编码 |
| 9 | opercd | VARCHAR(6) |  | 操作员 |
| 10 | backup | VARCHAR(255) |  | 备注 |
| 11 | gendate | TIMESTAMP |  | 创建日期 |
| 12 | useflg | VARCHAR(1) |  | 有效标志 |
| 13 | auditflg | VARCHAR(1) |  | 审核标志 |
| 14 | auditman | VARCHAR(6) |  | 审核人 |
| 15 | auditdate | TIMESTAMP |  | 审核日期 |
| 16 | created_at | TIMESTAMP | NOT NULL |  |
| 17 | updated_at | TIMESTAMP | NOT NULL |  |

#### 13. twh20_asset_c_a_dtl

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | opbillid | VARCHAR(8) | NOT NULL | 盘点单号 |
| 3 | custcard | VARCHAR(20) |  | 客户磁卡号 |
| 4 | custcd | VARCHAR(8) | NOT NULL | 客户编码 |
| 5 | planqty | INTEGER |  | 计划数量 |
| 6 | opqty | INTEGER |  | 实际数量 |
| 7 | clqty | INTEGER |  | 差异数量 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |
| 9 | impdate | TIMESTAMP |  | 实施日期 |
| 10 | traindate | TIMESTAMP |  | 培训日期 |
| 11 | newaddress | VARCHAR(255) |  | 新地址 |
| 12 | newcustcard | VARCHAR(20) |  | 新磁卡号 |
| 13 | address | VARCHAR(255) |  | 原地址 |
| 14 | newcustcd | VARCHAR(8) |  | 新客户编码 |
| 15 | eid | VARCHAR(13) |  | 设备EID |
| 16 | o_name | VARCHAR(100) |  | 原名称 |
| 17 | n_name | VARCHAR(100) |  | 新名称 |
| 18 | o_phoneno | VARCHAR(60) |  | 原电话 |
| 19 | n_phoneno | VARCHAR(60) |  | 新电话 |
| 20 | o_contactor | VARCHAR(10) |  | 原联系人 |
| 21 | n_contactor | VARCHAR(10) |  | 新联系人 |
| 22 | created_at | TIMESTAMP | NOT NULL |  |
| 23 | updated_at | TIMESTAMP | NOT NULL |  |

#### 14. twh21_pos_change

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL | 主键 |
| 2 | poseid | VARCHAR(20) |  | POS设备EID |
| 3 | opercd | VARCHAR(6) |  | 操作员 |
| 4 | upddate | TIMESTAMP |  | 更新日期 |
| 5 | useflg | VARCHAR(1) |  | 有效标志 |
| 6 | remark | VARCHAR(200) |  | 备注 |
| 7 | created_at | TIMESTAMP | NOT NULL |  |
| 8 | updated_at | TIMESTAMP | NOT NULL |  |

#### 15. twh22_pos_change_dt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL | 主键 |
| 2 | operation_id | INTEGER | NOT NULL | 变更操作ID |
| 3 | poseid | VARCHAR(20) |  | POS设备EID |
| 4 | changetype | INTEGER |  | 变更类型 |
| 5 | old_eid | VARCHAR(20) |  | 旧EID |
| 6 | new_eid | VARCHAR(20) |  | 新EID |
| 7 | opercd | VARCHAR(6) |  | 操作员 |
| 8 | upddate | TIMESTAMP |  | 更新日期 |
| 9 | useflg | VARCHAR(1) |  | 有效标志 |
| 10 | remark | VARCHAR(100) |  | 备注 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |


### 采购 (tpc) — 10 张表
> 采购计划/订单

#### 1. tpc01_pcplan

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | pcplanid | VARCHAR(8) | PK NOT NULL | 采购计划号 |
| 2 | slbillid | VARCHAR(8) |  | 关联销售单号 |
| 3 | pctyp | VARCHAR(1) |  | 采购类型 |
| 4 | ptimes | INTEGER |  | 打印次数 |
| 5 | opercd | VARCHAR(6) |  | 操作员 |
| 6 | memo | VARCHAR(255) |  | 备注 |
| 7 | gendate | TIMESTAMP |  | 创建日期 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |
| 9 | plandate | TIMESTAMP |  | 计划日期 |
| 10 | auditman | VARCHAR(6) |  | 审核人 |
| 11 | auditdate | TIMESTAMP |  | 审核日期 |
| 12 | checkmemo | VARCHAR(255) |  | 审核备注 |
| 13 | auditflg | VARCHAR(1) |  | 审核标志 |
| 14 | type | VARCHAR(1) |  | 类型 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tpc02_pcplandt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | pcplanid | VARCHAR(8) | NOT NULL | 采购计划号 |
| 3 | lineno | INTEGER | NOT NULL | 行号 |
| 4 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 5 | rgstqty | INTEGER |  | 登记数量 |
| 6 | units | VARCHAR(4) |  | 单位 |
| 7 | storeqty | INTEGER |  | 库存数量 |
| 8 | lowlimit | INTEGER |  | 库存下限 |
| 9 | upperlimit | INTEGER |  | 库存上限 |
| 10 | auditqty | INTEGER |  | 审批数量 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tpc03_pcplanstatus

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | itemcd | VARCHAR(6) | PK NOT NULL | 物料编码 |
| 2 | rgstqty | INTEGER |  | 登记数量 |
| 3 | auditqty | INTEGER |  | 审批数量 |
| 4 | pcqty | INTEGER |  | 采购数量 |
| 5 | opercd | VARCHAR(6) |  | 操作员 |
| 6 | memo | VARCHAR(255) |  | 备注 |
| 7 | gendate | TIMESTAMP |  | 创建日期 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |
| 9 | upddate | TIMESTAMP |  | 更新日期 |
| 10 | refbillid | VARCHAR(8) |  | 关联单号 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. tpc12_register

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | rgstbillid | VARCHAR(8) | PK NOT NULL | 登记单号 |
| 2 | suppliercd | VARCHAR(8) |  | 供应商编码 |
| 3 | pcrep | VARCHAR(6) |  | 采购代表 |
| 4 | ptimes | INTEGER |  | 打印次数 |
| 5 | opercd | VARCHAR(6) |  | 操作员 |
| 6 | memo | VARCHAR(255) |  | 备注 |
| 7 | gendate | TIMESTAMP |  | 创建日期 |
| 8 | auditman | VARCHAR(6) |  | 审核人 |
| 9 | auditdate | TIMESTAMP |  | 审核日期 |
| 10 | checkmemo | VARCHAR(255) |  | 审核备注 |
| 11 | auditflg | VARCHAR(1) |  | 审核标志 |
| 12 | useflg | VARCHAR(1) |  | 有效标志 |
| 13 | rgstdate | TIMESTAMP |  | 登记日期 |
| 14 | rgstamt | NUMERIC(12,2) |  | 登记金额 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |

#### 5. tpc13_registerdt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | rgstbillid | VARCHAR(8) | NOT NULL | 登记单号 |
| 3 | lineno | INTEGER | NOT NULL | 行号 |
| 4 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 5 | rgsqty | INTEGER |  | 登记数量 |
| 6 | memo | VARCHAR(255) |  | 备注 |
| 7 | units | VARCHAR(4) |  | 单位 |
| 8 | rgstprice | NUMERIC(16,8) |  | 登记单价 |
| 9 | deliverdate | TIMESTAMP |  | 交付日期 |
| 10 | inqty | INTEGER |  | 已入库数量 |
| 11 | auditqty | INTEGER |  | 审批数量 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 6. tpc14_pcbill

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | pcbillid | VARCHAR(8) | PK NOT NULL | 采购单号 |
| 2 | pctyp | VARCHAR(2) |  | 采购类型 |
| 3 | custcd | VARCHAR(8) |  | 客户编码 |
| 4 | refbillid | VARCHAR(8) |  | 关联单号 |
| 5 | pcdate | TIMESTAMP |  | 采购日期 |
| 6 | pcamt | NUMERIC(16,4) |  | 采购金额 |
| 7 | whcd | VARCHAR(2) |  | 入库仓库 |
| 8 | invoiceflg | VARCHAR(1) |  | 发票标志 |
| 9 | ptimes | INTEGER |  | 打印次数 |
| 10 | opercd | VARCHAR(6) |  | 操作员 |
| 11 | memo | VARCHAR(255) |  | 备注 |
| 12 | gendate | TIMESTAMP |  | 创建日期 |
| 13 | useflg | VARCHAR(1) |  | 有效标志 |
| 14 | created_at | TIMESTAMP | NOT NULL |  |
| 15 | updated_at | TIMESTAMP | NOT NULL |  |

#### 7. tpc16_rpcbill

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | pcbillid | VARCHAR(8) | PK NOT NULL | 退货单号 |
| 2 | custcd | VARCHAR(8) |  | 客户编码 |
| 3 | pcdate | TIMESTAMP |  | 退货日期 |
| 4 | pcamt | INTEGER |  | 退货金额 |
| 5 | whcd | VARCHAR(2) |  | 仓库编码 |
| 6 | invoiceflg | VARCHAR(2) |  | 发票标志 |
| 7 | ptimes | INTEGER |  | 打印次数 |
| 8 | opercd | VARCHAR(6) |  | 操作员 |
| 9 | memo | VARCHAR(255) |  | 备注 |
| 10 | useflg | VARCHAR(1) |  | 有效标志 |
| 11 | gendate | TIMESTAMP |  | 创建日期 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 8. tpc17_rpcbilldt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | pcbillid | VARCHAR(8) | NOT NULL | 退货单号 |
| 3 | lineno | INTEGER | NOT NULL | 行号 |
| 4 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 5 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 6 | eid | VARCHAR(13) |  | 设备EID |
| 7 | seid | VARCHAR(30) |  | 序列号 |
| 8 | rpcqty | INTEGER |  | 退货数量 |
| 9 | invoiceqty | INTEGER |  | 发票数量 |
| 10 | units | VARCHAR(4) |  | 单位 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |

#### 9. tpc20_suppappraisal

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | appid | VARCHAR(8) | PK NOT NULL | 评价单号 |
| 2 | sdate | TIMESTAMP |  | 开始日期 |
| 3 | edate | TIMESTAMP |  | 结束日期 |
| 4 | memo | VARCHAR(255) |  | 备注 |
| 5 | opercd | VARCHAR(6) |  | 操作员 |
| 6 | gendate | TIMESTAMP |  | 创建日期 |
| 7 | auditflg | VARCHAR(1) |  | 审核标志 |
| 8 | auditman | VARCHAR(6) |  | 审核人 |
| 9 | auditdate | TIMESTAMP |  | 审核日期 |
| 10 | useflg | VARCHAR(1) |  | 有效标志 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |

#### 10. tpc21_suppappraisaldt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | appid | VARCHAR(8) | NOT NULL | 评价单号 |
| 3 | lineno | INTEGER | NOT NULL | 行号 |
| 4 | supplierid | VARCHAR(8) | NOT NULL | 供应商编码 |
| 5 | appcode | VARCHAR(2) |  | 评价代码 |
| 6 | appscore | INTEGER |  | 评分 |
| 7 | appflg | VARCHAR(1) |  | 评价标志 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |


### 销售 (tsl) — 3 张表
> 销售/延期

#### 1. tsl01_extend

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | opbillid | VARCHAR(8) | PK NOT NULL | 延期单号 |
| 2 | slbillid | VARCHAR(8) |  | 关联销售单号 |
| 3 | custcd | VARCHAR(8) |  | 客户编码 |
| 4 | impdate | VARCHAR(6) |  | 实施日期 |
| 5 | traindate | VARCHAR(6) |  | 培训日期 |
| 6 | busityp | VARCHAR(2) |  | 业务类型 |
| 7 | sltyp | VARCHAR(2) |  | 销售类型 |
| 8 | itemcd | VARCHAR(6) |  | 物料编码 |
| 9 | opercd | VARCHAR(6) |  | 操作员 |
| 10 | backup | VARCHAR(255) |  | 备注 |
| 11 | gendate | TIMESTAMP |  | 创建日期 |
| 12 | useflg | VARCHAR(1) |  | 有效标志 |
| 13 | auditflg | VARCHAR(1) |  | 审核标志 |
| 14 | auditman | VARCHAR(6) |  | 审核人 |
| 15 | auditdate | TIMESTAMP |  | 审核日期 |
| 16 | created_at | TIMESTAMP | NOT NULL |  |
| 17 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tsl02_extenddt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | opbillid | VARCHAR(8) | NOT NULL | 延期单号 |
| 3 | custcard | VARCHAR(20) |  | 客户磁卡号 |
| 4 | custcd | VARCHAR(8) | NOT NULL | 客户编码 |
| 5 | planqty | INTEGER |  | 计划数量 |
| 6 | opqty | INTEGER |  | 实际数量 |
| 7 | clqty | INTEGER |  | 差异数量 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |
| 9 | impdate | TIMESTAMP |  | 实施日期 |
| 10 | traindate | TIMESTAMP |  | 培训日期 |
| 11 | newaddress | VARCHAR(255) |  | 新地址 |
| 12 | newcustcard | VARCHAR(20) |  | 新磁卡号 |
| 13 | address | VARCHAR(255) |  | 原地址 |
| 14 | newcustcd | VARCHAR(8) |  | 新客户编码 |
| 15 | eid | VARCHAR(13) |  | 设备EID |
| 16 | o_name | VARCHAR(100) |  | 原名称 |
| 17 | n_name | VARCHAR(100) |  | 新名称 |
| 18 | o_phoneno | VARCHAR(60) |  | 原电话 |
| 19 | n_phoneno | VARCHAR(60) |  | 新电话 |
| 20 | o_contactor | VARCHAR(10) |  | 原联系人 |
| 21 | n_contactor | VARCHAR(10) |  | 新联系人 |
| 22 | is_back | VARCHAR(1) |  | 是否退回 |
| 23 | ufdate | TIMESTAMP |  | 退回日期 |
| 24 | mr | VARCHAR(1) |  | MR标志 |
| 25 | created_at | TIMESTAMP | NOT NULL |  |
| 26 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tsl10_slbill

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | slbillid | VARCHAR(8) | PK NOT NULL | 销售单号 |
| 2 | custbillid | VARCHAR(20) |  | 客户单号 |
| 3 | sltyp | VARCHAR(2) |  | 销售类型 |
| 4 | custcd | VARCHAR(8) |  | 客户编码 |
| 5 | rgsdate | TIMESTAMP |  | 登记日期 |
| 6 | senddate | TIMESTAMP |  | 发货日期 |
| 7 | busityp | VARCHAR(2) |  | 业务类型 |
| 8 | ptimes | INTEGER |  | 打印次数 |
| 9 | opercd | VARCHAR(6) |  | 操作员 |
| 10 | memo | VARCHAR(255) |  | 备注 |
| 11 | gendate | TIMESTAMP |  | 创建日期 |
| 12 | auditman | VARCHAR(6) |  | 审核人 |
| 13 | auditdate | TIMESTAMP |  | 审核日期 |
| 14 | checkmemo | VARCHAR(255) |  | 审核备注 |
| 15 | auditflg | VARCHAR(1) |  | 审核标志 |
| 16 | pcplanflg | VARCHAR(1) |  | 采购计划标志 |
| 17 | rfpcplanid | VARCHAR(8) |  | 关联采购计划号 |
| 18 | itemcd | VARCHAR(6) |  | 物料编码 |
| 19 | rgsqty | INTEGER |  | 登记数量 |
| 20 | planqty | INTEGER |  | 计划数量 |
| 21 | openqty | INTEGER |  | 开通数量 |
| 22 | clqty | INTEGER |  | 关闭数量 |
| 23 | useflg | VARCHAR(1) |  | 有效标志 |
| 24 | created_at | TIMESTAMP | NOT NULL |  |
| 25 | updated_at | TIMESTAMP | NOT NULL |  |


### 财务 (tfn) — 5 张表
> 账务/支付

#### 1. tfn01_account

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | account_cd | VARCHAR(20) | PK NOT NULL | 科目编码 |
| 2 | account_nm | VARCHAR(100) | NOT NULL | 科目名称 |
| 3 | account_type | VARCHAR(10) | NOT NULL | 类型（AR=应收/AP=应付/INCOME=收入/EXPENSE=费用/ASSET=资产） |
| 4 | parent_cd | VARCHAR(20) |  | 上级科目 |
| 5 | useflg | VARCHAR(1) |  | 有效标志 |
| 6 | remark | VARCHAR(200) |  | 备注 |
| 7 | opercd | VARCHAR(6) |  | 操作人 |
| 8 | upddate | TIMESTAMP |  | 更新日期 |
| 9 | created_at | TIMESTAMP | NOT NULL |  |
| 10 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tfn02_receivable

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | ar_id | VARCHAR(20) | PK NOT NULL | 应收编号 |
| 2 | custcd | VARCHAR(10) | NOT NULL | 客户编码 |
| 3 | account_cd | VARCHAR(20) |  | 科目编码 |
| 4 | bill_id | VARCHAR(20) |  | 关联账单编号 |
| 5 | fpbh | VARCHAR(30) |  | 关联发票编号 |
| 6 | htbh | VARCHAR(20) |  | 关联合同编号 |
| 7 | ar_date | date | NOT NULL | 应收日期 |
| 8 | due_date | date |  | 到期日 |
| 9 | amount | NUMERIC(12,2) | NOT NULL | 应收金额 |
| 10 | paid_amount | NUMERIC(12,2) |  | 已收金额 |
| 11 | balance | NUMERIC(12,2) |  | 余额 |
| 12 | status | VARCHAR(10) |  | 状态（PENDING/PARTIAL/PAID/OVERDUE/CANCELLED） |
| 13 | remark | VARCHAR(200) |  | 备注 |
| 14 | opercd | VARCHAR(6) |  | 操作人 |
| 15 | upddate | TIMESTAMP |  | 更新日期 |
| 16 | created_at | TIMESTAMP | NOT NULL |  |
| 17 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tfn03_payable

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | ap_id | VARCHAR(20) | PK NOT NULL | 应付编号 |
| 2 | supp_cd | VARCHAR(20) | NOT NULL | 供应商编码 |
| 3 | account_cd | VARCHAR(20) |  | 科目编码 |
| 4 | po_id | VARCHAR(20) |  | 关联采购单号 |
| 5 | ap_date | date | NOT NULL | 应付日期 |
| 6 | due_date | date |  | 到期日 |
| 7 | amount | NUMERIC(12,2) | NOT NULL | 应付金额 |
| 8 | paid_amount | NUMERIC(12,2) |  | 已付金额 |
| 9 | balance | NUMERIC(12,2) |  | 余额 |
| 10 | status | VARCHAR(10) |  | 状态（PENDING/PARTIAL/PAID/OVERDUE/CANCELLED） |
| 11 | remark | VARCHAR(200) |  | 备注 |
| 12 | opercd | VARCHAR(6) |  | 操作人 |
| 13 | upddate | TIMESTAMP |  | 更新日期 |
| 14 | created_at | TIMESTAMP | NOT NULL |  |
| 15 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. tfn04_payment

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | pay_id | VARCHAR(20) | PK NOT NULL | 收付款编号 |
| 2 | pay_type | VARCHAR(10) | NOT NULL | 类型（RECEIVE=收款/PAY=付款） |
| 3 | ref_id | VARCHAR(20) |  | 关联编号（应收ar_id或应付ap_id） |
| 4 | custcd | VARCHAR(10) |  | 客户编码 |
| 5 | supp_cd | VARCHAR(20) |  | 供应商编码 |
| 6 | pay_date | date | NOT NULL | 收付款日期 |
| 7 | amount | NUMERIC(12,2) | NOT NULL | 收付款金额 |
| 8 | pay_method | VARCHAR(10) |  | 支付方式（CASH/BANK/CHECK/DEPOSIT_OFFSET） |
| 9 | bank_account | VARCHAR(30) |  | 银行账号 |
| 10 | remark | VARCHAR(200) |  | 备注 |
| 11 | opercd | VARCHAR(6) |  | 操作人 |
| 12 | upddate | TIMESTAMP |  | 更新日期 |
| 13 | created_at | TIMESTAMP | NOT NULL |  |
| 14 | updated_at | TIMESTAMP | NOT NULL |  |

#### 5. tfn05_depreciation

**索引**: `tfn05_depreciation_eid_key` (eid)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | eid | VARCHAR(50) | NOT NULL | 设备序列号 |
| 3 | item_cd | VARCHAR(20) |  | 物料编码 |
| 4 | original_value | NUMERIC(12,2) |  | 原值 |
| 5 | salvage_value | NUMERIC(12,2) |  | 残值 |
| 6 | useful_life_months | INTEGER |  | 使用年限（月） |
| 7 | method | VARCHAR(10) |  | 折旧方法（SL=直线法/DB=余额递减） |
| 8 | start_date | date |  | 折旧起始日 |
| 9 | monthly_amount | NUMERIC(10,2) |  | 月折旧额 |
| 10 | accumulated | NUMERIC(12,2) |  | 累计折旧 |
| 11 | net_value | NUMERIC(12,2) |  | 净值 |
| 12 | last_calc_date | date |  | 最后计算日期 |
| 13 | opercd | VARCHAR(6) |  | 操作人 |
| 14 | upddate | TIMESTAMP |  | 更新日期 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |


### 财务 (tac/tht) — 1 张表
> 合同/发票

#### 1. tac01_fpsk

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | fpbh | VARCHAR(30) | PK NOT NULL | 发票编号 |
| 2 | years | VARCHAR(4) |  | 年份 |
| 3 | classcd | VARCHAR(6) |  | 区域 |
| 4 | busityp | VARCHAR(2) |  | 合同属性 |
| 5 | feetyp | VARCHAR(2) |  | 费用类型 |
| 6 | htbh | VARCHAR(20) |  | 合同编号 |
| 7 | htq | VARCHAR(2) |  | 合同期 |
| 8 | qsr | VARCHAR(10) |  | 签收人 |
| 9 | lsh | VARCHAR(30) |  | 流水号 |
| 10 | kpdate | date |  | 开票日期 |
| 11 | kpamount | NUMERIC(10,2) |  | 开票金额 |
| 12 | hkdate | date |  | 回款日期 |
| 13 | hkamount | NUMERIC(10,2) |  | 回款金额 |
| 14 | sptype | VARCHAR(6) |  | 送票方式 |
| 15 | spr | VARCHAR(6) |  | 送票人 |
| 16 | htqdis | VARCHAR(1) |  | 合同签订与否 |
| 17 | htamount | NUMERIC(10,2) |  | 合同金额 |
| 18 | remark | VARCHAR(200) |  | 备注 |
| 19 | opercd | VARCHAR(6) |  | 更新人 |
| 20 | upddate | TIMESTAMP |  | 更新日期 |
| 21 | created_at | TIMESTAMP | NOT NULL |  |
| 22 | updated_at | TIMESTAMP | NOT NULL |  |


### 考勤 (tkq) — 2 张表
> 考勤

#### 1. tkq01_attendance

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | amonth | VARCHAR(6) | PK NOT NULL | 考勤月份 |
| 2 | adate | date | PK NOT NULL | 考勤日期 |
| 3 | operid | VARCHAR(6) | PK NOT NULL | 员工ID |
| 4 | opernm | VARCHAR(12) |  | 员工姓名 |
| 5 | arr_time | TIMESTAMP |  | 上班时间 |
| 6 | leave_time | TIMESTAMP |  | 下班时间 |
| 7 | latecount | INTEGER |  | 迟到时长(分钟) |
| 8 | leavecount | INTEGER |  | 早退时长(分钟) |
| 9 | punchnum | INTEGER |  | 打卡次数 |
| 10 | punchdetail | VARCHAR(100) |  | 打卡明细 |
| 11 | imp_num | INTEGER |  | 导入次数 |
| 12 | week | VARCHAR(2) |  | 星期 |
| 13 | useflg | VARCHAR(1) |  | 有效标记 |
| 14 | imp_date | TIMESTAMP |  | 导入日期 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |
| 17 | update_time | TIMESTAMP |  | 更新时间 |
| 18 | updator | VARCHAR(10) |  | 更新人 |

#### 2. tkq02_attendancecount

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | amonth | VARCHAR(6) | PK NOT NULL | 考勤月份 |
| 2 | operid | VARCHAR(6) | PK NOT NULL | 员工ID |
| 3 | opernm | VARCHAR(12) |  | 员工姓名 |
| 4 | d1 | VARCHAR(12) |  | 1号 |
| 5 | d2 | VARCHAR(12) |  | 2号 |
| 6 | d3 | VARCHAR(12) |  | 3号 |
| 7 | d4 | VARCHAR(12) |  | 4号 |
| 8 | d5 | VARCHAR(12) |  | 5号 |
| 9 | d6 | VARCHAR(12) |  | 6号 |
| 10 | d7 | VARCHAR(12) |  | 7号 |
| 11 | d8 | VARCHAR(12) |  | 8号 |
| 12 | d9 | VARCHAR(12) |  | 9号 |
| 13 | d10 | VARCHAR(12) |  | 10号 |
| 14 | d11 | VARCHAR(12) |  | 11号 |
| 15 | d12 | VARCHAR(12) |  | 12号 |
| 16 | d13 | VARCHAR(12) |  | 13号 |
| 17 | d14 | VARCHAR(12) |  | 14号 |
| 18 | d15 | VARCHAR(12) |  | 15号 |
| 19 | d16 | VARCHAR(12) |  | 16号 |
| 20 | d17 | VARCHAR(12) |  | 17号 |
| 21 | d18 | VARCHAR(12) |  | 18号 |
| 22 | d19 | VARCHAR(12) |  | 19号 |
| 23 | d20 | VARCHAR(12) |  | 20号 |
| 24 | d21 | VARCHAR(12) |  | 21号 |
| 25 | d22 | VARCHAR(12) |  | 22号 |
| 26 | d23 | VARCHAR(12) |  | 23号 |
| 27 | d24 | VARCHAR(12) |  | 24号 |
| 28 | d25 | VARCHAR(12) |  | 25号 |
| 29 | d26 | VARCHAR(12) |  | 26号 |
| 30 | d27 | VARCHAR(12) |  | 27号 |
| 31 | d28 | VARCHAR(12) |  | 28号 |
| 32 | d29 | VARCHAR(12) |  | 29号 |
| 33 | d30 | VARCHAR(12) |  | 30号 |
| 34 | d31 | VARCHAR(12) |  | 31号 |
| 35 | latecount | INTEGER |  | 迟到次数 |
| 36 | leavecount | INTEGER |  | 早退次数 |
| 37 | absentcount | INTEGER |  | 缺勤次数 |
| 38 | useflg | VARCHAR(1) |  | 有效标记 |
| 39 | created_at | TIMESTAMP | NOT NULL |  |
| 40 | updated_at | TIMESTAMP | NOT NULL |  |
| 41 | memo | VARCHAR(200) |  | 备注 |
| 42 | imp_num | INTEGER |  | 导入次数 |
| 43 | imp_date | TIMESTAMP |  | 导入日期 |
| 44 | update_time | TIMESTAMP |  | 更新时间 |
| 45 | updator | VARCHAR(10) |  | 更新人 |


### 库存预警 (tiv) — 4 张表
> 预警规则/库存明细

#### 1. tiv01_invlimit

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | itemcd | VARCHAR(8) | PK NOT NULL | 物料编码 |
| 2 | invlow | NUMERIC(12,4) |  | 库存下限 |
| 3 | invhigh | NUMERIC(12,4) |  | 库存上限 |
| 4 | daylow | INTEGER |  | 天数下限 |
| 5 | dayhigh | INTEGER |  | 天数上限 |
| 6 | opercd | VARCHAR(6) |  | 操作员 |
| 7 | gendate | TIMESTAMP |  | 创建日期 |
| 8 | upddate | TIMESTAMP |  | 更新日期 |
| 9 | useflg | VARCHAR(1) |  | 有效标志 |
| 10 | created_at | TIMESTAMP | NOT NULL |  |
| 11 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tiv02_invlimit_hi

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | itemcd | VARCHAR(8) | NOT NULL | 物料编码 |
| 3 | lineid | NUMERIC(12,4) |  | 行号 |
| 4 | invlow | NUMERIC(12,4) |  | 库存下限 |
| 5 | invhigh | NUMERIC(12,4) |  | 库存上限 |
| 6 | daylow | INTEGER |  | 天数下限 |
| 7 | dayhigh | INTEGER |  | 天数上限 |
| 8 | opercd | VARCHAR(6) |  | 操作员 |
| 9 | gendate | TIMESTAMP |  | 创建日期 |
| 10 | upddate | TIMESTAMP |  | 更新日期 |
| 11 | useflg | VARCHAR(1) |  | 有效标志 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tiv11_detail

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | itemcd | VARCHAR(8) | PK NOT NULL | 物料编码 |
| 2 | whcd | VARCHAR(2) |  | 仓库编码 |
| 3 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 4 | storeqty | NUMERIC(12,0) |  | 库存数量 |
| 5 | opercd | VARCHAR(6) |  | 操作员 |
| 6 | gendate | TIMESTAMP |  | 创建日期 |
| 7 | useflg | VARCHAR(1) |  | 有效标志 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. tiv12_detaildt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | seqno | INTEGER | PK NOT NULL | 流水号 |
| 2 | itemcd | VARCHAR(8) |  | 物料编码 |
| 3 | whcd | VARCHAR(2) |  | 仓库编码 |
| 4 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 5 | billid | VARCHAR(8) |  | 单号 |
| 6 | invdate | TIMESTAMP |  | 库存日期 |
| 7 | invtyp | VARCHAR(1) |  | 出入库类型 |
| 8 | itemqty | NUMERIC(12,0) |  | 本次数量 |
| 9 | storeqty | NUMERIC(12,0) |  | 库存数量 |
| 10 | opercd | VARCHAR(6) |  | 操作员 |
| 11 | gendate | TIMESTAMP |  | 创建日期 |
| 12 | useflg | VARCHAR(1) |  | 有效标志 |
| 13 | created_at | TIMESTAMP | NOT NULL |  |
| 14 | updated_at | TIMESTAMP | NOT NULL |  |


### 结算 (tbl) — 4 张表
> 结算规则/账单

#### 1. tbl01_billing_rule

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | rule_id | VARCHAR(20) | PK NOT NULL | 规则编号 |
| 2 | rule_name | VARCHAR(100) | NOT NULL | 规则名称 |
| 3 | billing_type | VARCHAR(10) | NOT NULL | 结算类型（RENT=租金/SALE=销售/SERVICE=服务费） |
| 4 | cycle_type | VARCHAR(10) | NOT NULL | 结算周期（MONTHLY/QUARTERLY/YEARLY/ONETIME） |
| 5 | price_source | VARCHAR(10) |  | 价格来源（MODEL=型号标准/CONTRACT=合同约定/CUSTOM=自定义） |
| 6 | tax_rate | NUMERIC(5,2) |  | 税率（百分比） |
| 7 | late_fee_rate | NUMERIC(5,4) |  | 滞纳金日费率 |
| 8 | remark | VARCHAR(200) |  | 备注 |
| 9 | useflg | VARCHAR(1) |  | 有效标志 |
| 10 | opercd | VARCHAR(6) |  | 操作人 |
| 11 | upddate | TIMESTAMP |  | 更新日期 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tbl02_bill

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | bill_id | VARCHAR(20) | PK NOT NULL | 账单编号 |
| 2 | custcd | VARCHAR(10) | NOT NULL | 客户编码 |
| 3 | billing_type | VARCHAR(10) | NOT NULL | 结算类型 |
| 4 | bill_period | VARCHAR(10) |  | 账单周期（如202604） |
| 5 | bill_date | date | NOT NULL | 账单日期 |
| 6 | due_date | date |  | 到期日 |
| 7 | total_amount | NUMERIC(12,2) |  | 账单总额 |
| 8 | tax_amount | NUMERIC(12,2) |  | 税额 |
| 9 | paid_amount | NUMERIC(12,2) |  | 已付金额 |
| 10 | status | VARCHAR(10) |  | 状态（PENDING/SENT/PARTIAL/PAID/OVERDUE/CANCELLED） |
| 11 | htbh | VARCHAR(20) |  | 关联合同编号 |
| 12 | batch_id | VARCHAR(20) |  | 生成批次号 |
| 13 | remark | VARCHAR(200) |  | 备注 |
| 14 | opercd | VARCHAR(6) |  | 操作人 |
| 15 | upddate | TIMESTAMP |  | 更新日期 |
| 16 | created_at | TIMESTAMP | NOT NULL |  |
| 17 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tbl03_bill_detail

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | bill_id | VARCHAR(20) | NOT NULL | 账单编号 |
| 3 | item_cd | VARCHAR(20) |  | 物料/设备编码 |
| 4 | model_cd | VARCHAR(8) |  | 型号编码 |
| 5 | eid | VARCHAR(50) |  | 设备序列号 |
| 6 | description | VARCHAR(200) |  | 费用说明 |
| 7 | quantity | INTEGER |  | 数量 |
| 8 | unit_price | NUMERIC(10,2) |  | 单价 |
| 9 | amount | NUMERIC(12,2) |  | 金额 |
| 10 | period_from | date |  | 计费起始日 |
| 11 | period_to | date |  | 计费截止日 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. tbl04_billing_batch

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | batch_id | VARCHAR(20) | PK NOT NULL | 批次编号 |
| 2 | batch_date | date | NOT NULL | 批次日期 |
| 3 | billing_type | VARCHAR(10) |  | 结算类型 |
| 4 | bill_period | VARCHAR(10) |  | 账单周期 |
| 5 | total_bills | INTEGER |  | 账单数量 |
| 6 | total_amount | NUMERIC(14,2) |  | 总金额 |
| 7 | status | VARCHAR(10) |  | 状态（RUNNING/COMPLETED/FAILED） |
| 8 | remark | VARCHAR(200) |  | 备注 |
| 9 | opercd | VARCHAR(6) |  | 操作人 |
| 10 | upddate | TIMESTAMP |  | 更新日期 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |


### 通知 (tntf) — 2 张表
> 通知模板/记录

#### 1. tntf01_template

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | template_id | VARCHAR(8) | PK NOT NULL | 模板ID |
| 2 | template_name | VARCHAR(50) | NOT NULL | 模板名称 |
| 3 | channel | VARCHAR(10) | NOT NULL | 渠道: sms/email/internal |
| 4 | subject | VARCHAR(200) |  | 标题模板 |
| 5 | body | text |  | 正文模板 |
| 6 | opercd | VARCHAR(6) |  | 操作员 |
| 7 | gendate | TIMESTAMP |  | 创建日期 |
| 8 | upddate | TIMESTAMP |  | 更新日期 |
| 9 | useflg | VARCHAR(1) |  | 有效标志 |
| 10 | created_at | TIMESTAMP | NOT NULL |  |
| 11 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tntf02_notification

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | template_id | VARCHAR(8) |  | 模板ID |
| 3 | channel | VARCHAR(10) | NOT NULL | 渠道: sms/email/internal |
| 4 | recipient | VARCHAR(100) | NOT NULL | 接收方(手机/邮箱/用户ID) |
| 5 | subject | VARCHAR(200) |  | 标题 |
| 6 | body | text |  | 正文 |
| 7 | ref_type | VARCHAR(20) |  | 关联业务类型 |
| 8 | ref_id | VARCHAR(20) |  | 关联业务ID |
| 9 | send_status | VARCHAR(10) |  | 发送状态: pending/sent/failed |
| 10 | send_time | TIMESTAMP |  | 发送时间 |
| 11 | error_msg | VARCHAR(500) |  | 错误信息 |
| 12 | opercd | VARCHAR(6) |  | 操作员 |
| 13 | gendate | TIMESTAMP |  | 创建日期 |
| 14 | useflg | VARCHAR(1) |  | 有效标志 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |


### SLA (sla) — 2 张表
> 服务级别

#### 1. sla_definition

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | sla_id | VARCHAR(8) | PK NOT NULL | SLA编号 |
| 2 | sla_name | VARCHAR(60) | NOT NULL | SLA名称 |
| 3 | levels | VARCHAR(2) |  | 关联响应等级（TIT01.LEVELS） |
| 4 | priority | VARCHAR(1) |  | 优先级（1高/2中/3低） |
| 5 | response_minutes | INTEGER | NOT NULL | 响应时限（分钟） |
| 6 | resolve_minutes | INTEGER | NOT NULL | 解决时限（分钟） |
| 7 | escalation_minutes | INTEGER |  | 升级时限（分钟） |
| 8 | business_hours_only | BOOLEAN |  | 是否仅计算工作时间 |
| 9 | description | VARCHAR(200) |  | SLA描述 |
| 10 | opercd | VARCHAR(6) |  | 操作员 |
| 11 | gendate | TIMESTAMP |  | 创建日期 |
| 12 | upddate | TIMESTAMP |  | 更新日期 |
| 13 | useflg | VARCHAR(1) |  | 有效标志 |
| 14 | created_at | TIMESTAMP | NOT NULL |  |
| 15 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. sla_ticket

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | sla_id | VARCHAR(8) | NOT NULL | SLA编号 |
| 3 | maintenance_id | VARCHAR(8) | NOT NULL | 维护单ID |
| 4 | maintenance_type | VARCHAR(10) | NOT NULL | 单据类型 |
| 5 | sla_status | VARCHAR(2) |  | SLA状态（00正常/01预警/02违约/99关闭） |
| 6 | created_time | TIMESTAMP | NOT NULL | 工单创建时间 |
| 7 | first_response_time | TIMESTAMP |  | 首次响应时间 |
| 8 | resolved_time | TIMESTAMP |  | 解决时间 |
| 9 | response_met | BOOLEAN |  | 响应是否达标 |
| 10 | resolve_met | BOOLEAN |  | 解决是否达标 |
| 11 | response_elapsed_minutes | INTEGER |  | 响应耗时（分钟） |
| 12 | resolve_elapsed_minutes | INTEGER |  | 解决耗时（分钟） |
| 13 | escalated | BOOLEAN |  | 是否已升级 |
| 14 | escalation_time | TIMESTAMP |  | 升级时间 |
| 15 | opercd | VARCHAR(6) |  | 操作员 |
| 16 | gendate | TIMESTAMP |  | 创建日期 |
| 17 | upddate | TIMESTAMP |  | 更新日期 |
| 18 | useflg | VARCHAR(1) |  | 有效标志 |
| 19 | created_at | TIMESTAMP | NOT NULL |  |
| 20 | updated_at | TIMESTAMP | NOT NULL |  |


### 门户 (tpt) — 3 张表
> 自助报修/评价

#### 1. tpt01_portal_user

**索引**: `tpt01_portal_user_login_name_key` (login_name)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | portal_uid | VARCHAR(20) | PK NOT NULL | 门户用户ID |
| 2 | custcd | VARCHAR(10) | NOT NULL | 关联客户编码 |
| 3 | login_name | VARCHAR(50) | NOT NULL | 登录名 |
| 4 | password_hash | VARCHAR(256) | NOT NULL | 密码哈希 |
| 5 | contact_name | VARCHAR(50) |  | 联系人姓名 |
| 6 | phone | VARCHAR(20) |  | 手机号 |
| 7 | email | VARCHAR(100) |  | 邮箱 |
| 8 | status | VARCHAR(10) |  | 状态（ACTIVE/DISABLED） |
| 9 | last_login | TIMESTAMP |  | 最后登录时间 |
| 10 | opercd | VARCHAR(6) |  | 操作人 |
| 11 | upddate | TIMESTAMP |  | 更新日期 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tpt02_repair_request

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | request_id | VARCHAR(20) | PK NOT NULL | 报修单号 |
| 2 | portal_uid | VARCHAR(20) | NOT NULL | 报修用户 |
| 3 | custcd | VARCHAR(10) | NOT NULL | 客户编码 |
| 4 | eid | VARCHAR(50) |  | 设备序列号 |
| 5 | fault_desc | VARCHAR(500) |  | 故障描述 |
| 6 | urgency | VARCHAR(10) |  | 紧急程度（LOW/NORMAL/HIGH/URGENT） |
| 7 | contact_name | VARCHAR(50) |  | 联系人 |
| 8 | contact_phone | VARCHAR(20) |  | 联系电话 |
| 9 | address | VARCHAR(200) |  | 服务地址 |
| 10 | status | VARCHAR(10) |  | 状态（SUBMITTED/ACCEPTED/PROCESSING/COMPLETED/CANCELLED） |
| 11 | maintenance_id | VARCHAR(20) |  | 关联ITSM维护单号 |
| 12 | submit_time | TIMESTAMP |  | 提交时间 |
| 13 | accept_time | TIMESTAMP |  | 受理时间 |
| 14 | complete_time | TIMESTAMP |  | 完成时间 |
| 15 | remark | VARCHAR(200) |  | 备注 |
| 16 | opercd | VARCHAR(6) |  | 操作人 |
| 17 | upddate | TIMESTAMP |  | 更新日期 |
| 18 | created_at | TIMESTAMP | NOT NULL |  |
| 19 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tpt03_service_rating

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | request_id | VARCHAR(20) |  | 关联报修单号 |
| 3 | maintenance_id | VARCHAR(20) |  | 关联维护单号 |
| 4 | portal_uid | VARCHAR(20) |  | 评价用户 |
| 5 | custcd | VARCHAR(10) |  | 客户编码 |
| 6 | rating | INTEGER |  | 评分（1-5星） |
| 7 | response_rating | INTEGER |  | 响应速度评分（1-5） |
| 8 | quality_rating | INTEGER |  | 服务质量评分（1-5） |
| 9 | attitude_rating | INTEGER |  | 服务态度评分（1-5） |
| 10 | comment | VARCHAR(500) |  | 评价内容 |
| 11 | rating_time | TIMESTAMP |  | 评价时间 |
| 12 | opercd | VARCHAR(6) |  | 操作人 |
| 13 | upddate | TIMESTAMP |  | 更新日期 |
| 14 | created_at | TIMESTAMP | NOT NULL |  |
| 15 | updated_at | TIMESTAMP | NOT NULL |  |


### IoT (tio) — 4 张表
> 设备接入/监控

#### 1. tio01_device_conn

**索引**: `tio01_device_conn_eid_key` (eid)

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | conn_id | VARCHAR(20) | PK NOT NULL | 接入编号 |
| 2 | eid | VARCHAR(50) | NOT NULL | 设备序列号 |
| 3 | protocol | VARCHAR(10) |  | 接入协议（MQTT/HTTP/TCP） |
| 4 | topic | VARCHAR(200) |  | MQTT主题 |
| 5 | endpoint | VARCHAR(200) |  | 接入端点地址 |
| 6 | heartbeat_interval | INTEGER |  | 心跳间隔（秒） |
| 7 | last_heartbeat | TIMESTAMP |  | 最后心跳时间 |
| 8 | online_status | VARCHAR(10) |  | 在线状态（ONLINE/OFFLINE/UNKNOWN） |
| 9 | useflg | VARCHAR(1) |  | 有效标志 |
| 10 | opercd | VARCHAR(6) |  | 操作人 |
| 11 | upddate | TIMESTAMP |  | 更新日期 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tio02_device_data

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | eid | VARCHAR(50) | NOT NULL | 设备序列号 |
| 3 | data_type | VARCHAR(20) | NOT NULL | 数据类型（TEMPERATURE/PRESSURE/STATUS/LOCATION/COUNTER等） |
| 4 | data_value | VARCHAR(100) |  | 数据值 |
| 5 | data_unit | VARCHAR(20) |  | 数据单位 |
| 6 | report_time | TIMESTAMP | NOT NULL | 上报时间 |
| 7 | quality | VARCHAR(10) |  | 数据质量（GOOD/BAD/UNCERTAIN） |
| 8 | opercd | VARCHAR(6) |  | 操作人 |
| 9 | upddate | TIMESTAMP |  | 更新日期 |
| 10 | created_at | TIMESTAMP | NOT NULL |  |
| 11 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tio03_alert_rule

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | rule_id | VARCHAR(20) | PK NOT NULL | 规则编号 |
| 2 | rule_name | VARCHAR(100) | NOT NULL | 规则名称 |
| 3 | data_type | VARCHAR(20) | NOT NULL | 监控数据类型 |
| 4 | condition_type | VARCHAR(10) | NOT NULL | 条件类型（GT/LT/EQ/RANGE/OFFLINE） |
| 5 | threshold_min | NUMERIC(10,2) |  | 下限阈值 |
| 6 | threshold_max | NUMERIC(10,2) |  | 上限阈值 |
| 7 | severity | VARCHAR(10) |  | 严重度（INFO/WARNING/CRITICAL） |
| 8 | notify_method | VARCHAR(20) |  | 通知方式（SMS/EMAIL/APP/ALL） |
| 9 | useflg | VARCHAR(1) |  | 有效标志 |
| 10 | opercd | VARCHAR(6) |  | 操作人 |
| 11 | upddate | TIMESTAMP |  | 更新日期 |
| 12 | created_at | TIMESTAMP | NOT NULL |  |
| 13 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. tio04_alert_log

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | rule_id | VARCHAR(20) | NOT NULL | 规则编号 |
| 3 | eid | VARCHAR(50) | NOT NULL | 设备序列号 |
| 4 | alert_time | TIMESTAMP | NOT NULL | 报警时间 |
| 5 | data_type | VARCHAR(20) |  | 数据类型 |
| 6 | data_value | VARCHAR(100) |  | 触发值 |
| 7 | severity | VARCHAR(10) |  | 严重度 |
| 8 | status | VARCHAR(10) |  | 状态（ACTIVE/ACKNOWLEDGED/RESOLVED） |
| 9 | ack_time | TIMESTAMP |  | 确认时间 |
| 10 | ack_user | VARCHAR(20) |  | 确认人 |
| 11 | resolve_time | TIMESTAMP |  | 解决时间 |
| 12 | remark | VARCHAR(200) |  | 备注 |
| 13 | opercd | VARCHAR(6) |  | 操作人 |
| 14 | upddate | TIMESTAMP |  | 更新日期 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |


### MES (tms) — 4 张表
> 生产工单/工序

#### 1. tms01_work_order

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | wo_id | VARCHAR(20) | PK NOT NULL | 工单编号 |
| 2 | item_cd | VARCHAR(20) | NOT NULL | 产品编码 |
| 3 | plan_qty | INTEGER | NOT NULL | 计划数量 |
| 4 | actual_qty | INTEGER |  | 实际完成数量 |
| 5 | plan_start | date |  | 计划开始日期 |
| 6 | plan_end | date |  | 计划完成日期 |
| 7 | actual_start | date |  | 实际开始日期 |
| 8 | actual_end | date |  | 实际完成日期 |
| 9 | status | VARCHAR(10) |  | 状态（DRAFT/RELEASED/IN_PROGRESS/COMPLETED/CANCELLED） |
| 10 | priority | VARCHAR(10) |  | 优先级 |
| 11 | warehouse_cd | VARCHAR(20) |  | 目标仓库 |
| 12 | remark | VARCHAR(200) |  | 备注 |
| 13 | opercd | VARCHAR(6) |  | 操作人 |
| 14 | upddate | TIMESTAMP |  | 更新日期 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tms02_process_def

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | process_cd | VARCHAR(20) | PK NOT NULL | 工序编码 |
| 2 | process_nm | VARCHAR(100) | NOT NULL | 工序名称 |
| 3 | process_type | VARCHAR(10) |  | 工序类型（ASSEMBLY/TEST/PACKAGE/OTHER） |
| 4 | std_hours | NUMERIC(6,2) |  | 标准工时（小时） |
| 5 | sort_no | INTEGER |  | 排序号 |
| 6 | useflg | VARCHAR(1) |  | 有效标志 |
| 7 | remark | VARCHAR(200) |  | 备注 |
| 8 | opercd | VARCHAR(6) |  | 操作人 |
| 9 | upddate | TIMESTAMP |  | 更新日期 |
| 10 | created_at | TIMESTAMP | NOT NULL |  |
| 11 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tms03_work_process

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | wo_id | VARCHAR(20) | NOT NULL | 工单编号 |
| 3 | process_cd | VARCHAR(20) | NOT NULL | 工序编码 |
| 4 | seq_no | INTEGER | NOT NULL | 工序序号 |
| 5 | plan_qty | INTEGER |  | 计划数量 |
| 6 | actual_qty | INTEGER |  | 完成数量 |
| 7 | defect_qty | INTEGER |  | 不良品数量 |
| 8 | status | VARCHAR(10) |  | 状态（PENDING/IN_PROGRESS/COMPLETED/SKIPPED） |
| 9 | start_time | TIMESTAMP |  | 开始时间 |
| 10 | end_time | TIMESTAMP |  | 结束时间 |
| 11 | worker_cd | VARCHAR(20) |  | 操作工 |
| 12 | remark | VARCHAR(200) |  | 备注 |
| 13 | opercd | VARCHAR(6) |  | 操作人 |
| 14 | upddate | TIMESTAMP |  | 更新日期 |
| 15 | created_at | TIMESTAMP | NOT NULL |  |
| 16 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. tms04_material_consume

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | wo_id | VARCHAR(20) | NOT NULL | 工单编号 |
| 3 | process_cd | VARCHAR(20) |  | 工序编码 |
| 4 | item_cd | VARCHAR(20) | NOT NULL | 物料编码 |
| 5 | plan_qty | NUMERIC(10,2) |  | 计划用量 |
| 6 | actual_qty | NUMERIC(10,2) |  | 实际用量 |
| 7 | unit | VARCHAR(10) |  | 单位 |
| 8 | warehouse_cd | VARCHAR(20) |  | 领料仓库 |
| 9 | consume_date | date |  | 领料日期 |
| 10 | remark | VARCHAR(200) |  | 备注 |
| 11 | opercd | VARCHAR(6) |  | 操作人 |
| 12 | upddate | TIMESTAMP |  | 更新日期 |
| 13 | created_at | TIMESTAMP | NOT NULL |  |
| 14 | updated_at | TIMESTAMP | NOT NULL |  |


### 押金 (tmm61) — 5 张表
> 押金管理

#### 1. tmm61_deposit

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | custcd | VARCHAR(10) | PK NOT NULL | 客户编码 |
| 2 | amount_money | NUMERIC(12,2) |  | 押金余额 |
| 3 | updatetime | TIMESTAMP |  | 更新时间 |
| 4 | r_billid | VARCHAR(20) |  | 关联单号 |
| 5 | modelcd | VARCHAR(20) |  | 型号编码 |
| 6 | modelnm | VARCHAR(20) |  | 型号名称 |
| 7 | created_at | TIMESTAMP | NOT NULL |  |
| 8 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tmm61_deposit_dtl

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | custcd | VARCHAR(10) | NOT NULL | 客户编码 |
| 3 | c_type | VARCHAR(10) |  | 变更类型 |
| 4 | old_a | NUMERIC(12,2) |  | 原金额 |
| 5 | new_a | NUMERIC(12,2) |  | 新金额 |
| 6 | change_a | NUMERIC(12,2) |  | 变更金额 |
| 7 | updatetime | TIMESTAMP |  | 更新时间 |
| 8 | r_billid | VARCHAR(10) |  | 关联单号 |
| 9 | confirm_a | NUMERIC(12,2) |  | 确认金额 |
| 10 | useflg | VARCHAR(1) |  | 有效标志 |
| 11 | remark | VARCHAR(200) |  | 备注 |
| 12 | gendate | TIMESTAMP |  | 创建日期 |
| 13 | created_at | TIMESTAMP | NOT NULL |  |
| 14 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tmm61_deposit_io

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | custcd | VARCHAR(10) | NOT NULL | 客户编码 |
| 3 | r_billid | INTEGER |  | 关联单号 |
| 4 | new_a | NUMERIC(12,2) |  | 新金额 |
| 5 | old_a | NUMERIC(12,2) |  | 原金额 |
| 6 | change_a | NUMERIC(12,2) |  | 变更金额 |
| 7 | update_time | TIMESTAMP |  | 更新时间 |
| 8 | created_at | TIMESTAMP | NOT NULL |  |
| 9 | updated_at | TIMESTAMP | NOT NULL |  |

#### 4. tmm61_deposit_list

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL |  |
| 2 | custcd | VARCHAR(10) | NOT NULL | 客户编码 |
| 3 | billid | VARCHAR(30) |  | 单据编号 |
| 4 | updatetime | TIMESTAMP |  | 更新时间 |
| 5 | remark | VARCHAR(100) |  | 备注 |
| 6 | useflg | VARCHAR(1) |  | 有效标志 |
| 7 | c_money | NUMERIC(12,2) |  | 金额 |
| 8 | c_a | VARCHAR(150) |  | 字段A |
| 9 | c_b | VARCHAR(150) |  | 字段B |
| 10 | c_c | VARCHAR(150) |  | 字段C |
| 11 | c_d | VARCHAR(150) |  | 字段D |
| 12 | c_e | VARCHAR(150) |  | 字段E |
| 13 | c_f | VARCHAR(150) |  | 字段F |
| 14 | c_g | VARCHAR(150) |  | 字段G |
| 15 | c_h | VARCHAR(150) |  | 字段H |
| 16 | c_i | VARCHAR(150) |  | 字段I |
| 17 | c_j | VARCHAR(150) |  | 字段J |
| 18 | c_k | VARCHAR(150) |  | 字段K |
| 19 | c_l | VARCHAR(150) |  | 字段L |
| 20 | c_m | VARCHAR(150) |  | 字段M |
| 21 | c_n | VARCHAR(150) |  | 字段N |
| 22 | c_o | VARCHAR(150) |  | 字段O |
| 23 | c_p | VARCHAR(150) |  | 字段P |
| 24 | c_q | VARCHAR(150) |  | 字段Q |
| 25 | c_r | VARCHAR(150) |  | 字段R |
| 26 | c_s | VARCHAR(150) |  | 字段S |
| 27 | c_t | VARCHAR(150) |  | 字段T |
| 28 | c_u | VARCHAR(150) |  | 字段U |
| 29 | c_v | VARCHAR(150) |  | 字段V |
| 30 | c_w | VARCHAR(150) |  | 字段W |
| 31 | c_x | VARCHAR(150) |  | 字段X |
| 32 | c_y | VARCHAR(150) |  | 字段Y |
| 33 | c_z | VARCHAR(150) |  | 字段Z |
| 34 | created_at | TIMESTAMP | NOT NULL |  |
| 35 | updated_at | TIMESTAMP | NOT NULL |  |

#### 5. tmm61_deposit_posmodel

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | model_cd | VARCHAR(8) | PK NOT NULL | 型号编码 |
| 2 | model_nm | VARCHAR(20) |  | 型号名称 |
| 3 | rent_money | NUMERIC(10,2) |  | 租金 |
| 4 | sale_money | NUMERIC(10,2) |  | 售价 |
| 5 | useflg | VARCHAR(1) |  | 有效标志 |
| 6 | created_at | TIMESTAMP | NOT NULL |  |
| 7 | updated_at | TIMESTAMP | NOT NULL |  |


### 质检 (tqc) — 3 张表
> 质检结果

#### 1. tqc10_result

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | qcbillid | VARCHAR(8) | PK NOT NULL | 质检单号 |
| 2 | optyp | VARCHAR(2) |  | 操作类型 |
| 3 | refbillid | VARCHAR(8) |  | 关联单号 |
| 4 | itemcd | VARCHAR(6) |  | 物料编码 |
| 5 | eid | VARCHAR(13) |  | 设备序列号 |
| 6 | opercd | VARCHAR(6) |  | 操作员 |
| 7 | gendate | TIMESTAMP |  | 创建日期 |
| 8 | upddate | TIMESTAMP |  | 更新日期 |
| 9 | useflg | VARCHAR(1) |  | 有效标志 |
| 10 | auditman | VARCHAR(6) |  | 审核人 |
| 11 | auditflg | VARCHAR(1) |  | 审核标志 |
| 12 | auditdate | TIMESTAMP |  | 审核日期 |
| 13 | qcstatus | VARCHAR(2) |  | 质检状态 |
| 14 | created_at | TIMESTAMP | NOT NULL |  |
| 15 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tqc11_resultdt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL | 主键 |
| 2 | qcbillid | VARCHAR(8) | NOT NULL | 质检单号 |
| 3 | itemcd | VARCHAR(6) | NOT NULL | 物料编码 |
| 4 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 5 | prddate | TIMESTAMP |  | 生产日期 |
| 6 | qcqty | NUMERIC(12,0) |  | 质检数量 |
| 7 | qcstatus | VARCHAR(2) |  | 质检状态 |
| 8 | inqty | NUMERIC(12,0) |  | 入库数量 |
| 9 | opercd | VARCHAR(6) |  | 操作员 |
| 10 | gendate | TIMESTAMP |  | 创建日期 |
| 11 | useflg | VARCHAR(1) |  | 有效标志 |
| 12 | lineno | INTEGER |  | 行号 |
| 13 | fault_desc | VARCHAR(50) |  | 故障描述 |
| 14 | maintain_desc | VARCHAR(50) |  | 维修描述 |
| 15 | inspector | VARCHAR(8) |  | 检验员 |
| 16 | qc_source | VARCHAR(1) |  | 质检来源 |
| 17 | remark | VARCHAR(100) |  | 备注 |
| 18 | created_at | TIMESTAMP | NOT NULL |  |
| 19 | updated_at | TIMESTAMP | NOT NULL |  |

#### 3. tqc11_resulteid

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL | 主键 |
| 2 | qcbillid | VARCHAR(8) | NOT NULL | 质检单号 |
| 3 | itemcd | VARCHAR(6) |  | 物料编码 |
| 4 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 5 | prddate | TIMESTAMP |  | 生产日期 |
| 6 | qcqty | NUMERIC(12,0) |  | 质检数量 |
| 7 | qcstatus | VARCHAR(2) |  | 质检状态 |
| 8 | inqty | NUMERIC(12,0) |  | 入库数量 |
| 9 | eid | VARCHAR(13) | NOT NULL | 设备序列号 |
| 10 | gendate | TIMESTAMP |  | 创建日期 |
| 11 | upddate | TIMESTAMP |  | 更新日期 |
| 12 | opercd | VARCHAR(6) |  | 操作员 |
| 13 | lineno | INTEGER |  | 行号 |
| 14 | fault_desc | VARCHAR(100) |  | 故障描述 |
| 15 | maintain_desc | VARCHAR(100) |  | 维修描述 |
| 16 | inspector | VARCHAR(8) |  | 检验员 |
| 17 | qc_source | VARCHAR(1) |  | 质检来源 |
| 18 | remark | VARCHAR(100) |  | 备注 |
| 19 | manuf_seq | VARCHAR(100) |  | 制造序列号 |
| 20 | created_at | TIMESTAMP | NOT NULL |  |
| 21 | updated_at | TIMESTAMP | NOT NULL |  |


### 调拨 (ttx) — 1 张表
> 调拨科目

#### 1. ttx01_txkmg

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | txkno | VARCHAR(30) | PK NOT NULL | 调拨科目编号 |
| 2 | commmode | VARCHAR(10) |  | 通讯方式 |
| 3 | remark | VARCHAR(100) |  | 备注 |
| 4 | by1 | VARCHAR(10) |  | 备用字段1 |
| 5 | by2 | VARCHAR(10) |  | 备用字段2 |
| 6 | opercd | VARCHAR(6) |  | 操作员 |
| 7 | upddate | TIMESTAMP |  | 更新日期 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |
| 9 | created_at | TIMESTAMP | NOT NULL |  |
| 10 | updated_at | TIMESTAMP | NOT NULL |  |


### 价格 (tip) — 2 张表
> 价格规则

#### 1. tip01_price

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | itemcd | VARCHAR(6) | PK NOT NULL | 物料编码 |
| 2 | busityp | VARCHAR(6) | PK NOT NULL | 业务类型 |
| 3 | unitcd | VARCHAR(6) |  | 单位 |
| 4 | itemprice | NUMERIC(16,8) |  | 物料单价 |
| 5 | opercd | VARCHAR(6) |  | 操作员 |
| 6 | gendate | TIMESTAMP |  | 创建日期 |
| 7 | upddate | TIMESTAMP |  | 更新日期 |
| 8 | useflg | VARCHAR(1) |  | 有效标志 |
| 9 | created_at | TIMESTAMP | NOT NULL |  |
| 10 | updated_at | TIMESTAMP | NOT NULL |  |

#### 2. tip03_adjprice

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | pabillid | VARCHAR(8) | PK NOT NULL | 调价单号 |
| 2 | lineno | INTEGER | PK NOT NULL | 行号 |
| 3 | itemcd | VARCHAR(6) |  | 物料编码 |
| 4 | busityp | VARCHAR(2) |  | 业务类型 |
| 5 | oldprice | NUMERIC(16,8) |  | 原价 |
| 6 | newprice | NUMERIC(16,8) |  | 新价 |
| 7 | opercd | VARCHAR(6) |  | 操作员 |
| 8 | gendate | TIMESTAMP |  | 创建日期 |
| 9 | useflg | VARCHAR(1) |  | 有效标志（AdjustPrice） |
| 10 | created_at | TIMESTAMP | NOT NULL |  |
| 11 | updated_at | TIMESTAMP | NOT NULL |  |


### 预计划 (plan) — 1 张表
> 预计划客户

#### 1. plan_cust

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | planno | VARCHAR(10) | PK NOT NULL | 计划编号 |
| 2 | plantyp | VARCHAR(2) |  | 计划类型 |
| 3 | custnew | VARCHAR(2) |  | 新旧客户标志 |
| 4 | custcard | VARCHAR(20) |  | 客户磁卡号 |
| 5 | custcd | VARCHAR(8) |  | 客户编码 |
| 6 | custnm | VARCHAR(80) |  | 客户名称 |
| 7 | classcd | VARCHAR(6) |  | 分类编码 |
| 8 | busityp | VARCHAR(2) |  | 业务类型 |
| 9 | pptcode | VARCHAR(10) |  | 属性代码 |
| 10 | is_contract | VARCHAR(2) |  | 是否合同 |
| 11 | address | VARCHAR(80) |  | 地址 |
| 12 | contactor | VARCHAR(10) |  | 联系人 |
| 13 | phoneno | VARCHAR(60) |  | 电话 |
| 14 | custrnm | VARCHAR(80) |  | 客户真实名称 |
| 15 | jl_contactor | VARCHAR(10) |  | 经理联系人 |
| 16 | jl_phoneno | VARCHAR(60) |  | 经理电话 |
| 17 | pos_from | VARCHAR(6) |  | POS来源 |
| 18 | pos_item | VARCHAR(6) |  | POS物料 |
| 19 | posid | VARCHAR(13) |  | POS设备ID |
| 20 | new_custcard | VARCHAR(20) |  | 新磁卡号 |
| 21 | new_custcd | VARCHAR(8) |  | 新客户编码 |
| 22 | new_phoneno | VARCHAR(60) |  | 新电话 |
| 23 | new_address | VARCHAR(80) |  | 新地址 |
| 24 | new_custnm | VARCHAR(80) |  | 新客户名称 |
| 25 | new_positem | VARCHAR(6) |  | 新POS物料 |
| 26 | new_posid | VARCHAR(13) |  | 新POS设备ID |
| 27 | solve_type | VARCHAR(2) |  | 处理方式 |
| 28 | back_status | VARCHAR(2) |  | 回退状态 |
| 29 | cust_useflg | VARCHAR(2) |  | 客户有效标志 |
| 30 | plan_status | VARCHAR(2) |  | 计划状态 |
| 31 | servetyp | VARCHAR(2) |  | 服务类型 |
| 32 | pl_serve_task | VARCHAR(200) |  | 服务任务 |
| 33 | imple_status | VARCHAR(2) |  | 实施状态 |
| 34 | commmode | VARCHAR(4) |  | 通讯方式 |
| 35 | serve_status | VARCHAR(2) |  | 服务状态 |
| 36 | plan_require | VARCHAR(200) |  | 计划需求 |
| 37 | imple_date | TIMESTAMP |  | 实施日期 |
| 38 | send_date | TIMESTAMP |  | 发送日期 |
| 39 | train_date | TIMESTAMP |  | 培训日期 |
| 40 | imple_mark | VARCHAR(200) |  | 实施备注 |
| 41 | imple_result | VARCHAR(10) |  | 实施结果 |
| 42 | fail_reason | VARCHAR(200) |  | 失败原因 |
| 43 | is_outflag | VARCHAR(2) |  | 出库标志 |
| 44 | status | VARCHAR(2) |  | 状态 |
| 45 | gendate | TIMESTAMP |  | 创建日期 |
| 46 | opercd | VARCHAR(6) |  | 操作员 |
| 47 | propo_item | VARCHAR(20) |  | 推荐物料 |
| 48 | serve_ercd | VARCHAR(6) |  | 服务工程师 |
| 49 | deposit | NUMERIC(12,2) |  | 押金金额 |
| 50 | is_rent | VARCHAR(1) |  | 是否租赁 |
| 51 | yun_type | VARCHAR(2) |  | 运营类型 |
| 52 | upload_type | VARCHAR(2) |  | 上传类型 |
| 53 | created_at | TIMESTAMP | NOT NULL |  |
| 54 | updated_at | TIMESTAMP | NOT NULL |  |


### 采购验收 (tmp) — 1 张表
> 采购验收明细

#### 1. tmp14_checkindt

| # | 列名 | 类型 | 约束 | 说明 |
|---|------|------|------|------|
| 1 | id | INTEGER | PK NOT NULL | 主键 |
| 2 | inbillid | VARCHAR(8) |  | 入库单号 |
| 3 | whcd | VARCHAR(2) |  | 仓库编码 |
| 4 | lineno | INTEGER |  | 行号 |
| 5 | itemtyp | VARCHAR(2) |  | 物料类型 |
| 6 | itemcd | VARCHAR(6) |  | 物料编码 |
| 7 | prddate | TIMESTAMP |  | 生产日期 |
| 8 | batchid | VARCHAR(50) |  | 批次号 |
| 9 | inqty | NUMERIC(12,0) |  | 入库数量 |
| 10 | reflineno | INTEGER |  | 关联行号 |
| 11 | created_at | TIMESTAMP | NOT NULL |  |
| 12 | updated_at | TIMESTAMP | NOT NULL |  |


---

## C. 关系图谱

> 🔗 详见：`数据库ER关系文档.md` §二（域模型分类 + ER 关联）和 §三（跨域关键关联）

---

## D. 附录

### D.1 索引清单

> 🟢 自动生成

| 表 | 索引名 | 列 |
|-----|--------|-----|
| tfn05_depreciation | tfn05_depreciation_eid_key | eid |
| tio01_device_conn | tio01_device_conn_eid_key | eid |
| tit02_liabilityregdt | uq_liabilityregdt | lbdt_cd, liab_cd |
| tit05_repairinfo | uq_repairinfo | rep_type, obj_cd |
| tit06_userarea | uq_userarea | area_id, user_cd |
| tit17_maintenance_plan | uq_maintenance_plan | plan_y, plan_yymm, area_id |
| tmc21_usergroup | uq_usergroup | user_cd, group_cd |
| tmm22_customers | tmm22_customers_cust_card_key | cust_card |
| tmm31_syscodes | uq_syscode | code_typ, code_cd |
| tmm35_cust_pos_rl | idx_cust_pos_rl_eid_useflg | eid, useflg |
| tmm43_eid_track | idx_eid_track_eid_itemcd | eid, itemcd |
| tmm43_eid_track | idx_eid_track_type_eid | type, eid |
| tmm44_pos_r_eid | idx_pos_r_eid_eid | eid |
| tmm44_pos_r_eid | idx_pos_r_eid_useflg | useflg, eid |
| tpt01_portal_user | tpt01_portal_user_login_name_key | login_name |

### D.2 业务模块前缀速查

> 🟡 手动维护

| 前缀 | 模块 | 说明 |
|------|------|------|
| `tmc%` | 系统管理 (tmc) | 用户/部门/菜单/权限/参数 |
| `tmm%` | 主数据 (tmm) | 客户/物料/设备/供应商/区域（不含押金） |
| `tit%` | ITSM 核心 (tit) | 维护/翻新/开通/归档/变更 |
| `twh%` | 仓储 (twh) | 入库/出库/库存/调拨 |
| `tpc%` | 采购 (tpc) | 采购计划/订单 |
| `tsl%` | 销售 (tsl) | 销售/延期 |
| `tfn%` | 财务 (tfn) | 账务/支付 |
| `tac%` | 财务 (tac/tht) | 合同/发票 |
| `tkq%` | 考勤 (tkq) | 考勤 |
| `tiv%` | 库存预警 (tiv) | 预警规则/库存明细 |
| `tbl%` | 结算 (tbl) | 结算规则/账单 |
| `tntf%` | 通知 (tntf) | 通知模板/记录 |
| `sla%` | SLA (sla) | 服务级别 |
| `tpt%` | 门户 (tpt) | 自助报修/评价 |
| `tio%` | IoT (tio) | 设备接入/监控 |
| `tms%` | MES (tms) | 生产工单/工序 |
| `tmm61%` | 押金 (tmm61) | 押金管理 |
| `tqc%` | 质检 (tqc) | 质检结果 |
| `ttx%` | 调拨 (ttx) | 调拨科目 |
| `tip%` | 价格 (tip) | 价格规则 |
| `plan%` | 预计划 (plan) | 预计划客户 |
| `tmp%` | 采购验收 (tmp) | 采购验收明细 |

