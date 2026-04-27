SET ECHO ON;
SET SERVEROUTPUT ON;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20111, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 阻塞回写：缺少ITSM_CORE目标映射，不执行切换 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH02' AS batch_no,
         'VIEW' AS object_type,
         'ALL_LIST_V' AS object_name,
         'STEP2_MAPPING_GATE' AS action_type,
         'BLOCKED' AS execute_status,
         'no ITSM_CORE target view mapping found' AS note
  FROM dual
  UNION ALL
  SELECT 'P1_BATCH02','VIEW','WHCD_ITEM_V','STEP2_MAPPING_GATE','BLOCKED','no ITSM_CORE target view mapping found' FROM dual
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

UPDATE MIG_P1_OBJECT_WORKPACK
   SET status = 'BLOCKED',
       updated_at = SYSDATE
 WHERE batch_no = 'P1_BATCH02'
   AND wave_no = 'WAVE_01'
   AND source_object_name IN ('ALL_LIST_V', 'WHCD_ITEM_V')
   AND target_object_name = 'TBD_TARGET_OBJECT';
/

PROMPT === 2) BATCH02 汇总 ===
SELECT source_object_name, target_object_name, status
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH02'
  AND wave_no = 'WAVE_01'
ORDER BY source_object_name;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH02'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
