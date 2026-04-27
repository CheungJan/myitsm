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
    raise_application_error(-20091, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 工作包表（不存在则创建） ===
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

PROMPT === 2) BATCH02 工作包登记（仅 mapped_migrate 且基线存在） ===
MERGE INTO MIG_P1_OBJECT_WORKPACK t
USING (
  WITH baseline AS (
    SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
    UNION ALL
    SELECT view_name  AS object_name, 'VIEW'  AS object_type FROM user_views
  ),
  migrate_set AS (
    SELECT UPPER(d.object_type) AS object_type,
           UPPER(d.object_name) AS object_name
    FROM DICT_OPTIMIZED_OBJECTS d
    JOIN baseline b
      ON b.object_name = UPPER(d.object_name)
     AND b.object_type = UPPER(d.object_type)
    WHERE d.governance_tag = UNISTR('\5F85\8FC1\79FB')
  )
  SELECT 'P1_BATCH02' AS batch_no,
         'WAVE_01' AS wave_no,
         object_type AS source_object_type,
         object_name AS source_object_name,
         CASE object_name
           WHEN 'PLAN_BIZ_V' THEN 'ITSM_CORE_PLAN_BIZ_V'
           WHEN 'TIT01_TIMEPOINT_CUST' THEN 'ITSM_CORE_TIMEPOINT_RULE_V'
           ELSE 'TBD_TARGET_OBJECT'
         END AS target_object_name,
         CASE
           WHEN object_type = 'VIEW' THEN 'COMPAT_VIEW_REWRITE'
           ELSE 'MIGRATE_TO_CORE_MODEL'
         END AS migration_strategy,
         CASE
           WHEN object_type = 'VIEW' THEN 'VIEW_VALID_AND_SAMPLE_QUERY'
           ELSE 'COUNT_CHECK_AND_KEY_RULE'
         END AS verify_rule
  FROM migrate_set
) s
ON (
  t.batch_no = s.batch_no
  AND t.wave_no = s.wave_no
  AND t.source_object_type = s.source_object_type
  AND t.source_object_name = s.source_object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.target_object_name = s.target_object_name,
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

PROMPT === 3) BATCH02 快照写入批次日志 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  WITH baseline AS (
    SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
    UNION ALL
    SELECT view_name  AS object_name, 'VIEW'  AS object_type FROM user_views
  ),
  migrate_set AS (
    SELECT UPPER(d.object_type) AS object_type,
           UPPER(d.object_name) AS object_name
    FROM DICT_OPTIMIZED_OBJECTS d
    JOIN baseline b
      ON b.object_name = UPPER(d.object_name)
     AND b.object_type = UPPER(d.object_type)
    WHERE d.governance_tag = UNISTR('\5F85\8FC1\79FB')
  )
  SELECT 'P1_BATCH02' AS batch_no,
         object_type,
         object_name,
         'SNAPSHOT' AS action_type,
         'READY' AS execute_status,
         'mapped_migrate snapshot for batch02' AS note
  FROM migrate_set
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

PROMPT === 4) 结果查看：BATCH02 对象清单 ===
SELECT batch_no,
       wave_no,
       source_object_type,
       source_object_name,
       target_object_name,
       migration_strategy,
       status
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH02'
  AND wave_no = 'WAVE_01'
ORDER BY source_object_type, source_object_name;

PROMPT === 5) 结果查看：BATCH02 快照状态 ===
SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH02'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
