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
    raise_application_error(-20371, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 审阅结果回写（仅状态，不执行下线） ===
MERGE INTO MIG_P1_DEP_REVIEW_DEC t
USING (
  SELECT d.batch_no,
         d.wave_no,
         d.source_object_type,
         d.source_object_name,
         CASE
           WHEN REGEXP_LIKE(d.source_object_name, '(^TMP_|_TMP$|_BAK$|_BK$|^OLD_|_OLD$|_HIS$|_HIST$|_TEST$|^ZZ_)')
                AND NVL(dep.ref_cnt, 0) = 0
             THEN 'APPROVED'
           ELSE 'REJECTED'
         END AS decision,
         CASE
           WHEN REGEXP_LIKE(d.source_object_name, '(^TMP_|_TMP$|_BAK$|_BK$|^OLD_|_OLD$|_HIS$|_HIST$|_TEST$|^ZZ_)')
                AND NVL(dep.ref_cnt, 0) = 0
             THEN 'approved by heuristic: temp-like name and no local dependency'
           ELSE 'rejected by gate: dependency exists or naming rule not strong enough'
         END AS decision_note
  FROM MIG_P1_DEP_REVIEW_DEC d
  LEFT JOIN (
    SELECT referenced_type,
           referenced_name,
           COUNT(*) AS ref_cnt
    FROM USER_DEPENDENCIES
    GROUP BY referenced_type, referenced_name
  ) dep
    ON dep.referenced_type = d.source_object_type
   AND dep.referenced_name = d.source_object_name
  WHERE d.batch_no = 'P1_DEPRECATE04'
    AND d.wave_no = 'WAVE_04'
    AND d.decision = 'TO_CONFIRM'
) s
ON (
  t.batch_no = s.batch_no
  AND t.wave_no = s.wave_no
  AND t.source_object_type = s.source_object_type
  AND t.source_object_name = s.source_object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.decision = s.decision,
    t.decision_note = s.decision_note,
    t.updated_at = SYSDATE;
/

PROMPT === 2) 写入批次日志（DEPRECATE05 审阅回写完成） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE05' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP2_REVIEW_DECISION_DONE' AS action_type,
         'DONE' AS execute_status,
         'review decision written back, no decommission executed' AS note
  FROM MIG_P1_DEP_REVIEW_DEC
  WHERE batch_no = 'P1_DEPRECATE04'
    AND wave_no = 'WAVE_04'
    AND decision IN ('APPROVED', 'REJECTED')
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

PROMPT === 3) DEPRECATE05 摘要 ===
SELECT decision, COUNT(*) AS cnt
FROM MIG_P1_DEP_REVIEW_DEC
WHERE batch_no = 'P1_DEPRECATE04'
  AND wave_no = 'WAVE_04'
GROUP BY decision
ORDER BY decision;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_DEPRECATE05'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
