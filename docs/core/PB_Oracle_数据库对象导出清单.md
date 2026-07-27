# PB Oracle 数据库对象导出清单

> 创建日期：2026-07-11
> 状态：✅ 定稿（作为 PB→Python 重构的数据库侧权威参考）

---

## 1. 背景与目的

PB 源码（`PBsrc/*.pbl`）中调用的**存储过程、函数、视图、序列、索引、触发器、包、类型**等数据库对象定义存储在 Oracle 数据库内部，不在 PB 源码中。分析 PB 业务功能时，必须结合这些数据库对象源码才能还原完整业务逻辑。

本文档记录从 PB 原 Oracle 数据库（`CCGL_TEST`）全量导出的数据库对象清单与存放位置，供 PB→Python 重构时作为权威参考。

---

## 2. 数据库连接信息

| 项 | 值 |
|----|-----|
| 连接串 | `ccgl/ccgl@CCGL_TEST` |
| 数据库版本 | Oracle Database 12c Enterprise Edition Release 12.1.0.1.0 - 64bit |
| Schema | `CCGL` |
| 导出工具 | `sqlplus` + `ALL_SOURCE` / `DBMS_METADATA.GET_DDL` |
| 字符集 | 源库 GBK，查询输出需 `iconv -f GBK -t UTF-8` 转码 |

> ⚠️ **安全提示**：连接串含明文密码，仅用于本地 PB 源码分析。重构代码中禁止硬编码，统一通过环境变量 `DATABASE_URL` 连接 PostgreSQL。

### 2.1 实时查询 PB Oracle 数据库

当 `PBsrc/pb_oracle_*/` 下的静态导出文件不足以满足分析需求（如需查看对象最新状态、跨对象搜索、动态统计等）时，可使用 `sqlplus` 实时查询 PB 原 Oracle 库。

**连接命令**：

```bash
sqlplus ccgl/ccgl@CCGL_TEST
```

**常用查询模板**：

```bash
# 1. 查看存储过程/函数/包/触发器/类型源码
sqlplus -L ccgl/ccgl@CCGL_TEST <<'EOF'
SET PAGESIZE 0 LINESIZE 4000 LONG 2000000 LONGCHUNKSIZE 2000000
SET FEEDBACK OFF HEADING OFF
SELECT TEXT FROM ALL_SOURCE
 WHERE OWNER='CCGL' AND NAME='<对象名>' AND TYPE='<PROCEDURE|FUNCTION|PACKAGE|TRIGGER|TYPE>'
 ORDER BY LINE;
EXIT;
EOF

# 2. 查看视图定义
sqlplus -L ccgl/ccgl@CCGL_TEST <<'EOF'
SET PAGESIZE 0 LINESIZE 4000 LONG 2000000 FEEDBACK OFF HEADING OFF
SELECT TEXT FROM ALL_VIEWS WHERE OWNER='CCGL' AND VIEW_NAME='<视图名>';
EXIT;
EOF

# 3. 查看序列/索引/表 DDL
sqlplus -L ccgl/ccgl@CCGL_TEST <<'EOF'
SET PAGESIZE 0 LINESIZE 4000 LONG 2000000 FEEDBACK OFF HEADING OFF
SELECT DBMS_METADATA.GET_DDL('<SEQUENCE|INDEX|TABLE>','<对象名>','CCGL') FROM DUAL;
EXIT;
EOF

# 4. 全库搜索涉及某表的数据库对象
sqlplus -L ccgl/ccgl@CCGL_TEST <<'EOF'
SET PAGESIZE 0 LINESIZE 200 FEEDBACK OFF HEADING ON
SELECT DISTINCT NAME, TYPE FROM ALL_SOURCE
 WHERE OWNER='CCGL' AND UPPER(TEXT) LIKE '%<表名>%'
 ORDER BY NAME;
EXIT;
EOF

# 5. 导出单个对象源码到文件（GBK→UTF-8）
sqlplus -L ccgl/ccgl@CCGL_TEST <<'EOF' | iconv -f GBK -t UTF-8 > <对象名>.sql
SET PAGESIZE 0 LINESIZE 4000 LONG 2000000 FEEDBACK OFF HEADING OFF
SELECT TEXT FROM ALL_SOURCE WHERE OWNER='CCGL' AND NAME='<对象名>' AND TYPE='PROCEDURE' ORDER BY LINE;
EXIT;
EOF
```

