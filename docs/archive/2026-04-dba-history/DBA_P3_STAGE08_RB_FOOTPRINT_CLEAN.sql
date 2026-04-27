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
    raise_application_error(-20571, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Ensure cleanup control and exec table ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_RB_CLEAN_CTRL (
      stage_no      VARCHAR2(30) NOT NULL,
      wave_no       VARCHAR2(30) NOT NULL,
      clean_flag    VARCHAR2(1)  NOT NULL,
      note          VARCHAR2(300),
      updated_at    DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_RB_CLEAN_CTRL PRIMARY KEY (stage_no, wave_no)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN RAISE; END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_RB_CLEAN_EXEC (
      stage_no      VARCHAR2(30)  NOT NULL,
      wave_no       VARCHAR2(30)  NOT NULL,
      backup_name   VARCHAR2(30)  NOT NULL,
      exec_status   VARCHAR2(20)  NOT NULL,
      note          VARCHAR2(400),
      updated_at    DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_RB_CLEAN_EXEC PRIMARY KEY (stage_no, wave_no, backup_name)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN RAISE; END IF;
END;
/

MERGE INTO MIG_P3_RB_CLEAN_CTRL t
USING (
  SELECT 'P3_STAGE08' AS stage_no,
         'WAVE_01' AS wave_no,
         'Y' AS clean_flag,
         'cleanup rollback footprint tables after trim execution' AS note
  FROM dual
) s
ON (t.stage_no=s.stage_no AND t.wave_no=s.wave_no)
WHEN MATCHED THEN
  UPDATE SET t.clean_flag=s.clean_flag, t.note=s.note, t.updated_at=SYSDATE
WHEN NOT MATCHED THEN
  INSERT (stage_no,wave_no,clean_flag,note,updated_at)
  VALUES (s.stage_no,s.wave_no,s.clean_flag,s.note,SYSDATE);
/

PROMPT === 2) Execute RB footprint cleanup ===
DECLARE
  v_clean_flag VARCHAR2(1);
  v_exists NUMBER;
  v_status VARCHAR2(20);
  v_note VARCHAR2(400);
  FUNCTION qname(p_name VARCHAR2) RETURN VARCHAR2 IS
  BEGIN
    RETURN '"' || REPLACE(p_name, '"', '""') || '"';
  END;
BEGIN
  SELECT clean_flag INTO v_clean_flag
  FROM MIG_P3_RB_CLEAN_CTRL
  WHERE stage_no='P3_STAGE08' AND wave_no='WAVE_01';

  IF v_clean_flag <> 'Y' THEN
    raise_application_error(-20572, 'RB cleanup flag is not enabled');
  END IF;

  FOR r IN (
    SELECT DISTINCT backup_name
    FROM MIG_P3_L0_TRIM_RB
    WHERE stage_no='P3_STAGE07'
      AND wave_no='WAVE_01'
      AND backup_name IS NOT NULL
    ORDER BY backup_name
  ) LOOP
    v_status := 'DONE';
    v_note := 'rollback backup table dropped';
    BEGIN
      SELECT COUNT(*) INTO v_exists FROM user_tables WHERE table_name = r.backup_name;
      IF v_exists > 0 THEN
        EXECUTE IMMEDIATE 'DROP TABLE ' || qname(r.backup_name) || ' PURGE';
      ELSE
        v_status := 'SKIPPED';
        v_note := 'backup table not exists';
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        v_status := 'FAILED';
        v_note := SUBSTR(SQLERRM,1,380);
    END;

    MERGE INTO MIG_P3_RB_CLEAN_EXEC t
    USING (
      SELECT 'P3_STAGE08' AS stage_no,
             'WAVE_01' AS wave_no,
             r.backup_name AS backup_name,
             v_status AS exec_status,
             v_note AS note
      FROM dual
    ) s
    ON (t.stage_no=s.stage_no AND t.wave_no=s.wave_no AND t.backup_name=s.backup_name)
    WHEN MATCHED THEN
      UPDATE SET t.exec_status=s.exec_status, t.note=s.note, t.updated_at=SYSDATE
    WHEN NOT MATCHED THEN
      INSERT (stage_no,wave_no,backup_name,exec_status,note,updated_at)
      VALUES (s.stage_no,s.wave_no,s.backup_name,s.exec_status,s.note,SYSDATE);
  END LOOP;
END;
/

PROMPT === 3) Write mainline log ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE08' AS batch_no,
         'TABLE' AS object_type,
         backup_name AS object_name,
         'STEP8_RB_FOOTPRINT_CLEAN' AS action_type,
         exec_status AS execute_status,
         note
  FROM MIG_P3_RB_CLEAN_EXEC
  WHERE stage_no='P3_STAGE08'
    AND wave_no='WAVE_01'
) s
ON (t.batch_no=s.batch_no AND t.object_type=s.object_type AND t.object_name=s.object_name AND t.action_type=s.action_type)
WHEN MATCHED THEN UPDATE SET t.execute_status=s.execute_status, t.note=s.note, t.executed_at=SYSDATE
WHEN NOT MATCHED THEN INSERT (batch_no,object_type,object_name,action_type,execute_status,note,executed_at)
                    VALUES (s.batch_no,s.object_type,s.object_name,s.action_type,s.execute_status,s.note,SYSDATE);
/

PROMPT === 4) Summary ===
SELECT exec_status, COUNT(*) AS cnt
FROM MIG_P3_RB_CLEAN_EXEC
WHERE stage_no='P3_STAGE08' AND wave_no='WAVE_01'
GROUP BY exec_status
ORDER BY exec_status;

SELECT 'TABLE' AS object_type, COUNT(*) AS cnt FROM user_tables
UNION ALL
SELECT 'VIEW' AS object_type, COUNT(*) AS cnt FROM user_views;

EXIT;
