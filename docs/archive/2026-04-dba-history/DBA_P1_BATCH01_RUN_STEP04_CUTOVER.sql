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
    raise_application_error(-20064, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 构建回退快照表（优先源库快照） ===
BEGIN
  EXECUTE IMMEDIATE 'CREATE TABLE TIT01_TIMEPOINT_CUST_B01_T AS SELECT * FROM TIT01_TIMEPOINT_CUST@CCGLPDB_LINK';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE = -955 THEN
      EXECUTE IMMEDIATE 'TRUNCATE TABLE TIT01_TIMEPOINT_CUST_B01_T';
      EXECUTE IMMEDIATE 'INSERT INTO TIT01_TIMEPOINT_CUST_B01_T SELECT * FROM TIT01_TIMEPOINT_CUST@CCGLPDB_LINK';
      COMMIT;
    ELSE
      RAISE;
    END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE 'CREATE TABLE PLAN_BIZ_V_B01_T AS SELECT * FROM PLAN_BIZ_V@CCGLPDB_LINK';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE = -955 THEN
      EXECUTE IMMEDIATE 'TRUNCATE TABLE PLAN_BIZ_V_B01_T';
      EXECUTE IMMEDIATE 'INSERT INTO PLAN_BIZ_V_B01_T SELECT * FROM PLAN_BIZ_V@CCGLPDB_LINK';
      COMMIT;
    ELSE
      RAISE;
    END IF;
END;
/

PROMPT === 2) 读流量切换：源视图重定向到新核心视图 ===
CREATE OR REPLACE VIEW TIT01_TIMEPOINT_CUST AS
SELECT
  area,
  location,
  timepoint,
  beforetm,
  aftertm,
  useflg
FROM ITSM_CORE_TIMEPOINT_RULE_V;
/

CREATE OR REPLACE VIEW PLAN_BIZ_V AS
SELECT
  planno,
  custcd,
  status,
  source_object
FROM ITSM_CORE_PLAN_BIZ_V;
/

PROMPT === 3) 切流后核验（状态 + 行数） ===
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
SELECT 'ITSM_CORE_TIMEPOINT_RULE_V', COUNT(*) FROM ITSM_CORE_TIMEPOINT_RULE_V
UNION ALL
SELECT 'PLAN_BIZ_V', COUNT(*) FROM PLAN_BIZ_V
UNION ALL
SELECT 'ITSM_CORE_PLAN_BIZ_V', COUNT(*) FROM ITSM_CORE_PLAN_BIZ_V;

PROMPT === 4) 写入批次日志（Step3.2） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no, 'VIEW' AS object_type, 'TIT01_TIMEPOINT_CUST' AS object_name, 'STEP3_2_READ_CUTOVER' AS action_type, 'DONE' AS execute_status, 'read cutover to ITSM_CORE_TIMEPOINT_RULE_V' AS note FROM dual
  UNION ALL
  SELECT 'P1_BATCH01', 'VIEW', 'PLAN_BIZ_V', 'STEP3_2_READ_CUTOVER', 'DONE', 'read cutover to ITSM_CORE_PLAN_BIZ_V' FROM dual
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

PROMPT === 5) 切流状态汇总 ===
SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

SELECT
  CASE
    WHEN SUM(CASE WHEN action_type IN ('RUN_STEP04', 'STEP3_2_READ_CUTOVER') AND execute_status = 'DONE' THEN cnt ELSE 0 END) >= 2
    THEN 'CUTOVER_ACTIVE'
    ELSE 'CUTOVER_NOT_ACTIVE'
  END AS cutover_state
FROM (
  SELECT action_type, execute_status, COUNT(*) AS cnt
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH01'
  GROUP BY action_type, execute_status
);

EXIT;
