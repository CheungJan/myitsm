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
    raise_application_error(-20441, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) P2 清单表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P2_STAGE_CHECK (
      stage_no      VARCHAR2(30)  NOT NULL,
      task_no       VARCHAR2(30)  NOT NULL,
      task_name     VARCHAR2(120) NOT NULL,
      task_status   VARCHAR2(20)  NOT NULL,
      note          VARCHAR2(400),
      updated_at    DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P2_STG_CHK PRIMARY KEY (stage_no, task_no)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 生成 P2_STAGE01 最小清单（回归/切换/兼容下线） ===
MERGE INTO MIG_P2_STAGE_CHECK t
USING (
  SELECT 'P2_STAGE01' AS stage_no,
         'TASK1_REGRESSION' AS task_no,
         UNISTR('\5206\6279\8FC1\79FB\56DE\5F52\6D4B\8BD5\5C31\7EEA') AS task_name,
         CASE
           WHEN EXISTS (
             SELECT 1
             FROM MIG_P1_BATCH_LOG
             WHERE batch_no = 'P2_STAGE00'
               AND action_type = 'STEP0_RESUME_GATE'
               AND execute_status = 'READY'
           ) THEN 'READY'
           ELSE 'BLOCKED'
         END AS task_status,
         'gate from P2_STAGE00 mainline resume' AS note
  FROM dual
  UNION ALL
  SELECT 'P2_STAGE01' AS stage_no,
         'TASK2_PY_SWITCH' AS task_no,
         UNISTR('\0050\0079\0074\0068\006F\006E\670D\52A1\5206\57DF\5207\6362\5C31\7EEA') AS task_name,
         CASE
           WHEN EXISTS (
             SELECT 1
             FROM MIG_P1_BATCH_LOG
             WHERE batch_no = 'E_STAGE01'
               AND action_type = 'STEP3_STABILITY_OK'
               AND execute_status = 'DONE'
           ) THEN 'READY'
           ELSE 'BLOCKED'
         END AS task_status,
         'gate from E_STAGE01 stability check' AS note
  FROM dual
  UNION ALL
  SELECT 'P2_STAGE01' AS stage_no,
         'TASK3_COMPAT_DOWN' AS task_no,
         UNISTR('\517C\5BB9\5C42\5206\6279\4E0B\7EBF\6392\7A0B') AS task_name,
         'HOLD' AS task_status,
         'follow after task1+task2 done' AS note
  FROM dual
) s
ON (
  t.stage_no = s.stage_no
  AND t.task_no = s.task_no
)
WHEN MATCHED THEN
  UPDATE SET
    t.task_name = s.task_name,
    t.task_status = s.task_status,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (stage_no, task_no, task_name, task_status, note, updated_at)
  VALUES (s.stage_no, s.task_no, s.task_name, s.task_status, s.note, SYSDATE);
/

PROMPT === 3) 回写主线日志（P2_STAGE01） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P2_STAGE01' AS batch_no,
         'MAINLINE' AS object_type,
         task_no AS object_name,
         'STEP1_CHECKLIST_READY' AS action_type,
         CASE
           WHEN task_status = 'READY' THEN 'READY'
           WHEN task_status = 'HOLD' THEN 'HOLD'
           ELSE 'BLOCKED'
         END AS execute_status,
         note AS note
  FROM MIG_P2_STAGE_CHECK
  WHERE stage_no = 'P2_STAGE01'
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

PROMPT === 4) P2_STAGE01 摘要 ===
SELECT task_no, task_status, note
FROM MIG_P2_STAGE_CHECK
WHERE stage_no = 'P2_STAGE01'
ORDER BY task_no;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P2_STAGE01'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
