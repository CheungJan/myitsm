SET ECHO ON;
SET SERVEROUTPUT ON;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) Safety gate: only CCGL_MIG service ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20063, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Build compatibility views for read cutover ===
CREATE OR REPLACE VIEW ITSM_CORE_TIMEPOINT_RULE_V AS
SELECT
  source_area     AS area,
  source_location AS location,
  timepoint,
  beforetm,
  aftertm,
  useflg
FROM ITSM_CORE_TIMEPOINT_RULE;
/

CREATE OR REPLACE VIEW ITSM_CORE_PLAN_BIZ_V AS
SELECT
  src_plan_no   AS planno,
  src_custcd    AS custcd,
  src_status    AS status,
  source_object AS source_object
FROM ITSM_CORE_PLAN_CUSTOMER_XREF;
/

PROMPT === 2) Compile and query smoke test ===
SELECT object_name, object_type, status
FROM user_objects
WHERE object_name IN ('ITSM_CORE_TIMEPOINT_RULE_V', 'ITSM_CORE_PLAN_BIZ_V')
ORDER BY object_name;

SELECT 'ITSM_CORE_TIMEPOINT_RULE_V' AS view_name, COUNT(*) AS row_count
FROM ITSM_CORE_TIMEPOINT_RULE_V
UNION ALL
SELECT 'ITSM_CORE_PLAN_BIZ_V' AS view_name, COUNT(*) AS row_count
FROM ITSM_CORE_PLAN_BIZ_V;

PROMPT === 3) Optional source-view comparison if exists ===
DECLARE
  v_has_src_tp_view NUMBER := 0;
  v_has_src_biz_view NUMBER := 0;
BEGIN
  SELECT COUNT(*) INTO v_has_src_tp_view FROM user_views WHERE view_name = 'TIT01_TIMEPOINT_CUST';
  SELECT COUNT(*) INTO v_has_src_biz_view FROM user_views WHERE view_name = 'PLAN_BIZ_V';

  IF v_has_src_tp_view > 0 THEN
    DBMS_OUTPUT.PUT_LINE('SRC_VIEW_EXISTS:TIT01_TIMEPOINT_CUST=Y');
  ELSE
    DBMS_OUTPUT.PUT_LINE('SRC_VIEW_EXISTS:TIT01_TIMEPOINT_CUST=N');
  END IF;

  IF v_has_src_biz_view > 0 THEN
    DBMS_OUTPUT.PUT_LINE('SRC_VIEW_EXISTS:PLAN_BIZ_V=Y');
  ELSE
    DBMS_OUTPUT.PUT_LINE('SRC_VIEW_EXISTS:PLAN_BIZ_V=N');
  END IF;
END;
/

PROMPT === 4) Update batch log (Step3.1) ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no, 'VIEW' AS object_type, 'TIT01_TIMEPOINT_CUST' AS object_name, 'STEP3_1_READINESS' AS action_type, 'DONE' AS execute_status, 'cutover view ITSM_CORE_TIMEPOINT_RULE_V ready' AS note FROM dual
  UNION ALL
  SELECT 'P1_BATCH01', 'VIEW', 'PLAN_BIZ_V', 'STEP3_1_READINESS', 'DONE', 'cutover view ITSM_CORE_PLAN_BIZ_V ready' FROM dual
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

PROMPT === 5) Readiness summary ===
SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

SELECT
  CASE
    WHEN SUM(CASE WHEN action_type = 'RUN_STEP01' AND execute_status = 'DONE' THEN cnt ELSE 0 END) >= 2
     AND SUM(CASE WHEN action_type = 'RUN_STEP02' AND execute_status = 'DONE' THEN cnt ELSE 0 END) >= 2
     AND SUM(CASE WHEN action_type IN ('RUN_STEP03', 'STEP3_1_READINESS') AND execute_status = 'DONE' THEN cnt ELSE 0 END) >= 2
    THEN 'CUTOVER_READY'
    ELSE 'CUTOVER_BLOCKED'
  END AS cutover_decision
FROM (
  SELECT action_type, execute_status, COUNT(*) AS cnt
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH01'
  GROUP BY action_type, execute_status
);

EXIT;
