SET PAGESIZE 200;
SET LINESIZE 220;
COLUMN source_object_type FORMAT A10;
COLUMN source_object_name FORMAT A40;
COLUMN target_object_name FORMAT A35;

SELECT source_object_type, source_object_name, target_object_name, migration_strategy, status
FROM MIG_P1_OBJECT_WORKPACK
WHERE batch_no = 'P1_BATCH07'
  AND wave_no = 'WAVE_01'
ORDER BY source_object_type, source_object_name;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH07'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

EXIT;
