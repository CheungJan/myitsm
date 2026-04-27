SET ECHO OFF;
SET FEEDBACK OFF;
SET HEADING ON;
SET PAGESIZE 50000;
SET LINESIZE 32767;
SET LONG 2000000;
SET LONGCHUNKSIZE 2000000;
SET TRIMSPOOL ON;
SET VERIFY OFF;
SET TERMOUT ON;
SET COLSEP ',';

PROMPT === 导出1/3：L1对象总览 ===
SPOOL L1_OBJECT_OVERVIEW.csv
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
       l1.freeze_status,
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
SPOOL OFF;

PROMPT === 导出2/3：L1表字段字典 ===
SPOOL L1_TABLE_COLUMNS.csv
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
SPOOL OFF;

PROMPT === 导出3/3：L1视图定义摘要 ===
SPOOL L1_VIEW_DEFINITION.csv
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
       DBMS_LOB.SUBSTR(DBMS_METADATA.GET_DDL('VIEW', v.view_name, USER), 2000, 1)
         AS view_sql_preview
FROM user_views v
JOIN l1_view
  ON l1_view.view_name = v.view_name
ORDER BY v.view_name;
SPOOL OFF;

SET FEEDBACK ON;

PROMPT === 导出完成：L1_OBJECT_OVERVIEW.csv / L1_TABLE_COLUMNS.csv / L1_VIEW_DEFINITION.csv ===
EXIT;
