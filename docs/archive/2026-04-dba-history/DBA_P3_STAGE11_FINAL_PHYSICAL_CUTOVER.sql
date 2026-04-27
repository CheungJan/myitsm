SET ECHO ON;
SET SERVEROUTPUT ON;
SET PAGESIZE 300;
SET LINESIZE 260;
WHENEVER SQLERROR EXIT SQL.SQLCODE;

PROMPT === 0) 安全门禁：仅允许在 CCGL_MIG 服务执行 ===
DECLARE
  v_service_name VARCHAR2(128);
BEGIN
  SELECT UPPER(SYS_CONTEXT('USERENV', 'SERVICE_NAME'))
    INTO v_service_name
    FROM dual;

  IF v_service_name <> 'CCGL_MIG' THEN
    raise_application_error(-20591, 'Wrong service: ' || v_service_name || ', expected CCGL_MIG');
  END IF;
END;
/

PROMPT === 1) 执行台账表存在性保障 ===
BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_FINAL_NAME_PLAN (
      stage_no          VARCHAR2(30)  NOT NULL,
      wave_no           VARCHAR2(30)  NOT NULL,
      object_type       VARCHAR2(30)  NOT NULL,
      source_name       VARCHAR2(128) NOT NULL,
      target_name       VARCHAR2(128),
      plan_action       VARCHAR2(40)  NOT NULL,
      plan_status       VARCHAR2(20)  NOT NULL,
      note              VARCHAR2(400),
      updated_at        DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_FINAL_NAME_PLAN PRIMARY KEY (
        stage_no, wave_no, object_type, source_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_FINAL_NAME_EXEC (
      stage_no          VARCHAR2(30)  NOT NULL,
      wave_no           VARCHAR2(30)  NOT NULL,
      object_type       VARCHAR2(30)  NOT NULL,
      object_name       VARCHAR2(128) NOT NULL,
      exec_action       VARCHAR2(40)  NOT NULL,
      exec_status       VARCHAR2(20)  NOT NULL,
      note              VARCHAR2(400),
      updated_at        DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_FINAL_NAME_EXEC PRIMARY KEY (
        stage_no, wave_no, object_type, object_name, exec_action
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE '
    CREATE TABLE MIG_P3_FINAL_NAME_RB (
      stage_no          VARCHAR2(30)  NOT NULL,
      wave_no           VARCHAR2(30)  NOT NULL,
      object_type       VARCHAR2(30)  NOT NULL,
      object_name       VARCHAR2(128) NOT NULL,
      rollback_sql      CLOB,
      ddl_text          CLOB,
      updated_at        DATE DEFAULT SYSDATE NOT NULL,
      CONSTRAINT PK_P3_FINAL_NAME_RB PRIMARY KEY (
        stage_no, wave_no, object_type, object_name
      )
    )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;
/

PROMPT === 2) 生成“目标名->原名”回切计划 ===
MERGE INTO MIG_P3_FINAL_NAME_PLAN t
USING (
  WITH obj_all AS (
    SELECT 'TABLE' AS object_type, table_name AS object_name FROM user_tables
    UNION ALL
    SELECT 'VIEW'  AS object_type, view_name  AS object_name FROM user_views
  ),
  l1 AS (
    SELECT source_object_type AS object_type,
           source_object_name AS source_name,
           NVL(target_object_name, source_object_name) AS target_name
    FROM MIG_P3_L1_OBJECT_SET
    WHERE stage_no='P3_STAGE02'
      AND wave_no='WAVE_01'
      AND freeze_status='FROZEN'
  )
  SELECT 'P3_STAGE11' AS stage_no,
         'WAVE_01' AS wave_no,
         l1.object_type,
         l1.source_name,
         l1.target_name,
         CASE
           WHEN l1.source_name = l1.target_name THEN 'KEEP_AS_IS'
           WHEN src.object_name IS NULL AND tgt.object_name IS NOT NULL THEN 'RENAME_TARGET_TO_SOURCE'
           WHEN src.object_name IS NOT NULL AND tgt.object_name IS NOT NULL THEN 'DROP_TARGET_DUP'
           WHEN src.object_name IS NOT NULL AND tgt.object_name IS NULL THEN 'KEEP_AS_IS'
           ELSE 'BLOCKED'
         END AS plan_action,
         CASE
           WHEN l1.source_name = l1.target_name THEN 'DONE'
           WHEN src.object_name IS NULL AND tgt.object_name IS NOT NULL THEN 'READY'
           WHEN src.object_name IS NOT NULL AND tgt.object_name IS NOT NULL THEN 'READY'
           WHEN src.object_name IS NOT NULL AND tgt.object_name IS NULL THEN 'DONE'
           ELSE 'BLOCKED'
         END AS plan_status,
         CASE
           WHEN l1.source_name = l1.target_name THEN 'source and target are same'
           WHEN src.object_name IS NULL AND tgt.object_name IS NOT NULL THEN 'rename target to source'
           WHEN src.object_name IS NOT NULL AND tgt.object_name IS NOT NULL THEN 'source exists, drop duplicated target'
           WHEN src.object_name IS NOT NULL AND tgt.object_name IS NULL THEN 'source already exists, target missing'
           ELSE 'source/target both missing'
         END AS note
  FROM l1
  LEFT JOIN obj_all src
    ON src.object_type = l1.object_type
   AND src.object_name = l1.source_name
  LEFT JOIN obj_all tgt
    ON tgt.object_type = l1.object_type
   AND tgt.object_name = l1.target_name
) s
ON (
  t.stage_no = s.stage_no
  AND t.wave_no = s.wave_no
  AND t.object_type = s.object_type
  AND t.source_name = s.source_name
)
WHEN MATCHED THEN
  UPDATE SET
    t.target_name = s.target_name,
    t.plan_action = s.plan_action,
    t.plan_status = s.plan_status,
    t.note = s.note,
    t.updated_at = SYSDATE
WHEN NOT MATCHED THEN
  INSERT (
    stage_no, wave_no, object_type, source_name, target_name,
    plan_action, plan_status, note, updated_at
  )
  VALUES (
    s.stage_no, s.wave_no, s.object_type, s.source_name, s.target_name,
    s.plan_action, s.plan_status, s.note, SYSDATE
  );
/

PROMPT === 3) 执行回切与去重 ===
DECLARE
  v_ddl CLOB;
  v_sql VARCHAR2(1200);
  v_rb_sql VARCHAR2(1200);
  v_status VARCHAR2(20);
  v_note VARCHAR2(400);
  FUNCTION qname(p_name VARCHAR2) RETURN VARCHAR2 IS
  BEGIN
    RETURN '"' || REPLACE(p_name, '"', '""') || '"';
  END;
BEGIN
  FOR r IN (
    SELECT object_type,
           source_name,
           target_name,
           plan_action
    FROM MIG_P3_FINAL_NAME_PLAN
    WHERE stage_no='P3_STAGE11'
      AND wave_no='WAVE_01'
      AND plan_status='READY'
    ORDER BY object_type, source_name
  ) LOOP
    v_status := 'DONE';
    v_note := 'ok';
    BEGIN
      IF r.plan_action = 'RENAME_TARGET_TO_SOURCE' THEN
        BEGIN
          SELECT DBMS_METADATA.GET_DDL(r.object_type, r.target_name, USER)
            INTO v_ddl
            FROM dual;
        EXCEPTION
          WHEN OTHERS THEN
            v_ddl := NULL;
        END;

        IF r.object_type = 'TABLE' THEN
          v_sql := 'ALTER TABLE ' || qname(r.target_name) || ' RENAME TO ' || qname(r.source_name);
        ELSE
          v_sql := 'RENAME ' || qname(r.target_name) || ' TO ' || qname(r.source_name);
        END IF;

        EXECUTE IMMEDIATE v_sql;
        v_rb_sql := 'RENAME ' || qname(r.source_name) || ' TO ' || qname(r.target_name);

        MERGE INTO MIG_P3_FINAL_NAME_RB t
        USING (
          SELECT 'P3_STAGE11' AS stage_no,
                 'WAVE_01' AS wave_no,
                 r.object_type AS object_type,
                 r.source_name AS object_name,
                 v_rb_sql AS rollback_sql,
                 v_ddl AS ddl_text
          FROM dual
        ) s
        ON (
          t.stage_no=s.stage_no
          AND t.wave_no=s.wave_no
          AND t.object_type=s.object_type
          AND t.object_name=s.object_name
        )
        WHEN MATCHED THEN
          UPDATE SET
            t.rollback_sql=s.rollback_sql,
            t.ddl_text=s.ddl_text,
            t.updated_at=SYSDATE
        WHEN NOT MATCHED THEN
          INSERT (stage_no,wave_no,object_type,object_name,rollback_sql,ddl_text,updated_at)
          VALUES (s.stage_no,s.wave_no,s.object_type,s.object_name,s.rollback_sql,s.ddl_text,SYSDATE);

      ELSIF r.plan_action = 'DROP_TARGET_DUP' THEN
        BEGIN
          SELECT DBMS_METADATA.GET_DDL(r.object_type, r.target_name, USER)
            INTO v_ddl
            FROM dual;
        EXCEPTION
          WHEN OTHERS THEN
            v_ddl := NULL;
        END;

        IF r.object_type = 'TABLE' THEN
          EXECUTE IMMEDIATE 'DROP TABLE ' || qname(r.target_name) || ' PURGE';
        ELSE
          EXECUTE IMMEDIATE 'DROP VIEW ' || qname(r.target_name);
        END IF;

        MERGE INTO MIG_P3_FINAL_NAME_RB t
        USING (
          SELECT 'P3_STAGE11' AS stage_no,
                 'WAVE_01' AS wave_no,
                 r.object_type AS object_type,
                 r.target_name AS object_name,
                 NULL AS rollback_sql,
                 v_ddl AS ddl_text
          FROM dual
        ) s
        ON (
          t.stage_no=s.stage_no
          AND t.wave_no=s.wave_no
          AND t.object_type=s.object_type
          AND t.object_name=s.object_name
        )
        WHEN MATCHED THEN
          UPDATE SET
            t.rollback_sql=s.rollback_sql,
            t.ddl_text=s.ddl_text,
            t.updated_at=SYSDATE
        WHEN NOT MATCHED THEN
          INSERT (stage_no,wave_no,object_type,object_name,rollback_sql,ddl_text,updated_at)
          VALUES (s.stage_no,s.wave_no,s.object_type,s.object_name,s.rollback_sql,s.ddl_text,SYSDATE);
      ELSE
        v_status := 'SKIPPED';
        v_note := 'unsupported action=' || r.plan_action;
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        v_status := 'FAILED';
        v_note := SUBSTR(SQLERRM, 1, 380);
    END;

    MERGE INTO MIG_P3_FINAL_NAME_EXEC t
    USING (
      SELECT 'P3_STAGE11' AS stage_no,
             'WAVE_01' AS wave_no,
             r.object_type AS object_type,
             r.source_name AS object_name,
             r.plan_action AS exec_action,
             v_status AS exec_status,
             v_note AS note
      FROM dual
    ) s
    ON (
      t.stage_no=s.stage_no
      AND t.wave_no=s.wave_no
      AND t.object_type=s.object_type
      AND t.object_name=s.object_name
      AND t.exec_action=s.exec_action
    )
    WHEN MATCHED THEN
      UPDATE SET
        t.exec_status=s.exec_status,
        t.note=s.note,
        t.updated_at=SYSDATE
    WHEN NOT MATCHED THEN
      INSERT (stage_no,wave_no,object_type,object_name,exec_action,exec_status,note,updated_at)
      VALUES (s.stage_no,s.wave_no,s.object_type,s.object_name,s.exec_action,s.exec_status,s.note,SYSDATE);
  END LOOP;
END;
/

PROMPT === 4) 清理不在最终保留集内的对象（表/视图） ===
DECLARE
  v_ddl CLOB;
  v_status VARCHAR2(20);
  v_note VARCHAR2(400);
  FUNCTION qname(p_name VARCHAR2) RETURN VARCHAR2 IS
  BEGIN
    RETURN '"' || REPLACE(p_name, '"', '""') || '"';
  END;
BEGIN
  FOR r IN (
    WITH final_keep AS (
      SELECT source_object_type AS object_type,
             source_object_name AS object_name
      FROM MIG_P3_L1_OBJECT_SET
      WHERE stage_no='P3_STAGE02'
        AND wave_no='WAVE_01'
        AND freeze_status='FROZEN'
    ),
    infra_keep AS (
      SELECT 'TABLE' AS object_type, 'MIG_P1_BATCH_LOG' AS object_name FROM dual
      UNION ALL SELECT 'TABLE', 'MIG_P3_FINAL_NAME_PLAN' FROM dual
      UNION ALL SELECT 'TABLE', 'MIG_P3_FINAL_NAME_EXEC' FROM dual
      UNION ALL SELECT 'TABLE', 'MIG_P3_FINAL_NAME_RB' FROM dual
    ),
    obj_all AS (
      SELECT 'TABLE' AS object_type, table_name AS object_name FROM user_tables
      UNION ALL
      SELECT 'VIEW' AS object_type, view_name AS object_name FROM user_views
    )
    SELECT a.object_type,
           a.object_name
    FROM obj_all a
    LEFT JOIN final_keep f
      ON f.object_type = a.object_type
     AND f.object_name = a.object_name
    LEFT JOIN infra_keep k
      ON k.object_type = a.object_type
     AND k.object_name = a.object_name
    WHERE f.object_name IS NULL
      AND k.object_name IS NULL
    ORDER BY a.object_type, a.object_name
  ) LOOP
    v_status := 'DONE';
    v_note := 'dropped non-final object';
    BEGIN
      BEGIN
        SELECT DBMS_METADATA.GET_DDL(r.object_type, r.object_name, USER)
          INTO v_ddl
          FROM dual;
      EXCEPTION
        WHEN OTHERS THEN
          v_ddl := NULL;
      END;

      IF r.object_type = 'TABLE' THEN
        EXECUTE IMMEDIATE 'DROP TABLE ' || qname(r.object_name) || ' PURGE';
      ELSE
        EXECUTE IMMEDIATE 'DROP VIEW ' || qname(r.object_name);
      END IF;

      MERGE INTO MIG_P3_FINAL_NAME_RB t
      USING (
        SELECT 'P3_STAGE11' AS stage_no,
               'WAVE_01' AS wave_no,
               r.object_type AS object_type,
               r.object_name AS object_name,
               NULL AS rollback_sql,
               v_ddl AS ddl_text
        FROM dual
      ) s
      ON (
        t.stage_no=s.stage_no
        AND t.wave_no=s.wave_no
        AND t.object_type=s.object_type
        AND t.object_name=s.object_name
      )
      WHEN MATCHED THEN
        UPDATE SET
          t.rollback_sql=s.rollback_sql,
          t.ddl_text=s.ddl_text,
          t.updated_at=SYSDATE
      WHEN NOT MATCHED THEN
        INSERT (stage_no,wave_no,object_type,object_name,rollback_sql,ddl_text,updated_at)
        VALUES (s.stage_no,s.wave_no,s.object_type,s.object_name,s.rollback_sql,s.ddl_text,SYSDATE);

    EXCEPTION
      WHEN OTHERS THEN
        v_status := 'FAILED';
        v_note := SUBSTR(SQLERRM, 1, 380);
    END;

    MERGE INTO MIG_P3_FINAL_NAME_EXEC t
    USING (
      SELECT 'P3_STAGE11' AS stage_no,
             'WAVE_01' AS wave_no,
             r.object_type AS object_type,
             r.object_name AS object_name,
             'DROP_NON_FINAL' AS exec_action,
             v_status AS exec_status,
             v_note AS note
      FROM dual
    ) s
    ON (
      t.stage_no=s.stage_no
      AND t.wave_no=s.wave_no
      AND t.object_type=s.object_type
      AND t.object_name=s.object_name
      AND t.exec_action=s.exec_action
    )
    WHEN MATCHED THEN
      UPDATE SET
        t.exec_status=s.exec_status,
        t.note=s.note,
        t.updated_at=SYSDATE
    WHEN NOT MATCHED THEN
      INSERT (stage_no,wave_no,object_type,object_name,exec_action,exec_status,note,updated_at)
      VALUES (s.stage_no,s.wave_no,s.object_type,s.object_name,s.exec_action,s.exec_status,s.note,SYSDATE);
  END LOOP;
END;
/

PROMPT === 5) 回写主线日志 ===
MERGE INTO MIG_P1_BATCH_LOG t
USING (
  SELECT 'P3_STAGE11' AS batch_no,
         object_type,
         object_name,
         exec_action AS action_type,
         exec_status AS execute_status,
         note
  FROM MIG_P3_FINAL_NAME_EXEC
  WHERE stage_no='P3_STAGE11'
    AND wave_no='WAVE_01'
) s
ON (
  t.batch_no=s.batch_no
  AND t.object_type=s.object_type
  AND t.object_name=s.object_name
  AND t.action_type=s.action_type
)
WHEN MATCHED THEN
  UPDATE SET
    t.execute_status=s.execute_status,
    t.note=s.note,
    t.executed_at=SYSDATE
WHEN NOT MATCHED THEN
  INSERT (batch_no,object_type,object_name,action_type,execute_status,note,executed_at)
  VALUES (s.batch_no,s.object_type,s.object_name,s.action_type,s.execute_status,s.note,SYSDATE);
/

PROMPT === 6) 摘要 ===
SELECT plan_action, plan_status, COUNT(*) AS cnt
FROM MIG_P3_FINAL_NAME_PLAN
WHERE stage_no='P3_STAGE11'
  AND wave_no='WAVE_01'
GROUP BY plan_action, plan_status
ORDER BY plan_action, plan_status;

SELECT exec_action, exec_status, COUNT(*) AS cnt
FROM MIG_P3_FINAL_NAME_EXEC
WHERE stage_no='P3_STAGE11'
  AND wave_no='WAVE_01'
GROUP BY exec_action, exec_status
ORDER BY exec_action, exec_status;

SELECT COUNT(*) AS rollback_items
FROM MIG_P3_FINAL_NAME_RB
WHERE stage_no='P3_STAGE11'
  AND wave_no='WAVE_01';

SELECT COUNT(*) AS final_tables FROM user_tables;
SELECT COUNT(*) AS final_views  FROM user_views;

EXIT;
