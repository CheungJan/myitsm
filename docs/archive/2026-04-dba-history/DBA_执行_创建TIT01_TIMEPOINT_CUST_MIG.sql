-- 文件说明：DBA执行脚本（CCGL_MIG沙箱创建兼容视图）
-- 目标对象：CCGL_MIG.TIT01_TIMEPOINT_CUST
-- 执行前提：以具备 CREATE VIEW 权限的账号连接 CCGL_MIG

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

-- 1) 安全校验：目标对象若已存在且不是VIEW则中止
DECLARE
  v_object_type VARCHAR2(30);
BEGIN
  SELECT object_type
    INTO v_object_type
    FROM user_objects
   WHERE object_name = 'TIT01_TIMEPOINT_CUST'
     AND ROWNUM = 1;

  IF v_object_type <> 'VIEW' THEN
    raise_application_error(-20001, 'Target object exists and is not a VIEW: ' || v_object_type);
  END IF;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    NULL;
END;
/

-- 2) 动态拼接JOIN条件（兼容不同字段存在性）
DECLARE
  v_has_c_area     NUMBER := 0;
  v_has_a_area     NUMBER := 0;
  v_has_c_location NUMBER := 0;
  v_has_a_location NUMBER := 0;
  v_has_c_levels   NUMBER := 0;
  v_has_a_levels   NUMBER := 0;
  v_join_added     NUMBER := 0;
  v_sql            CLOB;
BEGIN
  SELECT COUNT(*) INTO v_has_c_area
    FROM user_tab_columns
   WHERE table_name = 'TMM22_CUSTOMERS'
     AND column_name = 'AREA';

  SELECT COUNT(*) INTO v_has_a_area
    FROM user_tab_columns
   WHERE table_name = 'TIT01_TIMEPOINT_AREA'
     AND column_name = 'AREA';

  SELECT COUNT(*) INTO v_has_c_location
    FROM user_tab_columns
   WHERE table_name = 'TMM22_CUSTOMERS'
     AND column_name = 'LOCATION';

  SELECT COUNT(*) INTO v_has_a_location
    FROM user_tab_columns
   WHERE table_name = 'TIT01_TIMEPOINT_AREA'
     AND column_name = 'LOCATION';

  SELECT COUNT(*) INTO v_has_c_levels
    FROM user_tab_columns
   WHERE table_name = 'TMM22_CUSTOMERS'
     AND column_name = 'LEVELS';

  SELECT COUNT(*) INTO v_has_a_levels
    FROM user_tab_columns
   WHERE table_name = 'TIT01_TIMEPOINT_AREA'
     AND column_name = 'LEVELS';

  v_sql := 'CREATE OR REPLACE VIEW TIT01_TIMEPOINT_CUST AS '
        || 'SELECT c.custcd, a.timepoint, a.beforetm, a.aftertm, a.useflg '
        || 'FROM TMM22_CUSTOMERS c '
        || 'JOIN TIT01_TIMEPOINT_AREA a ON 1 = 1';

  IF v_has_c_area > 0 AND v_has_a_area > 0 THEN
    v_sql := v_sql || ' AND a.area = c.area';
    v_join_added := 1;
  END IF;

  IF v_has_c_location > 0 AND v_has_a_location > 0 THEN
    v_sql := v_sql || ' AND a.location = c.location';
    v_join_added := 1;
  END IF;

  IF v_join_added = 0 AND v_has_c_levels > 0 AND v_has_a_levels > 0 THEN
    v_sql := v_sql || ' AND a.levels = c.levels';
    v_join_added := 1;
  END IF;

  IF v_join_added = 0 THEN
    raise_application_error(-20002, 'No common join keys found between TMM22_CUSTOMERS and TIT01_TIMEPOINT_AREA');
  END IF;

  v_sql := v_sql || ' WHERE c.useflg = ''1'' AND a.useflg = ''1''';

  EXECUTE IMMEDIATE v_sql;
END;
/

PROMPT === 完成：请继续执行 DBA_验证_TIT01_TIMEPOINT_CUST_MIG.sql ===
