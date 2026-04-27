SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 200;
SET LINESIZE 220;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20076, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) TIT02_LIABILITYREG 最小影子试点（仅记录比对结果） ===
DECLARE
  v_has_liabcd      NUMBER := 0;
  v_expr_liabcd     VARCHAR2(200);
  v_liabcd          VARCHAR2(64);
  v_src_match_cnt   NUMBER := 0;
  v_compare_result  VARCHAR2(20);
  v_detail_msg      VARCHAR2(1000);
  v_sql             CLOB;
BEGIN
  SELECT COUNT(*) INTO v_has_liabcd
    FROM user_tab_columns
   WHERE table_name = 'TIT02_LIABILITYREG'
     AND column_name = 'LIABCD';

  IF v_has_liabcd > 0 THEN
    v_expr_liabcd := 'TO_CHAR(liabcd)';
  ELSE
    v_expr_liabcd := 'CAST(NULL AS VARCHAR2(64))';
  END IF;

  BEGIN
    SELECT src_liabcd
      INTO v_liabcd
      FROM (
        SELECT src_liabcd
          FROM ITSM_CORE_LIABILITY
         WHERE source_object = 'TIT02_LIABILITYREG'
           AND src_liabcd IS NOT NULL
         ORDER BY created_at_utc DESC
      )
     WHERE ROWNUM = 1;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      v_compare_result := 'ERROR';
      v_detail_msg := 'no sample row found in ITSM_CORE_LIABILITY';

      INSERT INTO MIG_P1_SHADOW_WRITE_LOG (
        shadow_id, batch_no, source_object, target_object, biz_key,
        action_type, compare_result, detail_msg
      ) VALUES (
        SYS_GUID(), 'P1_BATCH01', 'TIT02_LIABILITYREG', 'ITSM_CORE_LIABILITY',
        NULL, 'PILOT_LIAB', v_compare_result, v_detail_msg
      );

      RETURN;
  END;

  v_sql := 'SELECT COUNT(*) FROM TIT02_LIABILITYREG WHERE ' || v_expr_liabcd || ' = :1';
  EXECUTE IMMEDIATE v_sql INTO v_src_match_cnt USING v_liabcd;

  IF v_src_match_cnt > 0 THEN
    v_compare_result := 'MATCH';
    v_detail_msg := 'pilot compare matched by LIABCD';
  ELSE
    v_compare_result := 'DIFF';
    v_detail_msg := 'pilot compare not found in source TIT02_LIABILITYREG';
  END IF;

  INSERT INTO MIG_P1_SHADOW_WRITE_LOG (
    shadow_id, batch_no, source_object, target_object, biz_key,
    action_type, compare_result, detail_msg
  ) VALUES (
    SYS_GUID(), 'P1_BATCH01', 'TIT02_LIABILITYREG', 'ITSM_CORE_LIABILITY',
    v_liabcd, 'PILOT_LIAB', v_compare_result, v_detail_msg
  );
END;
/

PROMPT === 2) 写入批次日志（Step3.3 试点） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no,
         'CONTROL' AS object_type,
         'SHADOW_PILOT_TIT02' AS object_name,
         'STEP3_3_SHADOW_PILOT' AS action_type,
         'DONE' AS execute_status,
         'tit02 liability shadow pilot executed' AS note
  FROM dual
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

PROMPT === 3) 最近影子写入记录（前10条） ===
SELECT source_object, target_object, biz_key, action_type, compare_result, detail_msg, created_at_utc
FROM (
  SELECT source_object, target_object, biz_key, action_type, compare_result, detail_msg, created_at_utc
  FROM MIG_P1_SHADOW_WRITE_LOG
  WHERE batch_no = 'P1_BATCH01'
  ORDER BY created_at_utc DESC
)
WHERE ROWNUM <= 10;

EXIT;
