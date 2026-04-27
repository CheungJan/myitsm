SET ECHO ON;
SET PAGESIZE 300;
SET LINESIZE 260;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === P3_STAGE09 FINAL ACCEPTANCE REPORT (READ ONLY) ===

PROMPT === 1) L0/L1 收敛口径 ===
SELECT stage_no,
       wave_no,
       l0_total_objects,
       l1_frozen_objects,
       l1_verified_objects,
       reduction_ratio_pct,
       report_status
FROM MIG_P3_DUAL_LAYER_RPT
WHERE stage_no='P3_STAGE04'
  AND wave_no='WAVE_01';

PROMPT === 2) 裁剪执行结果 ===
SELECT exec_status, COUNT(*) AS cnt
FROM MIG_P3_L0_TRIM_EXEC
WHERE stage_no='P3_STAGE07'
  AND wave_no='WAVE_01'
GROUP BY exec_status
ORDER BY exec_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no='P3_STAGE07'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

PROMPT === 3) 回滚占位清理结果 ===
SELECT exec_status, COUNT(*) AS cnt
FROM MIG_P3_RB_CLEAN_EXEC
WHERE stage_no='P3_STAGE08'
  AND wave_no='WAVE_01'
GROUP BY exec_status
ORDER BY exec_status;

PROMPT === 4) 当前对象规模 ===
SELECT 'TABLE' AS object_type, COUNT(*) AS cnt FROM user_tables
UNION ALL
SELECT 'VIEW'  AS object_type, COUNT(*) AS cnt FROM user_views;

PROMPT === 5) 最终验收判定（技术口径） ===
SELECT CASE
         WHEN EXISTS (
           SELECT 1 FROM MIG_P3_DUAL_LAYER_RPT
           WHERE stage_no='P3_STAGE04'
             AND wave_no='WAVE_01'
             AND report_status='DONE'
         )
         AND NOT EXISTS (
           SELECT 1 FROM MIG_P3_L0_TRIM_EXEC
           WHERE stage_no='P3_STAGE07'
             AND wave_no='WAVE_01'
             AND exec_status='FAILED'
         )
         AND EXISTS (
           SELECT 1 FROM MIG_P3_RB_CLEAN_EXEC
           WHERE stage_no='P3_STAGE08'
             AND wave_no='WAVE_01'
             AND exec_status='DONE'
         )
         THEN 'ACCEPTED'
         ELSE 'NOT_ACCEPTED'
       END AS p3_acceptance_status
FROM dual;

EXIT;
