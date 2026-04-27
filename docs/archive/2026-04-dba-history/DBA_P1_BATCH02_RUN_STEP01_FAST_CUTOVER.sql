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
    raise_application_error(-20101, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 快速落地门禁（BATCH02快照就绪 + 24h影子绿态） ===
DECLARE
  v_ready_cnt NUMBER := 0;
  v_total_cnt NUMBER := 0;
  v_bad_cnt   NUMBER := 0;
BEGIN
  SELECT COUNT(*)
    INTO v_ready_cnt
    FROM MIG_P1_BATCH_LOG
   WHERE batch_no = 'P1_BATCH02'
     AND action_type = 'SNAPSHOT'
     AND execute_status = 'READY'
     AND object_name IN ('PLAN_BIZ_V', 'TIT01_TIMEPOINT_CUST');

  SELECT COUNT(*),
         SUM(CASE WHEN compare_result IN ('DIFF', 'ERROR') THEN 1 ELSE 0 END)
    INTO v_total_cnt, v_bad_cnt
    FROM MIG_P1_SHADOW_WRITE_LOG
   WHERE batch_no = 'P1_BATCH01'
     AND created_at_utc >= SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '1' DAY;

  IF v_ready_cnt < 2 THEN
    raise_application_error(-20102, 'BATCH02 snapshot not ready for required objects, ready_cnt=' || v_ready_cnt);
  END IF;

  IF v_total_cnt = 0 OR v_bad_cnt > 0 THEN
    raise_application_error(-20103, 'Shadow monitor blocked, total=' || v_total_cnt || ', bad=' || v_bad_cnt);
  END IF;
END;
/

PROMPT === 2) 回退快照（B02） ===
BEGIN
  EXECUTE IMMEDIATE 'CREATE TABLE TIT01_TIMEPOINT_CUST_B02_T AS SELECT * FROM TIT01_TIMEPOINT_CUST@CCGLPDB_LINK';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE = -955 THEN
      EXECUTE IMMEDIATE 'TRUNCATE TABLE TIT01_TIMEPOINT_CUST_B02_T';
      EXECUTE IMMEDIATE 'INSERT INTO TIT01_TIMEPOINT_CUST_B02_T SELECT * FROM TIT01_TIMEPOINT_CUST@CCGLPDB_LINK';
      COMMIT;
    ELSE
      RAISE;
    END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE 'CREATE TABLE PLAN_BIZ_V_B02_T AS SELECT * FROM PLAN_BIZ_V@CCGLPDB_LINK';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE = -955 THEN
      EXECUTE IMMEDIATE 'TRUNCATE TABLE PLAN_BIZ_V_B02_T';
      EXECUTE IMMEDIATE 'INSERT INTO PLAN_BIZ_V_B02_T SELECT * FROM PLAN_BIZ_V@CCGLPDB_LINK';
      COMMIT;
    ELSE
      RAISE;
    END IF;
END;
/

PROMPT === 3) 两对象快速切换（仅明确映射对象） ===
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

PROMPT === 4) 最小核验 ===
SELECT object_name, object_type, status
FROM user_objects
WHERE object_name IN (
  'TIT01_TIMEPOINT_CUST',
  'PLAN_BIZ_V',
  'TIT01_TIMEPOINT_CUST_B02_T',
  'PLAN_BIZ_V_B02_T'
)
ORDER BY object_name;

SELECT 'TIT01_TIMEPOINT_CUST' AS view_name, COUNT(*) AS row_count FROM TIT01_TIMEPOINT_CUST
UNION ALL
SELECT 'ITSM_CORE_TIMEPOINT_RULE_V', COUNT(*) FROM ITSM_CORE_TIMEPOINT_RULE_V
UNION ALL
SELECT 'PLAN_BIZ_V', COUNT(*) FROM PLAN_BIZ_V
UNION ALL
SELECT 'ITSM_CORE_PLAN_BIZ_V', COUNT(*) FROM ITSM_CORE_PLAN_BIZ_V;

PROMPT === 5) 回写批次日志与工作包状态 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH02' AS batch_no, 'VIEW' AS object_type, 'TIT01_TIMEPOINT_CUST' AS object_name, 'STEP1_FAST_CUTOVER' AS action_type, 'DONE' AS execute_status, 'fast cutover to ITSM_CORE_TIMEPOINT_RULE_V' AS note FROM dual
  UNION ALL
  SELECT 'P1_BATCH02', 'VIEW', 'PLAN_BIZ_V', 'STEP1_FAST_CUTOVER', 'DONE', 'fast cutover to ITSM_CORE_PLAN_BIZ_V' FROM dual
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

UPDATE MIG_P1_OBJECT_WORKPACK
   SET status = 'DONE',
       updated_at = SYSDATE
 WHERE batch_no = 'P1_BATCH02'
   AND wave_no = 'WAVE_01'
   AND source_object_name IN ('PLAN_BIZ_V', 'TIT01_TIMEPOINT_CUST');
/

PROMPT === 6) BATCH02 状态汇总 ===
SELECT source_object_name, target_object_name, migration_strategy, status
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH02'
  AND wave_no = 'WAVE_01'
ORDER BY source_object_name;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH02'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
