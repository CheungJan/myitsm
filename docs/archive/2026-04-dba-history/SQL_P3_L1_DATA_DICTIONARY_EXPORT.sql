SET ECHO ON;
SET PAGESIZE 500;
SET LINESIZE 320;
SET LONG 200000;
SET LONGCHUNKSIZE 200000;

PROMPT === 会话信息 ===
SELECT SYS_CONTEXT('USERENV', 'SERVICE_NAME') AS service_name,
       SYS_CONTEXT('USERENV', 'SESSION_USER') AS session_user
FROM dual;

PROMPT === L1 对象总览（P3_STAGE02 冻结口径） ===
WITH l1 AS (
  SELECT source_object_type,
         source_object_name,
         target_object_name,
         governance_tag,
         freeze_status
  FROM MIG_P3_L1_OBJECT_SET
  WHERE stage_no = 'P3_STAGE02'
    AND wave_no = 'WAVE_01'
    AND freeze_status = 'FROZEN'
),
obj AS (
  SELECT object_name,
         object_type
  FROM user_objects
  WHERE object_type IN ('TABLE', 'VIEW')
)
SELECT l1.source_object_type,
       l1.source_object_name,
       l1.target_object_name,
       l1.governance_tag,
       CASE
         WHEN EXISTS (
           SELECT 1
           FROM obj o
           WHERE o.object_name = NVL(l1.target_object_name, l1.source_object_name)
             AND o.object_type = l1.source_object_type
         ) THEN 'Y'
         ELSE 'N'
       END AS exists_now
FROM l1
ORDER BY l1.source_object_type, l1.source_object_name;

PROMPT === L1 表级数据字典（字段粒度） ===
WITH l1_table AS (
  SELECT DISTINCT
         NVL(target_object_name, source_object_name) AS object_name,
         governance_tag
  FROM MIG_P3_L1_OBJECT_SET
  WHERE stage_no = 'P3_STAGE02'
    AND wave_no = 'WAVE_01'
    AND freeze_status = 'FROZEN'
    AND source_object_type = 'TABLE'
),
pk_col AS (
  SELECT ucc.table_name,
         ucc.column_name
  FROM user_constraints uc
  JOIN user_cons_columns ucc
    ON uc.constraint_name = ucc.constraint_name
   AND uc.owner = ucc.owner
  WHERE uc.constraint_type = 'P'
)
SELECT c.table_name,
       tc.comments AS table_comment,
       l1_table.governance_tag,
       c.column_id,
       c.column_name,
       cc.comments AS column_comment,
       c.data_type,
       c.data_length,
       c.data_precision,
       c.data_scale,
       c.nullable,
       c.data_default,
       CASE WHEN pk_col.column_name IS NOT NULL THEN 'Y' ELSE 'N' END AS is_pk
FROM user_tab_columns c
JOIN l1_table
  ON l1_table.object_name = c.table_name
LEFT JOIN user_tab_comments tc
  ON tc.table_name = c.table_name
LEFT JOIN user_col_comments cc
  ON cc.table_name = c.table_name
 AND cc.column_name = c.column_name
LEFT JOIN pk_col
  ON pk_col.table_name = c.table_name
 AND pk_col.column_name = c.column_name
ORDER BY c.table_name, c.column_id;

PROMPT === L1 视图清单与定义摘要 ===
WITH l1_view AS (
  SELECT DISTINCT
         NVL(target_object_name, source_object_name) AS view_name,
         governance_tag
  FROM MIG_P3_L1_OBJECT_SET
  WHERE stage_no = 'P3_STAGE02'
    AND wave_no = 'WAVE_01'
    AND freeze_status = 'FROZEN'
    AND source_object_type = 'VIEW'
)
SELECT v.view_name,
       l1_view.governance_tag,
       SUBSTR(v.text, 1, 1000) AS view_sql_preview
FROM user_views v
JOIN l1_view
  ON l1_view.view_name = v.view_name
ORDER BY v.view_name;

PROMPT === L1 对象类型统计 ===
SELECT source_object_type,
       governance_tag,
       COUNT(*) AS cnt
FROM MIG_P3_L1_OBJECT_SET
WHERE stage_no = 'P3_STAGE02'
  AND wave_no = 'WAVE_01'
  AND freeze_status = 'FROZEN'
GROUP BY source_object_type, governance_tag
ORDER BY source_object_type, governance_tag;

EXIT;
