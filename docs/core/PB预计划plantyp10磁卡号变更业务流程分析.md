# PB 预计划 plantyp=10 磁卡号变更业务流程分析

> 基于 PB 源码 + Oracle 存储过程源码 + 数据库实际数据三方交叉验证
> 创建日期：2026-07-02
> 状态：✅ 定稿（可作为重构对齐基线）

---

## 1. 背景与问题

### 1.1 问题起源

重构 `SalesPlanService._build_downstream_payload` 时，需要判定 `plantyp=10`（磁卡号变更）的子类型 BG/CK/BQ。初期假设：

- 有设备变更 → `CHANGE_TYPE='BG'`
- 仅磁卡号变 → `CHANGE_TYPE='CK'`
- 信息变更 → `CHANGE_TYPE='BQ'`

但数据库实际数据观察发现：**PL 开头的 TIT16_DEVICE_CHANGE 几乎全是 CK（228/231），BG 只有 3 条，BQ 为 0**。由此引发疑问：

1. BG/CK/BQ 是 PB 老版本业务代码吗？
2. PB 正在使用的磁卡号变更是预计划管理 new 模块对应的 `plantyp=10` 吗？
3. 目前版本是否还在使用三种不同子类型？

### 1.2 分析方法

- **PB 源码**：`PBsrc/` 下 `.sru`（用户对象）、`.srd`（数据窗口）
- **Oracle 存储过程源码**：`USP_PLAN_IMPLE`、`USP_PLAN_CONFRIM`、`USP_ITSM_TRANS_IN`、`USP_TRANS_IN_CONFRIM`
- **数据库实际数据**：PostgreSQL myitsm 库 `tit16_device_change` 表分布统计
- **项目文档**：`docs/core/` 下已有设计文档交叉印证

---

## 2. 核心结论

### 2.1 关键概念辨析：三个容易混淆的 "BG"

在分析 PB 业务流程时，存在三个都叫 "BG" 但含义完全不同的概念，这是造成误解的根源：

| 概念 | 位置 | 含义 | 来源 |
|------|------|------|------|
| **单据号前缀 BG** | `TIT16_DEVICE_CHANGE.DEVICE_CHANGE_ID` | 变更单号的前缀（如 BG20230001） | `USP_PLAN_IMPLE` 调用 `UF_GET_BILLNOU('BG')` 生成 |
| **单据类型标识 BG** | `u_itsm_device_change.is_billtype='BG'` | PB 代码中的单据类型常量，用于查询附表/调用存储过程 | 老版本 ITSM 沿用 |
| **CHANGE_TYPE 字段 BG** | `TIT16_DEVICE_CHANGE.CHANGE_TYPE` | 变更类型字段值 | 老版本 ITSM 直接创建时写入 |

**关键事实**：
- **当前版本所有新变更单的 `DEVICE_CHANGE_ID` 前缀都是 BG**（来自 `UF_GET_BILLNOU('BG')`），这是单据号生成规则，与 `CHANGE_TYPE` 无关
- **当前版本所有新变更单的 `CHANGE_TYPE` 都是 CK**（`USP_PLAN_IMPLE` 硬编码），无论是否包含设备转移
- **`u_itsm_device_change.is_billtype='BG'`** 是 PB 代码中的单据类型标识常量，用于查询附表（D2D/RV/PAY）和调用 `usp_itsm_trans_in`，**不是创建功能**

### 2.2 三种子类型的真实来源（修正版）

| 子类型 | 真实来源 | 生成入口 | CHANGE_TYPE 字段位置 | 业务语义 | 当前版本状态 |
|--------|---------|---------|---------------------|---------|------------|
| **CK** | 预计划 plantyp=10 | `USP_PLAN_IMPLE` 硬编码 `'CK'` | `TIT16_DEVICE_CHANGE.CHANGE_TYPE` | 磁卡号变更（含设备转移） | ✅ 在用 |
| **BG** | **老版本** ITSM 直接创建 | 老版本 `u_itsm_device_change` 新建功能（已废弃） | `TIT16_DEVICE_CHANGE.CHANGE_TYPE` | 设备变更单（独立业务） | ❌ 老版本遗留数据 |
| **BQ** | 销售扩展 tsl01_extend | `usp_trans_in_confrim v_tftype='BQ'` | **不在 TIT16_DEVICE_CHANGE** | 门店搬迁（走 tsl01_extend） | 老版本/独立流程 |

### 2.3 关键发现

1. **当前版本 `u_itsm_device_change` 模块没有"新建变更单"功能**——PB 源码搜索确认：没有任何 `.sru` 文件直接 INSERT 到 `TIT16_DEVICE_CHANGE`，所有插入都通过 `USP_PLAN_IMPLE` 存储过程完成
2. **当前版本所有新变更单都由预计划 plantyp=10 创建**——`USP_PLAN_IMPLE` 是唯一的创建入口，硬编码 `CHANGE_TYPE='CK'`，单据号前缀 BG（`UF_GET_BILLNOU('BG')`）
3. **BG 前缀是老版本 ITSM 单据号的延续**——`is_billtype='BG'` 和 `UF_GET_BILLNOU('BG')` 都是老版本 ITSM 模块沿用的单据类型标识，当前版本仅用于查询附表和调用存储过程，不再用于创建
4. **OP 前缀的 REQUSET_PAPER_ID 记录是老版本遗留数据**——295 条 OP+BG、167 条 OP+BQ、4 条 OP+CK 都是老版本 ITSM 直接创建的历史数据，当前版本不再产生此类记录
5. **USP_PLAN_CONFRIM v_tftype='10' 内部按 `V_NEW_POSID` 隐式区分**设备转移语义——即使 CHANGE_TYPE='CK'，只要有 `V_NEW_POSID` 就会执行设备转移逻辑（旧设备 useflg='0', MAINTENANCETYP='BG'）

