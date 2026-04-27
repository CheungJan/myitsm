SET ECHO OFF;
SET FEEDBACK OFF;
SET HEADING OFF;
SET PAGESIZE 0;
SET LINESIZE 32767;
SET TRIMSPOOL ON;
SET SQLBLANKLINES ON;

SPOOL e:\project\myitsm\src\docs\FINAL_DB_DICTIONARY.md

PROMPT # 数据库字典（精简后最终版）
PROMPT 
PROMPT ## 1. 总体介绍
PROMPT 
PROMPT - 编写目的：说明精简后数据库结构，供开发、实施、运维统一参考。
PROMPT - 适用范围：当前 `CCGL_MIG` 精简后库（业务对象 + 最小治理留痕对象）。
PROMPT - 目录参考：`docs/仓储系统数据字典原始版本.doc`。
PROMPT 
PROMPT ## 2. 概述
PROMPT 
PROMPT | 项 | 值 |
PROMPT |---|---|
SELECT '| 优化状态 | ' ||
       CASE
         WHEN EXISTS (
           SELECT 1
           FROM MIG_P3_FINAL_NAME_EXEC
           WHERE stage_no='P3_STAGE11'
             AND wave_no='WAVE_01'
             AND exec_action='DROP_TARGET_DUP'
             AND exec_status='DONE'
         )
          AND NOT EXISTS (
           SELECT 1
           FROM MIG_P3_FINAL_NAME_EXEC
           WHERE stage_no='P3_STAGE11'
             AND wave_no='WAVE_01'
             AND exec_status='FAILED'
         )
         THEN 'OPTIMIZED_DONE'
         ELSE 'OPTIMIZED_NOT_DONE'
       END || ' |'
FROM dual;
SELECT '| 业务表数量 | ' || COUNT(*) || ' |'
FROM user_tables
WHERE table_name NOT LIKE 'MIG\_%' ESCAPE '\';
SELECT '| 业务视图数量 | ' || COUNT(*) || ' |'
FROM user_views
WHERE view_name NOT LIKE 'MIG\_%' ESCAPE '\';
SELECT '| MIG留痕表数量 | ' || COUNT(*) || ' |'
FROM user_tables
WHERE table_name LIKE 'MIG\_%' ESCAPE '\';
PROMPT 
PROMPT ## 3. 逻辑设计
PROMPT 
PROMPT ### 3.1 数据表实体清单
PROMPT 
PROMPT | 表名 | 程序作用说明 |
PROMPT |---|---|
SELECT '| ' || t.table_name || ' | ' ||
       REPLACE(REPLACE(REPLACE(NVL(tc.comments, ''), '|', '\|'), CHR(13), ' '), CHR(10), ' ') || ' |'
FROM user_tables t
LEFT JOIN user_tab_comments tc
  ON tc.table_name = t.table_name
WHERE t.table_name NOT LIKE 'MIG\_%' ESCAPE '\'
ORDER BY t.table_name;
PROMPT 
PROMPT ### 3.2 视图实体清单
PROMPT 
PROMPT | 视图名 | 说明 |
PROMPT |---|---|
SELECT '| ' || v.view_name || ' | ' ||
       REPLACE(REPLACE(REPLACE(NVL(tc.comments, ''), '|', '\|'), CHR(13), ' '), CHR(10), ' ') || ' |'
FROM user_views v
LEFT JOIN user_tab_comments tc
  ON tc.table_name = v.view_name
