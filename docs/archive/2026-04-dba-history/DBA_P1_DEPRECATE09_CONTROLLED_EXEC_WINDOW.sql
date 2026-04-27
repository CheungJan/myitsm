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
    raise_application_error(-20411, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) DEPRECATE09 执行窗口判定（仅受控执行，不做自动破坏性动作） ===
DECLARE
  v_dry_run_flag VARCHAR2(1);
  v_exec_flag    VARCHAR2(1);
  v_mode         VARCHAR2(30);
BEGIN
  SELECT dry_run_flag, exec_flag
    INTO v_dry_run_flag, v_exec_flag
    FROM MIG_P1_DEP_EXEC_CTRL
   WHERE batch_no = 'P1_DEPRECATE07'
     AND wave_no = 'WAVE_07';

  IF v_dry_run_flag = 'N' AND v_exec_flag = 'Y' THEN
    v_mode := 'EXEC_WINDOW_OPEN';
  ELSE
    v_mode := 'EXEC_WINDOW_HOLD';
  END IF;

  MERGE INTO MIG_P1_DEP_EXEC_RES t
  USING (
    SELECT 'P1_DEPRECATE09' AS batch_no,
           'WAVE_09' AS wave_no,
           r.source_object_type,
           r.source_object_name,
           CASE
             WHEN v_mode = 'EXEC_WINDOW_OPEN' THEN 'READY_FOR_MANUAL_EXEC'
             ELSE 'SKIPPED_BY_CTRL'
           END AS exec_status,
           CASE
             WHEN v_mode = 'EXEC_WINDOW_OPEN'
               THEN 'execution window open, waiting DBA manual execution'
             ELSE 'execution window hold, control switch not opened'
           END AS exec_note
      FROM MIG_P1_DEP_EXEC_RES r
     WHERE r.batch_no = 'P1_DEPRECATE08'
       AND r.wave_no = 'WAVE_08'
  ) s
  ON (
    t.batch_no = s.batch_no
    AND t.wave_no = s.wave_no
    AND t.source_object_type = s.source_object_type
    AND t.source_object_name = s.source_object_name
  )
  WHEN MATCHED THEN
    UPDATE SET
      t.exec_status = s.exec_status,
      t.exec_note = s.exec_note,
      t.updated_at = SYSDATE
  WHEN NOT MATCHED THEN
    INSERT (
      batch_no, wave_no, source_object_type, source_object_name,
      exec_status, exec_note, updated_at
    )
    VALUES (
      s.batch_no, s.wave_no, s.source_object_type, s.source_object_name,
      s.exec_status, s.exec_note, SYSDATE
    );
END;
/

PROMPT === 2) 批次日志回写（DEPRECATE09） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE09' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP6_EXEC_WINDOW' AS action_type,
         CASE
           WHEN exec_status = 'READY_FOR_MANUAL_EXEC' THEN 'READY'
           ELSE 'HOLD'
         END AS execute_status,
         exec_note AS note
    FROM MIG_P1_DEP_EXEC_RES
   WHERE batch_no = 'P1_DEPRECATE09'
     AND wave_no = 'WAVE_09'
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

PROMPT === 3) DEPRECATE09 摘要 ===
SELECT exec_status, COUNT(*) AS cnt
FROM MIG_P1_DEP_EXEC_RES
WHERE batch_no = 'P1_DEPRECATE09'
  AND wave_no = 'WAVE_09'
GROUP BY exec_status
ORDER BY exec_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_DEPRECATE09'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
