# CCGL_MIG执行入口与门禁说明

## 1. tnsnames.ora 建议新增
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

## 2. 连接方式
```powershell
sqlplus CCGL_MIG/ccgl_mig@CCGL_MIG
```

## 3. 强制门禁SQL（每次执行前）
```sql
SELECT SYS_CONTEXT('USERENV','SERVICE_NAME') AS service_name,
       SYS_CONTEXT('USERENV','DB_NAME')      AS db_name,
       SYS_CONTEXT('USERENV','SESSION_USER') AS session_user
FROM dual;
```
- 通过条件：
  - `SERVICE_NAME = CCGL_MIG`
  - `SESSION_USER = CCGL_MIG`（或你指定的迁移用户）

## 4. 执行顺序
1. 先执行P1：`TIT01_TIMEPOINT_CUST`
2. 再按 P2-A/B/C/D 分批执行
3. 单对象成功后立即跑只读验证

## 5. 严禁事项
- 严禁使用 `@CCGL` 或 `@CCGL_TEST` 执行迁移DDL。
- 严禁在同一窗口混用多个连接别名。
- 严禁跳过门禁SQL直接执行脚本。

## 6. 建议命令（含日志）
```powershell
sqlplus CCGL_MIG/ccgl_mig@CCGL_MIG @e:\project\myitsm\src\docs\DBA_执行_创建TIT01_TIMEPOINT_CUST.sql
sqlplus CCGL_MIG/ccgl_mig@CCGL_MIG @e:\project\myitsm\src\docs\DBA_验证_TIT01_TIMEPOINT_CUST.sql
```

> 说明：上述脚本建议先复制为`*_MIG.sql`版本，再加入“service门禁块”，避免误用到其他环境。