WHERE v.view_name NOT LIKE 'MIG\_%' ESCAPE '\'
ORDER BY v.view_name;
PROMPT 
PROMPT ### 3.3 字段级数据字典（按表分组）
PROMPT 
WITH tbl AS (
  SELECT t.table_name,
         NVL(tc.comments, '') AS table_comment
  FROM user_tables t
  LEFT JOIN user_tab_comments tc
    ON tc.table_name = t.table_name
  WHERE t.table_name NOT LIKE 'MIG\_%' ESCAPE '\'
),
pk_cols AS (
  SELECT ucc.table_name,
         ucc.column_name
  FROM user_constraints uc
  JOIN user_cons_columns ucc
    ON uc.owner = ucc.owner
   AND uc.constraint_name = ucc.constraint_name
  WHERE uc.constraint_type = 'P'
),
col_rows AS (
  SELECT c.table_name,
         c.column_id,
         CASE WHEN pk.column_name IS NOT NULL THEN 'P' ELSE '' END AS pk_flag,
         c.column_name,
         CASE
           WHEN c.data_type IN ('VARCHAR2','CHAR','NVARCHAR2','NCHAR') THEN c.data_type || '(' || c.data_length || ')'
           WHEN c.data_type = 'NUMBER' AND c.data_precision IS NULL THEN 'NUMBER'
           WHEN c.data_type = 'NUMBER' AND c.data_scale IS NULL THEN 'NUMBER(' || c.data_precision || ')'
           WHEN c.data_type = 'NUMBER' THEN 'NUMBER(' || c.data_precision || ',' || c.data_scale || ')'
           ELSE c.data_type
         END AS data_type_fmt,
         DECODE(c.nullable, 'N', 'N', 'Y') AS nullable_flag,
         NVL(cc.comments, '') AS column_comment
  FROM user_tab_columns c
  JOIN tbl t
    ON t.table_name = c.table_name
  LEFT JOIN pk_cols pk
    ON pk.table_name = c.table_name
   AND pk.column_name = c.column_name
  LEFT JOIN user_col_comments cc
    ON cc.table_name = c.table_name
   AND cc.column_name = c.column_name
)
SELECT line
FROM (
  SELECT t.table_name,
         1 AS grp_order,
         0 AS col_order,
         '| DB对象标识 | DB对象名称 | 制作人 | 制作日期 |' AS line
  FROM tbl t
  UNION ALL
  SELECT t.table_name,
         2 AS grp_order,
         0 AS col_order,
         '| --- | --- | --- | --- |' AS line
  FROM tbl t
  UNION ALL
  SELECT t.table_name,
         3 AS grp_order,
         0 AS col_order,
         '| ' || t.table_name || ' | ' || REPLACE(REPLACE(REPLACE(t.table_comment, '|', '\|'), CHR(13), ' '), CHR(10), ' ') || ' |  |  |' AS line
  FROM tbl t
  UNION ALL
  SELECT t.table_name,
         4 AS grp_order,
         0 AS col_order,
         '| 说明：' || REPLACE(REPLACE(REPLACE(t.table_comment, '|', '\|'), CHR(13), ' '), CHR(10), ' ') || ' |  |  |  |' AS line
  FROM tbl t
  UNION ALL
  SELECT t.table_name,
         5 AS grp_order,
         0 AS col_order,
         '| 表项标识 | 字段名 | 类型 | 说明 |' AS line
  FROM tbl t
  UNION ALL
  SELECT t.table_name,
         6 AS grp_order,
         0 AS col_order,
         '| --- | --- | --- | --- |' AS line
  FROM tbl t
  UNION ALL
  SELECT c.table_name,
         7 AS grp_order,
         c.column_id AS col_order,
         '| ' || c.pk_flag || ' | ' || c.column_name || ' | ' || c.data_type_fmt || ' | ' || REPLACE(REPLACE(REPLACE(c.column_comment, '|', '\|'), CHR(13), ' '), CHR(10), ' ') || ' |' AS line
  FROM col_rows c
  UNION ALL
  SELECT t.table_name,
         8 AS grp_order,
         0 AS col_order,
         '' AS line
  FROM tbl t
)
ORDER BY table_name, grp_order, col_order;
PROMPT 
PROMPT ## 4. 备注
PROMPT 
PROMPT - 本文档由当前数据库元数据自动生成。
PROMPT - 若结构变更，请重新执行导出并更新本文档。

SPOOL OFF;
EXIT;
