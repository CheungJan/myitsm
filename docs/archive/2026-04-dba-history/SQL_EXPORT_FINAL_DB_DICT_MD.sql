SET ECHO OFF;
SET FEEDBACK OFF;
SET HEADING OFF;
SET PAGESIZE 0;
SET LINESIZE 32767;
SET TRIMSPOOL ON;
SET SERVEROUTPUT ON SIZE UNLIMITED;

SPOOL e:\project\myitsm\src\docs\数据库字典_精简后_最终版.md

DECLARE
  v_business_tables NUMBER;
  v_business_views  NUMBER;
  v_mig_tables      NUMBER;
  v_status          VARCHAR2(40);
  v_idx_count       NUMBER;
  v_trg_count       NUMBER;
  v_seq             NUMBER := 0;

  FUNCTION esc(p_text IN VARCHAR2) RETURN VARCHAR2 IS
  BEGIN
    RETURN REPLACE(REPLACE(REPLACE(NVL(p_text, ''), '|', '\\|'), CHR(13), ' '), CHR(10), ' ');
  END;

  FUNCTION col_type_fmt(
    p_data_type      IN VARCHAR2,
    p_data_length    IN NUMBER,
    p_data_precision IN NUMBER,
    p_data_scale     IN NUMBER
  ) RETURN VARCHAR2 IS
  BEGIN
    IF p_data_type IN ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR') THEN
      RETURN p_data_type || '(' || p_data_length || ')';
    ELSIF p_data_type = 'NUMBER' THEN
      IF p_data_precision IS NULL THEN
        RETURN 'NUMBER';
      ELSIF p_data_scale IS NULL THEN
        RETURN 'NUMBER(' || p_data_precision || ')';
      ELSE
        RETURN 'NUMBER(' || p_data_precision || ',' || p_data_scale || ')';
      END IF;
    ELSE
      RETURN p_data_type;
    END IF;
  END;
