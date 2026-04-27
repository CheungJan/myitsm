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
    raise_application_error(-20361, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 人工确认结果表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_DEP_REVIEW_DEC (
      batch_no            VARCHAR2(30)  NOT NULL,
      wave_no             VARCHAR2(30)  NOT NULL,
      source_object_type  VARCHAR2(30)  NOT NULL,
      source_object_name  VARCHAR2(128) NOT NULL,
      decision            VARCHAR2(20)  NOT NULL,
      decision_note       VARCHAR2(400),
      updated_at          DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_DEP_REVIEW_DECISION PRIMARY KEY (
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

PROMPT === 2) 生成最小批次人工确认项（10条） ===
MERGE INTO MIG_P1_DEP_REVIEW_DEC t
USING (
  SELECT 'P1_DEPRECATE04' AS batch_no,
         'WAVE_04' AS wave_no,
         q.source_object_type,
         q.source_object_name,
         'TO_CONFIRM' AS decision,
         'pending business confirmation' AS decision_note
  FROM MIG_P1_DEPRECATE_REVIEW_QUEUE q
  WHERE q.batch_no = 'P1_DEPRECATE03'
    AND q.wave_no = 'WAVE_03'
) s
ON (
  t.batch_no = s.batch_no
  AND t.wave_no = s.wave_no
  AND t.source_object_type = s.source_object_type
  AND t.source_object_name = s.source_object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.decision = s.decision,
    t.decision_note = s.decision_note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    batch_no, wave_no, source_object_type, source_object_name,
    decision, decision_note, updated_at
  )
  VALUES (
    s.batch_no, s.wave_no, s.source_object_type, s.source_object_name,
    s.decision, s.decision_note, SYSDATE
  );
/

PROMPT === 3) 写入批次日志：审阅门禁就绪 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE04' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP1_REVIEW_GATE_READY' AS action_type,
         'READY' AS execute_status,
         'review decision queue prepared' AS note
  FROM MIG_P1_DEP_REVIEW_DEC
  WHERE batch_no = 'P1_DEPRECATE04'
    AND wave_no = 'WAVE_04'
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

PROMPT === 4) DEPRECATE04 摘要 ===
SELECT decision, COUNT(*) AS cnt
FROM MIG_P1_DEP_REVIEW_DEC
WHERE batch_no = 'P1_DEPRECATE04'
  AND wave_no = 'WAVE_04'
GROUP BY decision
ORDER BY decision;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_DEPRECATE04'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
