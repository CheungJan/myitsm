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
    raise_application_error(-20069, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 影子写入总体统计（按结果） ===
SELECT compare_result, COUNT(*) AS cnt
FROM MIG_P1_SHADOW_WRITE_LOG
WHERE batch_no = 'P1_BATCH01'
GROUP BY compare_result
ORDER BY compare_result;

PROMPT === 2) 最近24小时影子写入统计 ===
SELECT compare_result, COUNT(*) AS cnt
FROM MIG_P1_SHADOW_WRITE_LOG
WHERE batch_no = 'P1_BATCH01'
  AND created_at_utc >= SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '1' DAY
GROUP BY compare_result
ORDER BY compare_result;

PROMPT === 3) 最近100条异常明细（DIFF/ERROR） ===
SELECT source_object, target_object, biz_key, action_type, compare_result, detail_msg, created_at_utc
FROM (
  SELECT source_object, target_object, biz_key, action_type, compare_result, detail_msg, created_at_utc
  FROM MIG_P1_SHADOW_WRITE_LOG
  WHERE batch_no = 'P1_BATCH01'
    AND compare_result IN ('DIFF', 'ERROR')
  ORDER BY created_at_utc DESC
)
WHERE ROWNUM <= 100;

PROMPT === 4) 写灰度门禁判定（基于最近24小时） ===
WITH recent_data AS (
  SELECT
    COUNT(*) AS total_cnt,
    SUM(CASE WHEN compare_result = 'MATCH' THEN 1 ELSE 0 END) AS match_cnt,
    SUM(CASE WHEN compare_result IN ('DIFF', 'ERROR') THEN 1 ELSE 0 END) AS bad_cnt
  FROM MIG_P1_SHADOW_WRITE_LOG
  WHERE batch_no = 'P1_BATCH01'
    AND created_at_utc >= SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '1' DAY
)
SELECT
  total_cnt,
  match_cnt,
  bad_cnt,
  CASE
    WHEN total_cnt = 0 THEN 'NO_TRAFFIC'
    WHEN bad_cnt = 0 THEN 'WRITE_GRAY_READY'
    ELSE 'WRITE_GRAY_BLOCKED'
  END AS write_gray_decision
FROM recent_data;

PROMPT === 5) 写入批次日志（Step3.3 监控） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no,
         'CONTROL' AS object_type,
         'SHADOW_MONITOR' AS object_name,
         'STEP3_3_SHADOW_MONITOR' AS action_type,
         'CHECKED' AS execute_status,
         'shadow monitor executed' AS note
  FROM dual
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

EXIT;
