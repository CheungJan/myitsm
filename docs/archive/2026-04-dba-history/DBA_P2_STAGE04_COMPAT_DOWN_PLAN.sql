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
    raise_application_error(-20471, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Gate check: TASK3_COMPAT_DOWN must be READY ===
DECLARE
  v_status VARCHAR2(20);
BEGIN
  SELECT task_status
    INTO v_status
    FROM MIG_P2_STAGE_CHECK
   WHERE stage_no = 'P2_STAGE01'
     AND task_no = 'TASK3_COMPAT_DOWN';

  IF v_status <> 'READY' THEN
    raise_application_error(-20472, 'TASK3_COMPAT_DOWN is not READY');
  END IF;
END;
/

PROMPT === 2) Ensure compat plan table exists ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P2_COMPAT_PLAN (
      stage_no            VARCHAR2(30)  NOT NULL,
      wave_no             VARCHAR2(30)  NOT NULL,
      source_object_type  VARCHAR2(30)  NOT NULL,
      source_object_name  VARCHAR2(128) NOT NULL,
      plan_action         VARCHAR2(30)  NOT NULL,
      plan_status         VARCHAR2(20)  NOT NULL,
      rollback_required   VARCHAR2(10)  NOT NULL,
      note                VARCHAR2(400),
      updated_at          DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P2_COMP_PLAN PRIMARY KEY (
        stage_no, wave_no, source_object_type, source_object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 3) Build compat down plan (non-destructive) ===
MERGE INTO MIG_P2_COMPAT_PLAN t
USING (
  SELECT 'P2_STAGE04' AS stage_no,
         'WAVE_01' AS wave_no,
         p.source_object_type,
         p.source_object_name,
         'COMPAT_DOWN_PLAN' AS plan_action,
         'READY' AS plan_status,
         'YES' AS rollback_required,
         'plan only, no destructive execution' AS note
  FROM MIG_P1_DEPRECATE_EXEC_PLAN p
  WHERE p.batch_no = 'P1_DEPRECATE06'
    AND p.wave_no = 'WAVE_06'
    AND p.plan_action = 'PLAN_DECOM_ONLY'
    AND p.plan_status = 'READY'
) s
ON (
  t.stage_no = s.stage_no
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
    stage_no, wave_no, source_object_type, source_object_name,
    plan_action, plan_status, rollback_required, note, updated_at
  )
  VALUES (
    s.stage_no, s.wave_no, s.source_object_type, s.source_object_name,
    s.plan_action, s.plan_status, s.rollback_required, s.note, SYSDATE
  );
/

PROMPT === 4) Write P2_STAGE04 log and update task status ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P2_STAGE04' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP4_COMPAT_PLAN_READY' AS action_type,
         'READY' AS execute_status,
         'compat down planning only' AS note
  FROM MIG_P2_COMPAT_PLAN
  WHERE stage_no = 'P2_STAGE04'
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

MERGE INTO MIG_P2_STAGE_CHECK t
USING (
  SELECT 'P2_STAGE01' AS stage_no,
         'TASK3_COMPAT_DOWN' AS task_no,
         'DONE' AS task_status,
         'updated by P2_STAGE04 compat down planning' AS note
  FROM dual
) s
ON (
  t.stage_no = s.stage_no
  AND t.task_no = s.task_no
)
WHEN MATCHED THEN
  UPDATE SET t.task_status = s.task_status, t.note = s.note, t.updated_at = SYSDATE;
/

PROMPT === 5) Summary ===
SELECT plan_action, plan_status, COUNT(*) AS cnt
FROM MIG_P2_COMPAT_PLAN
WHERE stage_no = 'P2_STAGE04'
  AND wave_no = 'WAVE_01'
GROUP BY plan_action, plan_status
ORDER BY plan_action, plan_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P2_STAGE04'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

SELECT task_no, task_status, note
FROM MIG_P2_STAGE_CHECK
WHERE stage_no = 'P2_STAGE01'
  AND task_no = 'TASK3_COMPAT_DOWN';

EXIT;
