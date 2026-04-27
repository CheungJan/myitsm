SET ECHO ON;
SET SERVEROUTPUT ON;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20131, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 工作包表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_OBJECT_WORKPACK (
      batch_no            VARCHAR2(30)  NOT NULL,
      wave_no             VARCHAR2(30)  NOT NULL,
      source_object_type  VARCHAR2(30)  NOT NULL,
      source_object_name  VARCHAR2(128) NOT NULL,
      target_object_name  VARCHAR2(128) NOT NULL,
      migration_strategy  VARCHAR2(200) NOT NULL,
      verify_rule         VARCHAR2(500),
      status              VARCHAR2(20)  DEFAULT ''PLANNED'' NOT NULL,
      updated_at          DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_MIG_P1_OBJECT_WORKPACK PRIMARY KEY (
        batch_no, wave_no, source_object_type, source_object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 轻量自动抽取（仅入包，不切换） ===
MERGE INTO MIG_P1_OBJECT_WORKPACK t
USING (
  WITH baseline AS (
    SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
    UNION ALL
    SELECT view_name AS object_name, 'VIEW' AS object_type FROM user_views
  ),
  dict_data AS (
    SELECT UPPER(object_name) AS object_name,
           UPPER(object_type) AS object_type,
           governance_tag
    FROM DICT_OPTIMIZED_OBJECTS
  ),
  prior_used AS (
    SELECT source_object_name AS object_name, source_object_type AS object_type
    FROM MIG_P1_OBJECT_WORKPACK
    WHERE batch_no IN ('P1_BATCH01', 'P1_BATCH02')
  ),
  candidates AS (
    SELECT d.object_type,
           d.object_name,
           CASE
             WHEN REGEXP_LIKE(d.object_name, '^TIT') THEN 1
             WHEN REGEXP_LIKE(d.object_name, '^PLAN_|^TMM22') THEN 2
             ELSE 9
           END AS p1_priority
    FROM dict_data d
    JOIN baseline b
      ON b.object_name = d.object_name
     AND b.object_type = d.object_type
    LEFT JOIN prior_used p
      ON p.object_name = d.object_name
     AND p.object_type = d.object_type
    WHERE d.governance_tag IN (UNISTR('\4FDD\7559'), UNISTR('\5F85\8FC1\79FB'))
      AND p.object_name IS NULL
  ),
  limited_candidates AS (
    SELECT object_type,
           object_name,
           p1_priority,
           ROW_NUMBER() OVER (ORDER BY p1_priority, object_type, object_name) AS rn
    FROM candidates
    WHERE p1_priority IN (1, 2)
  )
  SELECT 'P1_BATCH03' AS batch_no,
         'WAVE_01' AS wave_no,
         object_type AS source_object_type,
         object_name AS source_object_name,
         'TBD_TARGET_OBJECT' AS target_object_name,
         'DISCOVERY_THEN_MIGRATE' AS migration_strategy,
         'MAPPING_CONFIRMED_AND_MIN_CHECK' AS verify_rule
  FROM limited_candidates
  WHERE rn <= 10
) s
ON (
  t.batch_no = s.batch_no
  AND t.wave_no = s.wave_no
  AND t.source_object_type = s.source_object_type
  AND t.source_object_name = s.source_object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.migration_strategy = s.migration_strategy,
    t.verify_rule = s.verify_rule,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    batch_no, wave_no, source_object_type, source_object_name,
    target_object_name, migration_strategy, verify_rule, status, updated_at
  )
  VALUES (
    s.batch_no, s.wave_no, s.source_object_type, s.source_object_name,
    s.target_object_name, s.migration_strategy, s.verify_rule, 'PLANNED', SYSDATE
  );
/

PROMPT === 3) BATCH03 快照日志（轻量启动） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH03' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'SNAPSHOT' AS action_type,
         'READY' AS execute_status,
         'light start: extracted to workpack only' AS note
  FROM MIG_P1_OBJECT_WORKPACK
  WHERE batch_no = 'P1_BATCH03'
    AND wave_no = 'WAVE_01'
) s
ON (
  t.batch_no = s.batch_no
  AND t.object_type = s.object_type
  AND t.object_name = s.object_name
  AND t.action_type = s.action_type
)
WHEN MATCHED THEN
  UPDATE SET t.execute_status = s.execute_status, t.note = s.note, t.executed_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (batch_no, object_type, object_name, action_type, execute_status, note, executed_at)
  VALUES (s.batch_no, s.object_type, s.object_name, s.action_type, s.execute_status, s.note, SYSDATE);
/

PROMPT === 4) BATCH03 工作包与快照汇总 ===
SELECT source_object_type, source_object_name, target_object_name, migration_strategy, status
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH03'
  AND wave_no = 'WAVE_01'
ORDER BY source_object_type, source_object_name;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH03'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
