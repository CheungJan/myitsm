SET PAGESIZE 200;
SET LINESIZE 220;

COLUMN category FORMAT A30;

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
  SELECT b.object_name,
         b.object_type,
         d.governance_tag,
         d.domain_name,
         CASE
           WHEN d.object_name IS NULL THEN 'baseline_only_unmapped'
           WHEN d.governance_tag = UNISTR('\4FDD\7559') THEN 'mapped_keep'
           WHEN d.governance_tag = UNISTR('\5F85\8FC1\79FB') THEN 'mapped_migrate'
           WHEN d.governance_tag = UNISTR('\5F85\4E0B\7EBF') THEN 'mapped_deprecate'
           ELSE 'mapped_other'
         END AS category,
         CASE
           WHEN REGEXP_LIKE(b.object_name, '^TIT') THEN 1
           WHEN REGEXP_LIKE(b.object_name, '^PLAN_|^TMM22') THEN 2
           WHEN REGEXP_LIKE(b.object_name, '^TWH') THEN 3
           WHEN REGEXP_LIKE(b.object_name, '^TMM') THEN 4
           WHEN REGEXP_LIKE(b.object_name, '^TPC|^TQC|^TSL') THEN 5
           ELSE 9
         END AS p1_priority
  FROM baseline b
  LEFT JOIN dict_data d
    ON d.object_name = b.object_name
   AND d.object_type = b.object_type
)
SELECT category, COUNT(*) AS cnt
FROM joined
GROUP BY category
ORDER BY category;

PROMPT === P1 candidate priority summary (keep+migrate in baseline) ===
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
  SELECT b.object_name,
         b.object_type,
         d.governance_tag,
         d.domain_name,
         CASE
           WHEN d.object_name IS NULL THEN 'baseline_only_unmapped'
           WHEN d.governance_tag = UNISTR('\4FDD\7559') THEN 'mapped_keep'
           WHEN d.governance_tag = UNISTR('\5F85\8FC1\79FB') THEN 'mapped_migrate'
           WHEN d.governance_tag = UNISTR('\5F85\4E0B\7EBF') THEN 'mapped_deprecate'
           ELSE 'mapped_other'
         END AS category,
         CASE
           WHEN REGEXP_LIKE(b.object_name, '^TIT') THEN 1
           WHEN REGEXP_LIKE(b.object_name, '^PLAN_|^TMM22') THEN 2
           WHEN REGEXP_LIKE(b.object_name, '^TWH') THEN 3
           WHEN REGEXP_LIKE(b.object_name, '^TMM') THEN 4
           WHEN REGEXP_LIKE(b.object_name, '^TPC|^TQC|^TSL') THEN 5
           ELSE 9
         END AS p1_priority
  FROM baseline b
  LEFT JOIN dict_data d
    ON d.object_name = b.object_name
   AND d.object_type = b.object_type
)
SELECT p1_priority, COUNT(*) AS cnt
FROM joined
WHERE category IN ('mapped_keep', 'mapped_migrate')
GROUP BY p1_priority
ORDER BY p1_priority;

PROMPT === dictionary objects missing in baseline ===
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
)
SELECT COUNT(*) AS dict_missing_cnt
FROM dict_data d
LEFT JOIN baseline b
  ON b.object_name = d.object_name
 AND b.object_type = d.object_type
WHERE b.object_name IS NULL
  AND d.governance_tag IN (UNISTR('\4FDD\7559'), UNISTR('\5F85\8FC1\79FB'));

EXIT;
