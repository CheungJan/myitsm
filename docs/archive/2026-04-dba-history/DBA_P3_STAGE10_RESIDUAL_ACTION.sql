SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 300;
SET LINESIZE 260;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME')) INTO v_service_name FROM dual;
  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20581, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 残留处置清单表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_RESIDUAL_ACTION (
      stage_no        VARCHAR2(30)  NOT NULL,
      wave_no         VARCHAR2(30)  NOT NULL,
      object_type     VARCHAR2(30)  NOT NULL,
      object_name     VARCHAR2(128) NOT NULL,
      action_plan     VARCHAR2(30)  NOT NULL,
      action_status   VARCHAR2(20)  NOT NULL,
      note            VARCHAR2(400),
      updated_at      DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_RES_ACTION PRIMARY KEY (
        stage_no, wave_no, object_type, object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN RAISE; END IF;
END;
/

PROMPT === 2) 装载仍存在的残留对象（若有） ===
MERGE INTO MIG_P3_RESIDUAL_ACTION t
USING (
  SELECT 'P3_STAGE10' AS stage_no,
         'WAVE_01' AS wave_no,
         c.object_type,
         c.object_name,
         'REVIEW_FINAL_DROP' AS action_plan,
         'PENDING_CONFIRM' AS action_status,
         'trim candidate still exists after P3_STAGE07/08' AS note
  FROM MIG_P3_L0_TRIM_CAND c
  WHERE c.stage_no='P3_STAGE05'
    AND c.wave_no='WAVE_01'
    AND c.candidate_type='TRIM_CANDIDATE'
    AND EXISTS (
      SELECT 1 FROM (
        SELECT 'TABLE' AS object_type, table_name AS object_name FROM user_tables
        UNION ALL
        SELECT 'VIEW'  AS object_type, view_name AS object_name FROM user_views
      ) a
      WHERE a.object_type = c.object_type
        AND a.object_name = c.object_name
    )
) s
ON (
  t.stage_no=s.stage_no
  AND t.wave_no=s.wave_no
  AND t.object_type=s.object_type
  AND t.object_name=s.object_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.action_plan=s.action_plan,
    t.action_status=s.action_status,
    t.note=s.note,
    t.updated_at=SYSDATE
WHEN NOT MATCHED THEN
  INSERT (stage_no,wave_no,object_type,object_name,action_plan,action_status,note,updated_at)
  VALUES (s.stage_no,s.wave_no,s.object_type,s.object_name,s.action_plan,s.action_status,s.note,SYSDATE);
/

PROMPT === 3) 回写主线日志 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE10' AS batch_no,
         object_type,
         object_name,
         'STEP10_RESIDUAL_ACTION' AS action_type,
         action_status AS execute_status,
         note
  FROM MIG_P3_RESIDUAL_ACTION
  WHERE stage_no='P3_STAGE10'
    AND wave_no='WAVE_01'
) s
ON (t.batch_no=s.batch_no AND t.object_type=s.object_type AND t.object_name=s.object_name AND t.action_type=s.action_type)
WHEN MATCHED THEN
  UPDATE SET t.execute_status=s.execute_status, t.note=s.note, t.executed_at=SYSDATE
WHEN NOT MATCHED THEN
  INSERT (batch_no,object_type,object_name,action_type,execute_status,note,executed_at)
  VALUES (s.batch_no,s.object_type,s.object_name,s.action_type,s.execute_status,s.note,SYSDATE);
/

PROMPT === 4) 摘要 ===
SELECT COUNT(*) AS residual_cnt
FROM MIG_P3_RESIDUAL_ACTION
WHERE stage_no='P3_STAGE10'
  AND wave_no='WAVE_01';

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no='P3_STAGE10'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
