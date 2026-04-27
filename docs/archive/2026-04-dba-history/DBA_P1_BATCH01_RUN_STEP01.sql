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
    raise_application_error(-20061, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 创建首轮目标表（若不存在） ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE ITSM_CORE_TIMEPOINT_RULE (
      rule_id            RAW(16)       NOT NULL,
      source_area        VARCHAR2(64),
      source_location    VARCHAR2(64),
      timepoint          DATE,
      beforetm           NUMBER,
      aftertm            NUMBER,
      useflg             VARCHAR2(8),
      source_object      VARCHAR2(64)  NOT NULL,
      created_at_utc     TIMESTAMP(6)  DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      CONSTRAINT PK_ITSM_CORE_TIMEPOINT_RULE PRIMARY KEY (rule_id)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE ITSM_CORE_PLAN_CUSTOMER_XREF (
      xref_id            RAW(16)       NOT NULL,
      src_plan_no        VARCHAR2(128),
      src_custcd         VARCHAR2(64),
      src_status         VARCHAR2(64),
      source_object      VARCHAR2(64)  NOT NULL,
      created_at_utc     TIMESTAMP(6)  DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      CONSTRAINT PK_ITSM_CORE_PLAN_CUST_XREF PRIMARY KEY (xref_id)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 执行首轮迁移（TIT01_TIMEPOINT_AREA -> ITSM_CORE_TIMEPOINT_RULE） ===
DECLARE
  v_sql            CLOB;
  v_has_area       NUMBER := 0;
  v_has_location   NUMBER := 0;
  v_has_timepoint  NUMBER := 0;
  v_has_beforetm   NUMBER := 0;
  v_has_aftertm    NUMBER := 0;
  v_has_useflg     NUMBER := 0;
BEGIN
  SELECT COUNT(*) INTO v_has_area FROM user_tab_columns WHERE table_name = 'TIT01_TIMEPOINT_AREA' AND column_name = 'AREA';
  SELECT COUNT(*) INTO v_has_location FROM user_tab_columns WHERE table_name = 'TIT01_TIMEPOINT_AREA' AND column_name = 'LOCATION';
  SELECT COUNT(*) INTO v_has_timepoint FROM user_tab_columns WHERE table_name = 'TIT01_TIMEPOINT_AREA' AND column_name = 'TIMEPOINT';
  SELECT COUNT(*) INTO v_has_beforetm FROM user_tab_columns WHERE table_name = 'TIT01_TIMEPOINT_AREA' AND column_name = 'BEFORETM';
  SELECT COUNT(*) INTO v_has_aftertm FROM user_tab_columns WHERE table_name = 'TIT01_TIMEPOINT_AREA' AND column_name = 'AFTERTM';
  SELECT COUNT(*) INTO v_has_useflg FROM user_tab_columns WHERE table_name = 'TIT01_TIMEPOINT_AREA' AND column_name = 'USEFLG';

  EXECUTE IMMEDIATE 'TRUNCATE TABLE ITSM_CORE_TIMEPOINT_RULE';

  v_sql := 'INSERT INTO ITSM_CORE_TIMEPOINT_RULE (rule_id, source_area, source_location, timepoint, beforetm, aftertm, useflg, source_object) '
        || 'SELECT SYS_GUID(), '
        || CASE WHEN v_has_area > 0 THEN 'TO_CHAR(area)' ELSE 'CAST(NULL AS VARCHAR2(64))' END || ', '
        || CASE WHEN v_has_location > 0 THEN 'TO_CHAR(location)' ELSE 'CAST(NULL AS VARCHAR2(64))' END || ', '
        || CASE WHEN v_has_timepoint > 0 THEN 'timepoint' ELSE 'CAST(NULL AS DATE)' END || ', '
        || CASE WHEN v_has_beforetm > 0 THEN 'beforetm' ELSE 'CAST(NULL AS NUMBER)' END || ', '
        || CASE WHEN v_has_aftertm > 0 THEN 'aftertm' ELSE 'CAST(NULL AS NUMBER)' END || ', '
        || CASE WHEN v_has_useflg > 0 THEN 'TO_CHAR(useflg)' ELSE 'CAST(NULL AS VARCHAR2(8))' END || ', '
        || '''TIT01_TIMEPOINT_AREA'' FROM TIT01_TIMEPOINT_AREA';

  EXECUTE IMMEDIATE v_sql;
END;
/

PROMPT === 3) 执行首轮迁移（PLAN_CUST -> ITSM_CORE_PLAN_CUSTOMER_XREF） ===
DECLARE
  v_sql            CLOB;
  v_has_planno     NUMBER := 0;
  v_has_plan_no    NUMBER := 0;
  v_has_billno     NUMBER := 0;
  v_has_plbillno   NUMBER := 0;
  v_has_custcd     NUMBER := 0;
  v_has_customercd NUMBER := 0;
  v_has_status     NUMBER := 0;
  v_has_planstatus NUMBER := 0;
  v_has_useflg     NUMBER := 0;
  v_expr_plan_no   VARCHAR2(200);
  v_expr_custcd    VARCHAR2(200);
  v_expr_status    VARCHAR2(200);
BEGIN
  SELECT COUNT(*) INTO v_has_planno FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'PLANNO';
  SELECT COUNT(*) INTO v_has_plan_no FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'PLAN_NO';
  SELECT COUNT(*) INTO v_has_billno FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'BILLNO';
  SELECT COUNT(*) INTO v_has_plbillno FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'PLBILLNO';
  SELECT COUNT(*) INTO v_has_custcd FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'CUSTCD';
  SELECT COUNT(*) INTO v_has_customercd FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'CUSTOMERCD';
  SELECT COUNT(*) INTO v_has_status FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'STATUS';
  SELECT COUNT(*) INTO v_has_planstatus FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'PLANSTATUS';
  SELECT COUNT(*) INTO v_has_useflg FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'USEFLG';

  EXECUTE IMMEDIATE 'TRUNCATE TABLE ITSM_CORE_PLAN_CUSTOMER_XREF';

  IF v_has_planno > 0 THEN
    v_expr_plan_no := 'TO_CHAR(planno)';
  ELSIF v_has_plan_no > 0 THEN
    v_expr_plan_no := 'TO_CHAR(plan_no)';
  ELSIF v_has_billno > 0 THEN
    v_expr_plan_no := 'TO_CHAR(billno)';
  ELSIF v_has_plbillno > 0 THEN
    v_expr_plan_no := 'TO_CHAR(plbillno)';
  ELSE
    v_expr_plan_no := 'CAST(NULL AS VARCHAR2(128))';
  END IF;

  IF v_has_custcd > 0 THEN
    v_expr_custcd := 'TO_CHAR(custcd)';
  ELSIF v_has_customercd > 0 THEN
    v_expr_custcd := 'TO_CHAR(customercd)';
  ELSE
    v_expr_custcd := 'CAST(NULL AS VARCHAR2(64))';
  END IF;

  IF v_has_status > 0 THEN
    v_expr_status := 'TO_CHAR(status)';
  ELSIF v_has_planstatus > 0 THEN
    v_expr_status := 'TO_CHAR(planstatus)';
  ELSIF v_has_useflg > 0 THEN
    v_expr_status := 'TO_CHAR(useflg)';
  ELSE
    v_expr_status := 'CAST(NULL AS VARCHAR2(64))';
  END IF;

  v_sql := 'INSERT INTO ITSM_CORE_PLAN_CUSTOMER_XREF (xref_id, src_plan_no, src_custcd, src_status, source_object) '
        || 'SELECT SYS_GUID(), '
        || v_expr_plan_no || ', '
        || v_expr_custcd || ', '
        || v_expr_status || ', '
        || '''PLAN_CUST'' FROM PLAN_CUST';

  EXECUTE IMMEDIATE v_sql;
END;
/

PROMPT === 4) 首轮核验 ===
SELECT 'ITSM_CORE_TIMEPOINT_RULE' AS target_table, COUNT(*) AS row_count
FROM ITSM_CORE_TIMEPOINT_RULE
UNION ALL
SELECT 'ITSM_CORE_PLAN_CUSTOMER_XREF' AS target_table, COUNT(*) AS row_count
FROM ITSM_CORE_PLAN_CUSTOMER_XREF;

PROMPT === 5) 更新批次状态 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no, 'TABLE' AS object_type, 'TIT01_TIMEPOINT_AREA' AS object_name, 'RUN_STEP01' AS action_type, 'DONE' AS execute_status, 'loaded into ITSM_CORE_TIMEPOINT_RULE' AS note FROM dual
  UNION ALL
  SELECT 'P1_BATCH01','TABLE','PLAN_CUST','RUN_STEP01','DONE','loaded into ITSM_CORE_PLAN_CUSTOMER_XREF' FROM dual
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

SELECT batch_no, action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
GROUP BY batch_no, action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
