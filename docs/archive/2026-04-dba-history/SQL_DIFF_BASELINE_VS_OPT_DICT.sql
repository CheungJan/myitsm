SET PAGESIZE 200;
SET LINESIZE 220;
SET VERIFY OFF;
SET FEEDBACK ON;

COLUMN object_name FORMAT A45;
COLUMN governance_tag FORMAT A14;
COLUMN domain_name FORMAT A20;
COLUMN diff_type FORMAT A28;

PROMPT === 0) 当前会话校验 ===
SELECT SYS_CONTEXT('USERENV','SERVICE_NAME') AS service_name,
       SYS_CONTEXT('USERENV','SESSION_USER') AS session_user
FROM dual;

PROMPT === 1) 创建三方整合台账表（首次执行） ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE DICT_OPTIMIZED_OBJECTS (
      object_name      VARCHAR2(128) NOT NULL,
      object_type      VARCHAR2(30)  DEFAULT ''TABLE'' NOT NULL,
      governance_tag   VARCHAR2(20)  NOT NULL,
      domain_name      VARCHAR2(100),
      source_note      VARCHAR2(400),
      updated_at       DATE DEFAULT SYSDATE,
      CONSTRAINT PK_DICT_OPTIMIZED_OBJECTS PRIMARY KEY (object_name, object_type)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 导入前检查：若台账为空，请先导入优化字典 ===
SELECT COUNT(*) AS dict_rows FROM DICT_OPTIMIZED_OBJECTS;

PROMPT === 3) 基线对象（CCGL_MIG 当前 Schema）===
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
SELECT 'BASELINE_ONLY' AS diff_type,
       b.object_type,
       b.object_name,
       CAST(NULL AS VARCHAR2(14)) AS governance_tag,
       CAST(NULL AS VARCHAR2(20)) AS domain_name
FROM baseline b
LEFT JOIN dict_data d
  ON d.object_name = b.object_name
 AND d.object_type = b.object_type
WHERE d.object_name IS NULL
ORDER BY b.object_type, b.object_name;

PROMPT === 4) 字典要求存在但基线缺失 ===
WITH baseline AS (
  SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
  UNION ALL
  SELECT view_name  AS object_name, 'VIEW'  AS object_type FROM user_views
),
dict_data AS (
  SELECT UPPER(object_name) AS object_name,
         UPPER(object_type) AS object_type,
         UPPER(governance_tag) AS governance_tag,
         domain_name
  FROM DICT_OPTIMIZED_OBJECTS
)
SELECT 'DICT_MISSING_IN_BASELINE' AS diff_type,
       d.object_type,
       d.object_name,
       d.governance_tag,
       d.domain_name
FROM dict_data d
LEFT JOIN baseline b
  ON b.object_name = d.object_name
 AND b.object_type = d.object_type
WHERE b.object_name IS NULL
  AND d.governance_tag IN (
    UNISTR('\4FDD\7559'),
    UNISTR('\5F85\8FC1\79FB')
  )
ORDER BY d.governance_tag, d.object_type, d.object_name;

PROMPT === 5) 已存在但标记待下线对象 ===
WITH baseline AS (
  SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
  UNION ALL
  SELECT view_name  AS object_name, 'VIEW'  AS object_type FROM user_views
),
dict_data AS (
  SELECT UPPER(object_name) AS object_name,
         UPPER(object_type) AS object_type,
         UPPER(governance_tag) AS governance_tag,
         domain_name
  FROM DICT_OPTIMIZED_OBJECTS
)
SELECT 'BASELINE_CANDIDATE_DEPRECATE' AS diff_type,
       d.object_type,
       d.object_name,
       d.governance_tag,
       d.domain_name
FROM dict_data d
JOIN baseline b
  ON b.object_name = d.object_name
 AND b.object_type = d.object_type
WHERE d.governance_tag = UNISTR('\5F85\4E0B\7EBF')
ORDER BY d.object_type, d.object_name;

PROMPT === 6) 分类汇总 ===
WITH baseline AS (
  SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
  UNION ALL
  SELECT view_name  AS object_name, 'VIEW'  AS object_type FROM user_views
),
dict_data AS (
  SELECT UPPER(object_name) AS object_name,
         UPPER(object_type) AS object_type,
         UPPER(governance_tag) AS governance_tag
  FROM DICT_OPTIMIZED_OBJECTS
)
SELECT NVL(d.governance_tag, UNISTR('\672A\5165\5B57\5178')) AS governance_tag,
       COUNT(*) AS object_count
FROM baseline b
LEFT JOIN dict_data d
  ON d.object_name = b.object_name
 AND d.object_type = b.object_type
GROUP BY NVL(d.governance_tag, UNISTR('\672A\5165\5B57\5178'))
ORDER BY 1;

EXIT;
