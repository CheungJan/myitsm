-- 文件说明：DBA回滚脚本（CCGL_MIG沙箱删除兼容视图）
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

BEGIN
  EXECUTE IMMEDIATE 'DROP VIEW TIT01_TIMEPOINT_CUST';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -942 THEN
      RAISE;
    END IF;
END;
/

SELECT object_name, object_type, status
FROM user_objects
WHERE object_name = 'TIT01_TIMEPOINT_CUST';
