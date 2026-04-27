SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 200;
SET LINESIZE 220;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20081, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 写入批次日志（应用灰度窗口就绪） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no,
         'CONTROL' AS object_type,
         'APP_GRAY_WINDOW' AS object_name,
         'STEP4_APP_WINDOW_READY' AS action_type,
         'READY' AS execute_status,
         'shadow monitor passed; app gray window can start' AS note
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

PROMPT === 2) 就绪状态摘要 ===
SELECT action_type, execute_status, note, executed_at
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
  AND object_name = 'APP_GRAY_WINDOW'
ORDER BY executed_at DESC;

EXIT;
