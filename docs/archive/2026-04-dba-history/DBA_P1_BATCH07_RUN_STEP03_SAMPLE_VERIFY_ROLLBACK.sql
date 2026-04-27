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
    raise_application_error(-20271, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 回退资产登记表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_BATCH_ROLLBACK_ASSET (
      batch_no             VARCHAR2(30)  NOT NULL,
      source_object_name   VARCHAR2(128) NOT NULL,
      rollback_table_name  VARCHAR2(30)  NOT NULL,
      status               VARCHAR2(20)  NOT NULL,
      note                 VARCHAR2(400),
      updated_at           DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_MIG_P1_BATCH_ROLLBACK_ASSET PRIMARY KEY (
        batch_no, source_object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 抽样核验 + 回退资产补齐（样本20） ===
DECLARE
  v_src_cnt NUMBER;
  v_tgt_cnt NUMBER;
  v_bad_cnt NUMBER := 0;
  v_sql     CLOB;
BEGIN
  FOR r IN (
    SELECT source_object_type,
           source_object_name,
           target_object_name,
           'RB7_' || SUBSTR(source_object_name, 1, 20) || '_' ||
           LPAD(TO_CHAR(MOD(ORA_HASH(source_object_name), 10000)), 4, '0') AS rollback_table_name
    FROM (
      SELECT source_object_type,
             source_object_name,
             target_object_name,
             ROW_NUMBER() OVER (ORDER BY source_object_type, source_object_name) AS rn
      FROM MIG_P1_OBJECT_WORKPACK
      WHERE batch_no = 'P1_BATCH07'
        AND wave_no = 'WAVE_01'
        AND status = 'DONE'
    )
    WHERE rn <= 20
  ) LOOP
    v_sql := 'SELECT COUNT(*) FROM ' || r.source_object_name;
    EXECUTE IMMEDIATE v_sql INTO v_src_cnt;

    v_sql := 'SELECT COUNT(*) FROM ' || r.target_object_name;
    EXECUTE IMMEDIATE v_sql INTO v_tgt_cnt;

    IF v_src_cnt != v_tgt_cnt THEN
      v_bad_cnt := v_bad_cnt + 1;
    END IF;

    DBMS_OUTPUT.PUT_LINE(
      RPAD(r.source_object_name, 35) || ' -> ' || RPAD(r.target_object_name, 30) ||
      ' SRC=' || TO_CHAR(v_src_cnt) || ', TGT=' || TO_CHAR(v_tgt_cnt)
    );

    BEGIN
      v_sql := 'CREATE TABLE ' || r.rollback_table_name || ' AS SELECT * FROM ' || r.source_object_name;
      EXECUTE IMMEDIATE v_sql;
    EXCEPTION
      WHEN OTHERS THEN
        IF SQLCODE = -955 THEN
          v_sql := 'TRUNCATE TABLE ' || r.rollback_table_name;
          EXECUTE IMMEDIATE v_sql;
          v_sql := 'INSERT INTO ' || r.rollback_table_name || ' SELECT * FROM ' || r.source_object_name;
          EXECUTE IMMEDIATE v_sql;
          COMMIT;
        ELSE
          RAISE;
        END IF;
    END;

    MERGE INTO MIG_P1_BATCH_ROLLBACK_ASSET t
    USING (
      SELECT 'P1_BATCH07' AS batch_no,
             r.source_object_name AS source_object_name,
             r.rollback_table_name AS rollback_table_name,
             'READY' AS status,
             'sample rollback snapshot from source object' AS note
      FROM dual
    ) s
    ON (
      t.batch_no = s.batch_no
      AND t.source_object_name = s.source_object_name
    )
    WHEN MATCHED THEN
      UPDATE SET
        t.rollback_table_name = s.rollback_table_name,
        t.status = s.status,
        t.note = s.note,
        t.updated_at = SYSDATE
    WHEN NOT MATCHED THEN
      INSERT (batch_no, source_object_name, rollback_table_name, status, note, updated_at)
      VALUES (s.batch_no, s.source_object_name, s.rollback_table_name, s.status, s.note, SYSDATE);
  END LOOP;

  IF v_bad_cnt > 0 THEN
    raise_application_error(-20272, 'sample verify mismatch cnt=' || v_bad_cnt);
  END IF;
END;
/

PROMPT === 3) 写入批次日志（样本核验 + 回退资产就绪） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH07' AS batch_no,
         source_object_type AS object_type,
         source_object_name AS object_name,
         'STEP3_SAMPLE_VERIFY' AS action_type,
         'DONE' AS execute_status,
         'sample check src/tgt count parity' AS note
  FROM (
    SELECT source_object_type,
           source_object_name,
           ROW_NUMBER() OVER (ORDER BY source_object_type, source_object_name) AS rn
    FROM MIG_P1_OBJECT_WORKPACK
    WHERE batch_no = 'P1_BATCH07'
      AND wave_no = 'WAVE_01'
      AND status = 'DONE'
  )
  WHERE rn <= 20
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

MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH07' AS batch_no,
         w.source_object_type AS object_type,
         w.source_object_name AS object_name,
         'STEP3_ROLLBACK_ASSET' AS action_type,
         'READY' AS execute_status,
         'rollback asset ready in MIG_P1_BATCH_ROLLBACK_ASSET' AS note
  FROM MIG_P1_OBJECT_WORKPACK w
  JOIN (
    SELECT source_object_name
    FROM (
      SELECT source_object_name,
             ROW_NUMBER() OVER (ORDER BY source_object_type, source_object_name) AS rn
      FROM MIG_P1_OBJECT_WORKPACK
      WHERE batch_no = 'P1_BATCH07'
        AND wave_no = 'WAVE_01'
        AND status = 'DONE'
    )
    WHERE rn <= 20
  ) s
    ON s.source_object_name = w.source_object_name
  WHERE w.batch_no = 'P1_BATCH07'
    AND w.wave_no = 'WAVE_01'
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

PROMPT === 4) BATCH07 STEP3 汇总 ===
SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P1_BATCH07'
  AND action_type IN ('STEP3_SAMPLE_VERIFY', 'STEP3_ROLLBACK_ASSET')
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

SELECT status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_ROLLBACK_ASSET
WHERE batch_no = 'P1_BATCH07'
GROUP BY status
ORDER BY status;

EXIT;
