SET PAGESIZE 200;
SET LINESIZE 200;
COLUMN tablespace_name FORMAT A30;

PROMPT === SOURCE USER_TABLES TABLESPACE ===
SELECT NVL(tablespace_name, '(NULL)') AS tablespace_name, COUNT(*) AS cnt
FROM user_tables@CCGLPDB_LINK
GROUP BY NVL(tablespace_name, '(NULL)')
ORDER BY 2 DESC;

PROMPT === SOURCE USER_INDEXES TABLESPACE ===
SELECT NVL(tablespace_name, '(NULL)') AS tablespace_name, COUNT(*) AS cnt
FROM user_indexes@CCGLPDB_LINK
GROUP BY NVL(tablespace_name, '(NULL)')
ORDER BY 2 DESC;

EXIT;
