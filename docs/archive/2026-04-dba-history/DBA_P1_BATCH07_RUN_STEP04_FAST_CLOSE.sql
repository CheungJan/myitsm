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
    raise_application_error(-20281, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 收口前置门禁（一次性快速收口） ===
DECLARE
  v_done_cnt      NUMBER := 0;
  v_snapshot_cnt  NUMBER := 0;
  v_step2_cnt     NUMBER := 0;
  v_step3_s_cnt   NUMBER := 0;
  v_step3_r_cnt   NUMBER := 0;
BEGIN
  SELECT COUNT(*) INTO v_done_cnt
  FROM MIG_P1_OBJECT_WORKPACK
  WHERE batch_no = 'P1_BATCH07'
    AND wave_no = 'WAVE_01'
    AND status = 'DONE';

  SELECT COUNT(*) INTO v_snapshot_cnt
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH07'
    AND action_type = 'SNAPSHOT'
    AND execute_status = 'READY';

  SELECT COUNT(*) INTO v_step2_cnt
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH07'
    AND action_type = 'STEP2_BULK_MIGRATE'
    AND execute_status = 'DONE';

  SELECT COUNT(*) INTO v_step3_s_cnt
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH07'
    AND action_type = 'STEP3_SAMPLE_VERIFY'
    AND execute_status = 'DONE';

  SELECT COUNT(*) INTO v_step3_r_cnt
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH07'
    AND action_type = 'STEP3_ROLLBACK_ASSET'
    AND execute_status = 'READY';

  IF v_done_cnt = 0 THEN
    raise_application_error(-20282, 'BATCH07 DONE object cnt=0');
  END IF;

  IF v_snapshot_cnt != v_done_cnt OR v_step2_cnt != v_done_cnt THEN
    raise_application_error(-20283,
      'precheck failed: snapshot=' || v_snapshot_cnt || ', step2=' || v_step2_cnt || ', done=' || v_done_cnt);
  END IF;

  IF v_step3_s_cnt < 10 OR v_step3_r_cnt < 10 THEN
    raise_application_error(-20284,
      'precheck failed: step3 sample/rollback too small, sample=' || v_step3_s_cnt || ', rollback=' || v_step3_r_cnt);
  END IF;
END;
/

PROMPT === 2) 一次性快速收口状态回写 ===
UPDATE MIG_P1_OBJECT_WORKPACK
SET verify_rule = 'FAST_CLOSE_MIN_CHECK',
    updated_at = SYSDATE
WHERE batch_no = 'P1_BATCH07'
  AND wave_no = 'WAVE_01'
  AND status = 'DONE';
/

MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH07' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP4_FAST_CLOSE' AS action_type,
         'DONE' AS execute_status,
         'fast close by full-load parity + minimal sample + rollback asset ready' AS note
  FROM MIG_P1_OBJECT_WORKPACK
  WHERE batch_no = 'P1_BATCH07'
    AND wave_no = 'WAVE_01'
    AND status = 'DONE'
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

PROMPT === 3) BATCH07 快速收口汇总 ===
SELECT status, COUNT(*) AS cnt
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH07'
GROUP BY status
ORDER BY status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH07'
  AND action_type IN ('SNAPSHOT', 'STEP2_BULK_MIGRATE', 'STEP3_SAMPLE_VERIFY', 'STEP3_ROLLBACK_ASSET', 'STEP4_FAST_CLOSE')
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
