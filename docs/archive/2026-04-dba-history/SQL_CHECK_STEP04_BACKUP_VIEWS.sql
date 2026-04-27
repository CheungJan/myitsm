SET ECHO ON;
SET PAGESIZE 200;
SET LINESIZE 220;

COLUMN view_name FORMAT A32;
COLUMN status FORMAT A10;
COLUMN text_preview FORMAT A120;

SELECT o.object_name AS view_name,
       o.status,
       SUBSTR(v.text, 1, 120) AS text_preview
FROM user_objects o
JOIN user_views v
  ON o.object_name = v.view_name
WHERE o.object_name IN ('TIT01_TIMEPOINT_CUST_B01', 'PLAN_BIZ_V_B01')
ORDER BY o.object_name;

SELECT 'TIT01_TIMEPOINT_CUST_B01' AS view_name, COUNT(*) AS row_count
FROM TIT01_TIMEPOINT_CUST_B01
UNION ALL
SELECT 'PLAN_BIZ_V_B01', COUNT(*) FROM PLAN_BIZ_V_B01;

EXIT;
