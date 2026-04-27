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
    raise_application_error(-20201, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 前置门禁：BATCH05 必须存在 PLANNED 对象 ===
DECLARE
  v_planned_cnt NUMBER := 0;
BEGIN
  SELECT COUNT(*)
    INTO v_planned_cnt
    FROM MIG_P1_OBJECT_WORKPACK
   WHERE batch_no = 'P1_BATCH05'
     AND wave_no = 'WAVE_01'
     AND status = 'PLANNED';

  IF v_planned_cnt = 0 THEN
    raise_application_error(-20202, 'BATCH05 planned objects not found, cnt=0');
  END IF;
END;
/

PROMPT === 2) 批量迁移（对 PLANNED 对象做 FULL LOAD，自动短名映射） ===
DECLARE
  v_sql      CLOB;
  v_src_name VARCHAR2(128);
  v_tgt_name VARCHAR2(30);
BEGIN
  FOR r IN (
    SELECT source_object_name AS src_name,
           'ITSM_C_' ||
           SUBSTR(source_object_name, 1, 18) ||
           '_' ||
           LPAD(TO_CHAR(MOD(ORA_HASH(source_object_name), 10000)), 4, '0') AS tgt_name
      FROM MIG_P1_OBJECT_WORKPACK
     WHERE batch_no = 'P1_BATCH05'
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

PROMPT === 3) 最小核验（逐对象输出源/目标行数） ===
DECLARE
  v_src_cnt NUMBER;
  v_tgt_cnt NUMBER;
  v_sql     VARCHAR2(4000);
BEGIN
  FOR r IN (
    SELECT source_object_name AS src_name,
           'ITSM_C_' ||
           SUBSTR(source_object_name, 1, 18) ||
           '_' ||
           LPAD(TO_CHAR(MOD(ORA_HASH(source_object_name), 10000)), 4, '0') AS tgt_name
      FROM MIG_P1_OBJECT_WORKPACK
     WHERE batch_no = 'P1_BATCH05'
       AND wave_no = 'WAVE_01'
     ORDER BY source_object_type, source_object_name
  ) LOOP
    v_sql := 'SELECT COUNT(*) FROM ' || r.src_name;
    EXECUTE IMMEDIATE v_sql INTO v_src_cnt;

    v_sql := 'SELECT COUNT(*) FROM ' || r.tgt_name;
    EXECUTE IMMEDIATE v_sql INTO v_tgt_cnt;

    DBMS_OUTPUT.PUT_LINE(
      RPAD(r.src_name, 40) || ' -> ' || RPAD(r.tgt_name, 30) ||
      ' SRC=' || TO_CHAR(v_src_cnt) || ', TGT=' || TO_CHAR(v_tgt_cnt)
    );
  END LOOP;
END;
/

PROMPT === 4) 状态回写（日志 + 工作包） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH05' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP2_BULK_MIGRATE' AS action_type,
         'DONE' AS execute_status,
         'bulk full-load to ' ||
         ('ITSM_C_' ||
          SUBSTR(source_object_name, 1, 18) ||
          '_' ||
          LPAD(TO_CHAR(MOD(ORA_HASH(source_object_name), 10000)), 4, '0')) AS note
    FROM MIG_P1_OBJECT_WORKPACK
   WHERE batch_no = 'P1_BATCH05'
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
   SET target_object_name = 'ITSM_C_' ||
                            SUBSTR(source_object_name, 1, 18) ||
                            '_' ||
                            LPAD(TO_CHAR(MOD(ORA_HASH(source_object_name), 10000)), 4, '0'),
       migration_strategy = 'FULL_LOAD_TABLE_BULK',
       status = 'DONE',
       updated_at = SYSDATE
 WHERE batch_no = 'P1_BATCH05'
   AND wave_no = 'WAVE_01'
   AND status = 'PLANNED';
/

PROMPT === 5) BATCH05 汇总状态 ===
SELECT source_object_name, target_object_name, migration_strategy, status
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH05'
  AND wave_no = 'WAVE_01'
ORDER BY source_object_name;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH05'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
