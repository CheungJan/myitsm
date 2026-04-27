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
    raise_application_error(-20461, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 门禁校验：P2 回归任务必须完成 ===
DECLARE
  v_reg_status VARCHAR2(20);
BEGIN
  SELECT task_status
    INTO v_reg_status
    FROM MIG_P2_STAGE_CHECK
   WHERE stage_no = 'P2_STAGE01'
     AND task_no = 'TASK1_REGRESSION';

  IF v_reg_status <> 'DONE' THEN
    raise_application_error(-20462, 'TASK1_REGRESSION is not DONE, cannot continue P2_STAGE03');
  END IF;
END;
/

PROMPT === 2) Python 分域切换结果回写（最小口径） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P2_STAGE03' AS batch_no,
         'MAINLINE' AS object_type,
         'PY_DOMAIN_SWITCH' AS object_name,
         'STEP3_PY_SWITCH_DONE' AS action_type,
         'DONE' AS execute_status,
         'python domain switch writeback after regression done' AS note
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

PROMPT === 3) 回写 P2_STAGE01 任务状态（TASK2 完成，TASK3 转 READY） ===
MERGE INTO MIG_P2_STAGE_CHECK t
USING (
  SELECT 'P2_STAGE01' AS stage_no,
         'TASK2_PY_SWITCH' AS task_no,
         'DONE' AS task_status,
         'updated by P2_STAGE03 python switch writeback' AS note
  FROM dual
) s
ON (
  t.stage_no = s.stage_no
  AND t.task_no = s.task_no
)
WHEN MATCHED THEN
  UPDATE SET t.task_status = s.task_status, t.note = s.note, t.updated_at = SYSDATE;
/

MERGE INTO MIG_P2_STAGE_CHECK t
USING (
  SELECT 'P2_STAGE01' AS stage_no,
         'TASK3_COMPAT_DOWN' AS task_no,
         'READY' AS task_status,
         'task1 and task2 done, compat down planning can start' AS note
  FROM dual
) s
ON (
  t.stage_no = s.stage_no
  AND t.task_no = s.task_no
)
WHEN MATCHED THEN
  UPDATE SET t.task_status = s.task_status, t.note = s.note, t.updated_at = SYSDATE;
/

PROMPT === 4) 摘要 ===
SELECT batch_no, action_type, execute_status, note
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P2_STAGE03';

SELECT task_no, task_status, note
FROM MIG_P2_STAGE_CHECK
WHERE stage_no = 'P2_STAGE01'
ORDER BY task_no;

EXIT;
