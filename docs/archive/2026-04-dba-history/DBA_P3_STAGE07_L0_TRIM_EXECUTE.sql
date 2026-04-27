SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 300;
SET LINESIZE 260;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) Safety gate ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME')) INTO v_service_name FROM dual;
  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20551, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Enable execution switch ===
MERGE INTO MIG_P3_L0_TRIM_CTRL t
USING (
  SELECT 'P3_STAGE06' AS stage_no,
         'WAVE_01' AS wave_no,
         'N' AS dry_run_flag,
         'Y' AS exec_flag,
         'execution enabled by operator confirmation' AS note
  FROM dual
) s
ON (t.stage_no = s.stage_no AND t.wave_no = s.wave_no)
WHEN MATCHED THEN
  UPDATE SET t.dry_run_flag = s.dry_run_flag, t.exec_flag = s.exec_flag, t.note = s.note, t.updated_at = SYSDATE;
/

PROMPT === 2) Ensure rollback/exec tables ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_L0_TRIM_RB (
      stage_no        VARCHAR2(30)  NOT NULL,
      wave_no         VARCHAR2(30)  NOT NULL,
      object_type     VARCHAR2(30)  NOT NULL,
      object_name     VARCHAR2(128) NOT NULL,
      backup_name     VARCHAR2(30),
      ddl_text        CLOB,
      updated_at      DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_L0_TRIM_RB PRIMARY KEY (stage_no, wave_no, object_type, object_name)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN RAISE; END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_L0_TRIM_EXEC (
      stage_no        VARCHAR2(30)  NOT NULL,
      wave_no         VARCHAR2(30)  NOT NULL,
      object_type     VARCHAR2(30)  NOT NULL,
      object_name     VARCHAR2(128) NOT NULL,
      exec_status     VARCHAR2(20)  NOT NULL,
      note            VARCHAR2(400),
      updated_at      DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_L0_TRIM_EXEC PRIMARY KEY (stage_no, wave_no, object_type, object_name)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN RAISE; END IF;
END;
/

PROMPT === 3) Execute trim with rollback assets ===
DECLARE
  v_exec_flag VARCHAR2(1);
  v_dry_flag  VARCHAR2(1);
  v_exists    NUMBER;
  v_backup_name VARCHAR2(30);
  v_view_ddl CLOB;
  v_note VARCHAR2(400);
  v_status VARCHAR2(20);
  FUNCTION qname(p_name VARCHAR2) RETURN VARCHAR2 IS
  BEGIN
    RETURN '"' || REPLACE(p_name, '"', '""') || '"';
  END;
BEGIN
  SELECT exec_flag, dry_run_flag INTO v_exec_flag, v_dry_flag
  FROM MIG_P3_L0_TRIM_CTRL
  WHERE stage_no = 'P3_STAGE06' AND wave_no = 'WAVE_01';

  IF v_exec_flag <> 'Y' OR v_dry_flag <> 'N' THEN
    raise_application_error(-20552, 'Trim execution switch not open');
  END IF;

  FOR r IN (
    SELECT object_type, object_name
    FROM MIG_P3_L0_TRIM_PLAN
    WHERE stage_no = 'P3_STAGE06'
      AND wave_no = 'WAVE_01'
      AND plan_status IN ('READY_FOR_REVIEW','READY_FOR_EXEC')
    ORDER BY object_type, object_name
  ) LOOP
    v_status := 'DONE';
    v_note := 'trim executed';
    v_backup_name := 'RB3_' || SUBSTR(REGEXP_REPLACE(UPPER(r.object_name), '[^A-Z0-9_]', '_'),1,12)
                     || '_' || TO_CHAR(MOD(ABS(DBMS_UTILITY.GET_HASH_VALUE(r.object_name,1,999999)),10000),'FM0000');
    BEGIN
      IF r.object_type = 'TABLE' THEN
        SELECT COUNT(*) INTO v_exists FROM user_tables WHERE table_name = r.object_name;
        IF v_exists = 0 THEN
          v_status := 'SKIPPED';
          v_note := 'source table not exists';
        ELSE
          BEGIN
            EXECUTE IMMEDIATE 'DROP TABLE ' || qname(v_backup_name) || ' PURGE';
          EXCEPTION WHEN OTHERS THEN NULL; END;
          EXECUTE IMMEDIATE 'CREATE TABLE ' || qname(v_backup_name)
                         || ' AS SELECT * FROM ' || qname(r.object_name);
          EXECUTE IMMEDIATE 'DROP TABLE ' || qname(r.object_name) || ' PURGE';

          MERGE INTO MIG_P3_L0_TRIM_RB t
          USING (SELECT 'P3_STAGE07' stage_no, 'WAVE_01' wave_no, r.object_type object_type, r.object_name object_name, v_backup_name backup_name FROM dual) s
          ON (t.stage_no=s.stage_no AND t.wave_no=s.wave_no AND t.object_type=s.object_type AND t.object_name=s.object_name)
          WHEN MATCHED THEN UPDATE SET t.backup_name=s.backup_name, t.ddl_text=NULL, t.updated_at=SYSDATE
          WHEN NOT MATCHED THEN INSERT (stage_no,wave_no,object_type,object_name,backup_name,ddl_text,updated_at)
                               VALUES (s.stage_no,s.wave_no,s.object_type,s.object_name,s.backup_name,NULL,SYSDATE);
        END IF;
      ELSIF r.object_type = 'VIEW' THEN
        SELECT COUNT(*) INTO v_exists FROM user_objects WHERE object_type='VIEW' AND object_name = r.object_name;
        IF v_exists = 0 THEN
          v_status := 'SKIPPED';
          v_note := 'source view not exists';
        ELSE
          SELECT DBMS_METADATA.GET_DDL('VIEW', r.object_name, USER) INTO v_view_ddl FROM dual;
          EXECUTE IMMEDIATE 'DROP VIEW ' || qname(r.object_name);

          MERGE INTO MIG_P3_L0_TRIM_RB t
          USING (SELECT 'P3_STAGE07' stage_no, 'WAVE_01' wave_no, r.object_type object_type, r.object_name object_name, CAST(NULL AS VARCHAR2(30)) backup_name, v_view_ddl ddl_text FROM dual) s
          ON (t.stage_no=s.stage_no AND t.wave_no=s.wave_no AND t.object_type=s.object_type AND t.object_name=s.object_name)
          WHEN MATCHED THEN UPDATE SET t.backup_name=s.backup_name, t.ddl_text=s.ddl_text, t.updated_at=SYSDATE
          WHEN NOT MATCHED THEN INSERT (stage_no,wave_no,object_type,object_name,backup_name,ddl_text,updated_at)
                               VALUES (s.stage_no,s.wave_no,s.object_type,s.object_name,s.backup_name,s.ddl_text,SYSDATE);
        END IF;
      ELSE
        v_status := 'SKIPPED';
        v_note := 'unsupported object type';
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        v_status := 'FAILED';
        v_note := SUBSTR(SQLERRM,1,380);
    END;

    MERGE INTO MIG_P3_L0_TRIM_EXEC t
    USING (SELECT 'P3_STAGE07' stage_no, 'WAVE_01' wave_no, r.object_type object_type, r.object_name object_name, v_status exec_status, v_note note FROM dual) s
    ON (t.stage_no=s.stage_no AND t.wave_no=s.wave_no AND t.object_type=s.object_type AND t.object_name=s.object_name)
    WHEN MATCHED THEN UPDATE SET t.exec_status=s.exec_status, t.note=s.note, t.updated_at=SYSDATE
    WHEN NOT MATCHED THEN INSERT (stage_no,wave_no,object_type,object_name,exec_status,note,updated_at)
                         VALUES (s.stage_no,s.wave_no,s.object_type,s.object_name,s.exec_status,s.note,SYSDATE);
  END LOOP;
END;
/

PROMPT === 4) Write batch log ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE07' AS batch_no,
         object_type,
         object_name,
         'STEP7_TRIM_EXEC' AS action_type,
         exec_status AS execute_status,
         note
  FROM MIG_P3_L0_TRIM_EXEC
  WHERE stage_no='P3_STAGE07' AND wave_no='WAVE_01'
) s
ON (t.batch_no=s.batch_no AND t.object_type=s.object_type AND t.object_name=s.object_name AND t.action_type=s.action_type)
WHEN MATCHED THEN UPDATE SET t.execute_status=s.execute_status, t.note=s.note, t.executed_at=SYSDATE
WHEN NOT MATCHED THEN INSERT (batch_no,object_type,object_name,action_type,execute_status,note,executed_at)
                    VALUES (s.batch_no,s.object_type,s.object_name,s.action_type,s.execute_status,s.note,SYSDATE);
/

PROMPT === 5) Summary ===
SELECT exec_status, COUNT(*) AS cnt
FROM MIG_P3_L0_TRIM_EXEC
WHERE stage_no='P3_STAGE07' AND wave_no='WAVE_01'
GROUP BY exec_status
ORDER BY exec_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no='P3_STAGE07'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

SELECT COUNT(*) AS rollback_assets
FROM MIG_P3_L0_TRIM_RB
WHERE stage_no='P3_STAGE07' AND wave_no='WAVE_01';

EXIT;
