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
    raise_application_error(-20531, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 候选清单表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_L0_TRIM_CAND (
      stage_no          VARCHAR2(30)  NOT NULL,
      wave_no           VARCHAR2(30)  NOT NULL,
      object_type       VARCHAR2(30)  NOT NULL,
      object_name       VARCHAR2(128) NOT NULL,
      candidate_type    VARCHAR2(30)  NOT NULL,
      reason            VARCHAR2(400),
      updated_at        DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_L0_TRIM_CAND PRIMARY KEY (
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

PROMPT === 2) 生成 L0 裁剪候选（只读口径，非破坏性） ===
MERGE INTO MIG_P3_L0_TRIM_CAND t
USING (
  WITH baseline AS (
    SELECT 'TABLE' AS object_type, table_name AS object_name FROM user_tables
    UNION ALL
    SELECT 'VIEW' AS object_type, view_name AS object_name FROM user_views
  ),
  l1_keep_src AS (
    SELECT source_object_type AS object_type,
           source_object_name AS object_name
    FROM MIG_P3_L1_OBJECT_SET
    WHERE stage_no = 'P3_STAGE02'
      AND wave_no = 'WAVE_01'
      AND freeze_status = 'FROZEN'
  ),
  l1_keep_tgt AS (
    SELECT source_object_type AS object_type,
           target_object_name AS object_name
    FROM MIG_P3_L1_OBJECT_SET
    WHERE stage_no = 'P3_STAGE02'
      AND wave_no = 'WAVE_01'
      AND freeze_status = 'FROZEN'
      AND target_object_name IS NOT NULL
  )
  SELECT 'P3_STAGE05' AS stage_no,
         'WAVE_01' AS wave_no,
         b.object_type,
         b.object_name,
         CASE
           WHEN EXISTS (
             SELECT 1 FROM l1_keep_src s
             WHERE s.object_type = b.object_type
               AND s.object_name = b.object_name
           ) THEN 'KEEP_SRC'
           WHEN EXISTS (
             SELECT 1 FROM l1_keep_tgt s
             WHERE s.object_type = b.object_type
               AND s.object_name = b.object_name
           ) THEN 'KEEP_TGT'
           WHEN b.object_name LIKE 'MIG\_%' ESCAPE '\' THEN 'INFRA'
           WHEN b.object_name LIKE 'ITSM\_%' ESCAPE '\' THEN 'INFRA'
           ELSE 'TRIM_CANDIDATE'
         END AS candidate_type,
         CASE
           WHEN EXISTS (
             SELECT 1 FROM l1_keep_src s
             WHERE s.object_type = b.object_type
               AND s.object_name = b.object_name
           ) THEN 'in L1 source keep set'
           WHEN EXISTS (
             SELECT 1 FROM l1_keep_tgt s
             WHERE s.object_type = b.object_type
               AND s.object_name = b.object_name
           ) THEN 'in L1 target keep set'
           WHEN b.object_name LIKE 'MIG\_%' ESCAPE '\' THEN 'migration governance infrastructure object'
           WHEN b.object_name LIKE 'ITSM\_%' ESCAPE '\' THEN 'target model or integration object'
           ELSE 'not in L1 keep set, candidate for L0 trim review'
         END AS reason
  FROM baseline b
) s
ON (
  t.stage_no = s.stage_no
  AND t.wave_no = s.wave_no
  AND t.object_type = s.object_type
  AND t.object_name = s.object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.candidate_type = s.candidate_type,
    t.reason = s.reason,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    stage_no, wave_no, object_type, object_name,
    candidate_type, reason, updated_at
  )
  VALUES (
    s.stage_no, s.wave_no, s.object_type, s.object_name,
    s.candidate_type, s.reason, SYSDATE
  );
/

PROMPT === 3) 回写主线日志 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE05' AS batch_no,
         object_type,
         object_name,
         'STEP5_TRIM_CANDIDATE_READY' AS action_type,
         CASE WHEN candidate_type = 'TRIM_CANDIDATE' THEN 'READY' ELSE 'DONE' END AS execute_status,
         reason AS note
  FROM MIG_P3_L0_TRIM_CAND
  WHERE stage_no = 'P3_STAGE05'
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

PROMPT === 4) 摘要 ===
SELECT candidate_type, COUNT(*) AS cnt
FROM MIG_P3_L0_TRIM_CAND
WHERE stage_no = 'P3_STAGE05'
  AND wave_no = 'WAVE_01'
GROUP BY candidate_type
ORDER BY candidate_type;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P3_STAGE05'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
