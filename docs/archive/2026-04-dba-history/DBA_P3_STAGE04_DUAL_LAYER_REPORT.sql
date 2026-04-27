SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 300;
SET LINESIZE 260;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) Safety gate: only run on CCGL_MIG ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20521, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) Gate check: P3_STAGE03 must be done ===
DECLARE
  v_done_cnt NUMBER;
BEGIN
  SELECT COUNT(*)
    INTO v_done_cnt
    FROM MIG_P1_BATCH_LOG
   WHERE batch_no = 'P3_STAGE03'
     AND action_type = 'STEP3_L1_VERIFY'
     AND execute_status = 'DONE';

  IF v_done_cnt = 0 THEN
    raise_application_error(-20522, 'P3_STAGE03 is not done');
  END IF;
END;
/

PROMPT === 2) Ensure dual-layer report table exists ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_DUAL_LAYER_RPT (
      stage_no             VARCHAR2(30) NOT NULL,
      wave_no              VARCHAR2(30) NOT NULL,
      l0_total_objects     NUMBER       NOT NULL,
      l1_frozen_objects    NUMBER       NOT NULL,
      l1_verified_objects  NUMBER       NOT NULL,
      reduction_ratio_pct  NUMBER(10,2) NOT NULL,
      report_status        VARCHAR2(20) NOT NULL,
      note                 VARCHAR2(400),
      updated_at           DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_DUAL_RPT PRIMARY KEY (stage_no, wave_no)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 3) Build dual-layer report (L0 baseline vs L1 simplified) ===
MERGE INTO MIG_P3_DUAL_LAYER_RPT t
USING (
  WITH l0 AS (
    SELECT COUNT(*) AS cnt
    FROM (
      SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
      UNION ALL
      SELECT view_name AS object_name, 'VIEW' AS object_type FROM user_views
    )
  ),
  l1f AS (
    SELECT COUNT(*) AS cnt
    FROM MIG_P3_L1_OBJECT_SET
    WHERE stage_no = 'P3_STAGE02'
      AND wave_no = 'WAVE_01'
      AND freeze_status = 'FROZEN'
  ),
  l1v AS (
    SELECT COUNT(*) AS cnt
    FROM MIG_P3_L1_VERIFY
    WHERE stage_no = 'P3_STAGE03'
      AND wave_no = 'WAVE_01'
      AND verify_status = 'DONE'
  )
  SELECT 'P3_STAGE04' AS stage_no,
         'WAVE_01' AS wave_no,
         l0.cnt AS l0_total_objects,
         l1f.cnt AS l1_frozen_objects,
         l1v.cnt AS l1_verified_objects,
         ROUND(CASE WHEN l0.cnt = 0 THEN 0 ELSE (1 - (l1f.cnt / l0.cnt)) * 100 END, 2) AS reduction_ratio_pct,
         CASE WHEN l1v.cnt > 0 THEN 'DONE' ELSE 'BLOCKED' END AS report_status,
         'L0 keeps full baseline; L1 is simplified governed set' AS note
  FROM l0, l1f, l1v
) s
ON (
  t.stage_no = s.stage_no
  AND t.wave_no = s.wave_no
)
WHEN MATCHED THEN
  UPDATE SET
    t.l0_total_objects = s.l0_total_objects,
    t.l1_frozen_objects = s.l1_frozen_objects,
    t.l1_verified_objects = s.l1_verified_objects,
    t.reduction_ratio_pct = s.reduction_ratio_pct,
    t.report_status = s.report_status,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    stage_no, wave_no, l0_total_objects, l1_frozen_objects, l1_verified_objects,
    reduction_ratio_pct, report_status, note, updated_at
  )
  VALUES (
    s.stage_no, s.wave_no, s.l0_total_objects, s.l1_frozen_objects, s.l1_verified_objects,
    s.reduction_ratio_pct, s.report_status, s.note, SYSDATE
  );
/

PROMPT === 4) Write P3_STAGE04 log ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE04' AS batch_no,
         'MAINLINE' AS object_type,
         'DUAL_LAYER_REPORT' AS object_name,
         'STEP4_DUAL_LAYER_REPORT' AS action_type,
         report_status AS execute_status,
         note AS note
  FROM MIG_P3_DUAL_LAYER_RPT
  WHERE stage_no = 'P3_STAGE04'
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

PROMPT === 5) Summary ===
SELECT stage_no,
       wave_no,
       l0_total_objects,
       l1_frozen_objects,
       l1_verified_objects,
       reduction_ratio_pct,
       report_status,
       note
FROM MIG_P3_DUAL_LAYER_RPT
WHERE stage_no = 'P3_STAGE04'
  AND wave_no = 'WAVE_01';

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P3_STAGE04'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