**注意事项**：

- `sqlplus` 输出默认 GBK 编码，重定向到文件后需 `iconv -f GBK -t UTF-8` 转码才能正确显示中文注释
- 使用 `SET LONG 2000000 LONGCHUNKSIZE 2000000` 避免大对象被截断
- 使用 `SET PAGESIZE 0` 关闭分页，`SET HEADING OFF` 去除列标题
- `-L` 参数表示连接失败后不重试，避免卡在交互式提示
- 查询 `ALL_SOURCE` 需指定 `OWNER='CCGL'` 过滤当前 schema
- 如需重新全量导出，参考 `/tmp/pb_oracle_export.sh` 脚本模板

### 2.2 TNS 配置与网络要求

`CCGL_TEST` 是 TNS 别名，定义在 Oracle Instant Client 的 `tnsnames.ora` 文件中。

**环境变量配置**（`~/.zshrc`）：

```bash
export ORACLE_HOME=/Users/cheungjan/Downloads/instantclient_23_26
export TNS_ADMIN=$ORACLE_HOME/network/admin
export DYLD_LIBRARY_PATH=$ORACLE_HOME
export PATH=$ORACLE_HOME:$PATH
```

**TNS 别名定义**（`$TNS_ADMIN/tnsnames.ora`）：

```
CCGL_TEST =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = DESKTOP-CKUSCUU)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = CCGLPDB)
    )
  )
```

| 项 | 值 | 说明 |
|----|-----|------|
| TNS 别名 | `CCGL_TEST` | `sqlplus ccgl/ccgl@CCGL_TEST` 使用的连接名 |
| HOST | `DESKTOP-CKUSCUU` | PB Oracle 数据库所在主机（Windows 主机名，通常为 Parallels 虚拟机或局域网服务器） |
| PORT | `1521` | Oracle 默认端口 |
| SERVICE_NAME | `CCGLPDB` | 实际 Oracle 服务名（PDB 名） |
| SERVER | `DEDICATED` | 专用服务器模式 |

**连接链路**：

```
sqlplus ccgl/ccgl@CCGL_TEST
    ↓
$TNS_ADMIN/tnsnames.ora  →  解析 CCGL_TEST
    ↓
TCP DESKTOP-CKUSCUU:1521  →  SERVICE_NAME=CCGLPDB
    ↓
登录 Schema: CCGL
```

**网络可达性要求**：

- PB Oracle 库**不在本机**，必须通过主机名 `DESKTOP-CKUSCUU` 访问（直接用 `localhost:1521/CCGLPDB` 会报 `ORA-12547: TNS:lost contact`）
- 若切换网络或 VPN 后连不上，检查 `DESKTOP-CKUSCUU` 主机名是否可达：`ping DESKTOP-CKUSCUU`
- `sqlnet.ora` 中 `TCP.CONNECT_TIMEOUT=10` 限制连接超时 10 秒，网络不稳定时可能需要调整
- 注：`sqlnet.ora` 注释提到"强制绑定真实网卡 IP，避免 Clash Verge TUN 虚拟网卡拦截"——若使用 Clash Verge 等 TUN 模式代理，可能需要关闭或配置绕行规则

---

## 3. 导出目录结构

所有导出文件存放在 `PBsrc/pb_oracle_<对象类型>/` 下，每个对象一个 `.sql` 文件，文件名为对象名。

```
PBsrc/
├── pb_oracle_PROCEDURE/       # 存储过程 (49 个)
├── pb_oracle_FUNCTION/        # 自定义函数 (22 个)
├── pb_oracle_PACKAGE/         # 包规范 (1 个)
├── pb_oracle_PACKAGE_BODY/    # 包体 (1 个)
├── pb_oracle_TRIGGER/         # 触发器 (12 个)
├── pb_oracle_TYPE/            # 类型规范 (3 个)
├── pb_oracle_TYPE_BODY/       # 类型体 (2 个)
├── pb_oracle_VIEW/            # 视图 (21 个)
├── pb_oracle_SEQUENCE/        # 序列 (15 个)
└── pb_oracle_INDEX/           # 索引 DDL (160 个)
```

