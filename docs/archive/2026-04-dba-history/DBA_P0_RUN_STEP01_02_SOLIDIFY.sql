SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 200;
SET LINESIZE 240;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20291, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 差异快照表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_OBJECT_DIFF_SNAPSHOT (
      snapshot_id         RAW(16)       NOT NULL,
      snapshot_batch_no   VARCHAR2(30)  NOT NULL,
      object_name         VARCHAR2(128) NOT NULL,
      object_type         VARCHAR2(10)  NOT NULL,
      governance_tag      VARCHAR2(20),
      domain_name         VARCHAR2(64),
      category            VARCHAR2(40)  NOT NULL,
      p1_priority         NUMBER(2)     NOT NULL,
      created_at_utc      TIMESTAMP(6) DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      CONSTRAINT PK_MIG_P1_OBJ_DIFF_SNAP PRIMARY KEY (snapshot_id)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 三类对象集合表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P0_CLASSIFIED_OBJECT_SET (
      snapshot_batch_no   VARCHAR2(30)  NOT NULL,
      object_set          VARCHAR2(20)  NOT NULL,
      object_type         VARCHAR2(10)  NOT NULL,
      object_name         VARCHAR2(128) NOT NULL,
      p1_priority         NUMBER(2)     NOT NULL,
      source_category     VARCHAR2(40)  NOT NULL,
      created_at_utc      TIMESTAMP(6) DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      CONSTRAINT PK_MIG_P0_CLASSIFIED_SET PRIMARY KEY (
        snapshot_batch_no, object_set, object_type, object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 3) 刷新差异快照（P0_SOLIDIFY01） ===
DELETE FROM MIG_P1_OBJECT_DIFF_SNAPSHOT
WHERE snapshot_batch_no = 'P0_SOLIDIFY01';
/

INSERT INTO MIG_P1_OBJECT_DIFF_SNAPSHOT (
  snapshot_id, snapshot_batch_no, object_name, object_type,
  governance_tag, domain_name, category, p1_priority
)
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
  SELECT b.object_name,
         b.object_type,
         d.governance_tag,
         d.domain_name,
         CASE
           WHEN d.object_name IS NULL THEN 'baseline_only_unmapped'
           WHEN d.governance_tag = UNISTR('\4FDD\7559') THEN 'mapped_keep'
           WHEN d.governance_tag = UNISTR('\5F85\8FC1\79FB') THEN 'mapped_migrate'
           WHEN d.governance_tag = UNISTR('\5F85\4E0B\7EBF') THEN 'mapped_deprecate'
           ELSE 'mapped_other'
         END AS category,
         CASE
           WHEN REGEXP_LIKE(b.object_name, '^TIT') THEN 1
           WHEN REGEXP_LIKE(b.object_name, '^PLAN_|^TMM22') THEN 2
           WHEN REGEXP_LIKE(b.object_name, '^TWH') THEN 3
           WHEN REGEXP_LIKE(b.object_name, '^TMM') THEN 4
           WHEN REGEXP_LIKE(b.object_name, '^TPC|^TQC|^TSL') THEN 5
           ELSE 9
         END AS p1_priority
  FROM baseline b
  LEFT JOIN dict_data d
    ON d.object_name = b.object_name
   AND d.object_type = b.object_type
)
SELECT SYS_GUID(),
       'P0_SOLIDIFY01',
       object_name,
       object_type,
       governance_tag,
       domain_name,
       category,
       p1_priority
FROM joined;

PROMPT === 4) 刷新三类对象集合（P0_SOLIDIFY01） ===
DELETE FROM MIG_P0_CLASSIFIED_OBJECT_SET
WHERE snapshot_batch_no = 'P0_SOLIDIFY01';
/

INSERT INTO MIG_P0_CLASSIFIED_OBJECT_SET (
  snapshot_batch_no, object_set, object_type, object_name, p1_priority, source_category
)
SELECT 'P0_SOLIDIFY01' AS snapshot_batch_no,
       CASE category
         WHEN 'mapped_keep' THEN 'KEEP'
         WHEN 'mapped_migrate' THEN 'MIGRATE'
         WHEN 'mapped_deprecate' THEN 'DEPRECATE'
       END AS object_set,
       object_type,
       object_name,
       p1_priority,
       category AS source_category
FROM MIG_P1_OBJECT_DIFF_SNAPSHOT
WHERE snapshot_batch_no = 'P0_SOLIDIFY01'
  AND category IN ('mapped_keep', 'mapped_migrate', 'mapped_deprecate');

PROMPT === 5) 固化结果汇总 ===
SELECT category, COUNT(*) AS cnt
FROM MIG_P1_OBJECT_DIFF_SNAPSHOT
WHERE snapshot_batch_no = 'P0_SOLIDIFY01'
GROUP BY category
ORDER BY category;

SELECT object_set, COUNT(*) AS cnt
FROM MIG_P0_CLASSIFIED_OBJECT_SET
WHERE snapshot_batch_no = 'P0_SOLIDIFY01'
GROUP BY object_set
ORDER BY object_set;

PROMPT === 6) 写入批次日志（P0 固化） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P0_SOLIDIFY01' AS batch_no, 'CONTROL' AS object_type, 'P0_DIFF_SNAPSHOT' AS object_name, 'STEP0_DIFF_SOLIDIFY' AS action_type, 'DONE' AS execute_status, 'diff snapshot solidified to MIG_P1_OBJECT_DIFF_SNAPSHOT' AS note FROM dual
  UNION ALL
  SELECT 'P0_SOLIDIFY01', 'CONTROL', 'P0_CLASSIFIED_SET', 'STEP0_CLASS_SOLIDIFY', 'DONE', 'keep/migrate/deprecate solidified to MIG_P0_CLASSIFIED_OBJECT_SET' FROM dual
) s
ON (
  t.batch_no = s.batch_no
  AND t.object_type = s.object_type
  AND t.object_name = s.object_name
  AND t.action_type = s.action_type
)
WHEN MATCHED THEN
  UPDATE SET t.execute_status = s.execute_status, t.note = s.note, t.executed_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (batch_no, object_type, object_name, action_type, execute_status, note, executed_at)
  VALUES (s.batch_no, s.object_type, s.object_name, s.action_type, s.execute_status, s.note, SYSDATE);
/

EXIT;
