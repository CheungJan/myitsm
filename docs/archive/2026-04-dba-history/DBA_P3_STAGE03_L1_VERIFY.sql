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
    raise_application_error(-20511, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Ensure L1 verify table exists ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_L1_VERIFY (
      stage_no             VARCHAR2(30)  NOT NULL,
      wave_no              VARCHAR2(30)  NOT NULL,
      source_object_type   VARCHAR2(30)  NOT NULL,
      source_object_name   VARCHAR2(128) NOT NULL,
      target_object_name   VARCHAR2(128) NOT NULL,
      row_check            VARCHAR2(10)  NOT NULL,
      exist_check          VARCHAR2(10)  NOT NULL,
      verify_status        VARCHAR2(20)  NOT NULL,
      note                 VARCHAR2(400),
      updated_at           DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_L1_VERIFY PRIMARY KEY (
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

PROMPT === 2) Verify L1 physical landing ===
DECLARE
  v_src_exists NUMBER;
  v_tgt_exists NUMBER;
  v_src_cnt NUMBER;
  v_tgt_cnt NUMBER;
  v_exist_check VARCHAR2(10);
  v_row_check VARCHAR2(10);
  v_verify_status VARCHAR2(20);
  v_note VARCHAR2(400);
BEGIN
  FOR r IN (
    SELECT source_object_type,
           source_object_name,
           target_object_name
    FROM MIG_P3_L1_OBJECT_SET
    WHERE stage_no = 'P3_STAGE02'
      AND wave_no = 'WAVE_01'
      AND freeze_status = 'FROZEN'
      AND target_object_name IS NOT NULL
  ) LOOP
    IF r.source_object_type = 'TABLE' THEN
      SELECT COUNT(*) INTO v_src_exists FROM user_tables WHERE table_name = r.source_object_name;
      SELECT COUNT(*) INTO v_tgt_exists FROM user_tables WHERE table_name = r.target_object_name;
    ELSE
      SELECT COUNT(*) INTO v_src_exists FROM user_objects WHERE object_name = r.source_object_name AND object_type = 'VIEW';
      SELECT COUNT(*) INTO v_tgt_exists FROM user_objects WHERE object_name = r.target_object_name AND object_type = 'VIEW';
    END IF;

    IF v_src_exists > 0 AND v_tgt_exists > 0 THEN
      v_exist_check := 'PASS';
    ELSE
      v_exist_check := 'FAIL';
    END IF;

    IF r.source_object_type = 'TABLE' AND v_exist_check = 'PASS' THEN
      EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM ' || DBMS_ASSERT.SQL_OBJECT_NAME(r.source_object_name) INTO v_src_cnt;
      EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM ' || DBMS_ASSERT.SQL_OBJECT_NAME(r.target_object_name) INTO v_tgt_cnt;
      v_row_check := CASE WHEN v_src_cnt = v_tgt_cnt THEN 'PASS' ELSE 'FAIL' END;
      v_note := 'src=' || v_src_cnt || ', tgt=' || v_tgt_cnt;
    ELSIF r.source_object_type = 'VIEW' THEN
      v_row_check := 'SKIP';
      v_note := 'view object, row check skipped';
    ELSE
      v_row_check := 'FAIL';
      v_note := 'source or target object missing';
    END IF;

    IF v_exist_check = 'PASS' AND v_row_check IN ('PASS', 'SKIP') THEN
      v_verify_status := 'DONE';
    ELSE
      v_verify_status := 'BLOCKED';
    END IF;

    MERGE INTO MIG_P3_L1_VERIFY t
    USING (
      SELECT 'P3_STAGE03' AS stage_no,
             'WAVE_01' AS wave_no,
             r.source_object_type AS source_object_type,
             r.source_object_name AS source_object_name,
             r.target_object_name AS target_object_name,
             v_row_check AS row_check,
             v_exist_check AS exist_check,
             v_verify_status AS verify_status,
             v_note AS note
      FROM dual
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
        t.row_check = s.row_check,
        t.exist_check = s.exist_check,
        t.verify_status = s.verify_status,
        t.note = s.note,
        t.updated_at = SYSDATE
    WHEN NOT MATCHED THEN
      INSERT (
        stage_no, wave_no, source_object_type, source_object_name,
        target_object_name, row_check, exist_check, verify_status, note, updated_at
      )
      VALUES (
        s.stage_no, s.wave_no, s.source_object_type, s.source_object_name,
        s.target_object_name, s.row_check, s.exist_check, s.verify_status, s.note, SYSDATE
      );
  END LOOP;
END;
/

PROMPT === 3) Write P3_STAGE03 log ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE03' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP3_L1_VERIFY' AS action_type,
         verify_status AS execute_status,
         note AS note
  FROM MIG_P3_L1_VERIFY
  WHERE stage_no = 'P3_STAGE03'
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

PROMPT === 4) Summary ===
SELECT verify_status, COUNT(*) AS cnt
FROM MIG_P3_L1_VERIFY
WHERE stage_no = 'P3_STAGE03'
  AND wave_no = 'WAVE_01'
GROUP BY verify_status
ORDER BY verify_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P3_STAGE03'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
