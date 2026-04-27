SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 200;
SET LINESIZE 220;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20068, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 历史 action_type 回填到 Step3.x（仅补写，不覆盖旧记录） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT
    batch_no,
    object_type,
    object_name,
    CASE
      WHEN action_type = 'RUN_STEP03' THEN 'STEP3_1_READINESS'
      WHEN action_type = 'RUN_STEP04' THEN 'STEP3_2_READ_CUTOVER'
      WHEN action_type = 'RUN_STEP05' AND object_name = 'WRITE_GATE' THEN 'STEP3_3_WRITE_GATE'
      WHEN action_type = 'RUN_STEP05' AND object_name = 'SHADOW_WRITE_TEMPLATE' THEN 'STEP3_3_SHADOW_TEMPLATE'
      ELSE NULL
    END AS action_type,
    execute_status,
    note,
    executed_at
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH01'
    AND action_type IN ('RUN_STEP03', 'RUN_STEP04', 'RUN_STEP05')
) s
ON (
  t.batch_no = s.batch_no
  AND t.object_type = s.object_type
  AND t.object_name = s.object_name
  AND t.action_type = s.action_type
)
WHEN NOT MATCHED THEN
  INSERT (batch_no, object_type, object_name, action_type, execute_status, note, executed_at)
  VALUES (
    s.batch_no,
    s.object_type,
    s.object_name,
    s.action_type,
    s.execute_status,
    '[BACKFILL_3PHASE] ' || s.note,
    NVL(s.executed_at, SYSDATE)
  );
/

PROMPT === 2) 回填后统计（旧值/新值并行展示） ===
SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
  AND action_type IN (
    'RUN_STEP03', 'RUN_STEP04', 'RUN_STEP05',
    'STEP3_1_READINESS', 'STEP3_2_READ_CUTOVER',
    'STEP3_3_WRITE_GATE', 'STEP3_3_SHADOW_TEMPLATE'
  )
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

PROMPT === 3) 三段式汇总口径 ===
WITH mapped AS (
  SELECT
    CASE
      WHEN action_type IN ('RUN_STEP01', 'RUN_STEP02') THEN 'STEP2_MIGRATE_AND_VERIFY'
      WHEN action_type IN ('RUN_STEP03', 'STEP3_1_READINESS') THEN 'STEP3_1_READINESS'
      WHEN action_type IN ('RUN_STEP04', 'STEP3_2_READ_CUTOVER') THEN 'STEP3_2_READ_CUTOVER'
      WHEN action_type IN ('RUN_STEP05', 'STEP3_3_WRITE_GATE', 'STEP3_3_SHADOW_TEMPLATE') THEN 'STEP3_3_WRITE_PREPARE'
      WHEN action_type = 'SNAPSHOT' THEN 'STEP1_WORKPACK_SNAPSHOT'
      ELSE action_type
    END AS action_type_3phase,
    execute_status
  FROM MIG_P1_BATCH_LOG
  WHERE batch_no = 'P1_BATCH01'
)
SELECT action_type_3phase, execute_status, COUNT(*) AS cnt
FROM mapped
GROUP BY action_type_3phase, execute_status
ORDER BY action_type_3phase, execute_status;

EXIT;
