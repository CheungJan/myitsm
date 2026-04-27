# P1_BATCH01 应用层联调与切换计划

## 1. 目的

在数据库侧已完成 `PLAN_CUST` 与 `TIT02` 写切换准入与执行记录的前提下，明确应用侧最小联调与切换动作，确保：

- 切换可执行（有步骤）
- 切换可验证（有口径）
- 切换可回退（有脚本）

## 2. 当前前置状态（已完成）

1. `PLAN_CUST`：已完成写灰度与写切换日志落库
2. `TIT02_LIABILITYREG`：已完成影子试点与写切换日志落库
3. 监控口径：`MIG_P1_SHADOW_WRITE_LOG` 最近 24 小时无 `DIFF/ERROR`

参考脚本：

- `DBA_P1_BATCH01_RUN_STEP10_WRITE_CUTOVER_PLAN_CUST.sql`
- `DBA_P1_BATCH01_RUN_STEP12_WRITE_CUTOVER_TIT02.sql`
- `DBA_P1_BATCH01_RUN_STEP06_SHADOW_MONITOR.sql`

## 3. 应用侧切换范围（最小集）

### 3.1 写路由切换对象

- `PLAN_CUST` 写入口 -> 新路径（`ITSM_CORE_PLAN_CUSTOMER_XREF`）
- `TIT02_LIABILITYREG` 写入口 -> 新路径（`ITSM_CORE_LIABILITY`）

### 3.2 读路径策略

- 本批次不做读路径大改动，保持现网可用
- 若应用已有新读路径能力，仅在灰度用户范围内启用

## 4. 执行步骤（应用侧）

### Step A：预检（上线前 10 分钟）

1. 执行监控脚本：`DBA_P1_BATCH01_RUN_STEP06_SHADOW_MONITOR.sql`
2. 必须满足：
   - `write_gray_decision = WRITE_GRAY_READY`
   - 最近 24 小时 `bad_cnt = 0`
3. 若不满足，停止切换

### Step B：应用配置切换（灰度）

1. 发布应用配置（仅打开 `PLAN_CUST`、`TIT02` 新写路径）
2. 灰度范围建议：
   - 按租户/机构白名单
   - 或按固定业务账号白名单
3. 灰度时长建议：30~60 分钟

### Step C：联调验证（灰度窗口内）

1. 执行 3 组业务用例：新增、修改、作废（或停用）
2. 每组至少 3 笔，核验：
   - 应用返回成功
   - 新模型表可查询到对应记录
   - 影子日志无 `DIFF/ERROR`

### Step D：扩大范围或保持灰度

- 若窗口内 `DIFF/ERROR = 0`，扩大灰度范围
- 若出现异常，立即执行回退（见第 6 节）

## 5. 验收口径

### 5.1 成功口径

- 关键流程成功率 `>= 99%`
- 影子日志最近窗口 `DIFF/ERROR = 0`
- 应用侧无 P1 阻断缺陷

### 5.2 失败口径

- 任一关键流程连续失败
- 影子日志出现 `DIFF/ERROR`
- 业务反馈可感知错误并影响主流程

## 6. 回退预案（应用优先）

### 6.1 应用回退（首选）

1. 关闭新写路径开关，恢复旧路径
2. 保留现场日志与请求样本
3. 通知 DBA 保持数据库侧为当前状态，不做额外破坏性处理

### 6.2 数据库审计回退标记（按需）

- `PLAN_CUST` 回退脚本：`DBA_P1_BATCH01_RUN_STEP10_WRITE_CUTOVER_ROLLBACK_PLAN_CUST.sql`
- `TIT02` 回退脚本：`DBA_P1_BATCH01_RUN_STEP12_WRITE_CUTOVER_ROLLBACK_TIT02.sql`

说明：数据库回退脚本用于审计与状态回写，不替代应用配置回退动作。

## 7. 责任分工

- 应用负责人：发布开关、灰度范围控制、接口联调
- DBA：门禁复核、监控复跑、回退脚本执行支持
- 业务代表：关键流程验收签字

## 8. 结论

当前已具备应用层联调与切换执行条件，建议按“最小范围灰度 -> 观察 -> 扩大”的节奏推进，不做一次性全量切换。
