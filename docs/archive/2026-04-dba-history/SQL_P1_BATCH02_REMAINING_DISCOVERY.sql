SET PAGESIZE 200;
SET LINESIZE 240;

COLUMN view_name FORMAT A40;
COLUMN text_preview FORMAT A120;
COLUMN column_name FORMAT A32;

PROMPT === 1) 源视图是否存在 ===
SELECT view_name
FROM user_views
WHERE view_name IN ('ALL_LIST_V', 'WHCD_ITEM_V')
ORDER BY view_name;

PROMPT === 2) 源视图字段 ===
SELECT table_name AS view_name, column_name, data_type, data_length
FROM user_tab_columns
WHERE table_name IN ('ALL_LIST_V', 'WHCD_ITEM_V')
ORDER BY table_name, column_id;

PROMPT === 3) 候选目标视图（ITSM_CORE） ===
SELECT view_name
FROM user_views
WHERE view_name LIKE 'ITSM_CORE%'
  AND (view_name LIKE '%ALL%' OR view_name LIKE '%WHCD%' OR view_name LIKE '%ITEM%')
ORDER BY view_name;

PROMPT === 4) 候选目标字段 ===
SELECT table_name AS view_name, column_name, data_type, data_length
FROM user_tab_columns
WHERE table_name LIKE 'ITSM_CORE%'
  AND (table_name LIKE '%ALL%' OR table_name LIKE '%WHCD%' OR table_name LIKE '%ITEM%')
ORDER BY table_name, column_id;

EXIT;
