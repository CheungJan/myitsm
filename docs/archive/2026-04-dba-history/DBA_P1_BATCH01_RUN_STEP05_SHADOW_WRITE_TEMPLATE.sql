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
    raise_application_error(-20067, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 影子写入日志表（不存在则创建） ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P1_SHADOW_WRITE_LOG (
      shadow_id           RAW(16)      NOT NULL,
      batch_no            VARCHAR2(30) NOT NULL,
      source_object       VARCHAR2(64) NOT NULL,
      target_object       VARCHAR2(64) NOT NULL,
      biz_key             VARCHAR2(128),
      action_type         VARCHAR2(20) NOT NULL,
      compare_result      VARCHAR2(20) NOT NULL,
      detail_msg          VARCHAR2(1000),
      created_at_utc      TIMESTAMP(6) DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      CONSTRAINT PK_MIG_P1_SHADOW_WRITE_LOG PRIMARY KEY (shadow_id)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 示例模板：PLAN_CUST 的影子写入比对（默认不执行，仅演示） ===
PROMPT -- 使用说明：
PROMPT -- 1) 将 :p_planno/:p_custcd/:p_status 替换为应用层即将写入的值；
PROMPT -- 2) 在同一事务内，先写旧路径，再影子写新表；
PROMPT -- 3) compare_result 取值建议：MATCH/DIFF/ERROR。
PROMPT
PROMPT -- 示例SQL（按需拷贝到应用侧事务脚本，不在本模板里自动执行）
PROMPT -- INSERT INTO PLAN_CUST (PLANNO, CUSTCD, STATUS) VALUES (:p_planno, :p_custcd, :p_status);
PROMPT -- INSERT INTO ITSM_CORE_PLAN_CUSTOMER_XREF (xref_id, src_plan_no, src_custcd, src_status, source_object)
PROMPT -- VALUES (SYS_GUID(), :p_planno, :p_custcd, :p_status, 'PLAN_CUST');
PROMPT -- INSERT INTO MIG_P1_SHADOW_WRITE_LOG (shadow_id, batch_no, source_object, target_object, biz_key, action_type, compare_result, detail_msg)
PROMPT -- VALUES (SYS_GUID(), 'P1_BATCH01', 'PLAN_CUST', 'ITSM_CORE_PLAN_CUSTOMER_XREF', :p_planno, 'INSERT', 'MATCH', 'shadow write demo');

PROMPT === 3) 示例模板：TIT02_LIABILITYREG 的影子写入比对（默认不执行，仅演示） ===
PROMPT -- 示例SQL（按需拷贝到应用侧事务脚本，不在本模板里自动执行）
PROMPT -- INSERT INTO TIT02_LIABILITYREG (LIABCD, LIABNM, DESCRIBE, LIABTYPE, PARENT, CHILDFLG, USEFLG, GENDATE, UPDDATE)
PROMPT -- VALUES (:p_liabcd, :p_liabnm, :p_describe, :p_liabtype, :p_parent, :p_childflg, :p_useflg, :p_gendate, :p_upddate);
PROMPT -- INSERT INTO ITSM_CORE_LIABILITY (liability_id, src_liabcd, src_liabnm, src_describe, src_liabtype, src_parent, src_childflg, src_useflg, src_gendate, src_upddate, source_object)
PROMPT -- VALUES (SYS_GUID(), :p_liabcd, :p_liabnm, :p_describe, :p_liabtype, :p_parent, :p_childflg, :p_useflg, :p_gendate, :p_upddate, 'TIT02_LIABILITYREG');
PROMPT -- INSERT INTO MIG_P1_SHADOW_WRITE_LOG (shadow_id, batch_no, source_object, target_object, biz_key, action_type, compare_result, detail_msg)
PROMPT -- VALUES (SYS_GUID(), 'P1_BATCH01', 'TIT02_LIABILITYREG', 'ITSM_CORE_LIABILITY', :p_liabcd, 'INSERT', 'MATCH', 'shadow write demo');

PROMPT === 4) 写入批次日志（Step3.3 Shadow Template） ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P1_BATCH01' AS batch_no,
         'CONTROL' AS object_type,
         'SHADOW_WRITE_TEMPLATE' AS object_name,
         'STEP3_3_SHADOW_TEMPLATE' AS action_type,
         'READY' AS execute_status,
         'shadow write template prepared' AS note
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

EXIT;
