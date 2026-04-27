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
    raise_application_error(-20321, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 扩围门禁：STEP0清单READY + STEP1发布DONE ===
DECLARE
  v_step0_ready NUMBER := 0;
  v_step1_done  NUMBER := 0;
BEGIN
  SELECT COUNT(*) INTO v_step0_ready
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no='E_STAGE01'
    AND object_name='APP_SWITCH_CHECKLIST'
    AND action_type='STEP0_CHECKLIST_READY'
    AND execute_status='READY';

  SELECT COUNT(*) INTO v_step1_done
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no='E_STAGE01'
    AND object_name='APP_RELEASE_WINDOW'
    AND action_type='STEP1_RELEASE_EXEC'
    AND execute_status='DONE';

  IF v_step0_ready = 0 OR v_step1_done = 0 THEN
    raise_application_error(-20322, 'scale-out blocked: step0=' || v_step0_ready || ', step1=' || v_step1_done);
  END IF;
END;
/

PROMPT === 2) 写入扩围完成状态 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'E_STAGE01' AS batch_no,
         'CONTROL' AS object_type,
         'APP_SCALE_OUT' AS object_name,
         'STEP2_SCALE_OUT_DONE' AS action_type,
         'DONE' AS execute_status,
         'app scale-out marker recorded after release window execution' AS note
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

PROMPT === 3) E_STAGE01 关键状态 ===
SELECT action_type, execute_status, note, executed_at
FROM MIG_P1_BATCH_LOG
WHERE batch_no='E_STAGE01'
  AND object_name IN ('APP_SWITCH_CHECKLIST','APP_RELEASE_WINDOW','APP_SCALE_OUT')
ORDER BY executed_at DESC;

EXIT;
