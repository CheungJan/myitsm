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
    raise_application_error(-20121, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 前置门禁：仅处理 BATCH02 中 BLOCKED 的两对象 ===
DECLARE
  v_blocked_cnt NUMBER := 0;
BEGIN
  SELECT COUNT(*)
    INTO v_blocked_cnt
    FROM MIG_P1_OBJECT_WORKPACK
   WHERE batch_no = 'P1_BATCH02'
     AND wave_no = 'WAVE_01'
     AND source_object_name IN ('ALL_LIST_V', 'WHCD_ITEM_V')
     AND status = 'BLOCKED';

  IF v_blocked_cnt < 2 THEN
    raise_application_error(-20122, 'blocked objects not ready for unblock, cnt=' || v_blocked_cnt);
  END IF;
END;
/

PROMPT === 2) 建立 ITSM_CORE 过渡目标视图（远端源兜底） ===
CREATE OR REPLACE VIEW ITSM_CORE_ALL_LIST_V AS
SELECT
  CUSTCD,
  CUSTNM,
  CUSTCARD,
  ADDRESS,
  PHONENO,
  POSCD,
  POSNAME,
  ITEMCD,
  ITEMNAME,
  ITEMEID,
  POSEID,
  OLD_DEGREE,
  START_DATE,
  END_DATE,
  POSCLASSCD,
  ITEMCLASSCD,
  ASSET_TYPE
FROM ALL_LIST_V@CCGLPDB_LINK;
/

CREATE OR REPLACE VIEW ITSM_CORE_WHCD_ITEM_V AS
SELECT
  CLASSCD,
  ITEMCD,
  ITEMNM,
  ITEMTYP,
  WHCD,
  TNUMBER,
  TWHCD
FROM WHCD_ITEM_V@CCGLPDB_LINK;
/

PROMPT === 3) 源视图切换到 ITSM_CORE 过渡目标 ===
CREATE OR REPLACE VIEW ALL_LIST_V AS
SELECT
  CUSTCD,
  CUSTNM,
  CUSTCARD,
  ADDRESS,
  PHONENO,
  POSCD,
  POSNAME,
  ITEMCD,
  ITEMNAME,
  ITEMEID,
  POSEID,
  OLD_DEGREE,
  START_DATE,
  END_DATE,
  POSCLASSCD,
  ITEMCLASSCD,
  ASSET_TYPE
FROM ITSM_CORE_ALL_LIST_V;
/

CREATE OR REPLACE VIEW WHCD_ITEM_V AS
SELECT
  CLASSCD,
  ITEMCD,
  ITEMNM,
  ITEMTYP,
  WHCD,
  TNUMBER,
  TWHCD
FROM ITSM_CORE_WHCD_ITEM_V;
/

PROMPT === 4) 最小核验（状态 + 行数） ===
SELECT object_name, object_type, status
FROM user_objects
WHERE object_name IN (
  'ALL_LIST_V',
  'WHCD_ITEM_V',
  'ITSM_CORE_ALL_LIST_V',
  'ITSM_CORE_WHCD_ITEM_V'
)
ORDER BY object_name;

SELECT 'ALL_LIST_V' AS view_name, COUNT(*) AS row_count FROM ALL_LIST_V
UNION ALL
SELECT 'ITSM_CORE_ALL_LIST_V', COUNT(*) FROM ITSM_CORE_ALL_LIST_V
UNION ALL
SELECT 'WHCD_ITEM_V', COUNT(*) FROM WHCD_ITEM_V
UNION ALL
SELECT 'ITSM_CORE_WHCD_ITEM_V', COUNT(*) FROM ITSM_CORE_WHCD_ITEM_V;

PROMPT === 5) 回写日志 + 工作包收口 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH02' AS batch_no, 'VIEW' AS object_type, 'ALL_LIST_V' AS object_name, 'STEP3_FAST_UNBLOCK' AS action_type, 'DONE' AS execute_status, 'mapped to ITSM_CORE_ALL_LIST_V via CCGLPDB_LINK' AS note FROM dual
  UNION ALL
  SELECT 'P1_BATCH02', 'VIEW', 'WHCD_ITEM_V', 'STEP3_FAST_UNBLOCK', 'DONE', 'mapped to ITSM_CORE_WHCD_ITEM_V via CCGLPDB_LINK' FROM dual
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
   SET target_object_name = CASE
                              WHEN source_object_name = 'ALL_LIST_V' THEN 'ITSM_CORE_ALL_LIST_V'
                              WHEN source_object_name = 'WHCD_ITEM_V' THEN 'ITSM_CORE_WHCD_ITEM_V'
                              ELSE target_object_name
                            END,
       status = 'DONE',
       updated_at = SYSDATE
 WHERE batch_no = 'P1_BATCH02'
   AND wave_no = 'WAVE_01'
   AND source_object_name IN ('ALL_LIST_V', 'WHCD_ITEM_V');
/

PROMPT === 6) BATCH02 汇总 ===
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
