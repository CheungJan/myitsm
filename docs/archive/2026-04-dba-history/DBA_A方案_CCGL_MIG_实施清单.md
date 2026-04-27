# A方案实施清单：新建独立PDB `CCGL_MIG`

## 1. 目标
- 在与现有正式/测试库完全隔离的容器中建立迁移沙箱 `CCGL_MIG`。
- 后续所有迁移优化动作（视图/同义词/兼容SQL）仅在 `CCGL_MIG` 执行。

## 2. 前置条件
1. 由DBA在CDB层具备 `SYSDBA` 权限。
2. 磁盘空间满足数据文件与归档日志增长。
3. 已确认监听可注册新服务名 `CCGL_MIG`。
4. 已审批变更窗口与回滚窗口。

## 3. 实施步骤
1. 执行 `DBA_创建PDB_CCGL_MIG.sql`：创建并打开PDB、保存启动状态。
2. 在 `tnsnames.ora` 新增别名 `CCGL_MIG`（指向新服务）。
3. 执行 `DBA_CCGL_MIG_初始化_SCHEMA.sql`：创建迁移用户、最小权限、目录对象。
4. 按需导入“只读快照数据”（建议Data Pump，优先结构+抽样数据）。
5. 执行 `DBA_CCGL_MIG_执行入口_门禁说明.md` 中的门禁SQL，确认会话在 `CCGL_MIG`。
6. 在 `CCGL_MIG` 执行P1/P2脚本，禁止连接到 `CCGL` / `CCGL_TEST`。

## 3.1 命令级操作（可直接执行）

### 步骤A：DBA创建PDB（必须先做）
```powershell
sqlplus / as sysdba
```

进入 SQL*Plus 后执行：
```sql
@e:\project\myitsm\src\docs\DBA_CREATE_PDB_CCGL_MIG.sql
```

再核验：
```sql
show pdbs;
SELECT name, open_mode FROM v$pdbs WHERE name = 'CCGL_MIG';
SELECT name, pdb, network_name FROM cdb_services WHERE pdb = 'CCGL_MIG';
```

### 步骤B：新增本地连接别名
在 `tnsnames.ora` 增加：
```ini
CCGL_MIG =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = localhost)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = CCGL_MIG)
    )
  )
```

并验证：
```powershell
tnsping CCGL_MIG
```

### 步骤C：初始化迁移Schema
```powershell
sqlplus pdb_admin/PdbAdmin_ChangeMe_2026@CCGL_MIG
```

进入 SQL*Plus 后执行：
```sql
@e:\project\myitsm\src\docs\DBA_INIT_SCHEMA_CCGL_MIG.sql
```

### 步骤D：迁移用户登录并执行门禁检查
```powershell
sqlplus CCGL_MIG/CcglMig_ChangeMe_2026@CCGL_MIG
```

进入 SQL*Plus 后执行：
```sql
SELECT SYS_CONTEXT('USERENV','SERVICE_NAME') AS service_name,
       SYS_CONTEXT('USERENV','DB_NAME')      AS db_name,
       SYS_CONTEXT('USERENV','SESSION_USER') AS session_user
FROM dual;
```

### 步骤E：在 CCGL_MIG 执行迁移脚本（示例P1）
```sql
@e:\project\myitsm\src\docs\DBA_执行_创建TIT01_TIMEPOINT_CUST.sql
@e:\project\myitsm\src\docs\DBA_验证_TIT01_TIMEPOINT_CUST.sql
```

## 4. 验收标准
- `SHOW PDBS` 可见 `CCGL_MIG` 且 `OPEN_MODE=READ WRITE`。
- `SERVICE_NAME` 校验结果为 `CCGL_MIG`。
- 迁移用户仅有沙箱最小权限，无正式库对象修改权限。
- P1脚本在 `CCGL_MIG` 成功，验证脚本通过。

## 5. 回滚策略
- 若创建阶段失败：`DROP PLUGGABLE DATABASE CCGL_MIG INCLUDING DATAFILES;`
- 若迁移阶段失败：仅回滚 `CCGL_MIG` 内对象，不影响 `CCGL` / `CCGL_TEST`。

## 6. 风险控制
- 强制会话门禁：脚本首段检查 `SERVICE_NAME='CCGL_MIG'`，不满足即中止。
- 强制日志落盘：每次执行均 `SPOOL`。
- 执行原则：先结构后数据、先小批后全量、先验证后推广。
