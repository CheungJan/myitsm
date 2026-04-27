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
    raise_application_error(-20381, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 生成 DEPRECATE06 下线执行计划（仅编排，不执行） ===
MERGE INTO MIG_P1_DEPRECATE_EXEC_PLAN t
USING (
  SELECT 'P1_DEPRECATE06' AS batch_no,
         'WAVE_06' AS wave_no,
         d.source_object_type,
         d.source_object_name,
         'PLAN_DECOM_ONLY' AS plan_action,
         'READY' AS plan_status,
         'YES' AS rollback_required,
         'execution plan staged from approved review set, no decommission executed' AS note
  FROM MIG_P1_DEP_REVIEW_DEC d
  WHERE d.batch_no = 'P1_DEPRECATE04'
    AND d.wave_no = 'WAVE_04'
    AND d.decision = 'APPROVED'
) s
ON (
  t.batch_no = s.batch_no
  AND t.wave_no = s.wave_no
  AND t.source_object_type = s.source_object_type
  AND t.source_object_name = s.source_object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.plan_action = s.plan_action,
    t.plan_status = s.plan_status,
    t.rollback_required = s.rollback_required,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    batch_no, wave_no, source_object_type, source_object_name,
    plan_action, plan_status, rollback_required, note, updated_at
  )
  VALUES (
    s.batch_no, s.wave_no, s.source_object_type, s.source_object_name,
    s.plan_action, s.plan_status, s.rollback_required, s.note, SYSDATE
  );
/

PROMPT === 2) 写入批次日志（计划编排完成） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE06' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP3_EXEC_PLAN_READY' AS action_type,
         'READY' AS execute_status,
         'decommission execution plan staged only' AS note
  FROM MIG_P1_DEPRECATE_EXEC_PLAN
  WHERE batch_no = 'P1_DEPRECATE06'
    AND wave_no = 'WAVE_06'
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

PROMPT === 3) DEPRECATE06 摘要 ===
SELECT plan_action, plan_status, COUNT(*) AS cnt
FROM MIG_P1_DEPRECATE_EXEC_PLAN
WHERE batch_no = 'P1_DEPRECATE06'
  AND wave_no = 'WAVE_06'
GROUP BY plan_action, plan_status
ORDER BY plan_action, plan_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_DEPRECATE06'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
