SET PAGESIZE 200;
SET LINESIZE 200;
COLUMN username FORMAT A30;
COLUMN default_tablespace FORMAT A30;

SELECT username, default_tablespace
FROM user_users;

SELECT tablespace_name, max_bytes
FROM user_ts_quotas
ORDER BY tablespace_name;

EXIT;
