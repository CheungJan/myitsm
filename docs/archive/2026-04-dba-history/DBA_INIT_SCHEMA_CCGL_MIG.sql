-- 文件说明：CCGL_MIG初始化脚本（迁移用户/最小权限/目录对象）
-- 执行身份：PDB管理员（连接到CCGL_MIG）

SET ECHO ON;
SET SERVEROUTPUT ON;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

-- 0) 安全门禁：仅允许在CCGL_MIG执行
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT SYS_CONTEXT('USERENV', 'SERVICE_NAME') INTO v_service_name FROM dual;
  IF UPPER(v_service_name) <> 'CCGL_MIG' THEN
    raise_application_error(-20011, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

-- 1) 创建迁移专用用户（兼容不同PDB表空间命名）
DECLARE
  v_default_ts VARCHAR2(30);
  v_temp_ts    VARCHAR2(30) := 'TEMP';
  v_db_create_file_dest VARCHAR2(4000);
  v_user_cnt   NUMBER;
BEGIN
  -- 优先使用 USERS；若不存在则回退到第一个永久表空间（排除SYSTEM/SYSAUX）
  SELECT CASE
           WHEN EXISTS (
             SELECT 1
             FROM dba_tablespaces
             WHERE tablespace_name = 'USERS'
           ) THEN 'USERS'
           ELSE (
             SELECT MIN(tablespace_name)
             FROM dba_tablespaces
             WHERE contents = 'PERMANENT'
               AND tablespace_name NOT IN ('SYSTEM', 'SYSAUX')
           )
         END
  INTO v_default_ts
  FROM dual;

  IF v_default_ts IS NULL THEN
    SELECT value
    INTO v_db_create_file_dest
    FROM v$parameter
    WHERE name = 'db_create_file_dest';

    IF v_db_create_file_dest IS NOT NULL THEN
      BEGIN
        EXECUTE IMMEDIATE
          'CREATE TABLESPACE CCGL_MIG_DATA DATAFILE SIZE 200M ' ||
          'AUTOEXTEND ON NEXT 50M MAXSIZE UNLIMITED';
      EXCEPTION
        WHEN OTHERS THEN
          IF SQLCODE != -959 THEN
            RAISE;
          END IF;
      END;
      v_default_ts := 'CCGL_MIG_DATA';
    ELSE
      raise_application_error(
        -20012,
        'No usable permanent tablespace found. Please create USERS/CCGL_MIG_DATA in CCGL_MIG'
      );
    END IF;
  END IF;

  SELECT COUNT(1)
  INTO v_user_cnt
  FROM dba_users
  WHERE username = 'CCGL_MIG';

  IF v_user_cnt = 0 THEN
    EXECUTE IMMEDIATE
      'CREATE USER CCGL_MIG IDENTIFIED BY "CcglMig_ChangeMe_2026" ' ||
      'DEFAULT TABLESPACE ' || v_default_ts || ' ' ||
      'TEMPORARY TABLESPACE ' || v_temp_ts || ' ' ||
      'QUOTA UNLIMITED ON ' || v_default_ts;
  ELSE
    EXECUTE IMMEDIATE
      'ALTER USER CCGL_MIG IDENTIFIED BY "CcglMig_ChangeMe_2026" ' ||
      'DEFAULT TABLESPACE ' || v_default_ts || ' ' ||
      'TEMPORARY TABLESPACE ' || v_temp_ts;
    EXECUTE IMMEDIATE
      'ALTER USER CCGL_MIG QUOTA UNLIMITED ON ' || v_default_ts;
  END IF;
END;
/

-- 2) 最小权限（仅沙箱内对象建设）
GRANT CREATE SESSION TO CCGL_MIG;
GRANT CREATE TABLE TO CCGL_MIG;
GRANT CREATE VIEW TO CCGL_MIG;
GRANT CREATE SYNONYM TO CCGL_MIG;
GRANT CREATE SEQUENCE TO CCGL_MIG;
GRANT CREATE PROCEDURE TO CCGL_MIG;

-- 3) 导入目录对象（按实际路径修改）
CREATE OR REPLACE DIRECTORY DPUMP_MIG_DIR AS 'E:\\project\\myitsm\\src\\docs\\dpump';
GRANT READ, WRITE ON DIRECTORY DPUMP_MIG_DIR TO CCGL_MIG;

-- 4) 结果确认
COLUMN USERNAME FORMAT A20;
SELECT USERNAME, ACCOUNT_STATUS FROM DBA_USERS WHERE USERNAME = 'CCGL_MIG';

SELECT GRANTEE, PRIVILEGE
FROM DBA_SYS_PRIVS
WHERE GRANTEE = 'CCGL_MIG'
ORDER BY PRIVILEGE;

PROMPT === 完成：可使用 CCGL_MIG 用户执行P1/P2迁移脚本 ===
