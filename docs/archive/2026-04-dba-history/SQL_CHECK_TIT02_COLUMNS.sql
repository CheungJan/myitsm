SET ECHO ON;
SET PAGESIZE 200;
SET LINESIZE 200;

COLUMN table_name FORMAT A24;
COLUMN column_name FORMAT A32;
COLUMN data_type FORMAT A20;

SELECT table_name, column_id, column_name, data_type
FROM user_tab_columns
WHERE table_name IN ('TIT02_LIABILITYREG', 'TIT02_LIABILITYREGDT')
ORDER BY table_name, column_id;

EXIT;
