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
    raise_application_error(-20062, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Create target tables if not exists ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE ITSM_CORE_LIABILITY (
      liability_id        RAW(16)      NOT NULL,
      src_liabcd          VARCHAR2(64),
      src_liabnm          VARCHAR2(200),
      src_describe        VARCHAR2(2000),
      src_liabtype        VARCHAR2(8),
      src_parent          VARCHAR2(64),
      src_childflg        VARCHAR2(8),
      src_useflg          VARCHAR2(8),
      src_gendate         DATE,
      src_upddate         DATE,
      source_object       VARCHAR2(64) NOT NULL,
      created_at_utc      TIMESTAMP(6) DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      CONSTRAINT PK_ITSM_CORE_LIAB PRIMARY KEY (liability_id)
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
    CREATE TABLE ITSM_CORE_LIABILITY_DTL (
      detail_id           RAW(16)      NOT NULL,
      src_lbdtcd          VARCHAR2(64),
      src_liabcd          VARCHAR2(64),
      src_define          VARCHAR2(2000),
      src_useflg          VARCHAR2(8),
      src_gendate         DATE,
      source_object       VARCHAR2(64) NOT NULL,
      created_at_utc      TIMESTAMP(6) DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      CONSTRAINT PK_ITSM_CORE_LIAB_DTL PRIMARY KEY (detail_id)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) Migrate TIT02_LIABILITYREG -> ITSM_CORE_LIABILITY ===
DECLARE
  v_sql           CLOB;
  v_has_liabcd    NUMBER := 0;
  v_has_liabnm    NUMBER := 0;
  v_has_describe  NUMBER := 0;
  v_has_liabtype  NUMBER := 0;
  v_has_parent    NUMBER := 0;
  v_has_childflg  NUMBER := 0;
  v_has_useflg    NUMBER := 0;
  v_has_gendate   NUMBER := 0;
  v_has_upddate   NUMBER := 0;
BEGIN
  SELECT COUNT(*) INTO v_has_liabcd FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREG' AND column_name = 'LIABCD';
  SELECT COUNT(*) INTO v_has_liabnm FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREG' AND column_name = 'LIABNM';
  SELECT COUNT(*) INTO v_has_describe FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREG' AND column_name = 'DESCRIBE';
  SELECT COUNT(*) INTO v_has_liabtype FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREG' AND column_name = 'LIABTYPE';
  SELECT COUNT(*) INTO v_has_parent FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREG' AND column_name = 'PARENT';
  SELECT COUNT(*) INTO v_has_childflg FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREG' AND column_name = 'CHILDFLG';
  SELECT COUNT(*) INTO v_has_useflg FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREG' AND column_name = 'USEFLG';
  SELECT COUNT(*) INTO v_has_gendate FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREG' AND column_name = 'GENDATE';
  SELECT COUNT(*) INTO v_has_upddate FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREG' AND column_name = 'UPDDATE';

  EXECUTE IMMEDIATE 'TRUNCATE TABLE ITSM_CORE_LIABILITY';

  v_sql := 'INSERT INTO ITSM_CORE_LIABILITY '
        || '(liability_id, src_liabcd, src_liabnm, src_describe, src_liabtype, src_parent, src_childflg, src_useflg, src_gendate, src_upddate, source_object) '
        || 'SELECT SYS_GUID(), '
        || CASE WHEN v_has_liabcd > 0 THEN 'TO_CHAR(liabcd)' ELSE 'CAST(NULL AS VARCHAR2(64))' END || ', '
        || CASE WHEN v_has_liabnm > 0 THEN 'TO_CHAR(liabnm)' ELSE 'CAST(NULL AS VARCHAR2(200))' END || ', '
        || CASE WHEN v_has_describe > 0 THEN 'TO_CHAR(describe)' ELSE 'CAST(NULL AS VARCHAR2(2000))' END || ', '
        || CASE WHEN v_has_liabtype > 0 THEN 'TO_CHAR(liabtype)' ELSE 'CAST(NULL AS VARCHAR2(8))' END || ', '
        || CASE WHEN v_has_parent > 0 THEN 'TO_CHAR(parent)' ELSE 'CAST(NULL AS VARCHAR2(64))' END || ', '
        || CASE WHEN v_has_childflg > 0 THEN 'TO_CHAR(childflg)' ELSE 'CAST(NULL AS VARCHAR2(8))' END || ', '
        || CASE WHEN v_has_useflg > 0 THEN 'TO_CHAR(useflg)' ELSE 'CAST(NULL AS VARCHAR2(8))' END || ', '
        || CASE WHEN v_has_gendate > 0 THEN 'gendate' ELSE 'CAST(NULL AS DATE)' END || ', '
        || CASE WHEN v_has_upddate > 0 THEN 'upddate' ELSE 'CAST(NULL AS DATE)' END || ', '
        || '''TIT02_LIABILITYREG'' FROM TIT02_LIABILITYREG';

  EXECUTE IMMEDIATE v_sql;
END;
/

PROMPT === 3) Migrate TIT02_LIABILITYREGDT -> ITSM_CORE_LIABILITY_DTL ===
DECLARE
  v_sql           CLOB;
  v_has_lbdtcd    NUMBER := 0;
  v_has_liabcd    NUMBER := 0;
  v_has_define    NUMBER := 0;
  v_has_useflg    NUMBER := 0;
  v_has_gendate   NUMBER := 0;
BEGIN
  SELECT COUNT(*) INTO v_has_lbdtcd FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREGDT' AND column_name = 'LBDTCD';
  SELECT COUNT(*) INTO v_has_liabcd FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREGDT' AND column_name = 'LIABCD';
  SELECT COUNT(*) INTO v_has_define FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREGDT' AND column_name = 'DEFINE';
  SELECT COUNT(*) INTO v_has_useflg FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREGDT' AND column_name = 'USEFLG';
  SELECT COUNT(*) INTO v_has_gendate FROM user_tab_columns WHERE table_name = 'TIT02_LIABILITYREGDT' AND column_name = 'GENDATE';

  EXECUTE IMMEDIATE 'TRUNCATE TABLE ITSM_CORE_LIABILITY_DTL';

  v_sql := 'INSERT INTO ITSM_CORE_LIABILITY_DTL '
        || '(detail_id, src_lbdtcd, src_liabcd, src_define, src_useflg, src_gendate, source_object) '
        || 'SELECT SYS_GUID(), '
        || CASE WHEN v_has_lbdtcd > 0 THEN 'TO_CHAR(lbdtcd)' ELSE 'CAST(NULL AS VARCHAR2(64))' END || ', '
        || CASE WHEN v_has_liabcd > 0 THEN 'TO_CHAR(liabcd)' ELSE 'CAST(NULL AS VARCHAR2(64))' END || ', '
        || CASE WHEN v_has_define > 0 THEN 'TO_CHAR(define)' ELSE 'CAST(NULL AS VARCHAR2(2000))' END || ', '
        || CASE WHEN v_has_useflg > 0 THEN 'TO_CHAR(useflg)' ELSE 'CAST(NULL AS VARCHAR2(8))' END || ', '
        || CASE WHEN v_has_gendate > 0 THEN 'gendate' ELSE 'CAST(NULL AS DATE)' END || ', '
        || '''TIT02_LIABILITYREGDT'' FROM TIT02_LIABILITYREGDT';

  EXECUTE IMMEDIATE v_sql;
END;
/

PROMPT === 4) Verification ===
SELECT 'SRC_TIT02_LIABILITYREG' AS check_item, COUNT(*) AS row_count FROM TIT02_LIABILITYREG
UNION ALL
SELECT 'TGT_ITSM_CORE_LIABILITY', COUNT(*) FROM ITSM_CORE_LIABILITY
UNION ALL
SELECT 'SRC_TIT02_LIABILITYREGDT', COUNT(*) FROM TIT02_LIABILITYREGDT
UNION ALL
SELECT 'TGT_ITSM_CORE_LIABILITY_DTL', COUNT(*) FROM ITSM_CORE_LIABILITY_DTL;

SELECT 'DTL_PARENT_COVERAGE_MISS' AS check_item, COUNT(*) AS miss_count
FROM ITSM_CORE_LIABILITY_DTL d
WHERE d.src_liabcd IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM ITSM_CORE_LIABILITY h
    WHERE h.src_liabcd = d.src_liabcd
  );

PROMPT === 5) Update batch log ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no, 'TABLE' AS object_type, 'TIT02_LIABILITYREG' AS object_name, 'RUN_STEP02' AS action_type, 'DONE' AS execute_status, 'loaded into ITSM_CORE_LIABILITY' AS note FROM dual
  UNION ALL
  SELECT 'P1_BATCH01', 'TABLE', 'TIT02_LIABILITYREGDT', 'RUN_STEP02', 'DONE', 'loaded into ITSM_CORE_LIABILITY_DTL' FROM dual
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