### 2.4 数据库数据印证

```
TIT16_DEVICE_CHANGE 完整分布（按 单据号前缀 + 关联单号前缀 + CHANGE_TYPE）：
┌──────────────┬──────────────────┬─────────────┬─────┐
│ 单据号前缀   │ REQUSET_PAPER_ID │ CHANGE_TYPE │ cnt │
├──────────────┼──────────────────┼─────────────┼─────┤
│ BG           │ OP（老版本ITSM） │ BG          │ 295 │ ← 老版本遗留
│ BG           │ OP（老版本ITSM） │ BQ          │ 167 │ ← 老版本遗留
│ BG           │ OP（老版本ITSM） │ CK          │   4 │ ← 老版本遗留
│ BG           │ PL（预计划）     │ BG          │   3 │ ← 异常数据
│ BG           │ PL（预计划）     │ CK          │ 228 │ ← 当前版本正常数据
└──────────────┴──────────────────┴─────────────┴─────┘
```

**关键观察**：
- **单据号前缀全部是 BG**（`UF_GET_BILLNOU('BG')` 生成），与 CHANGE_TYPE 无关
- **PL+CK（228 条）是当前版本预计划 plantyp=10 的正常数据**，占预计划入口的 98.7%（228/231）
- **PL+BG（3 条）是异常数据**，其中 1 条关联 plantyp=00（PL000037），2 条为测试/误操作
- **OP 前缀（466 条）全部是老版本 ITSM 直接创建的遗留数据**，当前版本不再产生
- **当前版本不再产生 CHANGE_TYPE='BG' 或 'BQ' 的新记录**

---

## 3. PB 一条龙完整业务流程（plantyp=10）

### 3.1 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│ 阶段1：预计划创建                                                │
│ plan_cust.plantyp='10', status='00'                             │
│ 填写：CUSTCARD(新磁卡号), NEW_CUSTCD, NEW_POSID, NEW_ADDRESS... │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段2：计划确认（u_plan_befor_new.oe_dobutton1）                 │
│ status 00→02（实施中）                                          │
│ 客户生命周期：TEMP → PENDING                                     │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段3：实施确认（u_plan_imple.oe_dobutton1）                     │
│ 调用 USP_PLAN_IMPLE(i_planno, '10', i_oper, o_return)           │
│                                                                 │
│ USP_PLAN_IMPLE 内部：                                           │
│   v_id := UF_GET_BILLNOU('BG')  -- 单号前缀 BG                  │
│   v_mchange.CHANGE_TYPE := 'CK'  -- ★硬编码 CK                  │
│   v_mchange.DEVICE_ID := V_PLAN.POSID                           │
│   v_mchange.NEW_STORE_CARD := V_PLAN.CUSTCARD                   │
│   insert into TIT16_DEVICE_CHANGE                               │
│                                                                 │
│ 结果：生成 TIT16_DEVICE_CHANGE 记录，CHANGE_TYPE='CK'           │
│ plan_cust.status 02→04（分派中/实施中）                         │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段4：变更单实施（工程师上门服务）                              │
│ TIT23_MAINTENANCE_D2D 上门记录                                  │
│ TIT16_DEVICE_CHANGE.CURRENT_STATUS 1→3（关单）                  │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段5：变更单关单（u_itsm_device_change 关单按钮）               │
│ of_update_plan()：                                              │
│   update PLAN_CUST set imple_Result, status='03'                │
│   where planno = :ls_planno  -- ★直接回写 plan_cust.status=03  │
│                                                                 │
│ DECLARE MYPROC FOR usp_itsm_trans_in(:is_mid, 0, 'BG')          │
│ USP_ITSM_TRANS_IN 内部（i_type='BG'）：                         │
│   insert into tmp_sm_in_open_result                             │
│     select ... from TIT16_DEVICE_CHANGE m, tmm22_customers c    │
│     where m.DEVICE_CHANGE_ID = i_master_id                      │
│   insert into sm_in_open_result  -- ★写入"数据接收"中间表       │
│                                                                 │
│ plan_cust.status 04→03（实施完成）                              │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段6：数据接收(业务反馈)确认（u_trans_in_ed1）                  │
│ 调用 USP_TRANS_IN_CONFRIM('1', id, userid, as_return)           │
│                                                                 │
│ USP_TRANS_IN_CONFRIM v_type='1'：                               │
│   从 sm_in_open_result 取 v_tfid(PL号), v_mid(变更单号)         │
│   if substr(v_tfid,1,2)='PL' then                               │
│     select PLANTYP into v_tftype from plan_cust                 │
│   end if                                                        │
│                                                                 │
│   if v_tftype='10' then  -- ★磁卡号变更分支                    │
│     usp_plan_confrim(as_type, as_id, as_userid, as_return)      │
│   end if                                                        │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段7：USP_PLAN_CONFRIM v_tftype='10'（磁卡号变更业务处理）     │
│                                                                 │
│   select STORE_ID into v_custcd                                 │
│     from TIT16_DEVICE_CHANGE where DEVICE_CHANGE_ID = v_mid     │
│                                                                 │
│   if V_NEW_POSID is not null then  -- ★有设备变更(BG语义)       │
│     -- 旧设备无效                                               │
│     update tmm35_cust_pos_rl set useflg='0', MAINTENANCETYP='BG'│
│       where eid=V_NEW_POSID and CUSTCD=V_NEW_CUSTCD            │
│     -- 新客户资产：已有则激活，否则插入                          │
│     if v_pos>0 then update useflg='1'                           │
│     else insert into tmm35_cust_pos_rl                          │
│   end if                                                        │
│                                                                 │
│   -- 更新客户主表（新磁卡号/姓名/地址/电话）                    │
│   update tmm22_customers                                        │
│     set custcard=v_custcard, CUSTNM=v_custnm,                   │
│         ADDRESS=V_ADDRESS, PHONENO=V_PHONENO,                   │
│         REPLACEDATE=SYSDATE, S_STATUS='1'                       │
│     where custcd=v_custcd                                       │
│                                                                 │
│   -- ★旧客户无效化（V_NEW_CUSTCD）                              │
│   update tmm22_customers set useflg='0'                         │
│     where custcd=V_NEW_CUSTCD                                   │
│                                                                 │
│   uf_update_cust(v_custcd, as_userid)                           │
│   uf_update_cust(V_NEW_CUSTCD, '')                              │
│                                                                 │
│   update plan_cust set status='01'  -- ★计划完成                │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 状态流转汇总

