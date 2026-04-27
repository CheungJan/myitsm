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
    raise_application_error(-20231, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 前置核验：BATCH01 遗留 6 对象一致性检查 ===
DECLARE
  v_src_cnt NUMBER;
  v_tgt_cnt NUMBER;
  v_status  VARCHAR2(20);
BEGIN
  FOR r IN (
    SELECT 'PLAN_CUST' AS src_name, 'ITSM_CORE_PLAN_CUSTOMER_XREF' AS tgt_name FROM dual
    UNION ALL SELECT 'TIT01_TIMEPOINT_AREA', 'ITSM_CORE_TIMEPOINT_RULE' FROM dual
    UNION ALL SELECT 'TIT02_LIABILITYREG', 'ITSM_CORE_LIABILITY' FROM dual
    UNION ALL SELECT 'TIT02_LIABILITYREGDT', 'ITSM_CORE_LIABILITY_DTL' FROM dual
  ) LOOP
    EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM ' || r.src_name INTO v_src_cnt;
    EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM ' || r.tgt_name INTO v_tgt_cnt;

    IF v_src_cnt != v_tgt_cnt THEN
      raise_application_error(-20232, 'count mismatch: ' || r.src_name || '(' || v_src_cnt || ') vs ' || r.tgt_name || '(' || v_tgt_cnt || ')');
    END IF;
  END LOOP;

  FOR v IN (
    SELECT 'PLAN_BIZ_V' AS view_name FROM dual
    UNION ALL SELECT 'ITSM_CORE_PLAN_BIZ_V' FROM dual
    UNION ALL SELECT 'TIT01_TIMEPOINT_CUST' FROM dual
    UNION ALL SELECT 'ITSM_CORE_TIMEPOINT_RULE_V' FROM dual
  ) LOOP
    SELECT status
      INTO v_status
      FROM user_objects
     WHERE object_type = 'VIEW'
       AND object_name = v.view_name;

    IF v_status <> 'VALID' THEN
      raise_application_error(-20233, 'view invalid: ' || v.view_name || ', status=' || v_status);
    END IF;
  END LOOP;
END;
/

PROMPT === 2) 回写 BATCH01 遗留对象状态为 DONE ===
UPDATE MIG_P1_OBJECT_WORKPACK
   SET status = 'DONE',
       updated_at = SYSDATE
 WHERE batch_no = 'P1_BATCH01'
   AND wave_no = 'WAVE_01'
   AND source_object_name IN (
     'PLAN_CUST',
     'TIT01_TIMEPOINT_AREA',
     'TIT02_LIABILITYREG',
     'TIT02_LIABILITYREGDT',
     'PLAN_BIZ_V',
     'TIT01_TIMEPOINT_CUST'
   )
   AND status = 'PLANNED';
/

PROMPT === 3) 写入批次日志（STEP16_REMAINING_RECONCILE） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no, 'TABLE' AS object_type, 'PLAN_CUST' AS object_name, 'STEP16_REMAINING_RECONCILE' AS action_type, 'DONE' AS execute_status, 'reconciled by src/tgt count parity' AS note FROM dual
  UNION ALL SELECT 'P1_BATCH01', 'TABLE', 'TIT01_TIMEPOINT_AREA', 'STEP16_REMAINING_RECONCILE', 'DONE', 'reconciled by src/tgt count parity' FROM dual
  UNION ALL SELECT 'P1_BATCH01', 'TABLE', 'TIT02_LIABILITYREG', 'STEP16_REMAINING_RECONCILE', 'DONE', 'reconciled by src/tgt count parity' FROM dual
  UNION ALL SELECT 'P1_BATCH01', 'TABLE', 'TIT02_LIABILITYREGDT', 'STEP16_REMAINING_RECONCILE', 'DONE', 'reconciled by src/tgt count parity' FROM dual
  UNION ALL SELECT 'P1_BATCH01', 'VIEW',  'PLAN_BIZ_V', 'STEP16_REMAINING_RECONCILE', 'DONE', 'reconciled by view valid check' FROM dual
  UNION ALL SELECT 'P1_BATCH01', 'VIEW',  'TIT01_TIMEPOINT_CUST', 'STEP16_REMAINING_RECONCILE', 'DONE', 'reconciled by view valid check' FROM dual
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

PROMPT === 4) BATCH01 收口汇总 ===
SELECT status, COUNT(*) AS cnt
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH01'
GROUP BY status
ORDER BY status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
