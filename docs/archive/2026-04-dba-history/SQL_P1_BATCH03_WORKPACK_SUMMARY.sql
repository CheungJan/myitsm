SET PAGESIZE 200;
SET LINESIZE 200;
COLUMN source_object_type FORMAT A10;
COLUMN source_object_name FORMAT A40;

SELECT source_object_type, source_object_name, status
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH03'
  AND wave_no = 'WAVE_01'
ORDER BY source_object_type, source_object_name;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH03'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
