SET ECHO ON;
SET PAGESIZE 300;
SET LINESIZE 260;

PROMPT === P3_STAGE10 分类口径报表（只读） ===

WITH obj_all AS (
  SELECT 'TABLE' AS object_type, table_name AS object_name FROM user_tables
  UNION ALL
  SELECT 'VIEW' AS object_type, view_name AS object_name FROM user_views
),
cat AS (
  SELECT c.object_type,
         c.object_name,
         c.candidate_type,
         CASE
           WHEN EXISTS (
             SELECT 1 FROM obj_all a
             WHERE a.object_type = c.object_type
               AND a.object_name = c.object_name
           ) THEN 'Y'
           ELSE 'N'
         END AS exists_now
  FROM MIG_P3_L0_TRIM_CAND c
  WHERE c.stage_no='P3_STAGE05'
    AND c.wave_no='WAVE_01'
)
SELECT candidate_type,
       exists_now,
       COUNT(*) AS cnt
FROM cat
GROUP BY candidate_type, exists_now
ORDER BY candidate_type, exists_now;

PROMPT === L1 目标对象概览 ===
SELECT governance_tag, COUNT(*) AS cnt
FROM MIG_P3_L1_OBJECT_SET
WHERE stage_no='P3_STAGE02'
  AND wave_no='WAVE_01'
  AND freeze_status='FROZEN'
GROUP BY governance_tag
ORDER BY governance_tag;

PROMPT === 仍存在的 TRIM_CANDIDATE（前50） ===
SELECT object_type, object_name, reason
FROM MIG_P3_L0_TRIM_CAND
WHERE stage_no='P3_STAGE05'
  AND wave_no='WAVE_01'
  AND candidate_type='TRIM_CANDIDATE'
  AND EXISTS (
    SELECT 1 FROM (
      SELECT 'TABLE' AS object_type, table_name AS object_name FROM user_tables
      UNION ALL
      SELECT 'VIEW' AS object_type, view_name AS object_name FROM user_views
    ) a
    WHERE a.object_type = MIG_P3_L0_TRIM_CAND.object_type
      AND a.object_name = MIG_P3_L0_TRIM_CAND.object_name
  )
ORDER BY object_type, object_name
FETCH FIRST 50 ROWS ONLY;

EXIT;
