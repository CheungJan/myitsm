# P3_STAGE10 对象分类说明（L0/L1 收敛口径）

## 1. 目的

用于解释“库内对象总量”和“三方整合简化目标”为什么不一致，并给出当前最终分类口径。

---

## 2. 分类口径

### A. L1 保留核心对象

- 来源：`MIG_P3_L1_OBJECT_SET`
- 冻结状态：`FROZEN=134`
- 说明：这是三方整合后用于长期运行的简化目标对象集（KEEP+MIGRATE）。

### B. 基础设施对象（INFRA）

- 来源：`MIG_P3_L0_TRIM_CAND.candidate_type='INFRA'`
- 当前数量：`27`
- 说明：迁移治理与目标模型运行所需基础对象（如 `MIG_*`、`ITSM_*`）。

### C. L0 裁剪候选对象（TRIM_CANDIDATE）

- 来源：`MIG_P3_L0_TRIM_CAND.candidate_type='TRIM_CANDIDATE'`
- 历史识别：`192`
- 执行后现状：`仍存在=0`
- 说明：已完成主裁剪，不再存在未处置候选。

---

## 3. 执行结果摘要

- `P3_STAGE07` 裁剪执行：`DONE=172`、`SKIPPED=20`、`FAILED=0`
- `P3_STAGE08` 占位清理：`DONE=172`
- `P3_STAGE10` 残留处置：`residual_cnt=0`
- 当前对象规模：`user_tables=293`、`user_views=8`

---

## 4. 结论

1. 三方整合“简化目标”已落地为可运行的 L1 对象集。
2. L0 大部分非目标对象已被裁剪，且无残留候选。
3. 当前总量仍大于 L1 是因为保留了必要基础设施与运行支撑对象，这属于设计内结果。
