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
    raise_application_error(-20431, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 主线切回门禁：DEPRECATE10 必须完成 ===
DECLARE
  v_done_cnt NUMBER;
BEGIN
  SELECT COUNT(*)
    INTO v_done_cnt
    FROM MIG_P1_BATCH_LOG
   WHERE batch_no = 'P1_DEPRECATE10'
     AND action_type = 'STEP7_CLOSEOUT_ARCHIVE'
     AND execute_status = 'DONE';

  IF v_done_cnt = 0 THEN
    raise_application_error(-20432, 'DEPRECATE10 not done, cannot resume P2/P3 mainline');
  END IF;
END;
/

PROMPT === 2) 回写 P2 主线恢复登记 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P2_STAGE00' AS batch_no,
         'MAINLINE' AS object_type,
         'P2_P3_RESUME' AS object_name,
         'STEP0_RESUME_GATE' AS action_type,
         'READY' AS execute_status,
         'mainline resumed after DEPRECATE10 closeout' AS note
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

PROMPT === 3) 摘要 ===
SELECT batch_no, action_type, execute_status, note
FROM MIG_P1_BATCH_LOG
WHERE batch_no IN ('P1_DEPRECATE10', 'P2_STAGE00')
ORDER BY batch_no, action_type;

EXIT;
