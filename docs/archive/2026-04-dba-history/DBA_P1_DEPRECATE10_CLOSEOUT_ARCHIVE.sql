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
    raise_application_error(-20421, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 收口归档表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_DEP_CLOSEOUT (
      batch_no         VARCHAR2(30) NOT NULL,
      wave_no          VARCHAR2(30) NOT NULL,
      total_cnt        NUMBER       NOT NULL,
      approved_cnt     NUMBER       NOT NULL,
      hold_cnt         NUMBER       NOT NULL,
      closeout_status  VARCHAR2(30) NOT NULL,
      closeout_note    VARCHAR2(300),
      updated_at       DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_DEP_CLOSEOUT PRIMARY KEY (batch_no, wave_no)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 收口归档计算（DEPRECATE09 -> DEPRECATE10） ===
MERGE INTO MIG_P1_DEP_CLOSEOUT t
USING (
  SELECT 'P1_DEPRECATE10' AS batch_no,
         'WAVE_10' AS wave_no,
         COUNT(*) AS total_cnt,
         SUM(CASE WHEN exec_status IN ('READY_FOR_MANUAL_EXEC', 'SKIPPED_BY_CTRL') THEN 1 ELSE 0 END) AS approved_cnt,
         SUM(CASE WHEN exec_status = 'SKIPPED_BY_CTRL' THEN 1 ELSE 0 END) AS hold_cnt,
         CASE
           WHEN SUM(CASE WHEN exec_status = 'SKIPPED_BY_CTRL' THEN 1 ELSE 0 END) > 0
             THEN 'CLOSED_HOLD'
           ELSE 'CLOSED_READY'
         END AS closeout_status,
         'deprecate closeout archived; non-destructive path retained' AS closeout_note
    FROM MIG_P1_DEP_EXEC_RES
   WHERE batch_no = 'P1_DEPRECATE09'
     AND wave_no = 'WAVE_09'
) s
ON (
  t.batch_no = s.batch_no
  AND t.wave_no = s.wave_no
)
WHEN MATCHED THEN
  UPDATE SET
    t.total_cnt = s.total_cnt,
    t.approved_cnt = s.approved_cnt,
    t.hold_cnt = s.hold_cnt,
    t.closeout_status = s.closeout_status,
    t.closeout_note = s.closeout_note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    batch_no, wave_no, total_cnt, approved_cnt, hold_cnt,
    closeout_status, closeout_note, updated_at
  )
  VALUES (
    s.batch_no, s.wave_no, s.total_cnt, s.approved_cnt, s.hold_cnt,
    s.closeout_status, s.closeout_note, SYSDATE
  );
/

PROMPT === 3) 批次日志回写（DEPRECATE10 收口完成） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_DEPRECATE10' AS batch_no,
         'CLOSEOUT' AS object_type,
         'DEPRECATE_PIPELINE' AS object_name,
         'STEP7_CLOSEOUT_ARCHIVE' AS action_type,
         CASE WHEN closeout_status IN ('CLOSED_HOLD', 'CLOSED_READY') THEN 'DONE' ELSE 'HOLD' END AS execute_status,
         closeout_note AS note
    FROM MIG_P1_DEP_CLOSEOUT
   WHERE batch_no = 'P1_DEPRECATE10'
     AND wave_no = 'WAVE_10'
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

PROMPT === 4) DEPRECATE10 摘要 ===
SELECT batch_no, wave_no, total_cnt, approved_cnt, hold_cnt, closeout_status
FROM MIG_P1_DEP_CLOSEOUT
WHERE batch_no = 'P1_DEPRECATE10'
  AND wave_no = 'WAVE_10';

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_DEPRECATE10'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
