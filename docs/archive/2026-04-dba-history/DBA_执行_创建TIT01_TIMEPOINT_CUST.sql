-- 文件说明：DBA执行脚本（创建兼容视图）
-- 目标对象：CCGL.TIT01_TIMEPOINT_CUST
-- 执行前提：以具备 CREATE VIEW 权限的账号连接 CCGLPDB

-- 安全校验：如果目标对象已存在且不是 VIEW，则直接停止，避免误操作。
DECLARE
    v_object_type VARCHAR2(30);
BEGIN
    SELECT object_type
      INTO v_object_type
      FROM all_objects
     WHERE owner = 'CCGL'
       AND object_name = 'TIT01_TIMEPOINT_CUST'
       AND ROWNUM = 1;

    IF v_object_type <> 'VIEW' THEN
        raise_application_error(-20001, 'Target object exists and is not a VIEW: ' || v_object_type);
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        NULL;
END;
/

-- 兼容处理：不同环境中可能不存在 LOCATION 列，按实库结构动态拼接 JOIN 条件。
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
    SELECT COUNT(*)
      INTO v_has_c_area
      FROM all_tab_columns
     WHERE owner = 'CCGL'
       AND table_name = 'TMM22_CUSTOMERS'
       AND column_name = 'AREA';

    SELECT COUNT(*)
      INTO v_has_a_area
      FROM all_tab_columns
     WHERE owner = 'CCGL'
       AND table_name = 'TIT01_TIMEPOINT_AREA'
       AND column_name = 'AREA';

    SELECT COUNT(*)
      INTO v_has_c_location
      FROM all_tab_columns
     WHERE owner = 'CCGL'
       AND table_name = 'TMM22_CUSTOMERS'
       AND column_name = 'LOCATION';

    SELECT COUNT(*)
      INTO v_has_a_location
      FROM all_tab_columns
     WHERE owner = 'CCGL'
       AND table_name = 'TIT01_TIMEPOINT_AREA'
       AND column_name = 'LOCATION';

    SELECT COUNT(*)
      INTO v_has_c_levels
      FROM all_tab_columns
     WHERE owner = 'CCGL'
       AND table_name = 'TMM22_CUSTOMERS'
       AND column_name = 'LEVELS';

    SELECT COUNT(*)
      INTO v_has_a_levels
      FROM all_tab_columns
     WHERE owner = 'CCGL'
       AND table_name = 'TIT01_TIMEPOINT_AREA'
       AND column_name = 'LEVELS';

    v_sql := 'CREATE OR REPLACE VIEW CCGL.TIT01_TIMEPOINT_CUST AS '
          || 'SELECT c.custcd, a.timepoint, a.beforetm, a.aftertm, a.useflg '
          || 'FROM CCGL.TMM22_CUSTOMERS c '
          || 'JOIN CCGL.TIT01_TIMEPOINT_AREA a ON 1 = 1';

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

-- 建议：执行后立即运行《DBA_验证_TIT01_TIMEPOINT_CUST.sql》进行只读验证。
