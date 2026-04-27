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
    raise_application_error(-20077, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 写切换门禁（TIT02试点成功 + 最近24小时无异常） ===
DECLARE
  v_total_cnt NUMBER := 0;
  v_bad_cnt   NUMBER := 0;
  v_pilot_ok  NUMBER := 0;
BEGIN
  SELECT COUNT(*),
         SUM(CASE WHEN compare_result IN ('DIFF', 'ERROR') THEN 1 ELSE 0 END)
    INTO v_total_cnt, v_bad_cnt
    FROM MIG_P1_SHADOW_WRITE_LOG
   WHERE batch_no = 'P1_BATCH01'
     AND created_at_utc >= SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '1' DAY;

  SELECT COUNT(*)
    INTO v_pilot_ok
    FROM MIG_P1_SHADOW_WRITE_LOG
   WHERE batch_no = 'P1_BATCH01'
     AND source_object = 'TIT02_LIABILITYREG'
     AND action_type = 'PILOT_LIAB'
     AND compare_result = 'MATCH';

  IF v_total_cnt < 10 OR v_bad_cnt > 0 OR v_pilot_ok = 0 THEN
    raise_application_error(
      -20078,
      'tit02 write cutover blocked: total=' || v_total_cnt || ', bad=' || v_bad_cnt || ', pilot_ok=' || v_pilot_ok
    );
  END IF;
END;
/

PROMPT === 2) 写入批次日志（Step3.3 写切换执行） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no,
         'CONTROL' AS object_type,
         'WRITE_CUTOVER_TIT02' AS object_name,
         'STEP3_3_WRITE_CUTOVER' AS action_type,
         'DONE' AS execute_status,
         'tit02 write cutover approved; app route switch to new path' AS note
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

PROMPT === 3) 切换后摘要 ===
SELECT action_type, execute_status, note, executed_at
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
  AND object_name = 'WRITE_CUTOVER_TIT02'
ORDER BY executed_at DESC;

EXIT;
