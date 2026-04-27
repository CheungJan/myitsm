SET ECHO ON;
SET SERVEROUTPUT ON;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20041, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 首批对象落地登记表（首次执行自动创建） ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_BATCH_LOG (
      batch_no        VARCHAR2(30)  NOT NULL,
      object_type     VARCHAR2(30)  NOT NULL,
      object_name     VARCHAR2(128) NOT NULL,
      action_type     VARCHAR2(30)  NOT NULL,
      execute_status  VARCHAR2(20)  NOT NULL,
      note            VARCHAR2(1000),
      executed_at     DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_MIG_P1_BATCH_LOG PRIMARY KEY (batch_no, object_type, object_name, action_type)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 首批对象清单快照入库（优先级1/2，保留+待迁移） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  WITH baseline AS (
    SELECT table_name AS object_name, 'TABLE' AS object_type FROM user_tables
    UNION ALL
    SELECT view_name  AS object_name, 'VIEW'  AS object_type FROM user_views
  ),
  dict_data AS (
    SELECT UPPER(object_name) AS object_name,
           UPPER(object_type) AS object_type,
           governance_tag,
           domain_name
    FROM DICT_OPTIMIZED_OBJECTS
  ),
  joined AS (
    SELECT d.object_type,
           d.object_name,
           d.governance_tag,
           CASE
             WHEN REGEXP_LIKE(d.object_name, '^TIT') THEN 1
             WHEN REGEXP_LIKE(d.object_name, '^PLAN_|^TMM22') THEN 2
             WHEN REGEXP_LIKE(d.object_name, '^TWH') THEN 3
             WHEN REGEXP_LIKE(d.object_name, '^TMM') THEN 4
             WHEN REGEXP_LIKE(d.object_name, '^TPC|^TQC|^TSL') THEN 5
             ELSE 9
           END AS p1_priority
    FROM dict_data d
    JOIN baseline b
      ON b.object_name = d.object_name
     AND b.object_type = d.object_type
    WHERE d.governance_tag IN (UNISTR('\4FDD\7559'), UNISTR('\5F85\8FC1\79FB'))
  )
  SELECT 'P1_BATCH01' AS batch_no,
         object_type,
         object_name,
         'SNAPSHOT' AS action_type,
         'READY' AS execute_status,
         'auto snapshot for batch execution' AS note
  FROM joined
  WHERE p1_priority IN (1, 2)
) s
ON (
  t.batch_no = s.batch_no
  AND t.object_type = s.object_type
  AND t.object_name = s.object_name
  AND t.action_type = s.action_type
)
WHEN NOT MATCHED THEN
  INSERT (batch_no, object_type, object_name, action_type, execute_status, note, executed_at)
  VALUES (s.batch_no, s.object_type, s.object_name, s.action_type, s.execute_status, s.note, SYSDATE);
/

PROMPT === 3) 本批核验结果 ===
SELECT batch_no,
       execute_status,
       COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH01'
GROUP BY batch_no, execute_status
ORDER BY execute_status;

PROMPT === 4) 回滚骨架（仅登记，不执行破坏性操作） ===
PROMPT 回滚建议：
PROMPT 1) 根据 MIG_P1_BATCH_LOG 快照逐对象回退 DDL/DML；
PROMPT 2) 若对象已改造，先 CREATE OR REPLACE 兼容视图；
PROMPT 3) 通过最小业务场景回归后再继续下一批；

EXIT;
