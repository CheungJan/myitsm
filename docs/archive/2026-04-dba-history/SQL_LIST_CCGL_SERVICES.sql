SET PAGESIZE 200;
SET LINESIZE 240;
COLUMN name FORMAT A30;
COLUMN pdb FORMAT A20;
COLUMN network_name FORMAT A80;

SELECT name, pdb, network_name
FROM cdb_services
WHERE UPPER(name) LIKE '%CCGL%'
   OR UPPER(network_name) LIKE '%CCGL%'
ORDER BY pdb, name;

EXIT;
