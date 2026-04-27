SET PAGESIZE 200;
SET LINESIZE 200;
COLUMN GRANTED_ROLE FORMAT A35;
COLUMN PRIVILEGE FORMAT A35;

SELECT granted_role
FROM user_role_privs
WHERE granted_role IN ('DATAPUMP_EXP_FULL_DATABASE', 'EXP_FULL_DATABASE')
ORDER BY granted_role;

SELECT privilege
FROM user_sys_privs
WHERE privilege IN ('CREATE TABLE', 'CREATE SESSION')
ORDER BY privilege;

SELECT directory_name
FROM all_directories
WHERE directory_name = 'DPUMP_MIG_DIR';

SELECT privilege
FROM all_tab_privs
WHERE table_name = 'DPUMP_MIG_DIR'
  AND table_schema = 'SYS'
  AND grantee = USER
ORDER BY privilege;

EXIT;
