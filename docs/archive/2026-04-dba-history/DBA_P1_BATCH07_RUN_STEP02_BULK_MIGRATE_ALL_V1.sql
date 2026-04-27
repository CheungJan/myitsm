SET ECHO ON;
SET SERVEROUTPUT ON;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;
  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20251, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 前置门禁：BATCH07 需存在 PLANNED ===
DECLARE
  v_planned_cnt NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_planned_cnt
  FROM MIG_P1_OBJECT_WORKPACK
  WHERE batch_no = 'P1_BATCH07'
    AND wave_no = 'WAVE_01'
    AND status = 'PLANNED';

  IF v_planned_cnt = 0 THEN
    raise_application_error(-20252, 'BATCH07 no planned objects');
  END IF;
END;
/

PROMPT === 2) 批量全量迁移（TABLE/VIEW 均落地为快照表） ===
DECLARE
  v_sql      CLOB;
  v_src_name VARCHAR2(128);
  v_tgt_name VARCHAR2(30);
BEGIN
  FOR r IN (
    SELECT source_object_type,
           source_object_name AS src_name,
           'ITSM_C_' ||
           SUBSTR(source_object_name, 1, 18) ||
           '_' ||
           LPAD(TO_CHAR(MOD(ORA_HASH(source_object_name), 10000)), 4, '0') AS tgt_name
    FROM MIG_P1_OBJECT_WORKPACK
    WHERE batch_no = 'P1_BATCH07'
      AND wave_no = 'WAVE_01'
      AND status = 'PLANNED'
    ORDER BY source_object_type, source_object_name
  ) LOOP
    v_src_name := r.src_name;
    v_tgt_name := r.tgt_name;

    BEGIN
      v_sql := 'CREATE TABLE ' || v_tgt_name || ' AS SELECT * FROM ' || v_src_name || ' WHERE 1=0';
      EXECUTE IMMEDIATE v_sql;
    EXCEPTION
      WHEN OTHERS THEN
        IF SQLCODE != -955 THEN
          RAISE;
        END IF;
    END;

    v_sql := 'TRUNCATE TABLE ' || v_tgt_name;
    EXECUTE IMMEDIATE v_sql;

    v_sql := 'INSERT INTO ' || v_tgt_name || ' SELECT * FROM ' || v_src_name;
    EXECUTE IMMEDIATE v_sql;

    COMMIT;
  END LOOP;
END;
/

PROMPT === 3) 状态回写 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH07' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP2_BULK_MIGRATE' AS action_type,
         'DONE' AS execute_status,
         'relaxed bulk full-load to ' ||
         ('ITSM_C_' || SUBSTR(source_object_name, 1, 18) || '_' || LPAD(TO_CHAR(MOD(ORA_HASH(source_object_name), 10000)), 4, '0')) AS note
  FROM MIG_P1_OBJECT_WORKPACK
  WHERE batch_no = 'P1_BATCH07'
    AND wave_no = 'WAVE_01'
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
SET target_object_name = 'ITSM_C_' || SUBSTR(source_object_name, 1, 18) || '_' || LPAD(TO_CHAR(MOD(ORA_HASH(source_object_name), 10000)), 4, '0'),
    migration_strategy = 'FULL_LOAD_TABLE_BULK_RELAXED',
    status = 'DONE',
    updated_at = SYSDATE
WHERE batch_no = 'P1_BATCH07'
  AND wave_no = 'WAVE_01'
  AND status = 'PLANNED';
/

PROMPT === 4) BATCH07 汇总 ===
SELECT status, COUNT(*) AS cnt
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH07'
GROUP BY status
ORDER BY status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH07'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
