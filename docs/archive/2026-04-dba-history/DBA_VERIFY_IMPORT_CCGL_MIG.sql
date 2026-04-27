SET ECHO ON;
SET PAGESIZE 200;
SET LINESIZE 200;
COLUMN service_name FORMAT A30;
COLUMN db_name FORMAT A20;
COLUMN session_user FORMAT A20;

SELECT SYS_CONTEXT('USERENV','SERVICE_NAME') AS service_name,
       SYS_CONTEXT('USERENV','DB_NAME')      AS db_name,
       SYS_CONTEXT('USERENV','SESSION_USER') AS session_user
FROM dual;

SELECT COUNT(*) AS table_count
FROM user_tables;

SELECT table_name
FROM user_tables
WHERE table_name IN ('TMM22_CUSTOMERS','TIT01_TIMEPOINT_AREA')
ORDER BY table_name;

SELECT COUNT(*) AS view_count
FROM user_views;

EXIT;
