-- ============================================================
-- TIT16设备变更单 + TMM22_CUSTOMERS_HISTORY历史记录表
-- 创建时间：2026-04-08
-- 最终版说明：
-- 1) 可重复执行（支持已创建后补齐缺失列）
-- 2) 使用 UNISTR 写中文注释，避免客户端编码导致乱码
-- 3) 按存在性创建索引与注释，避免重复执行报错
-- ============================================================

SET SERVEROUTPUT ON;

DECLARE
    v_cnt NUMBER;

    FUNCTION col_exists(p_table_name VARCHAR2, p_col_name VARCHAR2) RETURN BOOLEAN IS
        v_col_cnt NUMBER;
    BEGIN
        SELECT COUNT(*)
          INTO v_col_cnt
          FROM USER_TAB_COLUMNS
         WHERE TABLE_NAME = UPPER(p_table_name)
           AND COLUMN_NAME = UPPER(p_col_name);
        RETURN v_col_cnt > 0;
    END;

    FUNCTION idx_exists(p_idx_name VARCHAR2) RETURN BOOLEAN IS
        v_idx_cnt NUMBER;
    BEGIN
        SELECT COUNT(*)
          INTO v_idx_cnt
          FROM USER_INDEXES
         WHERE INDEX_NAME = UPPER(p_idx_name);
        RETURN v_idx_cnt > 0;
    END;

    PROCEDURE add_comment_column(p_col_name VARCHAR2, p_comment_nvarchar VARCHAR2) IS
    BEGIN
        IF col_exists('TMM22_CUSTOMERS_HISTORY', p_col_name) THEN
            EXECUTE IMMEDIATE
                'COMMENT ON COLUMN TMM22_CUSTOMERS_HISTORY.' || p_col_name ||
                ' IS ''' || p_comment_nvarchar || '''';
        END IF;
    END;

    PROCEDURE add_comment_tit16_column(p_col_name VARCHAR2, p_comment_nvarchar VARCHAR2) IS
    BEGIN
        IF col_exists('TIT16_DEVICE_CHANGE', p_col_name) THEN
            EXECUTE IMMEDIATE
                'COMMENT ON COLUMN TIT16_DEVICE_CHANGE.' || p_col_name ||
                ' IS ''' || p_comment_nvarchar || '''';
        END IF;
    END;
BEGIN
    -- 1. 历史表不存在则创建
    SELECT COUNT(*)
      INTO v_cnt
      FROM USER_TABLES
     WHERE TABLE_NAME = 'TMM22_CUSTOMERS_HISTORY';

    IF v_cnt = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE TABLE TMM22_CUSTOMERS_HISTORY (
                HISTORY_ID       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                CUSTCD           CHAR(8)               NOT NULL,
                CUSTCARD         VARCHAR2(20)          NOT NULL,
                CUSTNM           VARCHAR2(80),
                STORE_ID         VARCHAR2(8)           NOT NULL,
                CHANGE_TYPE      VARCHAR2(8),
                CHANGE_REASON    VARCHAR2(200),
                OLD_CUSTCARD     VARCHAR2(20),
                NEW_CUSTCARD     VARCHAR2(20),
                CHANGE_TIME      DATE                  NOT NULL,
                DEVICE_CHANGE_ID VARCHAR2(8),
                OPER_CD          CHAR(6),
                USEFLG           CHAR(1) DEFAULT '1'   NOT NULL,
                CREATE_TIME      DATE DEFAULT SYSDATE  NOT NULL,
                UPDATE_TIME      DATE DEFAULT SYSDATE  NOT NULL
            )
        ]';
        DBMS_OUTPUT.PUT_LINE('已创建表: TMM22_CUSTOMERS_HISTORY');
    END IF;

    -- 2. 若早期建表不完整，则补齐缺失列
    IF NOT col_exists('TMM22_CUSTOMERS_HISTORY', 'CHANGE_REASON') THEN
        EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY ADD (CHANGE_REASON VARCHAR2(200))';
        DBMS_OUTPUT.PUT_LINE('已补齐列: CHANGE_REASON');
    END IF;

    IF NOT col_exists('TMM22_CUSTOMERS_HISTORY', 'NEW_CUSTCARD') THEN
        EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY ADD (NEW_CUSTCARD VARCHAR2(20))';
        DBMS_OUTPUT.PUT_LINE('已补齐列: NEW_CUSTCARD');
    END IF;

    IF NOT col_exists('TMM22_CUSTOMERS_HISTORY', 'CHANGE_TIME') THEN
        EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY ADD (CHANGE_TIME DATE DEFAULT SYSDATE NOT NULL)';
        DBMS_OUTPUT.PUT_LINE('已补齐列: CHANGE_TIME');
    END IF;

    -- 2.0 修复CUSTNM长度（与TMM22_CUSTOMERS口径保持一致）
    SELECT COUNT(*)
      INTO v_cnt
      FROM USER_TAB_COLUMNS
     WHERE TABLE_NAME = 'TMM22_CUSTOMERS_HISTORY'
       AND COLUMN_NAME = 'CUSTNM'
       AND DATA_TYPE = 'VARCHAR2'
       AND CHAR_COL_DECL_LENGTH < 80;

    IF v_cnt > 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY MODIFY (CUSTNM VARCHAR2(80))';
        DBMS_OUTPUT.PUT_LINE('已修复列长度: CUSTNM -> VARCHAR2(80)');
    END IF;

    -- 2.1 修复CHANGE_TYPE长度（兼容早期CHAR(2)定义）
    SELECT COUNT(*)
      INTO v_cnt
      FROM USER_TAB_COLUMNS
     WHERE TABLE_NAME = 'TMM22_CUSTOMERS_HISTORY'
       AND COLUMN_NAME = 'CHANGE_TYPE'
       AND (
            (DATA_TYPE = 'CHAR' AND CHAR_COL_DECL_LENGTH < 4)
            OR (DATA_TYPE = 'VARCHAR2' AND CHAR_COL_DECL_LENGTH < 4)
       );

    IF v_cnt > 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY MODIFY (CHANGE_TYPE VARCHAR2(8))';
        DBMS_OUTPUT.PUT_LINE('已修复列长度: CHANGE_TYPE -> VARCHAR2(8)');
    END IF;

    -- 3. 注释（中文，使用UNISTR避免乱码）
    EXECUTE IMMEDIATE 'COMMENT ON TABLE TMM22_CUSTOMERS_HISTORY IS ''' ||
        UNISTR('\95E8\5E97\5BA2\6237\5386\53F2\8BB0\5F55\8868') || '''';

    add_comment_column('HISTORY_ID',       UNISTR('\5386\53F2\8BB0\5F55ID'));
    add_comment_column('CUSTCD',           UNISTR('\5BA2\6237\4EE3\7801\FF08\95E8\5E97ID\FF09'));
    add_comment_column('CUSTCARD',         UNISTR('\78C1\5361\53F7\FF08\5F53\524D\503C\FF09'));
    add_comment_column('CUSTNM',           UNISTR('\5BA2\6237\540D\79F0'));
    add_comment_column('STORE_ID',         UNISTR('\6240\5C5E\95E8\5E97ID'));
    add_comment_column('CHANGE_TYPE',      UNISTR('\53D8\66F4\7C7B\578B\FF1ACK=\78C1\5361\53F7\53D8\66F4,BQ=\4FE1\606F\53D8\66F4,BG=\8BBE\5907\53D8\66F4,INIT=\7CFB\7EDF\521D\59CB\5316'));
    add_comment_column('CHANGE_REASON',    UNISTR('\53D8\66F4\539F\56E0'));
    add_comment_column('OLD_CUSTCARD',     UNISTR('\539F\78C1\5361\53F7\FF08\4EC5\78C1\5361\53F7\53D8\66F4\65F6\8BB0\5F55\FF09'));
    add_comment_column('NEW_CUSTCARD',     UNISTR('\65B0\78C1\5361\53F7\FF08\4EC5\78C1\5361\53F7\53D8\66F4\65F6\8BB0\5F55\FF09'));
    add_comment_column('CHANGE_TIME',      UNISTR('\53D8\66F4\65F6\95F4'));
    add_comment_column('DEVICE_CHANGE_ID', UNISTR('\5173\8054\8BBE\5907\53D8\66F4\5355ID'));
    add_comment_column('OPER_CD',          UNISTR('\64CD\4F5C\4EBA\4EE3\7801'));
    add_comment_column('USEFLG',           UNISTR('\6709\6548\6807\5FD7\FF1A1=\6709\6548,0=\65E0\6548'));
    add_comment_column('CREATE_TIME',      UNISTR('\521B\5EFA\65F6\95F4'));
    add_comment_column('UPDATE_TIME',      UNISTR('\66F4\65B0\65F6\95F4'));

    -- 4. 索引（按存在性创建）
    IF NOT idx_exists('IDX_CUST_HIST_CARD') THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IDX_CUST_HIST_CARD ON TMM22_CUSTOMERS_HISTORY(CUSTCARD)';
    END IF;

    IF NOT idx_exists('IDX_CUST_HIST_STORE') THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IDX_CUST_HIST_STORE ON TMM22_CUSTOMERS_HISTORY(STORE_ID)';
    END IF;

    IF col_exists('TMM22_CUSTOMERS_HISTORY', 'CHANGE_TIME') AND NOT idx_exists('IDX_CUST_HIST_CHANGE') THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IDX_CUST_HIST_CHANGE ON TMM22_CUSTOMERS_HISTORY(CHANGE_TYPE, CHANGE_TIME)';
    END IF;

    IF NOT idx_exists('IDX_CUST_HIST_DEVICE') THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IDX_CUST_HIST_DEVICE ON TMM22_CUSTOMERS_HISTORY(DEVICE_CHANGE_ID)';
    END IF;

    IF col_exists('TMM22_CUSTOMERS_HISTORY', 'CHANGE_TIME') AND NOT idx_exists('IDX_CUST_HIST_TIME') THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IDX_CUST_HIST_TIME ON TMM22_CUSTOMERS_HISTORY(CHANGE_TIME)';
    END IF;

    -- 5. 基线数据初始化（仅空表时执行）
    SELECT COUNT(*) INTO v_cnt FROM TMM22_CUSTOMERS_HISTORY;
    IF v_cnt = 0 THEN
        SELECT COUNT(*)
          INTO v_cnt
          FROM TMM22_CUSTOMERS
         WHERE USEFLG = '1'
           AND CUSTCARD IS NULL;

        EXECUTE IMMEDIATE q'[
            INSERT INTO TMM22_CUSTOMERS_HISTORY (
                CUSTCD, CUSTCARD, CUSTNM, STORE_ID,
                CHANGE_TYPE, CHANGE_REASON, OLD_CUSTCARD, NEW_CUSTCARD,
                CHANGE_TIME, DEVICE_CHANGE_ID, OPER_CD, USEFLG, CREATE_TIME, UPDATE_TIME
            )
            SELECT
                CUSTCD,
                CUSTCARD,
                CUSTNM,
                CUSTCD AS STORE_ID,
                'INIT' AS CHANGE_TYPE,
                'System initialization - baseline record' AS CHANGE_REASON,
                NULL AS OLD_CUSTCARD,
                CUSTCARD AS NEW_CUSTCARD,
                SYSDATE AS CHANGE_TIME,
                NULL AS DEVICE_CHANGE_ID,
                'SYSTEM' AS OPER_CD,
                '1' AS USEFLG,
                SYSDATE AS CREATE_TIME,
                SYSDATE AS UPDATE_TIME
            FROM TMM22_CUSTOMERS
            WHERE USEFLG = '1'
              AND CUSTCARD IS NOT NULL
        ]';
        DBMS_OUTPUT.PUT_LINE('已初始化历史基线数据');
        IF v_cnt > 0 THEN
            DBMS_OUTPUT.PUT_LINE('提示：因CUSTCARD为空跳过初始化记录数=' || v_cnt);
        END IF;
    END IF;

    -- 6. TIT16_DEVICE_CHANGE 注释（按列存在性）
    EXECUTE IMMEDIATE 'COMMENT ON TABLE TIT16_DEVICE_CHANGE IS ''' ||
        UNISTR('\8BBE\5907\53D8\66F4\5355\FF08\8BB0\5F55\95E8\5E97\78C1\5361\53F7/\4FE1\606F/\8BBE\5907\53D8\66F4\FF09') || '''';

    add_comment_tit16_column('DEVICE_CHANGE_ID', UNISTR('\53D8\66F4\5355ID\FF0C\4E3B\952E'));
    add_comment_tit16_column('STORE_ID',         UNISTR('\539F\95E8\5E97ID'));
    add_comment_tit16_column('CHANGE_TYPE',      UNISTR('\53D8\66F4\7C7B\578B\FF1ACK=\6539\78C1\5361\53F7,BQ=\4FE1\606F\53D8\66F4,BG=\8BBE\5907\53D8\66F4'));
    add_comment_tit16_column('NEW_STORE_CARD',   UNISTR('\53D8\66F4\540E\95E8\5E97\78C1\5361\53F7\FF08CK\7C7B\578B\7528\FF09'));
    add_comment_tit16_column('NEW_STORE_ID',     UNISTR('\53D8\66F4\540E\95E8\5E97ID\FF08\8DE8\95E8\5E97BG\7C7B\578B\7528\FF09'));
    add_comment_tit16_column('CURRENT_STATUS',   UNISTR('\5F53\524D\72B6\6001\FF08\590D\7528\7EDF\4E00\72B6\6001\673A\FF09'));

    COMMIT;
END;
/

-- 7. 验证
-- SELECT COUNT(*) FROM TMM22_CUSTOMERS_HISTORY;
-- SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = 'TMM22_CUSTOMERS_HISTORY' ORDER BY COLUMN_ID;
