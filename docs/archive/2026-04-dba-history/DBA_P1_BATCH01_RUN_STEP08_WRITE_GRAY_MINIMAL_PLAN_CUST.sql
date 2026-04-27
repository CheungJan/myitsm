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
    raise_application_error(-20071, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) PLAN_CUST 最小写灰度：抽样1条并执行幂等双写 ===
DECLARE
  v_has_planno      NUMBER := 0;
  v_has_plan_no     NUMBER := 0;
  v_has_billno      NUMBER := 0;
  v_has_plbillno    NUMBER := 0;
  v_has_custcd      NUMBER := 0;
  v_has_customercd  NUMBER := 0;
  v_has_status      NUMBER := 0;
  v_has_state       NUMBER := 0;

  v_expr_plan_no    VARCHAR2(200);
  v_expr_custcd     VARCHAR2(200);
  v_expr_status     VARCHAR2(200);
  v_sql             CLOB;

  v_plan_no         VARCHAR2(128);
  v_custcd          VARCHAR2(64);
  v_status          VARCHAR2(64);
  v_src_cnt         NUMBER := 0;
  v_tgt_cnt         NUMBER := 0;
  v_compare_result  VARCHAR2(20);
  v_detail_msg      VARCHAR2(1000);
BEGIN
  SELECT COUNT(*) INTO v_has_planno FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'PLANNO';
  SELECT COUNT(*) INTO v_has_plan_no FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'PLAN_NO';
  SELECT COUNT(*) INTO v_has_billno FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'BILLNO';
  SELECT COUNT(*) INTO v_has_plbillno FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'PLBILLNO';
  SELECT COUNT(*) INTO v_has_custcd FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'CUSTCD';
  SELECT COUNT(*) INTO v_has_customercd FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'CUSTOMERCD';
  SELECT COUNT(*) INTO v_has_status FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'STATUS';
  SELECT COUNT(*) INTO v_has_state FROM user_tab_columns WHERE table_name = 'PLAN_CUST' AND column_name = 'STATE';

  IF v_has_planno > 0 THEN
    v_expr_plan_no := 'TO_CHAR(planno)';
  ELSIF v_has_plan_no > 0 THEN
    v_expr_plan_no := 'TO_CHAR(plan_no)';
  ELSIF v_has_billno > 0 THEN
    v_expr_plan_no := 'TO_CHAR(billno)';
  ELSIF v_has_plbillno > 0 THEN
    v_expr_plan_no := 'TO_CHAR(plbillno)';
  ELSE
    v_expr_plan_no := 'CAST(NULL AS VARCHAR2(128))';
  END IF;

  IF v_has_custcd > 0 THEN
    v_expr_custcd := 'TO_CHAR(custcd)';
  ELSIF v_has_customercd > 0 THEN
    v_expr_custcd := 'TO_CHAR(customercd)';
  ELSE
    v_expr_custcd := 'CAST(NULL AS VARCHAR2(64))';
  END IF;

  IF v_has_status > 0 THEN
    v_expr_status := 'TO_CHAR(status)';
  ELSIF v_has_state > 0 THEN
    v_expr_status := 'TO_CHAR(state)';
  ELSE
    v_expr_status := 'CAST(NULL AS VARCHAR2(64))';
  END IF;

  v_sql := 'SELECT src_plan_no, src_custcd, src_status FROM ('
        || ' SELECT ' || v_expr_plan_no || ' AS src_plan_no, '
        ||            v_expr_custcd || ' AS src_custcd, '
        ||            v_expr_status || ' AS src_status '
        || ' FROM PLAN_CUST '
        || ' WHERE ' || v_expr_plan_no || ' IS NOT NULL '
        || ' ORDER BY 1 DESC '
        || ') WHERE ROWNUM = 1';

  BEGIN
    EXECUTE IMMEDIATE v_sql INTO v_plan_no, v_custcd, v_status;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      v_compare_result := 'ERROR';
      v_detail_msg := 'no sample row found in PLAN_CUST';

      INSERT INTO MIG_P1_SHADOW_WRITE_LOG (
        shadow_id, batch_no, source_object, target_object, biz_key,
        action_type, compare_result, detail_msg
      ) VALUES (
        SYS_GUID(), 'P1_BATCH01', 'PLAN_CUST', 'ITSM_CORE_PLAN_CUSTOMER_XREF',
        NULL, 'GRAY_WRITE', v_compare_result, v_detail_msg
      );

      RETURN;
  END;

  MERGE INTO ITSM_CORE_PLAN_CUSTOMER_XREF t
  USING (
    SELECT v_plan_no AS src_plan_no,
           v_custcd AS src_custcd,
           v_status AS src_status
    FROM dual
  ) s
  ON (
    t.source_object = 'PLAN_CUST'
    AND t.src_plan_no = s.src_plan_no
    AND NVL(t.src_custcd, '~') = NVL(s.src_custcd, '~')
  )
  WHEN MATCHED THEN
    UPDATE SET t.src_status = s.src_status
  WHEN NOT MATCHED THEN
    INSERT (xref_id, src_plan_no, src_custcd, src_status, source_object)
    VALUES (SYS_GUID(), s.src_plan_no, s.src_custcd, s.src_status, 'PLAN_CUST');

  v_sql := 'SELECT COUNT(*) FROM PLAN_CUST WHERE ' || v_expr_plan_no || ' = :1'
        || ' AND NVL(' || v_expr_custcd || ', ''~'') = NVL(:2, ''~'')';
  EXECUTE IMMEDIATE v_sql INTO v_src_cnt USING v_plan_no, v_custcd;

  SELECT COUNT(*)
    INTO v_tgt_cnt
    FROM ITSM_CORE_PLAN_CUSTOMER_XREF
   WHERE source_object = 'PLAN_CUST'
     AND src_plan_no = v_plan_no
     AND NVL(src_custcd, '~') = NVL(v_custcd, '~');

  IF v_src_cnt > 0 AND v_tgt_cnt > 0 THEN
    v_compare_result := 'MATCH';
    v_detail_msg := 'gray write upsert success';
  ELSE
    v_compare_result := 'DIFF';
    v_detail_msg := 'gray write compare failed';
  END IF;

  INSERT INTO MIG_P1_SHADOW_WRITE_LOG (
    shadow_id, batch_no, source_object, target_object, biz_key,
    action_type, compare_result, detail_msg
  ) VALUES (
    SYS_GUID(), 'P1_BATCH01', 'PLAN_CUST', 'ITSM_CORE_PLAN_CUSTOMER_XREF',
    v_plan_no, 'GRAY_WRITE', v_compare_result,
    v_detail_msg || '; src_cnt=' || TO_CHAR(v_src_cnt) || '; tgt_cnt=' || TO_CHAR(v_tgt_cnt)
  );
END;
/

PROMPT === 2) 写入批次日志（Step3.3 最小写灰度） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no,
         'CONTROL' AS object_type,
         'WRITE_GRAY_PLAN_CUST_MIN' AS object_name,
         'STEP3_3_WRITE_GRAY' AS action_type,
         'DONE' AS execute_status,
         'plan_cust minimal write gray executed' AS note
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

PROMPT === 3) 最近20条影子写记录（GRAY_WRITE 优先） ===
SELECT source_object, target_object, biz_key, action_type, compare_result, detail_msg, created_at_utc
FROM (
  SELECT source_object, target_object, biz_key, action_type, compare_result, detail_msg, created_at_utc
  FROM MIG_P1_SHADOW_WRITE_LOG
  WHERE batch_no = 'P1_BATCH01'
  ORDER BY created_at_utc DESC
)
WHERE ROWNUM <= 20;

EXIT;