| 阶段 | plan_cust.status | 含义 | 触发动作 |
|------|-----------------|------|---------|
| 创建 | 00 | 待确认 | 预计划录入 |
| 计划确认 | 02 | 实施中 | `u_plan_befor_new.oe_dobutton1` |
| 实施确认 | 04 | 分派中/实施中 | `u_plan_imple.oe_dobutton1` → `USP_PLAN_IMPLE` |
| 变更单关单 | 03 | 实施完成 | `u_itsm_device_change` 关单 → `of_update_plan` |
| 数据接收确认 | 01 | 计划完成 | `u_trans_in_ed1` → `USP_TRANS_IN_CONFRIM` → `USP_PLAN_CONFRIM` |

---

## 4. 关键存储过程源码分析

### 4.1 USP_PLAN_IMPLE（i_type='10' 磁卡号变更分支）

**核心逻辑**：从 plan_cust 取数据，生成 TIT16_DEVICE_CHANGE 记录。

```sql
ELSIF i_type = '10' THEN
    -- 磁卡号变更
    v_mchange := null;
    v_id := UF_GET_BILLNOU('BG');  -- 单号前缀 BG（注意：单号前缀是 BG，但 CHANGE_TYPE 是 CK）
    
    v_mchange.DEVICE_CHANGE_ID  := v_id;
    v_mchange.STORE_ID          := V_PLAN.CUSTCD;
    v_mchange.REQUSET_PAPER_ID  := i_planno;
    v_mchange.CHANGE_TYPE       := 'CK';              -- ★硬编码 CK
    v_mchange.DEVICE_ID         := V_PLAN.POSID;      -- 变更 POS（原设备）
    v_mchange.NEW_ADDRESS       := V_PLAN.NEW_ADDRESS;
    v_mchange.NEW_STORE_CARD    := V_PLAN.CUSTCARD;   -- 变更磁卡（新磁卡号）
    v_mchange.NEW_TEL           := V_PLAN.NEW_PHONENO;
    v_mchange.IS_STORE_INSIDE_CHANGE := 'N';
    v_mchange.CURRENT_STATUS    := 1;
    -- NEW_STORE_ID 未赋值（始终为空）
    
    insert into TIT16_DEVICE_CHANGE values v_mchange;
```

**关键点**：
- `CHANGE_TYPE` 硬编码为 `'CK'`，不区分是否有设备变更
- `DEVICE_ID` 取自 `V_PLAN.POSID`（原设备）
- `NEW_STORE_CARD` 取自 `V_PLAN.CUSTCARD`（新磁卡号）
- `NEW_STORE_ID` 未赋值，始终为空

### 4.2 USP_PLAN_CONFRIM（v_tftype='10' 磁卡号变更分支）

**核心逻辑**：处理客户主表 + 客户设备关系表（tmm35）的变更。

```sql
IF v_tftype = '10' THEN
    SELECT STORE_ID INTO v_custcd 
      FROM TIT16_DEVICE_CHANGE WHERE DEVICE_CHANGE_ID = v_mid;
    
    -- ★按 V_NEW_POSID 是否为空隐式区分设备变更
    if V_NEW_POSID is not null then
        -- 旧设备无效
        update tmm35_cust_pos_rl 
           set useflg='0', MAINTENANCETYP='BG', 
               maintenanceno=v_mid, maintenancedate=sysdate
         WHERE eid=V_NEW_POSID AND CUSTCD=V_NEW_CUSTCD;
        
        -- 新客户资产：已有则激活，否则插入
        SELECT count(1) INTO v_pos 
          FROM TMM35_CUST_POS_RL 
         WHERE eid=V_NEW_POSID AND CUSTCD=V_CUSTCD;
        
        IF v_pos > 0 THEN
            update tmm35_cust_pos_rl 
               set useflg='1', MAINTENANCETYP='BG', 
                   maintenanceno=v_mid, maintenancedate=SYSDATE,
                   posupddate=SYSDATE
             WHERE eid=V_NEW_POSID AND CUSTCD=V_CUSTCD AND useflg='0';
        ELSE
            -- 生成新客户资产（从旧客户复制）
            insert into tmm35_cust_pos_rl (...)
            select v_custcd, eid, itemcd, ... 
              from tmm35_cust_pos_rl
             where eid=V_NEW_POSID AND CUSTCD=V_NEW_CUSTCD;
        END IF;
    end if;
    
    -- 更新客户主表（新磁卡号/姓名/地址/电话）
    update tmm22_customers
       set custcard=v_custcard, CUSTNM=v_custnm, 
           ADDRESS=V_ADDRESS, PHONENO=V_PHONENO, 
           REPLACEDATE=SYSDATE, S_STATUS='1'
     where custcd=v_custcd;
    
    -- ★旧客户无效化
    update tmm22_customers set useflg='0'
     where custcd=V_NEW_CUSTCD;
    
    uf_update_cust(v_custcd, as_userid);
    uf_update_cust(V_NEW_CUSTCD, '');
    
    update plan_cust set status='01';  -- 计划完成
END IF;
```

