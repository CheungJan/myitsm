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
    raise_application_error(-20066, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 核验关键对象状态（读切换后） ===
SELECT object_name, object_type, status
FROM user_objects
WHERE object_name IN (
  'ITSM_CORE_TIMEPOINT_RULE',
  'ITSM_CORE_PLAN_CUSTOMER_XREF',
  'ITSM_CORE_LIABILITY',
  'ITSM_CORE_LIABILITY_DTL',
  'ITSM_CORE_TIMEPOINT_RULE_V',
  'ITSM_CORE_PLAN_BIZ_V',
  'TIT01_TIMEPOINT_CUST',
  'PLAN_BIZ_V'
)
ORDER BY object_type, object_name;

PROMPT === 2) 核验回退资产可用性（快照表） ===
SELECT table_name, num_rows
FROM user_tables
WHERE table_name IN ('TIT01_TIMEPOINT_CUST_B01_T', 'PLAN_BIZ_V_B01_T')
ORDER BY table_name;

SELECT 'TIT01_TIMEPOINT_CUST_B01_T' AS asset_name, COUNT(*) AS row_count
FROM TIT01_TIMEPOINT_CUST_B01_T
UNION ALL
SELECT 'PLAN_BIZ_V_B01_T', COUNT(*) FROM PLAN_BIZ_V_B01_T;

PROMPT === 3) 核验批次前置步骤是否完成 ===
SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

PROMPT === 4) 写切换前总判定（仅判定，不做写切换，Step3.3） ===
SELECT
  CASE
    WHEN SUM(CASE WHEN action_type = 'RUN_STEP01' AND execute_status = 'DONE' THEN cnt ELSE 0 END) >= 2
     AND SUM(CASE WHEN action_type = 'RUN_STEP02' AND execute_status = 'DONE' THEN cnt ELSE 0 END) >= 2
     AND SUM(CASE WHEN action_type IN ('RUN_STEP03', 'STEP3_1_READINESS') AND execute_status = 'DONE' THEN cnt ELSE 0 END) >= 2
     AND SUM(CASE WHEN action_type IN ('RUN_STEP04', 'STEP3_2_READ_CUTOVER') AND execute_status = 'DONE' THEN cnt ELSE 0 END) >= 2
    THEN 'WRITE_GATE_READY'
    ELSE 'WRITE_GATE_BLOCKED'
  END AS write_gate_decision
FROM (
  SELECT action_type, execute_status, COUNT(*) AS cnt
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH01'
  GROUP BY action_type, execute_status
);

PROMPT === 5) 写入批次日志（Step3.3 Gate） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no,
         'CONTROL' AS object_type,
         'WRITE_GATE' AS object_name,
         'STEP3_3_WRITE_GATE' AS action_type,
         'CHECKED' AS execute_status,
         'write gate checklist executed' AS note
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

EXIT;
