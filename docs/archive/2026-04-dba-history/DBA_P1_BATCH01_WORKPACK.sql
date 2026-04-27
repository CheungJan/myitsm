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
    raise_application_error(-20051, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 首批工作包表（首次执行自动创建） ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_OBJECT_WORKPACK (
      batch_no            VARCHAR2(30)  NOT NULL,
      wave_no             VARCHAR2(30)  NOT NULL,
      source_object_type  VARCHAR2(30)  NOT NULL,
      source_object_name  VARCHAR2(128) NOT NULL,
      target_object_name  VARCHAR2(128) NOT NULL,
      migration_strategy  VARCHAR2(200) NOT NULL,
      verify_rule         VARCHAR2(500),
      status              VARCHAR2(20)  DEFAULT ''PLANNED'' NOT NULL,
      updated_at          DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_MIG_P1_OBJECT_WORKPACK PRIMARY KEY (
        batch_no, wave_no, source_object_type, source_object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 首批对象工作包登记（WAVE_01） ===
MERGE INTO MIG_P1_OBJECT_WORKPACK t
USING (
  SELECT 'P1_BATCH01' AS batch_no,
         'WAVE_01' AS wave_no,
         'TABLE' AS source_object_type,
         'TIT01_TIMEPOINT_AREA' AS source_object_name,
         'ITSM_CORE_TIMEPOINT_RULE' AS target_object_name,
         'FULL_LOAD_AND_STANDARDIZE' AS migration_strategy,
         'COUNT_CHECK_AND_KEY_NOT_NULL' AS verify_rule
    FROM dual
  UNION ALL
  SELECT 'P1_BATCH01','WAVE_01','VIEW','TIT01_TIMEPOINT_CUST','ITSM_CORE_TIMEPOINT_RULE_V','COMPAT_VIEW_MAPPING','VIEW_COMPILE_AND_QUERY' FROM dual
  UNION ALL
  SELECT 'P1_BATCH01','WAVE_01','TABLE','PLAN_CUST','ITSM_CORE_PLAN_CUSTOMER_XREF','FULL_LOAD_AND_KEY_MAPPING','COUNT_CHECK_AND_CUSTCD_MATCH' FROM dual
  UNION ALL
  SELECT 'P1_BATCH01','WAVE_01','VIEW','PLAN_BIZ_V','ITSM_CORE_PLAN_BIZ_V','COMPAT_VIEW_MAPPING','VIEW_COMPILE_AND_QUERY' FROM dual
  UNION ALL
  SELECT 'P1_BATCH01','WAVE_01','TABLE','TIT02_LIABILITYREG','ITSM_CORE_LIABILITY','MAIN_TABLE_MIGRATION','PK_UNIQUE_AND_STATUS_CHECK' FROM dual
  UNION ALL
  SELECT 'P1_BATCH01','WAVE_01','TABLE','TIT02_LIABILITYREGDT','ITSM_CORE_LIABILITY_DTL','DETAIL_TABLE_MIGRATION','DETAIL_COUNT_AND_FK_COVERAGE' FROM dual
) s
ON (
  t.batch_no = s.batch_no
  AND t.wave_no = s.wave_no
  AND t.source_object_type = s.source_object_type
  AND t.source_object_name = s.source_object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.target_object_name = s.target_object_name,
    t.migration_strategy = s.migration_strategy,
    t.verify_rule = s.verify_rule,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    batch_no, wave_no, source_object_type, source_object_name,
    target_object_name, migration_strategy, verify_rule, status, updated_at
  )
  VALUES (
    s.batch_no, s.wave_no, s.source_object_type, s.source_object_name,
    s.target_object_name, s.migration_strategy, s.verify_rule, 'PLANNED', SYSDATE
  );
/

PROMPT === 3) 工作包结果查看 ===
SELECT batch_no, wave_no, source_object_type, source_object_name,
       target_object_name, migration_strategy, status
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH01'
  AND wave_no = 'WAVE_01'
ORDER BY source_object_type, source_object_name;

EXIT;