BEGIN
  SELECT COUNT(*) INTO v_business_tables
  FROM user_tables
  WHERE table_name NOT LIKE 'MIG\_%' ESCAPE '\\';

  SELECT COUNT(*) INTO v_business_views
  FROM user_views
  WHERE view_name NOT LIKE 'MIG\_%' ESCAPE '\\';

  SELECT COUNT(*) INTO v_mig_tables
  FROM user_tables
  WHERE table_name LIKE 'MIG\_%' ESCAPE '\\';

  SELECT CASE
           WHEN EXISTS (
             SELECT 1
             FROM MIG_P3_FINAL_NAME_EXEC
             WHERE stage_no='P3_STAGE11'
               AND wave_no='WAVE_01'
               AND exec_action='DROP_TARGET_DUP'
               AND exec_status='DONE'
           )
            AND NOT EXISTS (
             SELECT 1
             FROM MIG_P3_FINAL_NAME_EXEC
             WHERE stage_no='P3_STAGE11'
               AND wave_no='WAVE_01'
               AND exec_status='FAILED'
           )
           THEN 'OPTIMIZED_DONE'
           ELSE 'OPTIMIZED_NOT_DONE'
         END
    INTO v_status
    FROM dual;

  DBMS_OUTPUT.PUT_LINE('# 数据库字典（精简后最终版）');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('## 1. 总体介绍');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('- 编写目的：说明精简后数据库结构，供开发、实施、运维统一参考。');
  DBMS_OUTPUT.PUT_LINE('- 适用范围：CCGL_MIG 当前精简后库（业务对象 + 最小治理留痕对象）。');
  DBMS_OUTPUT.PUT_LINE('- 生成方式：由系统字典自动导出。');
  DBMS_OUTPUT.PUT_LINE('');

  DBMS_OUTPUT.PUT_LINE('## 2. 概述');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('| 项 | 值 |');
  DBMS_OUTPUT.PUT_LINE('|---|---|');
  DBMS_OUTPUT.PUT_LINE('| 优化状态 | ' || v_status || ' |');
  DBMS_OUTPUT.PUT_LINE('| 业务表数量 | ' || v_business_tables || ' |');
  DBMS_OUTPUT.PUT_LINE('| 业务视图数量 | ' || v_business_views || ' |');
  DBMS_OUTPUT.PUT_LINE('| MIG留痕表数量 | ' || v_mig_tables || ' |');
  DBMS_OUTPUT.PUT_LINE('');

  DBMS_OUTPUT.PUT_LINE('## 3. 物理设计');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('### 3.1 对象规模');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('- 本文档聚焦业务表与业务视图。');
  DBMS_OUTPUT.PUT_LINE('- MIG 开头对象为迁移治理与审计留痕，不纳入业务实体设计章节。');
  DBMS_OUTPUT.PUT_LINE('');

  DBMS_OUTPUT.PUT_LINE('## 4. 安全设计');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('- 通过业务账号访问业务对象。');
  DBMS_OUTPUT.PUT_LINE('- 迁移治理对象与业务对象权限建议隔离维护。');
  DBMS_OUTPUT.PUT_LINE('');

  DBMS_OUTPUT.PUT_LINE('## 5. 逻辑设计');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('### 5.1 实体说明');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('#### 5.1.1 数据表实体清单');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('| 表名 | 说明 |');
  DBMS_OUTPUT.PUT_LINE('|---|---|');
  FOR t IN (
    SELECT t.table_name,
           NVL(tc.comments, '') AS table_comment
    FROM user_tables t
    LEFT JOIN user_tab_comments tc
      ON tc.table_name = t.table_name
    WHERE t.table_name NOT LIKE 'MIG\_%' ESCAPE '\\'
    ORDER BY t.table_name
  ) LOOP
    DBMS_OUTPUT.PUT_LINE('| ' || t.table_name || ' | ' || esc(t.table_comment) || ' |');
  END LOOP;
  DBMS_OUTPUT.PUT_LINE('');

  DBMS_OUTPUT.PUT_LINE('#### 5.1.2 视图实体清单');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('| 视图名 | 说明 |');
  DBMS_OUTPUT.PUT_LINE('|---|---|');
  FOR v IN (
    SELECT v.view_name,
           NVL(tc.comments, '') AS view_comment
    FROM user_views v
    LEFT JOIN user_tab_comments tc
      ON tc.table_name = v.view_name
    WHERE v.view_name NOT LIKE 'MIG\_%' ESCAPE '\\'
    ORDER BY v.view_name
  ) LOOP
    DBMS_OUTPUT.PUT_LINE('| ' || v.view_name || ' | ' || esc(v.view_comment) || ' |');
  END LOOP;
  DBMS_OUTPUT.PUT_LINE('');

  DBMS_OUTPUT.PUT_LINE('### 5.2 实体设计');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('#### 5.2.1 数据表实体');
  DBMS_OUTPUT.PUT_LINE('');

  FOR t IN (
    SELECT t.table_name,
           NVL(tc.comments, '') AS table_comment
    FROM user_tables t
    LEFT JOIN user_tab_comments tc
      ON tc.table_name = t.table_name
    WHERE t.table_name NOT LIKE 'MIG\_%' ESCAPE '\\'
    ORDER BY t.table_name
  ) LOOP
    v_seq := v_seq + 1;
    DBMS_OUTPUT.PUT_LINE('### ' || v_seq || ') ' || t.table_name || '：' || esc(t.table_comment));
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('| 表项标识 | 字段名 | 类型 | 可空 | 说明 |');
    DBMS_OUTPUT.PUT_LINE('|---|---|---|---|---|');

    FOR c IN (
      SELECT c.column_id,
             CASE WHEN pk.column_name IS NOT NULL THEN 'P' ELSE '' END AS pk_flag,
             c.column_name,
             col_type_fmt(c.data_type, c.data_length, c.data_precision, c.data_scale) AS data_type_fmt,
             CASE c.nullable WHEN 'N' THEN '否' ELSE '是' END AS nullable_text,
             NVL(cc.comments, '') AS column_comment
      FROM user_tab_columns c
      LEFT JOIN (
        SELECT ucc.table_name,
               ucc.column_name
        FROM user_constraints uc
        JOIN user_cons_columns ucc
          ON uc.owner = ucc.owner
         AND uc.constraint_name = ucc.constraint_name
        WHERE uc.constraint_type = 'P'
      ) pk
        ON pk.table_name = c.table_name
       AND pk.column_name = c.column_name
      LEFT JOIN user_col_comments cc
        ON cc.table_name = c.table_name
       AND cc.column_name = c.column_name
      WHERE c.table_name = t.table_name
      ORDER BY c.column_id
    ) LOOP
      DBMS_OUTPUT.PUT_LINE('| ' || c.pk_flag || ' | ' || c.column_name || ' | ' || c.data_type_fmt || ' | ' || c.nullable_text || ' | ' || esc(c.column_comment) || ' |');
    END LOOP;

    SELECT COUNT(*) INTO v_idx_count
    FROM user_indexes
    WHERE table_name = t.table_name;

    SELECT COUNT(*) INTO v_trg_count
    FROM user_triggers
    WHERE table_name = t.table_name;

    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('- 索引数量：' || v_idx_count);
    DBMS_OUTPUT.PUT_LINE('- 触发器数量：' || v_trg_count);
    DBMS_OUTPUT.PUT_LINE('');
  END LOOP;

  DBMS_OUTPUT.PUT_LINE('#### 5.2.2 视图实体');
  DBMS_OUTPUT.PUT_LINE('');
  FOR v IN (
    SELECT view_name,
           text_length
    FROM user_views
    WHERE view_name NOT LIKE 'MIG\_%' ESCAPE '\\'
    ORDER BY view_name
  ) LOOP
    DBMS_OUTPUT.PUT_LINE('- ' || v.view_name || '（定义长度：' || v.text_length || '）');
  END LOOP;
  DBMS_OUTPUT.PUT_LINE('');

  DBMS_OUTPUT.PUT_LINE('## 6. 备注');
  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('- 本文档由数据库元数据自动生成。');
  DBMS_OUTPUT.PUT_LINE('- 若结构变更，请重新执行导出脚本同步更新。');
END;
/

SPOOL OFF;
EXIT;