**统计汇总**：共 286 个文件，总大小约 1.6 MB。

---

## 4. 关键存储过程清单（重构高频参考）

### 4.1 预计划实施与确认

| 存储过程 | 作用 | 重构对应 |
|---------|------|----------|
| `USP_PLAN_IMPLE` | 预计划实施确认，按 `i_type` 生成下游 ITSM 单据（00→TIT13, 10→TIT16, 20→TIT15, 30→TIT10, 40→TIT18） | `sales_service.py::implement` + `_build_downstream_payload` |
| `USP_PLAN_CONFRIM` | 预计划确认，处理客户主表 + 客户设备关系变更 | `sales_service.py::confirm`（待补齐） |
| `USP_PLANSTATUS` | 预计划状态流转 | `sales_service.py` 状态机 |
| `USP_PLAN_RP` / `USP_PLAN_RP_ALL` | 预计划报表 | 报表模块 |

### 4.2 ITSM 单据流转

| 存储过程 | 作用 | 重构对应 |
|---------|------|----------|
| `USP_ITSM_TRANS_IN` | ITSM 单据数据接收，写中间表 `sm_in_open_result` / `sm_in_part_change` | `itsm_service.py`（待补齐） |
| `USP_TRANS_IN_CONFRIM` | 数据接收确认，回写 `plan_cust.status` | `itsm_service.py`（待补齐） |
| `USP_TRANS_IN` / `USP_TRANS_IN_BILLALL` / `USP_TRANS_IN_UPDATE` | 数据接收相关 | 待分析 |
| `USP_TRANS_OUT` / `USP_TRANS_OUT_NEW` | 数据发送相关 | 待分析 |
| `USP_TRANS_ITSM_CONFRIM` / `USP_TRANS_UNIT_CONFRIM` | ITSM/单位确认 | 待分析 |
| `USP_ITSM_EXTEND_NEW` | 销售扩展 `tsl01_extend` 审核生成 ITSM 单据 | 重构未实现（缺失功能） |
| `USP_ITSM_ARCHIVE` | ITSM 单据归档 | 待分析 |
| `USP_ITSM_WHD_AUTO` | ITSM WHD 自动处理 | 待分析 |

### 4.3 仓储与出入库

| 存储过程 | 作用 | 重构对应 |
|---------|------|----------|
| `USP_WH` | 仓储通用处理 | `warehouse_service.py` |
| `USP_WH_IN` | 入库（`is_invtyp` 区分类型） | `StockInService` |
| `USP_WH_OUT` | 出库（`is_invtyp` 区分类型） | `StockOutService` |
| `USP_WH_OUT_ALLOCATE_FIX` | 出库调拨修正 | 待分析 |
| `USP_WH_CHANGEL1POS` | L1 POS 变更 | 待分析 |

### 4.4 其他业务

| 存储过程 | 作用 | 重构对应 |
|---------|------|----------|
| `USP_ADJPRICE` | 价格调整 | `price_service.py` |
| `USP_ASSET_C_A` | 资产 C→A 转换 | 待分析 |
| `USP_CHECK` | 校验 | 待分析 |
| `USP_CREATE_CONTRACT_MONTH` | 合同月度生成 | `contract_service.py` |
| `USP_CREATE_ITSM_REPORT` | ITSM 报表生成 | 报表模块 |
| `USP_CREATE_PCPLAN` | PC 计划生成 | 待分析 |
| `USP_C_HS_POS` / `USP_C_TMM22` / `USP_C_TMM44` / `USP_C_TMM44_CHANGE` / `USP_C_TMM44_CHANGE_POS` / `USP_C_TSL` | 各类数据维护 | 待分析 |
| `USP_INSERT_TRANITEM` | 事务项插入 | 待分析 |
| `USP_OVERLOST_AUDIT` | 超损审核 | 待分析 |
| `USP_QCSTATUS` | 质检状态流转 | `qc_service.py` |
| `USP_SESSIONMANAGER` | 会话管理 | 已由 JWT 替代 |
| `USP_TSL10_STATUS` | 销售 TSL10 状态流转 | `sales_service.py` |
| `SP_ITSM_DATAMOVE` | ITSM 数据迁移（外部表→TIT10，**唯一写 `IS_OLD='Y'` 的入口**） | 数据迁移脚本 |
| `SP_KQ_IMPA` / `SP_KQ_STATISTIC` | 考勤统计 | `attendance_service.py` |
| `SP_REPORT_TEST` / `USP_TEST` | 测试存储过程 | 忽略 |
| `UP_GETDATA` / `UP_GETITEMNM` | 数据/物料名获取 | 待分析 |
| `USP_CASE_ITEM_V_TABLE` / `USP_CASE_STEP_V_TABLE` | 案例项/步骤表 | 待分析 |

