SET PAGESIZE 200;
SET LINESIZE 240;

PROMPT === 1) 关键里程碑完成情况（数据库优化主线） ===
SELECT action_type,
       execute_status,
       MAX(executed_at) AS last_time,
       COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
  AND action_type IN (
    'RUN_STEP01',
    'RUN_STEP02',
    'STEP3_1_READINESS',
    'STEP3_2_READ_CUTOVER',
    'STEP3_3_WRITE_GATE',
    'STEP3_3_WRITE_GRAY',
    'STEP3_3_WRITE_CUTOVER',
    'STEP0_DIFF_SNAPSHOT',
    'STEP4_APP_WINDOW_READY'
  )
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

PROMPT === 2) 影子写一致性（最近24小时） ===
WITH recent_data AS (
  SELECT COUNT(*) AS total_cnt,
         SUM(CASE WHEN compare_result = 'MATCH' THEN 1 ELSE 0 END) AS match_cnt,
         SUM(CASE WHEN compare_result IN ('DIFF', 'ERROR') THEN 1 ELSE 0 END) AS bad_cnt
  FROM MIG_P1_SHADOW_WRITE_LOG
  WHERE batch_no = 'P1_BATCH01'
    AND created_at_utc >= SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '1' DAY
)
SELECT total_cnt,
       match_cnt,
       bad_cnt,
       CASE
         WHEN total_cnt = 0 THEN 'NO_TRAFFIC'
         WHEN bad_cnt = 0 THEN 'WRITE_GRAY_READY'
         ELSE 'WRITE_GRAY_BLOCKED'
       END AS write_gray_decision
FROM recent_data;

PROMPT === 3) 首批核心对象数据量 ===
SELECT 'SRC_PLAN_CUST' AS metric_name, COUNT(*) AS metric_value FROM PLAN_CUST
UNION ALL
SELECT 'TGT_PLAN_XREF', COUNT(*) FROM ITSM_CORE_PLAN_CUSTOMER_XREF
UNION ALL
SELECT 'SRC_TIT02_LIABILITYREG', COUNT(*) FROM TIT02_LIABILITYREG
UNION ALL
SELECT 'TGT_ITSM_CORE_LIABILITY', COUNT(*) FROM ITSM_CORE_LIABILITY
UNION ALL
SELECT 'SRC_TIT02_LIABILITYREGDT', COUNT(*) FROM TIT02_LIABILITYREGDT
UNION ALL
SELECT 'TGT_ITSM_CORE_LIABILITY_DTL', COUNT(*) FROM ITSM_CORE_LIABILITY_DTL;

PROMPT === 4) P0 差异快照统计（最新口径） ===
SELECT category, COUNT(*) AS cnt
FROM MIG_P1_OBJECT_DIFF_SNAPSHOT
WHERE snapshot_batch_no = 'P1_BATCH01'
GROUP BY category
ORDER BY category;

PROMPT === 5) 总体进度估算（按10项数据库任务） ===
WITH checkpoints AS (
  SELECT 'RUN_STEP01' AS k FROM dual UNION ALL
  SELECT 'RUN_STEP02' FROM dual UNION ALL
  SELECT 'STEP3_1_READINESS' FROM dual UNION ALL
  SELECT 'STEP3_2_READ_CUTOVER' FROM dual UNION ALL
  SELECT 'STEP3_3_WRITE_GATE' FROM dual UNION ALL
  SELECT 'STEP3_3_WRITE_GRAY' FROM dual UNION ALL
  SELECT 'STEP3_3_WRITE_CUTOVER' FROM dual UNION ALL
  SELECT 'STEP0_DIFF_SNAPSHOT' FROM dual UNION ALL
  SELECT 'STEP4_APP_WINDOW_READY' FROM dual UNION ALL
  SELECT 'APP_ROUTE_SWITCH_DONE' FROM dual
),
done_set AS (
  SELECT DISTINCT action_type
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH01'
    AND execute_status IN ('DONE', 'READY', 'CHECKED')
)
SELECT COUNT(*) AS total_items,
       SUM(CASE WHEN d.action_type IS NOT NULL THEN 1 ELSE 0 END) AS done_items,
       ROUND(SUM(CASE WHEN d.action_type IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS progress_pct
FROM checkpoints c
LEFT JOIN done_set d
  ON d.action_type = c.k;

EXIT;
