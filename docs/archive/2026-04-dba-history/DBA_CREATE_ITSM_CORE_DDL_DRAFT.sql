SET ECHO ON;
SET SERVEROUTPUT ON;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

-- 0) 安全门禁：仅允许在 CCGL_MIG 服务执行
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20031, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

-- 1) 创建核心实体表：客户主数据
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE ITSM_CORE_CUSTOMER (
      customer_id         VARCHAR2(64)  NOT NULL,
      legacy_custcd       VARCHAR2(32),
      customer_name       VARCHAR2(200),
      area_code           VARCHAR2(64),
      location_code       VARCHAR2(64),
      customer_level      VARCHAR2(32),
      status_code         VARCHAR2(32),
      source_system       VARCHAR2(32)  DEFAULT ''CCGL'' NOT NULL,
      created_at_utc      TIMESTAMP(6)  DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      updated_at_utc      TIMESTAMP(6)  DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      CONSTRAINT PK_ITSM_CORE_CUSTOMER PRIMARY KEY (customer_id)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

-- 2) 创建核心实体表：开通计划主表
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE ITSM_CORE_PLAN (
      plan_id             VARCHAR2(64)  NOT NULL,
      legacy_planno       VARCHAR2(64),
      customer_id         VARCHAR2(64)  NOT NULL,
      plan_type_code      VARCHAR2(32),
      plan_status_code    VARCHAR2(32)  NOT NULL,
      result_code         VARCHAR2(32),
      fail_reason         VARCHAR2(1000),
      planned_at_utc      TIMESTAMP(6),
      finished_at_utc     TIMESTAMP(6),
      source_system       VARCHAR2(32)  DEFAULT ''CCGL'' NOT NULL,
      created_at_utc      TIMESTAMP(6)  DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      updated_at_utc      TIMESTAMP(6)  DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      CONSTRAINT PK_ITSM_CORE_PLAN PRIMARY KEY (plan_id),
      CONSTRAINT FK_ITSM_CORE_PLAN_CUSTOMER FOREIGN KEY (customer_id)
        REFERENCES ITSM_CORE_CUSTOMER (customer_id)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

-- 3) 创建核心实体表：计划状态事件（审计轨迹）
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE ITSM_CORE_PLAN_EVENT (
      event_id            VARCHAR2(64)  NOT NULL,
      plan_id             VARCHAR2(64)  NOT NULL,
      from_status_code    VARCHAR2(32),
      to_status_code      VARCHAR2(32)  NOT NULL,
      event_time_utc      TIMESTAMP(6)  DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
      operator_id         VARCHAR2(64),
      event_note          VARCHAR2(1000),
      source_system       VARCHAR2(32)  DEFAULT ''CCGL'' NOT NULL,
      CONSTRAINT PK_ITSM_CORE_PLAN_EVENT PRIMARY KEY (event_id),
      CONSTRAINT FK_ITSM_CORE_EVENT_PLAN FOREIGN KEY (plan_id)
        REFERENCES ITSM_CORE_PLAN (plan_id)
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

-- 4) 索引（幂等创建）
BEGIN
  EXECUTE IMMEDIATE 'CREATE INDEX IDX_CORE_PLAN_CUSTOMER ON ITSM_CORE_PLAN (customer_id)';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE 'CREATE INDEX IDX_CORE_PLAN_STATUS ON ITSM_CORE_PLAN (plan_status_code)';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE 'CREATE INDEX IDX_CORE_EVENT_PLAN_TIME ON ITSM_CORE_PLAN_EVENT (plan_id, event_time_utc)';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

-- 5) 基础校验
PROMPT === VERIFY TABLES ===
SELECT table_name
FROM user_tables
WHERE table_name IN ('ITSM_CORE_CUSTOMER', 'ITSM_CORE_PLAN', 'ITSM_CORE_PLAN_EVENT')
ORDER BY table_name;

PROMPT === VERIFY INDEXES ===
SELECT index_name, table_name
FROM user_indexes
WHERE table_name IN ('ITSM_CORE_CUSTOMER', 'ITSM_CORE_PLAN', 'ITSM_CORE_PLAN_EVENT')
ORDER BY table_name, index_name;

EXIT;
