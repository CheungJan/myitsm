# TNSPING `CCGL_MIG` 初次失败故障排查手册

## 1. 问题现象
在已创建 `CCGL_MIG` PDB 且数据库端状态正常（`READ WRITE`）的前提下，执行：

```powershell
tnsping CCGL_MIG
```

出现：

- `TNS-03505: 无法解析名称`

同时，SQL Developer 可能可以连接成功，表现为“工具A可连、工具B不可连”。

---

## 2. 根因结论
本次问题根因不是数据库服务异常，而是**Oracle 客户端解析链路不一致**：

1. 机器上存在多个 Oracle 客户端（例如 `dbhome_1` 与 `instantclient`）。
2. `tnsping.exe` 来自 `dbhome_1`，默认读取该 Oracle Home 下的 `network\admin`。
3. SQL Developer 可能使用另一套客户端或“基本连接模式”（host/port/service），因此看起来可连。
4. `setx TNS_ADMIN ...` 仅对新进程生效，当前终端不会立即生效，导致排障中出现“有时失败、有时成功”。

---

## 3. 快速诊断命令

```powershell
where.exe tnsping
echo $env:TNS_ADMIN
tnsping CCGL_MIG
```

判定方法：

- `where.exe tnsping`：确认当前调用的是哪一个 `tnsping.exe`。
- `echo $env:TNS_ADMIN`：若为空，说明当前会话未显式指定统一目录。
- `tnsping` 输出中的 `Used parameter files`：可看到实际读取的 `sqlnet.ora` 路径。

---

## 4. 标准解决方案（推荐）

### 4.1 统一 TNS 目录
建议统一到：

- `D:\instantclient_12_1\NETWORK\ADMIN`

并确保该目录下同时存在：

- `tnsnames.ora`
- `sqlnet.ora`

### 4.2 当前会话立即生效

```powershell
$env:TNS_ADMIN = "D:\instantclient_12_1\NETWORK\ADMIN"
echo $env:TNS_ADMIN
tnsping CCGL_MIG
```

### 4.3 持久化（对新终端生效）

```powershell
setx TNS_ADMIN "D:\instantclient_12_1\NETWORK\ADMIN"
```

> 注意：执行 `setx` 后需新开终端，旧终端不自动更新环境变量。

---

## 5. 配置样例

### 5.1 tnsnames.ora

```ini
CCGL_MIG =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = localhost)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = ccgl_mig)
    )
  )
```

### 5.2 sqlnet.ora

```ini
NAMES.DIRECTORY_PATH = (TNSNAMES, EZCONNECT)
```

---

## 6. 验收标准
满足以下三条即可判定修复成功：

1. `echo $env:TNS_ADMIN` 输出为统一目录。
2. `tnsping CCGL_MIG` 返回 `OK (0)`。
3. `sqlplus pdb_admin/PdbAdmin_ChangeMe_2026@CCGL_MIG` 可登录。

---

## 7. 回退与兜底方案
若短期内不便统一 TNS，可临时使用 EZCONNECT 直连（不依赖别名）：

```powershell
sqlplus pdb_admin/PdbAdmin_ChangeMe_2026@localhost:1521/ccgl_mig
```

该方式可用于继续执行 `DBA_INIT_SCHEMA_CCGL_MIG.sql`，不阻塞迁移验证。

---

## 8. 本次案例结论
本次 `CCGL_MIG` 问题最终通过以下方式解决：

- 在**正确的客户端会话**中设置 `TNS_ADMIN`；
- 使用统一目录下的 `tnsnames.ora/sqlnet.ora`；
- 复测 `tnsping CCGL_MIG` 连续成功（`OK (0)`）。
