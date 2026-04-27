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
    raise_application_error(-20141, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 前置门禁：BATCH03 试点对象必须 READY ===
DECLARE
  v_ready_cnt NUMBER := 0;
BEGIN
  SELECT COUNT(*)
    INTO v_ready_cnt
    FROM MIG_P1_BATCH_LOG
   WHERE batch_no = 'P1_BATCH03'
     AND action_type = 'SNAPSHOT'
     AND execute_status = 'READY'
     AND object_name IN ('TIT03_SYSCODES', 'TIT04_ARCHIVECODE');

  IF v_ready_cnt < 2 THEN
    raise_application_error(-20142, 'BATCH03 pilot objects not ready, cnt=' || v_ready_cnt);
  END IF;
END;
/

PROMPT === 2) 试点迁移：TIT03_SYSCODES -> ITSM_CORE_TIT03_SYSCODES ===
BEGIN
  EXECUTE IMMEDIATE 'CREATE TABLE ITSM_CORE_TIT03_SYSCODES AS SELECT * FROM TIT03_SYSCODES WHERE 1=0';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

TRUNCATE TABLE ITSM_CORE_TIT03_SYSCODES;
INSERT INTO ITSM_CORE_TIT03_SYSCODES SELECT * FROM TIT03_SYSCODES;
COMMIT;

PROMPT === 3) 试点迁移：TIT04_ARCHIVECODE -> ITSM_CORE_TIT04_ARCHIVECODE ===
BEGIN
  EXECUTE IMMEDIATE 'CREATE TABLE ITSM_CORE_TIT04_ARCHIVECODE AS SELECT * FROM TIT04_ARCHIVECODE WHERE 1=0';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

TRUNCATE TABLE ITSM_CORE_TIT04_ARCHIVECODE;
INSERT INTO ITSM_CORE_TIT04_ARCHIVECODE SELECT * FROM TIT04_ARCHIVECODE;
COMMIT;

PROMPT === 4) 最小核验（行数一致） ===
SELECT 'TIT03_SYSCODES' AS metric_name, COUNT(*) AS metric_value FROM TIT03_SYSCODES
UNION ALL
SELECT 'ITSM_CORE_TIT03_SYSCODES', COUNT(*) FROM ITSM_CORE_TIT03_SYSCODES
UNION ALL
SELECT 'TIT04_ARCHIVECODE', COUNT(*) FROM TIT04_ARCHIVECODE
UNION ALL
SELECT 'ITSM_CORE_TIT04_ARCHIVECODE', COUNT(*) FROM ITSM_CORE_TIT04_ARCHIVECODE;

PROMPT === 5) 状态回写（日志+工作包） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH03' AS batch_no, 'TABLE' AS object_type, 'TIT03_SYSCODES' AS object_name, 'STEP1_PILOT_MIGRATE' AS action_type, 'DONE' AS execute_status, 'pilot full-load to ITSM_CORE_TIT03_SYSCODES' AS note FROM dual
  UNION ALL
  SELECT 'P1_BATCH03', 'TABLE', 'TIT04_ARCHIVECODE', 'STEP1_PILOT_MIGRATE', 'DONE', 'pilot full-load to ITSM_CORE_TIT04_ARCHIVECODE' FROM dual
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
   SET target_object_name = CASE
                              WHEN source_object_name = 'TIT03_SYSCODES' THEN 'ITSM_CORE_TIT03_SYSCODES'
                              WHEN source_object_name = 'TIT04_ARCHIVECODE' THEN 'ITSM_CORE_TIT04_ARCHIVECODE'
                              ELSE target_object_name
                            END,
       migration_strategy = 'FULL_LOAD_TABLE_PILOT',
       status = 'DONE',
       updated_at = SYSDATE
 WHERE batch_no = 'P1_BATCH03'
   AND wave_no = 'WAVE_01'
   AND source_object_name IN ('TIT03_SYSCODES', 'TIT04_ARCHIVECODE');
/

PROMPT === 6) BATCH03 状态汇总 ===
SELECT source_object_name, target_object_name, migration_strategy, status
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH03'
  AND wave_no = 'WAVE_01'
ORDER BY source_object_name;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH03'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
