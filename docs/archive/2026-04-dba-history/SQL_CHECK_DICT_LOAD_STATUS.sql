SET PAGESIZE 200;
SET LINESIZE 220;

COLUMN governance_tag FORMAT A20;

PROMPT === 会话信息 ===
SELECT SYS_CONTEXT('USERENV','SERVICE_NAME') AS service_name,
       SYS_CONTEXT('USERENV','SESSION_USER') AS session_user
FROM dual;

PROMPT === 台账总量 ===
SELECT COUNT(*) AS dict_rows
FROM DICT_OPTIMIZED_OBJECTS;

PROMPT === 治理标签分布 ===
SELECT governance_tag, COUNT(*) AS cnt
FROM DICT_OPTIMIZED_OBJECTS
GROUP BY governance_tag
ORDER BY governance_tag;

PROMPT === 对象类型分布 ===
SELECT object_type, COUNT(*) AS cnt
FROM DICT_OPTIMIZED_OBJECTS
GROUP BY object_type
ORDER BY object_type;

EXIT;
