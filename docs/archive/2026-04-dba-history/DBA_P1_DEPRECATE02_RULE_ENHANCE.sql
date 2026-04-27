SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 200;
SET LINESIZE 240;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20341, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 待下线治理工作表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_DEPRECATE_WORKLIST (
      wave_no             VARCHAR2(30)  NOT NULL,
      source_object_type  VARCHAR2(30)  NOT NULL,
      source_object_name  VARCHAR2(128) NOT NULL,
      governance_tag      VARCHAR2(40)  NOT NULL,
      status              VARCHAR2(20)  DEFAULT ''PLANNED'' NOT NULL,
      note                VARCHAR2(400),
      updated_at          DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_MIG_P1_DEPRECATE_WORKLIST PRIMARY KEY (
        wave_no, source_object_type, source_object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) DEPRECATE02 规则补齐发现（仅登记，不做破坏性变更） ===
MERGE INTO MIG_P1_DEPRECATE_WORKLIST t
USING (
  WITH baseline AS (
    SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
    UNION ALL
    SELECT view_name  AS object_name, 'VIEW'  AS object_type FROM user_views
  ),
  dict_data AS (
    SELECT UPPER(object_name) AS object_name,
           UPPER(object_type) AS object_type,
           governance_tag
    FROM DICT_OPTIMIZED_OBJECTS
  ),
  direct_deprecate AS (
    SELECT 'WAVE_02' AS wave_no,
           b.object_type AS source_object_type,
           b.object_name AS source_object_name,
           d.governance_tag AS governance_tag,
           'PLANNED' AS status,
           'deprecate by dict governance tag' AS note
    FROM baseline b
    JOIN dict_data d
      ON d.object_name = b.object_name
     AND d.object_type = b.object_type
    WHERE d.governance_tag = UNISTR('\5F85\4E0B\7EBF')
  ),
  heuristic_deprecate AS (
    SELECT 'WAVE_02' AS wave_no,
           b.object_type AS source_object_type,
           b.object_name AS source_object_name,
           'RULE_HEURISTIC' AS governance_tag,
           'PLANNED' AS status,
           'deprecate by naming heuristic, review before execution' AS note
    FROM baseline b
    LEFT JOIN dict_data d
      ON d.object_name = b.object_name
     AND d.object_type = b.object_type
    WHERE d.object_name IS NULL
      AND (
        REGEXP_LIKE(b.object_name, '(^TMP_|_TMP$|_BAK$|_BK$|^OLD_|_OLD$|_HIS$|_HIST$|_TEST$|^ZZ_)')
      )
  )
  SELECT * FROM direct_deprecate
  UNION ALL
  SELECT * FROM heuristic_deprecate
) s
ON (
  t.wave_no = s.wave_no
  AND t.source_object_type = s.source_object_type
  AND t.source_object_name = s.source_object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.governance_tag = s.governance_tag,
    t.status = s.status,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    wave_no, source_object_type, source_object_name,
    governance_tag, status, note, updated_at
  )
  VALUES (
    s.wave_no, s.source_object_type, s.source_object_name,
    s.governance_tag, s.status, s.note, SYSDATE
  );
/

PROMPT === 3) 写入批次日志（P1_DEPRECATE02） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE02' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'SNAPSHOT' AS action_type,
         'READY' AS execute_status,
         'deprecate rule-enhanced discovery snapshot only' AS note
  FROM MIG_P1_DEPRECATE_WORKLIST
  WHERE wave_no = 'WAVE_02'
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

PROMPT === 4) DEPRECATE02 摘要 ===
SELECT governance_tag, status, COUNT(*) AS cnt
FROM MIG_P1_DEPRECATE_WORKLIST
WHERE wave_no = 'WAVE_02'
GROUP BY governance_tag, status
ORDER BY governance_tag, status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_DEPRECATE02'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
