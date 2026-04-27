SET ECHO ON;
SET PAGESIZE 200;
SET LINESIZE 220;

PROMPT === P1_BATCH01 三段式进度视图（只读映射，不改历史日志） ===

WITH mapped AS (
  SELECT
    batch_no,
    object_type,
    object_name,
    action_type,
    execute_status,
    note,
    executed_at,
    CASE
      WHEN action_type IN ('RUN_STEP01', 'RUN_STEP02') THEN 'STEP2_MIGRATE_AND_VERIFY'
      WHEN action_type IN ('RUN_STEP03', 'STEP3_1_READINESS') THEN 'STEP3_1_READINESS'
      WHEN action_type IN ('RUN_STEP04', 'STEP3_2_READ_CUTOVER') THEN 'STEP3_2_READ_CUTOVER'
      WHEN action_type IN ('RUN_STEP05', 'STEP3_3_WRITE_GATE', 'STEP3_3_SHADOW_TEMPLATE') THEN 'STEP3_3_WRITE_PREPARE'
      WHEN action_type = 'SNAPSHOT' THEN 'STEP1_WORKPACK_SNAPSHOT'
      ELSE action_type
    END AS action_type_3phase
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH01'
)
SELECT action_type_3phase, execute_status, COUNT(*) AS cnt
FROM mapped
GROUP BY action_type_3phase, execute_status
ORDER BY action_type_3phase, execute_status;

PROMPT === 明细（最近执行在前） ===
WITH mapped AS (
  SELECT
    batch_no,
    object_type,
    object_name,
    action_type,
    execute_status,
    note,
    executed_at,
    CASE
      WHEN action_type IN ('RUN_STEP01', 'RUN_STEP02') THEN 'STEP2_MIGRATE_AND_VERIFY'
      WHEN action_type IN ('RUN_STEP03', 'STEP3_1_READINESS') THEN 'STEP3_1_READINESS'
      WHEN action_type IN ('RUN_STEP04', 'STEP3_2_READ_CUTOVER') THEN 'STEP3_2_READ_CUTOVER'
      WHEN action_type IN ('RUN_STEP05', 'STEP3_3_WRITE_GATE', 'STEP3_3_SHADOW_TEMPLATE') THEN 'STEP3_3_WRITE_PREPARE'
      WHEN action_type = 'SNAPSHOT' THEN 'STEP1_WORKPACK_SNAPSHOT'
      ELSE action_type
    END AS action_type_3phase
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH01'
)
SELECT action_type_3phase, action_type, object_type, object_name, execute_status, executed_at, note
FROM (
  SELECT action_type_3phase, action_type, object_type, object_name, execute_status, executed_at, note
  FROM mapped
  ORDER BY executed_at DESC NULLS LAST
)
WHERE ROWNUM <= 100;

EXIT;