**关键点**：
- `V_NEW_POSID` 非空时执行设备转移（BG 语义），但 CHANGE_TYPE 仍是 CK
- 旧设备 `useflg='0'`，`MAINTENANCETYP='BG'`（注意：这里写的是 'BG' 类型标记）
- 新客户资产：已有则激活，没有则从旧客户复制插入
- 旧客户 `useflg='0'`（无效化）
- 最后 `plan_cust.status='01'`（计划完成）

### 4.3 USP_ITSM_TRANS_IN（i_type='BG' 设备变更分支）

**核心逻辑**：变更单关单时，写入"数据接收"中间表 `sm_in_open_result`。

```sql
ELSIF i_type='BG' THEN
    -- 注意：这里 i_type='BG' 是单据类型标识，不是 CHANGE_TYPE
    INSERT INTO tmp_sm_in_open_result
        (id, plan_no, case_no, cardcode, serialno, completeddate, 
         result, insert_time, syn_time, sys_status)
    SELECT SM_OPEN_SEQNO.NEXTVAL, 
           m.requset_paper_id,    -- PL 单号
           m.DEVICE_CHANGE_ID,    -- 变更单号
           c.custcard, 
           '',                     -- serialno 为空
           m.CREATE_TIME, 
           '', m.CREATE_TIME, m.CREATE_TIME, '1'
      FROM TIT16_DEVICE_CHANGE m, tmm22_customers c
     WHERE c.custcd = m.STORE_ID
       AND m.DEVICE_CHANGE_ID = i_master_id;
    
    INSERT INTO sm_in_open_result
    SELECT id, plan_no, case_no, cardcode, serialno, completeddate, 
           result, sysdate, syn_time, sys_status
      FROM tmp_sm_in_open_result
     Where NOT Exists (SELECT 1 FROM sm_in_open_result 
                        WHERE sm_in_open_result.id = tmp_sm_in_open_result.id);
```

**关键点**：
- `i_type='BG'` 是 PB 调用方传入的单据类型标识（`u_itsm_device_change.is_billtype='BG'`），不是 `TIT16_DEVICE_CHANGE.CHANGE_TYPE`
- 作用是把变更单数据写入 `sm_in_open_result` 中间表，供后续 `USP_TRANS_IN_CONFRIM` 处理
- `serialno` 字段为空——设备变更不涉及新设备序列号

### 4.4 USP_TRANS_IN_CONFRIM（v_type='1' 整机顺流）

**核心逻辑**：数据接收确认，根据 plan_cust.plantyp 分发到 USP_PLAN_CONFRIM。

```sql
If v_type = '1' Then
    select plan_no, case_no, cardcode, serialno, COMPLETEDDATE
      into v_tfid, v_mid, v_custcard, v_str1, v_startdate
      from sm_in_open_result
     where id = v_id;
    
    IF substr(v_tfid,1,2) = 'PL' THEN
        -- PL 开头：预计划入口
        SELECT PLANTYP, POS_FROM, SOLVE_TYPE, CUST_USEFLG, 
               NEW_CUSTCARD, NEW_POSID, NEW_POSITEM, OPERCD
          into v_tftype, V_POS_FROM, V_SOLVE_TYPE, V_CUST_USEFLG, 
               V_NEW_CUSTCARD, V_NEW_POSID, V_NEW_POSITEM, V_PLANERCD
          FROM PLAN_CUST WHERE PLANNO = v_tfid;
    ELSE
        -- 非 PL：销售扩展入口
        select sltyp, itemcd into v_tftype, v_itemcd
          from tsl01_extend b
         where opbillid = v_tfid;
    END IF;
    
    -- 新流程：PL 开头按 plantyp 分发
    IF v_tftype = '00' THEN 
        usp_plan_confrim(as_type, as_id, as_userid, as_return);
    END IF;
    IF v_tftype = '10' THEN  -- ★磁卡号变更
        usp_plan_confrim(as_type, as_id, as_userid, as_return);
    END IF;
    IF v_tftype = '20' THEN 
        usp_plan_confrim(as_type, as_id, as_userid, as_return);
    END IF;
    
    update sm_in_open_result set sys_status='2' where id=v_id;
END IF;
```

**关键点**：
- PL 开头走预计划流程，按 `plantyp` 分发到 `usp_plan_confrim`
- 非 PL 开头走销售扩展流程（tsl01_extend），按 `sltyp` 处理（XZ/GX/GH/GB/BQ/CK/BG）
- **两套流程互斥**：PL 走新流程（USP_PLAN_CONFRIM），非 PL 走老流程（销售扩展）

---

## 5. PB 源码证据

### 5.1 u_plan_befor_new.sru（预计划管理 new 模块）

