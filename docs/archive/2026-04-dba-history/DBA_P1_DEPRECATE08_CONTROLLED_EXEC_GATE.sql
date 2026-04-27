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
    raise_application_error(-20401, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 受控执行结果表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_DEP_EXEC_RES (
      batch_no            VARCHAR2(30)  NOT NULL,
      wave_no             VARCHAR2(30)  NOT NULL,
      source_object_type  VARCHAR2(30)  NOT NULL,
      source_object_name  VARCHAR2(128) NOT NULL,
      exec_status         VARCHAR2(30)  NOT NULL,
      exec_note           VARCHAR2(300),
      updated_at          DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_DEP_EXEC_RES PRIMARY KEY (
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

PROMPT === 2) 按执行开关回写受控状态（不执行破坏性下线） ===
DECLARE
  v_dry_run_flag VARCHAR2(1);
  v_exec_flag    VARCHAR2(1);
  v_exec_status  VARCHAR2(30);
  v_exec_note    VARCHAR2(300);
BEGIN
  SELECT dry_run_flag, exec_flag
    INTO v_dry_run_flag, v_exec_flag
    FROM MIG_P1_DEP_EXEC_CTRL
   WHERE batch_no = 'P1_DEPRECATE07'
     AND wave_no = 'WAVE_07';

  IF v_dry_run_flag = 'Y' AND v_exec_flag = 'N' THEN
    v_exec_status := 'SKIPPED_BY_CTRL';
    v_exec_note := 'exec switch is OFF, keep non-destructive mode';
  ELSIF v_dry_run_flag = 'N' AND v_exec_flag = 'Y' THEN
    v_exec_status := 'READY_FOR_EXEC';
    v_exec_note := 'exec switch ON, pending manual execution window';
  ELSE
    raise_application_error(-20402, 'Invalid execute control combination');
  END IF;

  MERGE INTO MIG_P1_DEP_EXEC_RES t
  USING (
    SELECT 'P1_DEPRECATE08' AS batch_no,
           'WAVE_08' AS wave_no,
           p.source_object_type,
           p.source_object_name,
           v_exec_status AS exec_status,
           v_exec_note AS exec_note
      FROM MIG_P1_DEPRECATE_EXEC_PLAN p
     WHERE p.batch_no = 'P1_DEPRECATE06'
       AND p.wave_no = 'WAVE_06'
       AND p.plan_action = 'PLAN_DECOM_ONLY'
       AND p.plan_status = 'READY'
  ) s
  ON (
    t.batch_no = s.batch_no
    AND t.wave_no = s.wave_no
    AND t.source_object_type = s.source_object_type
    AND t.source_object_name = s.source_object_name
  )
  WHEN MATCHED THEN
    UPDATE SET
      t.exec_status = s.exec_status,
      t.exec_note = s.exec_note,
      t.updated_at = SYSDATE
  WHEN NOT MATCHED THEN
    INSERT (
      batch_no, wave_no, source_object_type, source_object_name,
      exec_status, exec_note, updated_at
    )
    VALUES (
      s.batch_no, s.wave_no, s.source_object_type, s.source_object_name,
      s.exec_status, s.exec_note, SYSDATE
    );
END;
/

PROMPT === 3) 写入批次日志（DEPRECATE08 受控门禁） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE08' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP5_EXEC_GATE' AS action_type,
         CASE
           WHEN exec_status = 'READY_FOR_EXEC' THEN 'READY'
           ELSE 'HOLD'
         END AS execute_status,
         exec_note AS note
    FROM MIG_P1_DEP_EXEC_RES
   WHERE batch_no = 'P1_DEPRECATE08'
     AND wave_no = 'WAVE_08'
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

PROMPT === 4) DEPRECATE08 摘要 ===
SELECT exec_status, COUNT(*) AS cnt
FROM MIG_P1_DEP_EXEC_RES
WHERE batch_no = 'P1_DEPRECATE08'
  AND wave_no = 'WAVE_08'
GROUP BY exec_status
ORDER BY exec_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_DEPRECATE08'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
