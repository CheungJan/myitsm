# P1_BATCH01 三段式执行口径说明

## 1. 目标
为避免“步骤编号不断增加”导致的理解偏差，统一将 P1_BATCH01 的推进口径固定为三段式主线：

1. Step1：工作包与快照
2. Step2：迁移与核验
3. Step3：切流与写准备（可细分 3.1/3.2/3.3）

## 2. 旧命名与新口径映射
- `SNAPSHOT` -> `STEP1_WORKPACK_SNAPSHOT`
- `RUN_STEP01`/`RUN_STEP02` -> `STEP2_MIGRATE_AND_VERIFY`
- `RUN_STEP03` 或 `STEP3_1_READINESS` -> `Step3.1 读切换就绪`
- `RUN_STEP04` 或 `STEP3_2_READ_CUTOVER` -> `Step3.2 读切流与回退`
- `RUN_STEP05` 或 `STEP3_3_WRITE_GATE` 或 `STEP3_3_SHADOW_TEMPLATE` -> `Step3.3 写门禁与影子写准备`

说明：历史日志不强制重写，查询统计时按映射统一展示。

## 3. 当前执行边界
- 已完成：Step1、Step2、Step3.1、Step3.2、Step3.3（准备态）。
- 未执行：真实写切换（生产写路径切主），当前仅到“写灰度准备”。

## 4. 推荐看板查询
使用脚本：`SQL_P1_BATCH01_PROGRESS_3PHASE.sql`

该脚本会把历史 `action_type` 映射为三段式口径展示，避免团队在日志名上反复讨论。

## 5. 后续执行约定
后续新增脚本建议继续沿用：
- Step3.1 前缀：`STEP3_1_*`
- Step3.2 前缀：`STEP3_2_*`
- Step3.3 前缀：`STEP3_3_*`

并在脚本头部 `PROMPT` 中明确“这是 Step3.x 的哪一段”。
