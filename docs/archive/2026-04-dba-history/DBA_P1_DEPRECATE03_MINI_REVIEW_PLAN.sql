SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 200;
SET LINESIZE 240;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) Safety gate: only run on CCGL_MIG ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20351, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Ensure review queue table exists ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_DEPRECATE_REVIEW_QUEUE (
      batch_no            VARCHAR2(30)  NOT NULL,
      wave_no             VARCHAR2(30)  NOT NULL,
      source_object_type  VARCHAR2(30)  NOT NULL,
      source_object_name  VARCHAR2(128) NOT NULL,
      review_status       VARCHAR2(20)  NOT NULL,
      review_note         VARCHAR2(400),
      updated_at          DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_DEP_REV_Q PRIMARY KEY (
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

PROMPT === 2) Ensure execution plan table exists ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_DEPRECATE_EXEC_PLAN (
      batch_no            VARCHAR2(30)  NOT NULL,
      wave_no             VARCHAR2(30)  NOT NULL,
      source_object_type  VARCHAR2(30)  NOT NULL,
      source_object_name  VARCHAR2(128) NOT NULL,
      plan_action         VARCHAR2(30)  NOT NULL,
      plan_status         VARCHAR2(20)  NOT NULL,
      rollback_required   VARCHAR2(10)  NOT NULL,
      note                VARCHAR2(400),
      updated_at          DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_DEP_EXEC_PLAN PRIMARY KEY (
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

PROMPT === 3) Build minimal review queue (top 10 from DEPRECATE02) ===
MERGE INTO MIG_P1_DEPRECATE_REVIEW_QUEUE t
USING (
  SELECT 'P1_DEPRECATE03' AS batch_no,
         'WAVE_03' AS wave_no,
         source_object_type,
         source_object_name,
         'PENDING' AS review_status,
         'mini-batch review from DEPRECATE02 top10' AS review_note
  FROM (
    SELECT source_object_type,
           source_object_name,
           ROW_NUMBER() OVER (ORDER BY source_object_type, source_object_name) AS rn
    FROM MIG_P1_DEPRECATE_WORKLIST
    WHERE wave_no = 'WAVE_02'
      AND status = 'PLANNED'
  )
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
    t.review_status = s.review_status,
    t.review_note = s.review_note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    batch_no, wave_no, source_object_type, source_object_name,
    review_status, review_note, updated_at
  )
  VALUES (
    s.batch_no, s.wave_no, s.source_object_type, s.source_object_name,
    s.review_status, s.review_note, SYSDATE
  );
/

PROMPT === 4) Build non-destructive execution plan for same 10 ===
MERGE INTO MIG_P1_DEPRECATE_EXEC_PLAN t
USING (
  SELECT q.batch_no,
         q.wave_no,
         q.source_object_type,
         q.source_object_name,
         'REVIEW_ONLY' AS plan_action,
         'PLANNED' AS plan_status,
         'YES' AS rollback_required,
         'non-destructive plan: confirm owner and usage before any decommission' AS note
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
    t.plan_action = s.plan_action,
    t.plan_status = s.plan_status,
    t.rollback_required = s.rollback_required,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    batch_no, wave_no, source_object_type, source_object_name,
    plan_action, plan_status, rollback_required, note, updated_at
  )
  VALUES (
    s.batch_no, s.wave_no, s.source_object_type, s.source_object_name,
    s.plan_action, s.plan_status, s.rollback_required, s.note, SYSDATE
  );
/

PROMPT === 5) Write batch log for P1_DEPRECATE03 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE03' AS batch_no,
         q.source_object_type AS object_type,
         q.source_object_name AS object_name,
         'SNAPSHOT' AS action_type,
         'READY' AS execute_status,
         'mini-batch review queue prepared' AS note
  FROM MIG_P1_DEPRECATE_REVIEW_QUEUE q
  WHERE q.batch_no = 'P1_DEPRECATE03'
    AND q.wave_no = 'WAVE_03'
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

PROMPT === 6) Summary ===
SELECT review_status, COUNT(*) AS cnt
FROM MIG_P1_DEPRECATE_REVIEW_QUEUE
WHERE batch_no='P1_DEPRECATE03'
  AND wave_no='WAVE_03'
GROUP BY review_status
ORDER BY review_status;

SELECT plan_action, plan_status, COUNT(*) AS cnt
FROM MIG_P1_DEPRECATE_EXEC_PLAN
WHERE batch_no='P1_DEPRECATE03'
  AND wave_no='WAVE_03'
GROUP BY plan_action, plan_status
ORDER BY plan_action, plan_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no='P1_DEPRECATE03'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