```powerbuilder
// L462-623
String ls_planno, ls_plantyp
...
ls_plantyp = dw_data.object.plantyp[ll_find]
...
if ls_plantyp = '10' then //变更
   select count(1) into :ll_count 
     from TIT16_DEVICE_CHANGE 
    where REQUSET_PAPER_ID = :ls_planno;
```

**印证**：`plantyp='10'` 关联 `TIT16_DEVICE_CHANGE` 表。

### 5.2 u_plan_imple.sru（实施确认）

```powerbuilder
// L241-242
case '10'//磁卡号变更
    select count(1) into :ll_row 
      from TIT16_DEVICE_CHANGE 
     where REQUSET_PAPER_ID = :as_planno;
...
// L476-477
Declare myproc Procedure For USP_PLAN_IMPLE(
    :ls_planno, :ls_plantyp, ...
```

**印证**：`plantyp='10'` 实施确认时调用 `USP_PLAN_IMPLE`。

### 5.3 u_itsm_device_change.sru（设备变更单）

```powerbuilder
// L140
string is_billtype = 'BG'  -- 单据类型标识

// L594
DECLARE MYPROC PROCEDURE FOR usp_itsm_trans_in(:is_mid, 0, 'BG') USING SQLCA;

// of_update_plan 函数
public function integer of_update_plan();
    // 回写计划
    ls_planno = dw_data.object.REQUSET_PAPER_ID[ll_row]
    If left(ls_planno, 2) = 'PL' Then
        if dw_data.object.is_success[ll_row] = '1' then 
            ls_Result = '00'  -- 实施结果成功
        else
            ls_Result = '01'  -- 实施结果失败
        end if
        
        update PLAN_CUST 
           set imple_Result = :ls_Result, 
               fail_Reason = :ls_descripiton, 
               status = '03' 
         where planno = :ls_planno;
    End If
    return 1
end function
```

**印证**：
- `is_billtype='BG'` 是单据类型标识常量，用于查询附表（D2D/RV/PAY）和传给 `usp_itsm_trans_in` 的 `i_type` 参数
- **当前版本 `u_itsm_device_change` 模块没有"新建变更单"功能**——PB 源码中没有任何 INSERT 到 TIT16_DEVICE_CHANGE 的操作，只有查询、显示、关单
- 关单时 `of_update_plan` 直接回写 `plan_cust.status='03'`（实施完成）
- 只有 PL 开头的才回写 plan_cust（OP 开头是老版本遗留数据，不回写）

### 5.4 u_ex_ck.sru / u_ex_gb.sru（销售扩展模块——易混淆）

```powerbuilder
// u_ex_ck.sru（搬迁单）
lnv_Attrib.ia_RetrieveArgs[2] = 'CK'
ls_Where += " and sltyp='CK' "

// u_ex_gb.sru（门店关闭）
ls_Where += " and sltyp='GB' "
```

**重要区分**：
- 这里的 `sltyp='CK'`（搬迁）和 `sltyp='GB'`（门店关闭）是**销售扩展模块**的 `TSL01_Extend.sltyp` 字段
- 与 `TIT16_DEVICE_CHANGE.CHANGE_TYPE` 的 CK/BG **含义完全不同**，只是碰巧用了相同字母
- 销售扩展走 `tsl01_extend/tsl02_extenddt` 表，不写入 `TIT16_DEVICE_CHANGE`

---

## 6. 两套业务对比

| 维度 | 当前版本（预计划→ITSM 设备变更） | 老版本（ITSM 直接创建） | 老版本（销售扩展） |
|------|-------------------------------|----------------------|-------------------|
| 入口 | 预计划管理 `plantyp=10` | ITSM 设备变更单模块（已废弃新建功能） | 销售扩展菜单 |
| 主表 | `TIT16_DEVICE_CHANGE` | `TIT16_DEVICE_CHANGE` | `TSL01_Extend` |
| 类型字段 | `CHANGE_TYPE='CK'`（硬编码） | `CHANGE_TYPE` = BG/BQ/CK | `sltyp` = XZ/GX/GH/GB/BQ/CK/BG |
| 创建方式 | `USP_PLAN_IMPLE` 存储过程 | 老版本 `u_itsm_device_change` 新建（已废弃） | 直接操作 TSL01 |
| 单据号前缀 | BG（`UF_GET_BILLNOU('BG')`） | BG | — |
| REQUSET_PAPER_ID | PL 开头 | OP 开头 | — |
| PB 对象 | `u_itsm_device_change`（仅查询/关单） | `u_itsm_device_change`（老版本有新建） | `u_ex_ck` / `u_ex_gb` |
| 数据接收 | `USP_ITSM_TRANS_IN` → `USP_TRANS_IN_CONFRIM` | 同左 | `USP_TRANS_IN_CONFRIM` 老 v_tftype 分支 |
| 当前状态 | **✅ 在用** | ❌ 老版本遗留数据（466 条） | 老版本/独立流程 |

**关键结论**：当前版本 `u_itsm_device_change` 模块仅用于**查询、显示、关单**设备变更单，不再有新建功能。所有新设备变更单都由预计划 plantyp=10 通过 `USP_PLAN_IMPLE` 创建。

---

## 7. 对重构代码的启示

### 7.1 已实施的修正（2026-07-02）

**修正前问题**：`_build_downstream_payload` 按 PB 逻辑判定 BG/CK/BQ，关单时用 `change_type == "BG"` 触发设备转移——但预计划入口永远产生 CK，导致设备转移逻辑对正常业务流程永不执行（结构性错误）。

**修正后方案**（已落地，4 个测试通过）：

