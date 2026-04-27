-- 文件说明：DBA验证脚本（CCGL_MIG沙箱，只读）
-- 目标对象：CCGL_MIG.TIT01_TIMEPOINT_CUST

SET ECHO ON;
SET SERVEROUTPUT ON;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

-- 0) 安全门禁：仅允许在CCGL_MIG执行
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT SYS_CONTEXT('USERENV', 'SERVICE_NAME') INTO v_service_name FROM dual;
  IF UPPER(v_service_name) <> 'CCGL_MIG' THEN
    raise_application_error(-20021, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

-- 1) 对象是否存在且有效
SELECT object_name, object_type, status
FROM user_objects
WHERE object_name = 'TIT01_TIMEPOINT_CUST';

-- 2) 字段结构检查
SELECT column_id, column_name, data_type, data_length, nullable
FROM user_tab_columns
WHERE table_name = 'TIT01_TIMEPOINT_CUST'
ORDER BY column_id;

-- 3) 数据可读性检查（只读）
SELECT COUNT(*) AS total_rows
FROM TIT01_TIMEPOINT_CUST;

SELECT *
FROM (
  SELECT custcd, timepoint, beforetm, aftertm, useflg
  FROM TIT01_TIMEPOINT_CUST
  ORDER BY custcd
)
WHERE ROWNUM <= 20;
