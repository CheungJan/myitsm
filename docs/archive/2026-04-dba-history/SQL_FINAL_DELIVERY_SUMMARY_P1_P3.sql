SET ECHO ON;
SET PAGESIZE 300;
SET LINESIZE 260;

PROMPT === FINAL DELIVERY SUMMARY (P1 -> P3) ===

PROMPT === 1) P1 DEPRECATE closeout ===
SELECT batch_no,
       action_type,
       execute_status,
       COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no IN ('P1_DEPRECATE09', 'P1_DEPRECATE10')
GROUP BY batch_no, action_type, execute_status
ORDER BY batch_no, action_type, execute_status;

SELECT batch_no,
       wave_no,
       total_cnt,
       approved_cnt,
       hold_cnt,
       closeout_status
FROM MIG_P1_DEP_CLOSEOUT
WHERE batch_no = 'P1_DEPRECATE10'
  AND wave_no = 'WAVE_10';

PROMPT === 2) P2 mainline status ===
SELECT batch_no,
       action_type,
       execute_status,
       COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no IN ('P2_STAGE00', 'P2_STAGE01', 'P2_STAGE02', 'P2_STAGE03', 'P2_STAGE04')
GROUP BY batch_no, action_type, execute_status
ORDER BY batch_no, action_type, execute_status;

SELECT stage_no,
       task_no,
       task_status,
       note
FROM MIG_P2_STAGE_CHECK
WHERE stage_no = 'P2_STAGE01'
ORDER BY task_no;

SELECT stage_no,
       wave_no,
       plan_action,
       plan_status,
       COUNT(*) AS cnt
FROM MIG_P2_COMPAT_PLAN
WHERE stage_no = 'P2_STAGE04'
  AND wave_no = 'WAVE_01'
GROUP BY stage_no, wave_no, plan_action, plan_status
ORDER BY plan_action, plan_status;

PROMPT === 3) P3 final archive ===
SELECT stage_no,
       wave_no,
       reg_done_cnt,
       py_switch_done_cnt,
       compat_ready_cnt,
       overall_status,
       note
FROM MIG_P3_FINAL_ARCH
WHERE stage_no = 'P3_STAGE01'
  AND wave_no = 'WAVE_01';

SELECT batch_no,
       action_type,
       execute_status,
       COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P3_STAGE01'
GROUP BY batch_no, action_type, execute_status
ORDER BY batch_no, action_type, execute_status;

PROMPT === 4) One-line release gate ===
SELECT CASE
         WHEN EXISTS (
           SELECT 1 FROM MIG_P3_FINAL_ARCH
           WHERE stage_no = 'P3_STAGE01'
             AND wave_no = 'WAVE_01'
             AND overall_status = 'DONE'
         ) THEN 'READY_FOR_RELEASE'
         ELSE 'HOLD'
       END AS release_gate
FROM dual;

EXIT;
