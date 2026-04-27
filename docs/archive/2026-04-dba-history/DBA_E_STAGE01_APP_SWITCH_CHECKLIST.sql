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
    raise_application_error(-20301, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 应用切换清单表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_E_APP_SWITCH_CHECKLIST (
      stage_no           VARCHAR2(30)  NOT NULL,
      item_code          VARCHAR2(40)  NOT NULL,
      item_name          VARCHAR2(200) NOT NULL,
      source_batch_no    VARCHAR2(30),
      check_value        VARCHAR2(200),
      check_status       VARCHAR2(20)  NOT NULL,
      note               VARCHAR2(400),
      updated_at         DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_MIG_E_APP_SWITCH_CHECK PRIMARY KEY (stage_no, item_code)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 刷新 E_STAGE01 应用切换清单 ===
DELETE FROM MIG_E_APP_SWITCH_CHECKLIST
WHERE stage_no = 'E_STAGE01';
/

INSERT INTO MIG_E_APP_SWITCH_CHECKLIST (
  stage_no, item_code, item_name, source_batch_no, check_value, check_status, note, updated_at
)
WITH metrics AS (
  SELECT
    (SELECT COUNT(*) FROM MIG_P1_OBJECT_WORKPACK WHERE batch_no='P1_BATCH07' AND status='DONE') AS b07_done_cnt,
    (SELECT COUNT(*) FROM MIG_P1_BATCH_LOG WHERE batch_no='P1_BATCH07' AND action_type='STEP4_FAST_CLOSE' AND execute_status='DONE') AS b07_fast_close_cnt,
    (SELECT COUNT(*) FROM MIG_P1_BATCH_ROLLBACK_ASSET WHERE batch_no='P1_BATCH07' AND status='READY') AS b07_rollback_ready_cnt,
    (SELECT COUNT(*) FROM MIG_P1_BATCH_LOG WHERE batch_no='P0_SOLIDIFY01' AND action_type='STEP0_DIFF_SOLIDIFY' AND execute_status='DONE') AS p0_diff_ok,
    (SELECT COUNT(*) FROM MIG_P1_BATCH_LOG WHERE batch_no='P0_SOLIDIFY01' AND action_type='STEP0_CLASS_SOLIDIFY' AND execute_status='DONE') AS p0_class_ok,
    (SELECT COUNT(*) FROM MIG_P1_BATCH_LOG WHERE batch_no='P1_BATCH01' AND object_name='APP_GRAY_WINDOW' AND action_type='STEP4_APP_WINDOW_READY' AND execute_status='READY') AS app_window_ok,
    (SELECT COUNT(*) FROM MIG_P1_BATCH_LOG WHERE batch_no='P1_BATCH01' AND object_name='APP_ROUTE_SWITCH' AND action_type='APP_ROUTE_SWITCH_DONE' AND execute_status='DONE') AS app_route_ok
  FROM dual
)
SELECT 'E_STAGE01', 'DB_B07_FAST_CLOSE', 'DB batch fast close (BATCH07)', 'P1_BATCH07',
       'DONE=' || TO_CHAR(m.b07_done_cnt) || ', FAST_CLOSE=' || TO_CHAR(m.b07_fast_close_cnt),
       CASE WHEN m.b07_done_cnt > 0 AND m.b07_fast_close_cnt = m.b07_done_cnt THEN 'READY' ELSE 'BLOCKED' END,
       'require STEP4_FAST_CLOSE cover all DONE objects', SYSDATE
FROM metrics m
UNION ALL
SELECT 'E_STAGE01', 'DB_B07_ROLLBACK', 'DB rollback assets ready (BATCH07)', 'P1_BATCH07',
       'ROLLBACK_READY=' || TO_CHAR(m.b07_rollback_ready_cnt),
       CASE WHEN m.b07_rollback_ready_cnt >= 10 THEN 'READY' ELSE 'BLOCKED' END,
       'minimum rollback assets threshold is 10', SYSDATE
FROM metrics m
UNION ALL
SELECT 'E_STAGE01', 'DB_P0_SOLIDIFY', 'P0 snapshot solidified', 'P0_SOLIDIFY01',
       'DIFF=' || TO_CHAR(m.p0_diff_ok) || ', CLASS=' || TO_CHAR(m.p0_class_ok),
       CASE WHEN m.p0_diff_ok > 0 AND m.p0_class_ok > 0 THEN 'READY' ELSE 'BLOCKED' END,
       'require both STEP0_DIFF_SOLIDIFY and STEP0_CLASS_SOLIDIFY', SYSDATE
FROM metrics m
UNION ALL
SELECT 'E_STAGE01', 'APP_GRAY_WINDOW', 'App gray window ready', 'P1_BATCH01',
       'WINDOW_READY=' || TO_CHAR(m.app_window_ok),
       CASE WHEN m.app_window_ok > 0 THEN 'READY' ELSE 'BLOCKED' END,
       'derived from STEP4_APP_WINDOW_READY result', SYSDATE
FROM metrics m
UNION ALL
SELECT 'E_STAGE01', 'APP_ROUTE_SWITCH', 'App route switch done record', 'P1_BATCH01',
       'ROUTE_DONE=' || TO_CHAR(m.app_route_ok),
       CASE WHEN m.app_route_ok > 0 THEN 'READY' ELSE 'PENDING' END,
       'if not DONE, application team should execute and write back', SYSDATE
FROM metrics m;

PROMPT === 3) 写入批次日志（E_STAGE01 清单状态） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'E_STAGE01' AS batch_no,
         'CONTROL' AS object_type,
         'APP_SWITCH_CHECKLIST' AS object_name,
         'STEP0_CHECKLIST_READY' AS action_type,
         CASE
           WHEN SUM(CASE WHEN check_status = 'BLOCKED' THEN 1 ELSE 0 END) = 0 THEN 'READY'
           ELSE 'BLOCKED'
         END AS execute_status,
         'application switch checklist persisted in MIG_E_APP_SWITCH_CHECKLIST' AS note
  FROM MIG_E_APP_SWITCH_CHECKLIST
  WHERE stage_no = 'E_STAGE01'
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

PROMPT === 4) E_STAGE01 清单摘要 ===
SELECT item_code, item_name, source_batch_no, check_value, check_status
FROM MIG_E_APP_SWITCH_CHECKLIST
WHERE stage_no = 'E_STAGE01'
ORDER BY item_code;

SELECT action_type, execute_status, note, executed_at
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'E_STAGE01'
  AND object_name = 'APP_SWITCH_CHECKLIST'
ORDER BY executed_at DESC;

EXIT;
