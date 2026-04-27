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
    raise_application_error(-20079, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 写入批次日志（Step3.3 写切换回退） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no,
         'CONTROL' AS object_type,
         'WRITE_CUTOVER_TIT02' AS object_name,
         'STEP3_3_WRITE_CUTOVER' AS action_type,
         'ROLLED_BACK' AS execute_status,
         'tit02 write cutover rolled back; app route switch to old path' AS note
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

PROMPT === 2) 回退后摘要 ===
SELECT action_type, execute_status, note, executed_at
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
  AND object_name = 'WRITE_CUTOVER_TIT02'
ORDER BY executed_at DESC;

EXIT;
