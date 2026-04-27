SET ECHO ON;
SET PAGESIZE 200;
SET LINESIZE 240;
COLUMN directory_name FORMAT A30;
COLUMN directory_path FORMAT A120;

ALTER SESSION SET CONTAINER = CCGLPDB;
PROMPT === CCGLPDB Directories ===
SELECT directory_name, directory_path FROM dba_directories ORDER BY directory_name;

ALTER SESSION SET CONTAINER = CCGL_MIG;
PROMPT === CCGL_MIG Directories ===
SELECT directory_name, directory_path FROM dba_directories ORDER BY directory_name;

EXIT;
