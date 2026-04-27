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
    raise_application_error(-20561, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Rollback P3_STAGE07 objects ===
DECLARE
  FUNCTION qname(p_name VARCHAR2) RETURN VARCHAR2 IS
  BEGIN
    RETURN '"' || REPLACE(p_name, '"', '""') || '"';
  END;

  v_exists NUMBER;
  v_status VARCHAR2(20);
  v_note VARCHAR2(400);
BEGIN
  FOR r IN (
    SELECT object_type, object_name, backup_name, ddl_text
    FROM MIG_P3_L0_TRIM_RB
    WHERE stage_no='P3_STAGE07'
      AND wave_no='WAVE_01'
    ORDER BY object_type, object_name
  ) LOOP
    v_status := 'DONE';
    v_note := 'rollback restored';
    BEGIN
      IF r.object_type = 'TABLE' THEN
        SELECT COUNT(*) INTO v_exists FROM user_tables WHERE table_name = r.object_name;
        IF v_exists = 0 AND r.backup_name IS NOT NULL THEN
          EXECUTE IMMEDIATE 'ALTER TABLE ' || qname(r.backup_name) || ' RENAME TO ' || qname(r.object_name);
        ELSE
          v_status := 'SKIPPED';
          v_note := 'table already exists or backup missing';
        END IF;
      ELSIF r.object_type = 'VIEW' THEN
        SELECT COUNT(*) INTO v_exists FROM user_objects WHERE object_type='VIEW' AND object_name=r.object_name;
        IF v_exists = 0 AND r.ddl_text IS NOT NULL THEN
          EXECUTE IMMEDIATE TO_CHAR(r.ddl_text);
        ELSE
          v_status := 'SKIPPED';
          v_note := 'view already exists or ddl missing';
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

    MERGE INTO MIG_P1_BATCH_LOG t
    USING (
      SELECT 'P3_STAGE07_RB' AS batch_no,
             r.object_type AS object_type,
             r.object_name AS object_name,
             'STEP_RB_RESTORE' AS action_type,
             v_status AS execute_status,
             v_note AS note
      FROM dual
    ) s
    ON (
      t.batch_no=s.batch_no AND t.object_type=s.object_type AND t.object_name=s.object_name AND t.action_type=s.action_type
    )
    WHEN MATCHED THEN
      UPDATE SET t.execute_status=s.execute_status, t.note=s.note, t.executed_at=SYSDATE
    WHEN NOT MATCHED THEN
      INSERT (batch_no,object_type,object_name,action_type,execute_status,note,executed_at)
      VALUES (s.batch_no,s.object_type,s.object_name,s.action_type,s.execute_status,s.note,SYSDATE);
  END LOOP;
END;
/

PROMPT === 2) Summary ===
SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no='P3_STAGE07_RB'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
