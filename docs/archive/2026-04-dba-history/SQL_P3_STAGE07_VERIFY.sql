SET ECHO ON;
SET PAGESIZE 300;
SET LINESIZE 260;

PROMPT === P3_STAGE07 执行结果核验 ===

PROMPT === 1) 执行状态汇总 ===
SELECT exec_status, COUNT(*) AS cnt
FROM MIG_P3_L0_TRIM_EXEC
WHERE stage_no='P3_STAGE07'
  AND wave_no='WAVE_01'
GROUP BY exec_status
ORDER BY exec_status;

PROMPT === 2) 失败原因Top10 ===
SELECT note, COUNT(*) AS cnt
FROM MIG_P3_L0_TRIM_EXEC
WHERE stage_no='P3_STAGE07'
  AND wave_no='WAVE_01'
  AND exec_status='FAILED'
GROUP BY note
ORDER BY cnt DESC, note;

PROMPT === 3) 当前对象规模（CCGL_MIG） ===
SELECT 'TABLE' AS object_type, COUNT(*) AS cnt FROM user_tables
UNION ALL
SELECT 'VIEW' AS object_type, COUNT(*) AS cnt FROM user_views;

PROMPT === 4) 已生成回滚资产 ===
SELECT COUNT(*) AS rollback_assets
FROM MIG_P3_L0_TRIM_RB
WHERE stage_no='P3_STAGE07'
  AND wave_no='WAVE_01';

EXIT;
