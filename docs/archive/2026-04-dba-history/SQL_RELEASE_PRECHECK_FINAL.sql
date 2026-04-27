SET ECHO ON;
SET PAGESIZE 300;
SET LINESIZE 260;

PROMPT === 上线前最终预检（只读） ===

PROMPT === 1) 主线关键状态 ===
SELECT batch_no,
       action_type,
       execute_status,
       COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE (batch_no = 'P2_STAGE02' AND action_type = 'STEP2_REGRESSION_EXEC')
   OR (batch_no = 'P2_STAGE03' AND action_type = 'STEP3_PY_SWITCH_DONE')
   OR (batch_no = 'P2_STAGE04' AND action_type = 'STEP4_COMPAT_PLAN_READY')
   OR (batch_no = 'P3_STAGE01' AND action_type = 'STEP1_FINAL_ARCHIVE')
GROUP BY batch_no, action_type, execute_status
ORDER BY batch_no, action_type, execute_status;

PROMPT === 2) P2 任务状态 ===
SELECT stage_no,
       task_no,
       task_status,
       note
FROM MIG_P2_STAGE_CHECK
WHERE stage_no = 'P2_STAGE01'
ORDER BY task_no;

PROMPT === 3) 阻塞项扫描（为空即通过） ===
SELECT batch_no,
       object_type,
       object_name,
       action_type,
       execute_status,
       note
FROM MIG_P1_BATCH_LOG
WHERE batch_no IN ('P2_STAGE02', 'P2_STAGE03', 'P2_STAGE04', 'P3_STAGE01')
  AND execute_status IN ('BLOCKED', 'FAILED', 'ERROR')
ORDER BY batch_no, action_type, object_name;

PROMPT === 4) 最终放行判定 ===
SELECT CASE
         WHEN EXISTS (
           SELECT 1 FROM MIG_P3_FINAL_ARCH
           WHERE stage_no = 'P3_STAGE01'
             AND wave_no = 'WAVE_01'
             AND overall_status = 'DONE'
         )
         AND NOT EXISTS (
           SELECT 1
           FROM MIG_P1_BATCH_LOG
           WHERE batch_no IN ('P2_STAGE02', 'P2_STAGE03', 'P2_STAGE04', 'P3_STAGE01')
             AND execute_status IN ('BLOCKED', 'FAILED', 'ERROR')
         )
         AND NOT EXISTS (
           SELECT 1
           FROM MIG_P2_STAGE_CHECK
           WHERE stage_no = 'P2_STAGE01'
             AND task_status <> 'DONE'
         )
         THEN 'GO'
         ELSE 'NO_GO'
       END AS final_release_decision
FROM dual;

EXIT;