| 修正点 | 文件 | 修正内容 | 对齐 PB |
|--------|------|---------|---------|
| 1 | `sales_service.py:239-250` | `_build_downstream_payload` 始终传 `change_type='CK'` | ✅ USP_PLAN_IMPLE 硬编码 |
| 2 | `itsm_service.py:670-676` | 关单设备转移条件从 `change_type=='BG'` 改为 `device_id and new_store_id` | ✅ USP_PLAN_CONFRIM V_NEW_POSID |
| 3 | `tests/test_device_change_11b.py` | 新增 `test_ck_with_device_transfer_triggers_rl_transfer` 覆盖预计划入口正常场景 | ✅ |

### 7.2 修正后的业务语义

- **创建时**：`plantyp=10` 预计划实施 → `USP_PLAN_IMPLE` 等价 → `TIT16_DEVICE_CHANGE.CHANGE_TYPE='CK'`（始终）
- **关单时**：按 `device_id + new_store_id` 隐式判断设备转移
  - 有 `device_id` 且有 `new_store_id` → 执行 EidTrack + rl 转移 + 设备回库 + 目标客户合并（对齐 PB V_NEW_POSID 非空分支）
  - 无 `device_id` 或无 `new_store_id` → 仅同步客户主表 + 写历史 + 回写计划
- **老数据兼容**：OP 前缀老数据 `CHANGE_TYPE='BG'/'BQ'` 仍能在关单时走 `_sync_customer_and_history`（因为条件是 `change_type in ("CK","BG","BQ")`）

### 7.2.1 重构版本子类型与触发条件

**结论：重构版本 `plantyp=10` 磁卡号变更只有一个子类型 `CK`**（对齐 PB 当前版本 `USP_PLAN_IMPLE` 硬编码），但关单时按数据条件隐式区分两条处理路径：

| 子类型 | 创建入口 | 关单触发条件 | 处理逻辑 | 对齐 PB |
|--------|---------|------------|---------|---------|
| **CK（纯磁卡号变更，无设备）** | `_build_downstream_payload` 始终 `change_type='CK'`；`device_id = new_posid or posid or None` | `device_id` 为空 **或** `new_store_id` 为空 | `_sync_customer_and_history` 同步客户主表（custcard/custnm/address/phoneno）+ 写 `TMM22_CUSTOMERS_HISTORY` + 回写 `plan_status='01'` | USP_PLAN_CONFRIM V_NEW_POSID 为空分支 |
| **CK（含设备转移）** | 同上 | `device_id` 非空 **且** `new_store_id` 非空 | 在纯磁卡号变更基础上追加：`_write_eid_track_on_close_bg`（type='T'）+ `_transfer_rl_on_close_bg`（旧 rl 失效/新 rl 新建/`maintenancetyp='BG'`）+ 目标客户 `useflg='0'`；**设备 `sflg` 保持原值不变** | USP_PLAN_CONFRIM V_NEW_POSID 非空分支 |

**关键区别**：
- PB 老版本通过 `CHANGE_TYPE` 字段值（BG/CK/BQ）区分三种独立业务
- 重构版本（对齐 PB 当前版本）`CHANGE_TYPE` 始终为 `CK`，通过 **数据条件**（`device_id + new_store_id` 是否非空）隐式区分是否包含设备转移
- 两条路径都执行 `_sync_customer_and_history` + `_write_back_plan_status`，区别仅在于是否追加设备转移逻辑

**`device_id` 取值规则**（`sales_service.py:250`）：
- 优先 `new_posid`（换设备场景）
- 为空则回退 `posid`（不换设备，源磁卡号设备转移到新磁卡号下）
- 都为空则 `None`（纯磁卡号变更无设备）

**设备 `sflg` 处理**（`itsm_service.py:982-984`）：
- 磁卡号变更设备从旧客户转到新客户，**不经过仓库**，`sflg` 保持原值不变
- 对齐 PB `USP_PLAN_CONFRIM`（不更新 `tmm43_eid.sflg`）
- 注：旧实现设 `sflg='8'`（在库）不正确，已于 2026-07-02 修正

**代码位置**：
- 创建：`sales_service.py:239-252`（`_build_downstream_payload` plantyp=='10' 分支）
- 关单：`itsm_service.py:846-859`（`DeviceChangeService.transition` to_status=='5' 分支）

### 7.3 关单回写逻辑

对齐 PB `of_update_plan`：
- 变更单关单时，若 `requset_paper_id` 以 PL 开头，直接回写 `plan_cust.status='03'`（实施完成）
- 同时调用 `usp_itsm_trans_in` 写入 `sm_in_open_result` 中间表
- 数据接收确认时调用 `usp_plan_confrim` 处理客户主表 + tmm35 + plan_cust.status='01'

### 7.4 已修复的中等问题（2026-07-02）

| # | 问题 | 位置 | 修复内容 | 状态 |
|---|------|------|---------|------|
| 3 | 旧/新 rl 缺 `MAINTENANCETYP='BG'`, `maintenanceno`, `maintenancedate` | `itsm_service.py:_transfer_rl_on_close_bg` | 旧 rl 失效时写入 `maintenancetyp='BG'`, `maintenanceno=变更单号`, `maintenancedate=now`；新 rl 新建/更新时同样写入 | ✅ 已修复 |
| 5 | `sm_in_open_result` 中间表缺失 | 新增实现 | **不实现**（见下方决策说明） | ✅ 已决策 |
| 6 | 翻新/回收/门店关闭关单未更新 `tmm43_eid.sflg` | `itsm_service.py` 三处关单方法 | 旧机/回收设备 `sflg='3'`（待检），对齐 PB `USP_PLAN_CONFRIM`；设备变更 BG（磁卡号变更）`sflg` 保持原值不变（设备在门店不经过仓库） | ✅ 已修复 |

