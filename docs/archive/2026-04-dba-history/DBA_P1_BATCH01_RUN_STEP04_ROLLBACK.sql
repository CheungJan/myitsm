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
    raise_application_error(-20065, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 回退读视图（优先本地快照表，兜底源库） ===
DECLARE
  v_has_tit01_snapshot NUMBER := 0;
BEGIN
  SELECT COUNT(*)
    INTO v_has_tit01_snapshot
    FROM user_tables
   WHERE table_name = 'TIT01_TIMEPOINT_CUST_B01_T';

  IF v_has_tit01_snapshot > 0 THEN
    EXECUTE IMMEDIATE '
      CREATE OR REPLACE VIEW TIT01_TIMEPOINT_CUST AS
      SELECT custcd, timepoint, beforetm, aftertm, useflg
      FROM TIT01_TIMEPOINT_CUST_B01_T';
  ELSE
    EXECUTE IMMEDIATE '
      CREATE OR REPLACE VIEW TIT01_TIMEPOINT_CUST AS
      SELECT custcd, timepoint, beforetm, aftertm, useflg
      FROM TIT01_TIMEPOINT_CUST@CCGLPDB_LINK';
  END IF;
END;
/

DECLARE
  v_has_plan_snapshot NUMBER := 0;
BEGIN
  SELECT COUNT(*)
    INTO v_has_plan_snapshot
    FROM user_tables
   WHERE table_name = 'PLAN_BIZ_V_B01_T';

  IF v_has_plan_snapshot > 0 THEN
    EXECUTE IMMEDIATE '
      CREATE OR REPLACE VIEW PLAN_BIZ_V AS
      SELECT *
      FROM PLAN_BIZ_V_B01_T';
  ELSE
    EXECUTE IMMEDIATE '
      CREATE OR REPLACE VIEW PLAN_BIZ_V AS
      SELECT *
      FROM PLAN_BIZ_V@CCGLPDB_LINK';
  END IF;
END;
/

PROMPT === 2) 回退后核验 ===
SELECT object_name, object_type, status
FROM user_objects
WHERE object_name IN (
  'TIT01_TIMEPOINT_CUST',
  'PLAN_BIZ_V',
  'TIT01_TIMEPOINT_CUST_B01_T',
  'PLAN_BIZ_V_B01_T'
)
ORDER BY object_name;

SELECT 'TIT01_TIMEPOINT_CUST' AS view_name, COUNT(*) AS row_count
FROM TIT01_TIMEPOINT_CUST
UNION ALL
SELECT 'TIT01_TIMEPOINT_CUST_B01_T', COUNT(*) FROM TIT01_TIMEPOINT_CUST_B01_T
UNION ALL
SELECT 'PLAN_BIZ_V', COUNT(*) FROM PLAN_BIZ_V
UNION ALL
SELECT 'PLAN_BIZ_V_B01_T', COUNT(*) FROM PLAN_BIZ_V_B01_T;

PROMPT === 3) 写入批次日志（回退） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no, 'VIEW' AS object_type, 'TIT01_TIMEPOINT_CUST' AS object_name, 'STEP3_2_READ_CUTOVER' AS action_type, 'ROLLBACK' AS execute_status, 'rollback to TIT01_TIMEPOINT_CUST_B01_T' AS note FROM dual
  UNION ALL
  SELECT 'P1_BATCH01', 'VIEW', 'PLAN_BIZ_V', 'STEP3_2_READ_CUTOVER', 'ROLLBACK', 'rollback to PLAN_BIZ_V_B01_T' FROM dual
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

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