---

## 5. 关键函数清单

| 函数 | 作用 | 重构对应 |
|------|------|----------|
| `UF_GET_BILLNOU` | **单号生成**（按类型前缀，如 MO/BG/GB/MR/MD/RC） | `IdMaster.generate_id` |
| `UF_GET_BUSINESSID` | 业务 ID 生成 | 待分析 |
| `UF_INSERT_BUSINESS` / `UF_UPDATE_BUSINESS` | 业务表插入/更新 | 待分析 |
| `UF_INSERT_POSITEM` / `UF_INSERT_POSUNIT` / `UF_INSERT_TRANITEM` | POS 物料/单位/事务项插入 | 待分析 |
| `UF_UPDATE_CUST` | 客户主表更新 | `customer_service.py` |
| `UF_GETPRICE` | 价格获取 | `price_service.py` |
| `UF_CHECKPERIOD` / `UF_CHECKPERIOD_MEMO` | 质保期校验 | 待分析 |
| `UF_ITSM_CHECKPERIOD` / `UF_ITSM_CHECKPERIOD_MEMO` | ITSM 质保期校验 | 待分析 |
| `UF_GETPLAN_F_TIME` / `UF_GETPLAN_LAST_SRVBACK` / `UF_GETPLAN_LAST_TIT` | 预计划时间查询 | 待分析 |
| `UF_STOREPOSINFO` / `UF_STOREPOSINFO_QJ` | 门店 POS 信息 | 待分析 |
| `UF_SM_PART_ERRINFO` | 配件错误信息 | 待分析 |
| `UF_WH_HISTORYKC` | 仓储历史库存 | 待分析 |
| `GETFIRSTPY` | 首字母拼音 | 待分析 |
| `WM_CONCAT` | 聚合拼接（Oracle 内置兼容） | PostgreSQL `string_agg` 替代 |

---

## 6. 视图清单（21 个）

| 视图 | 作用 |
|------|------|
| `PLAN_BIZ_V` | 预计划业务视图 |
| `TIT01_TIMEPOINT_CUST` | 时间点客户视图 |
| `TMM43_WHCD_ITEMTYP_V` | EID 仓储物料类型视图 |
| `V_BILLID_TYPE` | 单据 ID 类型视图 |
| `V_CHECK_SUM_ITSM` | ITSM 校验汇总 |
| `V_CUST_20141204` | 客户快照（2014-12-04） |
| `V_CUST_MAINTENANCE_LAST` | 客户最近维护记录 |
| `V_GETDATA` | 通用数据视图 |
| `V_IN_REFBILL_EID` | 入库关联单据 EID |
| `V_ITSMALLBILL` | ITSM 全部单据 |
| `V_ITSM_BILLALL` | ITSM 全部单据（别名） |
| `V_ITSM_MD_SUM` | ITSM 维护单汇总 |
| `V_ITSM_PAPER_AVERAGEL_DB` | ITSM 单据平均 DB |
| `V_OPBIZ_ACCOUNT` | 运营业务核算 |
| `V_OUT_LIST` | 出库清单 |
| `V_QC_USER` | 质检用户 |
| `V_SM_IN` / `V_SM_IN_ERROR` | 数据接收/错误 |
| `V_TIT_SATUS` | ITSM 单据状态 |
| `V_TWH_TMM43_ERR` | TWH/TMM43 异常 |
| `WHCD_ITEM_V` | 仓储物料视图 |

