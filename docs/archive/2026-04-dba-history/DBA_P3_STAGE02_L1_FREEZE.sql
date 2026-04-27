SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 300;
SET LINESIZE 260;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) Safety gate: only run on CCGL_MIG ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20501, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Ensure L1 freeze table exists ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_L1_OBJECT_SET (
      stage_no             VARCHAR2(30)  NOT NULL,
      wave_no              VARCHAR2(30)  NOT NULL,
      source_object_type   VARCHAR2(30)  NOT NULL,
      source_object_name   VARCHAR2(128) NOT NULL,
      target_object_name   VARCHAR2(128),
      governance_tag       VARCHAR2(30),
      freeze_status        VARCHAR2(20)  NOT NULL,
      updated_at           DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_L1_OBJ_SET PRIMARY KEY (
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

PROMPT === 2) Freeze L1 object set (KEEP + MIGRATE) ===
MERGE INTO MIG_P3_L1_OBJECT_SET t
USING (
  SELECT 'P3_STAGE02' AS stage_no,
         'WAVE_01' AS wave_no,
         w.source_object_type,
         w.source_object_name,
         w.target_object_name,
         d.governance_tag,
         'FROZEN' AS freeze_status
  FROM (
    SELECT source_object_type,
           source_object_name,
           MAX(target_object_name) AS target_object_name
    FROM MIG_P1_OBJECT_WORKPACK
    WHERE status = 'DONE'
      AND source_object_type IN ('TABLE', 'VIEW')
    GROUP BY source_object_type, source_object_name
  ) w
  JOIN DICT_OPTIMIZED_OBJECTS d
    ON UPPER(d.object_type) = w.source_object_type
   AND UPPER(d.object_name) = w.source_object_name
  WHERE d.governance_tag IN (UNISTR('\4FDD\7559'), UNISTR('\5F85\8FC1\79FB'))
) s
ON (
  t.stage_no = s.stage_no
  AND t.wave_no = s.wave_no
  AND t.source_object_type = s.source_object_type
  AND t.source_object_name = s.source_object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.target_object_name = s.target_object_name,
    t.governance_tag = s.governance_tag,
    t.freeze_status = s.freeze_status,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    stage_no, wave_no, source_object_type, source_object_name,
    target_object_name, governance_tag, freeze_status, updated_at
  )
  VALUES (
    s.stage_no, s.wave_no, s.source_object_type, s.source_object_name,
    s.target_object_name, s.governance_tag, s.freeze_status, SYSDATE
  );
/

PROMPT === 3) Write P3_STAGE02 log ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE02' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP2_L1_FREEZE' AS action_type,
         'DONE' AS execute_status,
         'l1 simplified object set frozen' AS note
  FROM MIG_P3_L1_OBJECT_SET
  WHERE stage_no = 'P3_STAGE02'
    AND wave_no = 'WAVE_01'
    AND freeze_status = 'FROZEN'
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

PROMPT === 4) Summary ===
SELECT freeze_status, COUNT(*) AS cnt
FROM MIG_P3_L1_OBJECT_SET
WHERE stage_no = 'P3_STAGE02'
  AND wave_no = 'WAVE_01'
GROUP BY freeze_status
ORDER BY freeze_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P3_STAGE02'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
