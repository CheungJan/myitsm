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
    raise_application_error(-20451, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 回归结果表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P2_REG_RESULT (
      batch_no             VARCHAR2(30)  NOT NULL,
      wave_no              VARCHAR2(30)  NOT NULL,
      source_object_name   VARCHAR2(128) NOT NULL,
      target_object_name   VARCHAR2(128) NOT NULL,
      row_check            VARCHAR2(10)  NOT NULL,
      key_check            VARCHAR2(10)  NOT NULL,
      status_check         VARCHAR2(10)  NOT NULL,
      overall_status       VARCHAR2(20)  NOT NULL,
      note                 VARCHAR2(400),
      updated_at           DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P2_REG_RES PRIMARY KEY (
        batch_no, wave_no, source_object_name, target_object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 执行最小回归（样本上限20，行数必检，键/状态可检则检） ===
DECLARE
  v_src_cnt           NUMBER;
  v_tgt_cnt           NUMBER;
  v_row_check         VARCHAR2(10);
  v_key_check         VARCHAR2(10);
  v_status_check      VARCHAR2(10);
  v_overall           VARCHAR2(20);
  v_note              VARCHAR2(400);
  v_key_col           VARCHAR2(128);
  v_status_col        VARCHAR2(128);
  v_src_key_cnt       NUMBER;
  v_tgt_key_cnt       NUMBER;
  v_src_status_dcnt   NUMBER;
  v_tgt_status_dcnt   NUMBER;
BEGIN
  FOR r IN (
    SELECT source_object_name,
           target_object_name
    FROM (
      SELECT w.source_object_name,
             w.target_object_name,
             ROW_NUMBER() OVER (ORDER BY w.source_object_name) AS rn
      FROM MIG_P1_OBJECT_WORKPACK w
      WHERE w.status = 'DONE'
        AND w.source_object_type = 'TABLE'
        AND w.target_object_name IS NOT NULL
    )
    WHERE rn <= 20
  ) LOOP
    EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM ' || DBMS_ASSERT.SQL_OBJECT_NAME(r.source_object_name)
      INTO v_src_cnt;
    EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM ' || DBMS_ASSERT.SQL_OBJECT_NAME(r.target_object_name)
      INTO v_tgt_cnt;

    v_row_check := CASE WHEN v_src_cnt = v_tgt_cnt THEN 'PASS' ELSE 'FAIL' END;

    v_key_col := NULL;
    BEGIN
      SELECT col_name
      INTO v_key_col
      FROM (
        SELECT c.column_name AS col_name,
               CASE c.column_name
                 WHEN 'ID' THEN 1
                 WHEN 'PLAN_ID' THEN 2
                 WHEN 'BIZ_ID' THEN 3
                 WHEN 'CUST_ID' THEN 4
                 ELSE 99
               END AS ord
        FROM user_tab_cols c
        JOIN user_tab_cols t
          ON t.table_name = r.target_object_name
         AND t.column_name = c.column_name
        WHERE c.table_name = r.source_object_name
          AND c.column_name IN ('ID', 'PLAN_ID', 'BIZ_ID', 'CUST_ID')
        ORDER BY ord
      )
      WHERE ROWNUM = 1;
    EXCEPTION
      WHEN NO_DATA_FOUND THEN
        v_key_col := NULL;
    END;

    IF v_key_col IS NOT NULL THEN
      EXECUTE IMMEDIATE
        'SELECT COUNT(DISTINCT ' || v_key_col || ') FROM ' || DBMS_ASSERT.SQL_OBJECT_NAME(r.source_object_name)
        INTO v_src_key_cnt;
      EXECUTE IMMEDIATE
        'SELECT COUNT(DISTINCT ' || v_key_col || ') FROM ' || DBMS_ASSERT.SQL_OBJECT_NAME(r.target_object_name)
        INTO v_tgt_key_cnt;
      v_key_check := CASE WHEN v_src_key_cnt = v_tgt_key_cnt THEN 'PASS' ELSE 'FAIL' END;
    ELSE
      v_key_check := 'SKIP';
    END IF;

    v_status_col := NULL;
    BEGIN
      SELECT col_name
      INTO v_status_col
      FROM (
        SELECT c.column_name AS col_name,
               CASE c.column_name
                 WHEN 'STATUS' THEN 1
                 WHEN 'STATE' THEN 2
                 WHEN 'IS_VALID' THEN 3
                 WHEN 'ENABLED_FLAG' THEN 4
                 ELSE 99
               END AS ord
        FROM user_tab_cols c
        JOIN user_tab_cols t
          ON t.table_name = r.target_object_name
         AND t.column_name = c.column_name
        WHERE c.table_name = r.source_object_name
          AND c.column_name IN ('STATUS', 'STATE', 'IS_VALID', 'ENABLED_FLAG')
        ORDER BY ord
      )
      WHERE ROWNUM = 1;
    EXCEPTION
      WHEN NO_DATA_FOUND THEN
        v_status_col := NULL;
    END;

    IF v_status_col IS NOT NULL THEN
      EXECUTE IMMEDIATE
        'SELECT COUNT(DISTINCT ' || v_status_col || ') FROM ' || DBMS_ASSERT.SQL_OBJECT_NAME(r.source_object_name)
        INTO v_src_status_dcnt;
      EXECUTE IMMEDIATE
        'SELECT COUNT(DISTINCT ' || v_status_col || ') FROM ' || DBMS_ASSERT.SQL_OBJECT_NAME(r.target_object_name)
        INTO v_tgt_status_dcnt;
      v_status_check := CASE WHEN v_src_status_dcnt = v_tgt_status_dcnt THEN 'PASS' ELSE 'FAIL' END;
    ELSE
      v_status_check := 'SKIP';
    END IF;

    IF v_row_check = 'FAIL'
       OR v_key_check = 'FAIL'
       OR v_status_check = 'FAIL' THEN
      v_overall := 'BLOCKED';
    ELSE
      v_overall := 'DONE';
    END IF;

    v_note := 'src=' || v_src_cnt || ', tgt=' || v_tgt_cnt || ', key=' || v_key_check || ', status=' || v_status_check;

    MERGE INTO MIG_P2_REG_RESULT t
    USING (
      SELECT 'P2_STAGE02' AS batch_no,
             'WAVE_01' AS wave_no,
             r.source_object_name AS source_object_name,
             r.target_object_name AS target_object_name,
             v_row_check AS row_check,
             v_key_check AS key_check,
             v_status_check AS status_check,
             v_overall AS overall_status,
             v_note AS note
      FROM dual
    ) s
    ON (
      t.batch_no = s.batch_no
      AND t.wave_no = s.wave_no
      AND t.source_object_name = s.source_object_name
      AND t.target_object_name = s.target_object_name
    )
    WHEN MATCHED THEN
      UPDATE SET
        t.row_check = s.row_check,
        t.key_check = s.key_check,
        t.status_check = s.status_check,
        t.overall_status = s.overall_status,
        t.note = s.note,
        t.updated_at = SYSDATE
    WHEN NOT MATCHED THEN
      INSERT (
        batch_no, wave_no, source_object_name, target_object_name,
        row_check, key_check, status_check, overall_status, note, updated_at
      )
      VALUES (
        s.batch_no, s.wave_no, s.source_object_name, s.target_object_name,
        s.row_check, s.key_check, s.status_check, s.overall_status, s.note, SYSDATE
      );
  END LOOP;
END;
/

PROMPT === 3) 回写 P2 主线日志（P2_STAGE02） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P2_STAGE02' AS batch_no,
         'MAINLINE' AS object_type,
         source_object_name AS object_name,
         'STEP2_REGRESSION_EXEC' AS action_type,
         overall_status AS execute_status,
         note AS note
  FROM MIG_P2_REG_RESULT
  WHERE batch_no = 'P2_STAGE02'
    AND wave_no = 'WAVE_01'
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

PROMPT === 4) 更新 P2_STAGE01 回归任务状态 ===
MERGE INTO MIG_P2_STAGE_CHECK t
USING (
  SELECT 'P2_STAGE01' AS stage_no,
         'TASK1_REGRESSION' AS task_no,
         CASE
           WHEN SUM(CASE WHEN overall_status = 'BLOCKED' THEN 1 ELSE 0 END) > 0 THEN 'BLOCKED'
           ELSE 'DONE'
         END AS task_status,
         'updated by P2_STAGE02 regression execution' AS note
  FROM MIG_P2_REG_RESULT
  WHERE batch_no = 'P2_STAGE02'
    AND wave_no = 'WAVE_01'
) s
ON (
  t.stage_no = s.stage_no
  AND t.task_no = s.task_no
)
WHEN MATCHED THEN
  UPDATE SET t.task_status = s.task_status, t.note = s.note, t.updated_at = SYSDATE;
/

PROMPT === 5) 摘要 ===
SELECT overall_status, COUNT(*) AS cnt
FROM MIG_P2_REG_RESULT
WHERE batch_no = 'P2_STAGE02'
  AND wave_no = 'WAVE_01'
GROUP BY overall_status
ORDER BY overall_status;

SELECT action_type, execute_status, COUNT(*) AS cnt
FROM MIG_P1_BATCH_LOG
WHERE batch_no = 'P2_STAGE02'
GROUP BY action_type, execute_status
ORDER BY action_type, execute_status;

SELECT task_no, task_status, note
FROM MIG_P2_STAGE_CHECK
WHERE stage_no = 'P2_STAGE01'
  AND task_no = 'TASK1_REGRESSION';

EXIT;
