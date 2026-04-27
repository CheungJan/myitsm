SET PAGESIZE 200;
SET LINESIZE 240;
COLUMN directory_name FORMAT A30;
COLUMN directory_path FORMAT A120;
COLUMN privilege FORMAT A20;

SELECT directory_name, directory_path
FROM all_directories
WHERE directory_name = 'DATA_PUMP_DIR';

SELECT privilege
FROM all_tab_privs
WHERE table_schema = 'SYS'
  AND table_name = 'DATA_PUMP_DIR'
  AND grantee = USER
ORDER BY privilege;

SELECT granted_role
FROM user_role_privs
WHERE granted_role IN ('DATAPUMP_EXP_FULL_DATABASE','EXP_FULL_DATABASE')
ORDER BY granted_role;

EXIT;
