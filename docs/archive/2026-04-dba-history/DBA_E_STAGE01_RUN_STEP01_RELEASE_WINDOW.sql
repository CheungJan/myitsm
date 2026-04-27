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
    raise_application_error(-20311, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 发布门禁：E_STAGE01 清单READY + 24h影子写无异常 ===
DECLARE
  v_checklist_ready NUMBER := 0;
  v_total_cnt       NUMBER := 0;
  v_bad_cnt         NUMBER := 0;
BEGIN
  SELECT COUNT(*)
    INTO v_checklist_ready
    FROM MIG_P1_BATCH_LOG
   WHERE batch_no = 'E_STAGE01'
     AND object_name = 'APP_SWITCH_CHECKLIST'
     AND action_type = 'STEP0_CHECKLIST_READY'
     AND execute_status = 'READY';

  SELECT COUNT(*),
         SUM(CASE WHEN compare_result IN ('DIFF', 'ERROR') THEN 1 ELSE 0 END)
    INTO v_total_cnt, v_bad_cnt
    FROM MIG_P1_SHADOW_WRITE_LOG
   WHERE created_at_utc >= SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '1' DAY;

  IF v_checklist_ready = 0 OR v_bad_cnt > 0 THEN
    raise_application_error(
      -20312,
      'release blocked: checklist=' || v_checklist_ready || ', total=' || v_total_cnt || ', bad=' || v_bad_cnt
    );
  END IF;
END;
/

PROMPT === 2) 写入发布窗口执行状态 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'E_STAGE01' AS batch_no,
         'CONTROL' AS object_type,
         'APP_RELEASE_WINDOW' AS object_name,
         'STEP1_RELEASE_EXEC' AS action_type,
         'DONE' AS execute_status,
         'release window executed: checklist ready and shadow green in last 24h' AS note
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

PROMPT === 3) 发布窗口状态摘要 ===
SELECT action_type, execute_status, note, executed_at
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'E_STAGE01'
  AND object_name IN ('APP_SWITCH_CHECKLIST', 'APP_RELEASE_WINDOW')
ORDER BY executed_at DESC;

EXIT;
