SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 200;
SET LINESIZE 240;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20391, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 执行控制表存在性保障（默认 DRY_RUN） ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_DEP_EXEC_CTRL (
      batch_no      VARCHAR2(30) NOT NULL,
      wave_no       VARCHAR2(30) NOT NULL,
      dry_run_flag  VARCHAR2(1)  NOT NULL,
      exec_flag     VARCHAR2(1)  NOT NULL,
      note          VARCHAR2(200),
      updated_at    DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_DEP_EXEC_CTRL PRIMARY KEY (batch_no, wave_no)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

MERGE INTO MIG_P1_DEP_EXEC_CTRL t
USING (
  SELECT 'P1_DEPRECATE07' AS batch_no,
         'WAVE_07' AS wave_no,
         'Y' AS dry_run_flag,
         'N' AS exec_flag,
         'release window dry run only, no destructive decommission' AS note
  FROM dual
) s
ON (
  t.batch_no = s.batch_no
  AND t.wave_no = s.wave_no
)
WHEN MATCHED THEN
  UPDATE SET
    t.dry_run_flag = s.dry_run_flag,
    t.exec_flag = s.exec_flag,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (batch_no, wave_no, dry_run_flag, exec_flag, note, updated_at)
  VALUES (s.batch_no, s.wave_no, s.dry_run_flag, s.exec_flag, s.note, SYSDATE);
/

PROMPT === 2) 发布窗口 DRY_RUN 门禁校验 ===
DECLARE
  v_ready_cnt NUMBER;
  v_dry_run_flag VARCHAR2(1);
  v_exec_flag VARCHAR2(1);
BEGIN
  SELECT COUNT(*)
    INTO v_ready_cnt
    FROM MIG_P1_DEPRECATE_EXEC_PLAN
   WHERE batch_no = 'P1_DEPRECATE06'
     AND wave_no = 'WAVE_06'
     AND plan_action = 'PLAN_DECOM_ONLY'
     AND plan_status = 'READY';

  IF v_ready_cnt = 0 THEN
    raise_application_error(-20392, 'No ready execution plan rows for P1_DEPRECATE06/WAVE_06');
  END IF;

  SELECT dry_run_flag, exec_flag
    INTO v_dry_run_flag, v_exec_flag
    FROM MIG_P1_DEP_EXEC_CTRL
   WHERE batch_no = 'P1_DEPRECATE07'
     AND wave_no = 'WAVE_07';

  IF v_dry_run_flag <> 'Y' OR v_exec_flag <> 'N' THEN
    raise_application_error(-20393, 'Dry run control not satisfied: dry_run_flag must be Y and exec_flag must be N');
  END IF;
END;
/

PROMPT === 3) 回写批次日志（仅 DRY_RUN 就绪） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE07' AS batch_no,
         p.source_object_type AS object_type,
         p.source_object_name AS object_name,
         'STEP4_RELEASE_DRY_RUN' AS action_type,
         'READY' AS execute_status,
         'dry run passed, no destructive decommission executed' AS note
    FROM MIG_P1_DEPRECATE_EXEC_PLAN p
   WHERE p.batch_no = 'P1_DEPRECATE06'
     AND p.wave_no = 'WAVE_06'
     AND p.plan_action = 'PLAN_DECOM_ONLY'
     AND p.plan_status = 'READY'
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

PROMPT === 4) DEPRECATE07 摘要 ===
SELECT batch_no, wave_no, dry_run_flag, exec_flag, note
FROM MIG_P1_DEP_EXEC_CTRL
WHERE batch_no = 'P1_DEPRECATE07'
  AND wave_no = 'WAVE_07';

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_DEPRECATE07'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