---

## 7. 触发器清单（12 个）

| 触发器 | 作用 |
|--------|------|
| `TRIG_D_TMM43_TRACK` | TMM43 删除追踪 |
| `TRIG_D_TPC03` | TPC03 删除触发 |
| `TRIG_I_TMM43_TRACK` | TMM43 插入追踪 |
| `TRIG_I_TPC03` | TPC03 插入触发 |
| `TRIG_N_TMM22_CONTRACT` | TMM22 合同新增 |
| `TRIG_U_PLAN_STATUS` | 预计划状态更新 |
| `TRIG_U_SM_OPEN_STATUS` | 数据接收开通状态更新 |
| `TRIG_U_SM_PART_STATUS` | 数据接收配件状态更新 |
| `TRIG_U_TMM22_CONTRACT` | TMM22 合同更新 |
| `TRIG_U_TMM43_TRACK` | TMM43 更新追踪 |
| `TRIG_U_TPC03` | TPC03 更新触发 |
| `T_TMM22_CUSTOMERS` | TMM22 客户触发 |

> ⚠️ 重构版使用 SQLAlchemy 应用层逻辑替代触发器，触发器源码仅用于业务逻辑还原参考。

---

## 8. 序列清单（15 个）

| 序列 | 作用 |
|------|------|
| `SM_OPEN_SEQNO` | 数据接收开通序列 |
| `SM_PART_SEQNO` | 数据接收配件序列 |
| `SEQ_MIG_BY_IMPORT_STG` | 迁移导入序列 |
| 其余 12 个 | 待逐一标注 |

> 重构版 PostgreSQL 使用 `IdMaster` 表 + 应用层生成，序列 DDL 仅用于号段参考。

---

## 9. 索引清单（160 个）

索引 DDL 通过 `DBMS_METADATA.GET_DDL('INDEX', ...)` 导出，存放于 `pb_oracle_INDEX/`。

重构版 PostgreSQL 索引在 Alembic 迁移脚本中定义，参考 PB 索引清单确保查询性能对齐。

---

## 10. 使用方法

### 10.1 查找存储过程源码

```bash
# 直接查看文件
cat PBsrc/pb_oracle_PROCEDURE/USP_PLAN_IMPLE.sql

# 搜索涉及某表的存储过程
grep -rl "TIT13_MAINTENANCE_OPEN" PBsrc/pb_oracle_*/
```

### 10.2 分析 PB 功能时的交叉验证流程

1. **PB 源码**：`PBsrc/<module>.pbl/*.sru`（用户对象/窗口逻辑）
2. **Oracle 对象**：`PBsrc/pb_oracle_*/<对象名>.sql`（存储过程/函数/触发器/视图）
3. **重构代码**：`app/services/*.py` + `app/repositories/*.py`
4. **数据库实际数据**：PostgreSQL `myitsm` 库

四份证据交叉验证，确保重构逻辑与 PB 原版一致。

---

## 11. 导出脚本

导出脚本存放在 `/tmp/pb_oracle_export.sh`（临时文件，如需重新导出请联系管理员）。

核心逻辑：
- 源码类对象（PROCEDURE/FUNCTION/PACKAGE/TRIGGER/TYPE）：查询 `ALL_SOURCE.TEXT`
- 视图：查询 `ALL_VIEWS.TEXT`
- 序列/索引：调用 `DBMS_METADATA.GET_DDL`
- 导出后统一 `iconv -f GBK -t UTF-8` 转码

---

## 12. 维护说明

- 本导出为 **2026-07-11 快照**，PB Oracle 库后续变更不会自动同步
- 如 PB 库结构变更，需重新导出并更新本清单
- 导出文件已纳入 Git 版本管理，位于 `PBsrc/pb_oracle_*/` 下

---

## 变更记录

| 日期 | 变更内容 | 作者 |
|------|---------|------|
| 2026-07-11 | 初始导出：10 类对象共 286 个文件，含 PROCEDURE/FUNCTION/PACKAGE/TRIGGER/TYPE/VIEW/SEQUENCE/INDEX | Cascade |
