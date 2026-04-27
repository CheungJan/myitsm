SET ECHO ON;
SET SERVEROUTPUT ON;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

-- 自动定位包含 CCGL 服务的PDB（排除 CCGL_MIG），并切换容器后授权
DECLARE
  v_pdb_name VARCHAR2(128);
BEGIN
  BEGIN
    SELECT pdb
      INTO v_pdb_name
      FROM cdb_services
     WHERE UPPER(name) LIKE '%CCGL%'
       AND UPPER(pdb) <> 'CCGL_MIG'
       AND ROWNUM = 1;

    EXECUTE IMMEDIATE 'ALTER SESSION SET CONTAINER = ' || v_pdb_name;
  EXCEPTION
    WHEN OTHERS THEN
      NULL;
  END;
END;
/

-- 授予 Data Pump 导出角色
GRANT DATAPUMP_EXP_FULL_DATABASE TO CCGL;
GRANT EXP_FULL_DATABASE TO CCGL;

-- 目录对象不存在则创建（使用既有路径）
DECLARE
  v_cnt NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_cnt
  FROM dba_directories
  WHERE directory_name = 'DPUMP_MIG_DIR';

  IF v_cnt = 0 THEN
    EXECUTE IMMEDIATE q'[CREATE DIRECTORY DPUMP_MIG_DIR AS 'E:\project\myitsm\src\docs\dpump']';
  END IF;
END;
/

GRANT READ, WRITE ON DIRECTORY DPUMP_MIG_DIR TO CCGL;

-- 校验输出
COLUMN granted_role FORMAT A35;
SELECT granted_role FROM dba_role_privs WHERE grantee = 'CCGL' ORDER BY granted_role;

COLUMN directory_name FORMAT A30;
SELECT directory_name, directory_path FROM dba_directories WHERE directory_name = 'DPUMP_MIG_DIR';

SELECT privilege
FROM dba_tab_privs
WHERE owner = 'SYS'
  AND table_name = 'DPUMP_MIG_DIR'
  AND grantee = 'CCGL'
ORDER BY privilege;

EXIT;
