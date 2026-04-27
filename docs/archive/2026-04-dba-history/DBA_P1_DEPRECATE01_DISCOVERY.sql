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
    raise_application_error(-20261, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 建立待下线治理工作表（不存在则创建） ===
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

PROMPT === 2) 待下线对象发现与入包（仅登记，不做DDL/DML下线） ===
MERGE INTO MIG_P1_DEPRECATE_WORKLIST t
USING (
  WITH baseline AS (
    SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
    UNION ALL
    SELECT view_name AS object_name, 'VIEW' AS object_type FROM user_views
  )
  SELECT 'WAVE_01' AS wave_no,
         UPPER(d.object_type) AS source_object_type,
         UPPER(d.object_name) AS source_object_name,
         d.governance_tag,
         'PLANNED' AS status,
         'deprecate discovery only, no destructive change' AS note
  FROM DICT_OPTIMIZED_OBJECTS d
  JOIN baseline b
    ON b.object_name = UPPER(d.object_name)
   AND b.object_type = UPPER(d.object_type)
  WHERE d.governance_tag = UNISTR('\5F85\4E0B\7EBF')
) s
ON (
  t.wave_no = s.wave_no
  AND t.source_object_type = s.source_object_type
  AND t.source_object_name = s.source_object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.governance_tag = s.governance_tag,
    t.status = 'PLANNED',
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

PROMPT === 3) 写入治理批次快照日志 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE01' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'SNAPSHOT' AS action_type,
         'READY' AS execute_status,
         'deprecate discovery snapshot only' AS note
  FROM MIG_P1_DEPRECATE_WORKLIST
  WHERE wave_no = 'WAVE_01'
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

PROMPT === 4) 待下线治理摘要 ===
SELECT status, COUNT(*) AS cnt
FROM MIG_P1_DEPRECATE_WORKLIST
WHERE wave_no = 'WAVE_01'
GROUP BY status
ORDER BY status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_DEPRECATE01'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
