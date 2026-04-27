SET PAGESIZE 200;
SET LINESIZE 240;

COLUMN p1_priority FORMAT 999;
COLUMN object_type FORMAT A6;
COLUMN object_name FORMAT A45;
COLUMN governance_tag FORMAT A12;
COLUMN domain_name FORMAT A14;

WITH baseline AS (
  SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
  UNION ALL
  SELECT view_name  AS object_name, 'VIEW'  AS object_type FROM user_views
),
dict_data AS (
  SELECT UPPER(object_name) AS object_name,
         UPPER(object_type) AS object_type,
         governance_tag,
         domain_name
  FROM DICT_OPTIMIZED_OBJECTS
),
joined AS (
  SELECT d.object_type,
         d.object_name,
         d.governance_tag,
         d.domain_name,
         CASE
           WHEN REGEXP_LIKE(d.object_name, '^TIT') THEN 1
           WHEN REGEXP_LIKE(d.object_name, '^PLAN_|^TMM22') THEN 2
           WHEN REGEXP_LIKE(d.object_name, '^TWH') THEN 3
           WHEN REGEXP_LIKE(d.object_name, '^TMM') THEN 4
           WHEN REGEXP_LIKE(d.object_name, '^TPC|^TQC|^TSL') THEN 5
           ELSE 9
         END AS p1_priority
  FROM dict_data d
  JOIN baseline b
    ON b.object_name = d.object_name
   AND b.object_type = d.object_type
  WHERE d.governance_tag IN (
    UNISTR('\4FDD\7559'),
    UNISTR('\5F85\8FC1\79FB')
  )
)
SELECT p1_priority,
       object_type,
       object_name,
       governance_tag,
       domain_name
FROM joined
ORDER BY p1_priority, object_type, object_name;

EXIT;