**问题 6 修复详情**（方案 A 落地）：

| 方法 | 文件位置 | 修改内容 |
|------|---------|---------|
| `_transfer_rl_on_close_renovate` | `itsm_service.py:548-567` | 旧机 rl 失效后追加 `tmm43_eid.sflg='3'` |
| `_invalidate_rl_on_close_recycle` | `itsm_service.py:1254-1295` | 每个 asset_id rl 失效后追加 `tmm43_eid.sflg='3'` |
| `_invalidate_rl_on_close_store` | `itsm_service.py:1017-1048` | 所有设备 rl 失效后批量 `tmm43_eid.sflg='3'` |

**sflg 取值语义**（对齐 `warehouse_service.py` 中已有用法）：
- `'1'` 在门店使用（正常使用，`warehouse_service.py:1337,1671`）
- `'2'` **已报废**（`warehouse_service.py:1345,1903` 报废出库/结案）
- `'3'` 待检/待核实（`warehouse_service.py:686` 返修入库）← 回收设备用此值
- `'5'` 返修中（`warehouse_service.py:1350`）
- `'6'` 借出中（`warehouse_service.py:1341` 借出出库）
- `'7'` 生产中/翻新中（`warehouse_service.py:1354,1358`）
- `'8'` 翻新完成/在库（`warehouse_service.py:584,660` 翻新/生产入库）
- `'S'` 已销售（`warehouse_service.py:1362`）

**设计决策**：
- **翻新/回收/门店关闭** → `sflg='3'`（待检）：从门店回收的设备需要仓库核实身份和实物状态
- **设备变更 BG（磁卡号变更，客户间转移）** → `sflg` **保持原值不变**：设备物理位置不动，只改客户归属，不经过仓库，对齐 PB `USP_PLAN_CONFRIM`（不更新 `tmm43_eid.sflg`）
- **方案 B（回收设备核实环节）暂不实施**：方案 A 修复后仓库可通过 `sflg='3' + rl.asset_status='RETURNED'` 查到待处理设备，观察业务需要再补

> **⚠️ 修正记录**：
> 1. 初版误用 `sflg='2'`（已报废），经用户提示核实后修正为 `sflg='3'`（待检）。`sflg='2'` 在系统中是"已报废"语义，用于报废出库和 QC 结案场景。
> 2. 设备变更 BG 初版设 `sflg='8'`（在库）不正确——磁卡号变更设备在门店使用，不经过仓库，`sflg` 应保持原值（通常为 `'1'` 在门店）。已于 2026-07-02 修正为保持原值不变，对齐 PB `USP_PLAN_CONFRIM`。

**问题 5 决策说明**：`sm_in_open_result` 在 PB 中是"数据接收确认"中间表，作用是：
1. `usp_itsm_trans_in`（关单时）写入中间表
2. `usp_trans_in_confrim`（数据接收确认时）读取中间表并分发到 `usp_plan_confrim`

重构中已将 PB 的两步合并为**关单时直接处理**（`_sync_customer_and_history` + `_transfer_rl_on_close_bg` + `_write_back_plan_status`），业务结果等价于 PB 的 `USP_PLAN_CONFRIM` 处理结果。因此 `sm_in_open_result` 中间表在重构中**不是必须**，除非将来有报表/查询依赖此表——届时再按需新增模型和写入逻辑。

### 7.5 关单自动创建入库草稿（2026-07-02 新增）

**功能背景**：PB 老版本中，ITSM 关单后需要仓库人员手动创建入库单接收回收/返还的设备。重构版本在此基础上**自动化**此环节，关单时按业务类型自动创建对应类型的入库草稿（`auditflg='0'`），仓库人员只需在入库单页面审核即可。

**触发场景与入库类型**：

| ITSM 单据类型 | 关单状态 | 入库类型 (invtyp) | sysparm 配置键 | 筛选条件 |
|--------------|---------|------------------|---------------|---------|
| 日常维护单 `TIT10_MAINTENANCEDAY` | `CURRENT_STATUS='5'` | IV=3 服务返还 | `stock_in_whcd_3` | `TIT25_ACCESSORIES_UPDATE.old_accessories_id` 对应 EID，且 `asset_owner != '01'`（自有资产），排除耗材（`consume != '1'`）和已标记不入库的配件 |
| 旧机翻新单 `TIT15_MAINTENANCE_RENOVATE` | `CURRENT_STATUS='5'` | IV=7 回收入库 | `stock_in_whcd_7` | 旧机 `old_device_id` 对应 EID，且 `asset_owner != '01'`（自有资产） |
| 取机回收任务 `TIT20_RECYCLE_TASK` | `CURRENT_STATUS='5'` | IV=7 回收入库 | `stock_in_whcd_7` | 明细 `asset_id` 对应 EID，且 `asset_owner != '01'`（自有资产） |
| 门店关闭单 `TIT18_STORE_CLOSE` | `CURRENT_STATUS='5'` | IV=7 回收入库 | `stock_in_whcd_7` | 门店刚失效 rl（`asset_status='RETURNED'`）对应的 EID，且 `asset_owner != '01'`（自有资产） |

