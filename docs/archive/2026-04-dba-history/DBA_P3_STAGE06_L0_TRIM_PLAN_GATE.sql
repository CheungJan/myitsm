SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 300;
SET LINESIZE 260;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20541, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 裁剪控制表存在性保障（默认不开启执行） ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_L0_TRIM_CTRL (
      stage_no      VARCHAR2(30) NOT NULL,
      wave_no       VARCHAR2(30) NOT NULL,
      dry_run_flag  VARCHAR2(1)  NOT NULL,
      exec_flag     VARCHAR2(1)  NOT NULL,
      note          VARCHAR2(300),
      updated_at    DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_L0_TRIM_CTRL PRIMARY KEY (stage_no, wave_no)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

MERGE INTO MIG_P3_L0_TRIM_CTRL t
USING (
  SELECT 'P3_STAGE06' AS stage_no,
         'WAVE_01' AS wave_no,
         'Y' AS dry_run_flag,
         'N' AS exec_flag,
         'trim execution is disabled by default, plan only' AS note
  FROM dual
) s
ON (
  t.stage_no = s.stage_no
  AND t.wave_no = s.wave_no
)
WHEN MATCHED THEN
  UPDATE SET
    t.dry_run_flag = s.dry_run_flag,
    t.exec_flag = s.exec_flag,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (stage_no, wave_no, dry_run_flag, exec_flag, note, updated_at)
  VALUES (s.stage_no, s.wave_no, s.dry_run_flag, s.exec_flag, s.note, SYSDATE);
/

PROMPT === 2) 裁剪计划表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_L0_TRIM_PLAN (
      stage_no        VARCHAR2(30)  NOT NULL,
      wave_no         VARCHAR2(30)  NOT NULL,
      object_type     VARCHAR2(30)  NOT NULL,
      object_name     VARCHAR2(128) NOT NULL,
      plan_action     VARCHAR2(30)  NOT NULL,
      plan_status     VARCHAR2(20)  NOT NULL,
      rollback_req    VARCHAR2(10)  NOT NULL,
      note            VARCHAR2(400),
      updated_at      DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_L0_TRIM_PLAN PRIMARY KEY (
        stage_no, wave_no, object_type, object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 3) 生成受控裁剪执行计划（仅计划，不执行） ===
MERGE INTO MIG_P3_L0_TRIM_PLAN t
USING (
  SELECT 'P3_STAGE06' AS stage_no,
         'WAVE_01' AS wave_no,
         c.object_type,
         c.object_name,
         'REVIEW_DROP' AS plan_action,
         CASE
           WHEN ctrl.exec_flag = 'Y' AND ctrl.dry_run_flag = 'N' THEN 'READY_FOR_EXEC'
           ELSE 'READY_FOR_REVIEW'
         END AS plan_status,
         'YES' AS rollback_req,
         'candidate from P3_STAGE05, execution still gated' AS note
  FROM MIG_P3_L0_TRIM_CAND c
  CROSS JOIN MIG_P3_L0_TRIM_CTRL ctrl
  WHERE c.stage_no = 'P3_STAGE05'
    AND c.wave_no = 'WAVE_01'
    AND c.candidate_type = 'TRIM_CANDIDATE'
    AND ctrl.stage_no = 'P3_STAGE06'
    AND ctrl.wave_no = 'WAVE_01'
) s
ON (
  t.stage_no = s.stage_no
  AND t.wave_no = s.wave_no
  AND t.object_type = s.object_type
  AND t.object_name = s.object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.plan_action = s.plan_action,
    t.plan_status = s.plan_status,
    t.rollback_req = s.rollback_req,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    stage_no, wave_no, object_type, object_name,
    plan_action, plan_status, rollback_req, note, updated_at
  )
  VALUES (
    s.stage_no, s.wave_no, s.object_type, s.object_name,
    s.plan_action, s.plan_status, s.rollback_req, s.note, SYSDATE
  );
/

PROMPT === 4) 回写主线日志 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE06' AS batch_no,
         object_type,
         object_name,
         'STEP6_TRIM_PLAN_GATE' AS action_type,
         CASE
           WHEN plan_status = 'READY_FOR_EXEC' THEN 'READY'
           ELSE 'HOLD'
         END AS execute_status,
         note AS note
  FROM MIG_P3_L0_TRIM_PLAN
  WHERE stage_no = 'P3_STAGE06'
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

PROMPT === 5) 摘要 ===
SELECT dry_run_flag, exec_flag, note
FROM MIG_P3_L0_TRIM_CTRL
WHERE stage_no = 'P3_STAGE06'
  AND wave_no = 'WAVE_01';

SELECT plan_status, COUNT(*) AS cnt
FROM MIG_P3_L0_TRIM_PLAN
WHERE stage_no = 'P3_STAGE06'
  AND wave_no = 'WAVE_01'
GROUP BY plan_status
ORDER BY plan_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P3_STAGE06'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
