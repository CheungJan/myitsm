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
    raise_application_error(-20481, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Gate check for full-chain closeout ===
DECLARE
  v_reg_done NUMBER;
  v_py_done NUMBER;
  v_cp_ready NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_reg_done
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P2_STAGE02'
    AND action_type = 'STEP2_REGRESSION_EXEC'
    AND execute_status = 'DONE';

  SELECT COUNT(*) INTO v_py_done
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P2_STAGE03'
    AND action_type = 'STEP3_PY_SWITCH_DONE'
    AND execute_status = 'DONE';

  SELECT COUNT(*) INTO v_cp_ready
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P2_STAGE04'
    AND action_type = 'STEP4_COMPAT_PLAN_READY'
    AND execute_status = 'READY';

  IF v_reg_done = 0 OR v_py_done = 0 OR v_cp_ready = 0 THEN
    raise_application_error(-20482, 'P2 chain not complete for P3_STAGE01 closeout');
  END IF;
END;
/

PROMPT === 2) Ensure P3 archive table exists ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_FINAL_ARCH (
      stage_no           VARCHAR2(30) NOT NULL,
      wave_no            VARCHAR2(30) NOT NULL,
      reg_done_cnt       NUMBER       NOT NULL,
      py_switch_done_cnt NUMBER       NOT NULL,
      compat_ready_cnt   NUMBER       NOT NULL,
      overall_status     VARCHAR2(20) NOT NULL,
      note               VARCHAR2(400),
      updated_at         DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_FINAL_ARCH PRIMARY KEY (stage_no, wave_no)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 3) Archive full-chain result ===
MERGE INTO MIG_P3_FINAL_ARCH t
USING (
  SELECT 'P3_STAGE01' AS stage_no,
         'WAVE_01' AS wave_no,
         (SELECT COUNT(*) FROM MIG_P1_BATCH_LOG
           WHERE batch_no = 'P2_STAGE02'
             AND action_type = 'STEP2_REGRESSION_EXEC'
             AND execute_status = 'DONE') AS reg_done_cnt,
         (SELECT COUNT(*) FROM MIG_P1_BATCH_LOG
           WHERE batch_no = 'P2_STAGE03'
             AND action_type = 'STEP3_PY_SWITCH_DONE'
             AND execute_status = 'DONE') AS py_switch_done_cnt,
         (SELECT COUNT(*) FROM MIG_P1_BATCH_LOG
           WHERE batch_no = 'P2_STAGE04'
             AND action_type = 'STEP4_COMPAT_PLAN_READY'
             AND execute_status = 'READY') AS compat_ready_cnt,
         'DONE' AS overall_status,
         'full-chain archived after P2 mainline completion' AS note
  FROM dual
) s
ON (
  t.stage_no = s.stage_no
  AND t.wave_no = s.wave_no
)
WHEN MATCHED THEN
  UPDATE SET
    t.reg_done_cnt = s.reg_done_cnt,
    t.py_switch_done_cnt = s.py_switch_done_cnt,
    t.compat_ready_cnt = s.compat_ready_cnt,
    t.overall_status = s.overall_status,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    stage_no, wave_no, reg_done_cnt, py_switch_done_cnt, compat_ready_cnt,
    overall_status, note, updated_at
  )
  VALUES (
    s.stage_no, s.wave_no, s.reg_done_cnt, s.py_switch_done_cnt, s.compat_ready_cnt,
    s.overall_status, s.note, SYSDATE
  );
/

PROMPT === 4) Write P3 mainline log ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE01' AS batch_no,
         'MAINLINE' AS object_type,
         'FINAL_ARCHIVE' AS object_name,
         'STEP1_FINAL_ARCHIVE' AS action_type,
         'DONE' AS execute_status,
         'p3 full-chain closeout archived' AS note
  FROM dual
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

PROMPT === 5) Summary ===
SELECT stage_no, wave_no, reg_done_cnt, py_switch_done_cnt, compat_ready_cnt, overall_status
FROM MIG_P3_FINAL_ARCH
WHERE stage_no = 'P3_STAGE01'
  AND wave_no = 'WAVE_01';

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P3_STAGE01'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