**关键设计**：
- **草稿状态**：`auditflg='0'`，仓库人员需在入库单页面审核后才真正入库
- **仓库来源**：统一从 `SysParm` 读取 `stock_in_whcd_{invtyp}` 配置（前端 `/warehouse/config` 页面维护）
- **未配置跳过**：sysparm 未配置或为空时，关单仍正常完成，仅跳过入库草稿创建
- **客户资产排除**：`asset_owner='01'`（客户资产）不纳入自动入库（对齐 PB 业务语义，客户资产不回仓库）
- **设备状态联动**：翻新/回收/门店关闭关单时同步设置 `tmm43_eid.sflg='3'`（待检），仓库审核入库后再更新为对应状态

**代码位置**：

| 方法 | 文件位置 | 说明 |
|------|---------|------|
| `_get_sysparm_whcd` | `itsm_service.py:74-79` | 从 SysParm 读取仓库编码 |
| `_create_stock_in_draft` | `itsm_service.py:82-118` | 通用入库草稿创建辅助函数 |
| `_create_service_return_inbound` | `itsm_service.py:256-325` | 日常维护单 → IV=3 |
| `_create_recycle_inbound_renovate` | `itsm_service.py:739-786` | 翻新单 → IV=7 |
| `_create_recycle_inbound_recycle` | `itsm_service.py:1529-1583` | 回收任务 → IV=7 |
| `_create_recycle_inbound_store` | `itsm_service.py:1226-1283` | 门店关闭 → IV=7 |

**前端配置**：`frontend/src/views/warehouse/WarehouseConfig.vue` 新增"入库类型默认仓库"分区，列出 IV=1~8 共8个入库类型仓库配置项，用户可为每种入库类型配置默认仓库。

**测试覆盖**：
- `test_maintenance_renovate_11c.py` 新增3个用例（自动创建/未配置仓库/客户资产不创建）
- `test_recycle_task_11d.py` 新增2个用例（自动创建/未配置仓库）
- `test_store_close_11e.py` 新增2个用例（自动创建/未配置仓库）
- 共 25 个测试全部通过

**与 PB 的差异**：
- PB 老版本：关单 → 仓库人员手动创建入库单 → 审核
- 重构版本：关单 → **自动创建入库草稿** → 仓库人员只需审核
- 业务结果等价，减少人工操作步骤，避免遗漏

---

## 8. 相关文档

- `docs/core/预计划设备来源与EID绑定专项设计.md`——预计划全链路设计
- `docs/core/预计划设备来源与EID绑定_前端操作验收手册.md`——前端操作验收
- `docs/core/ITSM重构项目需求设计文档.md`——PB 源码分析与重构路线图
- `docs/core/系统功能对比分析与扩展规划.md`——功能映射与扩展规划
- `docs/core/全阶段模型字段核对报告.md`——TIT16_DEVICE_CHANGE 字段核对

---

## 9. 变更记录

| 日期 | 变更内容 | 作者 |
|------|---------|------|
| 2026-07-02 | 初始版本，基于 PB 源码 + Oracle 存储过程源码 + 数据库数据三方交叉验证 | Cascade |
| 2026-07-02 | 修正 BG 类型来源：BG 是老版本 ITSM 直接创建遗留数据，当前版本 `u_itsm_device_change` 无新建功能；新增"三个容易混淆的 BG"概念辨析；数据库完整分布印证（OP 前缀 466 条为老版本遗留） | Cascade |
| 2026-07-02 | 落地代码修正：`sales_service.py` 始终 CK，`itsm_service.py` 关单设备转移条件改为 `device_id + new_store_id`，新增 CK+设备转移测试，4 个测试通过 | Cascade |
| 2026-07-02 | 修复中等问题 #3：`_transfer_rl_on_close_bg` 补写旧/新 rl 的 `MAINTENANCETYP='BG'`/`maintenanceno`/`maintenancedate`；决策中等问题 #5：不实现 `sm_in_open_result` 中间表（关单已直接处理业务逻辑） | Cascade |
| 2026-07-02 | 修复中等问题 #6（方案 A）：翻新/回收/门店关闭关单补写 `tmm43_eid.sflg='3'`（待检），对齐 PB USP_PLAN_CONFRIM；设备变更 BG 保持 `sflg='8'`；新增 3 处测试断言，36 个测试通过 | Cascade |
| 2026-07-02 | 修正 sflg 取值：初版误用 `sflg='2'`（已报废），经用户提示核实后修正为 `sflg='3'`（待检）。`sflg='2'` 在 `warehouse_service.py:1345,1903` 是"已报废"语义 | Cascade |
| 2026-07-02 | 新增 §7.2.1 重构版本子类型说明：`plantyp=10` 只有一个子类型 `CK`，关单时按 `device_id + new_store_id` 隐式区分纯磁卡号变更与含设备转移两条路径 | Cascade |
| 2026-07-02 | 新增 §7.5 关单自动创建入库草稿功能：日常维护→IV=3、翻新/回收/门店关闭→IV=7，sysparm 统一 `stock_in_whcd_{invtyp}`，仅自有资产，草稿状态 `auditflg='0'`；前端 WarehouseConfig.vue 新增 IV=1~8 配置项；25 个测试通过 | Cascade |
| 2026-07-02 | 修正 `device_id` 取值：`new_posid or posid or None`，兼容不换设备场景（源磁卡号设备转移到新磁卡号下）；修正 `_transfer_rl_on_close_bg` 设备 `sflg` 保持原值不变（对齐 PB USP_PLAN_CONFRIM，磁卡号变更不经过仓库）；新增 3 个单元测试，7 个测试通过 | Cascade |
