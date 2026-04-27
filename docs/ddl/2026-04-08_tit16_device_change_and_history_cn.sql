-- ============================================================
-- TIT16 设备变更单 + TMM22_CUSTOMERS_HISTORY 历史表（中文注释最终执行版）
-- 创建时间：2026-04-08
-- 适用场景：
-- 1) 已有 TIT16_DEVICE_CHANGE，仅需补齐历史表与注释
-- 2) 历史表已存在但字段不完整，自动补齐
-- 3) 中文注释使用 UNISTR，避免客户端编码导致乱码
-- ============================================================

SET DEFINE OFF;
SET SERVEROUTPUT ON;

DECLARE
    v_cnt NUMBER;

    FUNCTION table_exists(p_table_name VARCHAR2) RETURN BOOLEAN IS
        v_table_cnt NUMBER;
    BEGIN
        SELECT COUNT(*)
          INTO v_table_cnt
          FROM USER_TABLES
         WHERE TABLE_NAME = UPPER(p_table_name);
        RETURN v_table_cnt > 0;
    END;

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

    PROCEDURE cmt_hist_col(p_col_name VARCHAR2, p_comment VARCHAR2) IS
    BEGIN
        IF col_exists('TMM22_CUSTOMERS_HISTORY', p_col_name) THEN
            EXECUTE IMMEDIATE
                'COMMENT ON COLUMN TMM22_CUSTOMERS_HISTORY.' || p_col_name ||
                ' IS ''' || p_comment || '''';
        END IF;
    END;

    PROCEDURE cmt_tit16_col(p_col_name VARCHAR2, p_comment VARCHAR2) IS
    BEGIN
        IF col_exists('TIT16_DEVICE_CHANGE', p_col_name) THEN
            EXECUTE IMMEDIATE
                'COMMENT ON COLUMN TIT16_DEVICE_CHANGE.' || p_col_name ||
                ' IS ''' || p_comment || '''';
        END IF;
    END;
BEGIN
    -- 1) 历史表不存在则创建（字段以当前确认版本为准）
    IF NOT table_exists('TMM22_CUSTOMERS_HISTORY') THEN
        EXECUTE IMMEDIATE q'[
            CREATE TABLE TMM22_CUSTOMERS_HISTORY (
                HISTORY_ID       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                CUSTCD           CHAR(8)               NOT NULL,
                CUSTCARD         VARCHAR2(20)          NOT NULL,
                CUSTNM           VARCHAR2(80),
                STORE_ID         VARCHAR2(8)           NOT NULL,
                CHANGE_TYPE      VARCHAR2(8),
                OLD_CUSTCARD     VARCHAR2(20),
                DEVICE_CHANGE_ID VARCHAR2(8),
                OPER_CD          CHAR(6),
                USEFLG           CHAR(1) DEFAULT '1'   NOT NULL,
                CREATE_TIME      DATE DEFAULT SYSDATE  NOT NULL,
                UPDATE_TIME      DATE DEFAULT SYSDATE  NOT NULL,
                CHANGE_REASON    VARCHAR2(200),
                NEW_CUSTCARD     VARCHAR2(20),
                CHANGE_TIME      DATE DEFAULT SYSDATE  NOT NULL
            )
        ]';
        DBMS_OUTPUT.PUT_LINE('已创建表：TMM22_CUSTOMERS_HISTORY');
    END IF;

    -- 2) 历史表补齐缺失字段（兼容早期错误执行）
    IF NOT col_exists('TMM22_CUSTOMERS_HISTORY', 'CHANGE_REASON') THEN
        EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY ADD (CHANGE_REASON VARCHAR2(200))';
        DBMS_OUTPUT.PUT_LINE('已补齐列：CHANGE_REASON');
    END IF;

    IF NOT col_exists('TMM22_CUSTOMERS_HISTORY', 'NEW_CUSTCARD') THEN
        EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY ADD (NEW_CUSTCARD VARCHAR2(20))';
        DBMS_OUTPUT.PUT_LINE('已补齐列：NEW_CUSTCARD');
    END IF;

    IF NOT col_exists('TMM22_CUSTOMERS_HISTORY', 'CHANGE_TIME') THEN
        EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY ADD (CHANGE_TIME DATE DEFAULT SYSDATE NOT NULL)';
        DBMS_OUTPUT.PUT_LINE('已补齐列：CHANGE_TIME');
    END IF;

    IF col_exists('TMM22_CUSTOMERS_HISTORY', 'CUSTNM') THEN
        SELECT COUNT(*) INTO v_cnt
        FROM USER_TAB_COLUMNS
        WHERE TABLE_NAME = 'TMM22_CUSTOMERS_HISTORY'
          AND COLUMN_NAME = 'CUSTNM'
          AND DATA_TYPE = 'VARCHAR2'
          AND CHAR_COL_DECL_LENGTH < 80;
        IF v_cnt > 0 THEN
            EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY MODIFY (CUSTNM VARCHAR2(80))';
            DBMS_OUTPUT.PUT_LINE('已修复列长度：CUSTNM -> VARCHAR2(80)');
        END IF;
    END IF;

    IF col_exists('TMM22_CUSTOMERS_HISTORY', 'CHANGE_TYPE') THEN
        SELECT COUNT(*) INTO v_cnt
        FROM USER_TAB_COLUMNS
        WHERE TABLE_NAME = 'TMM22_CUSTOMERS_HISTORY'
          AND COLUMN_NAME = 'CHANGE_TYPE'
          AND ((DATA_TYPE = 'CHAR' AND CHAR_COL_DECL_LENGTH < 8)
               OR (DATA_TYPE = 'VARCHAR2' AND CHAR_COL_DECL_LENGTH < 8));
        IF v_cnt > 0 THEN
            EXECUTE IMMEDIATE 'ALTER TABLE TMM22_CUSTOMERS_HISTORY MODIFY (CHANGE_TYPE VARCHAR2(8))';
            DBMS_OUTPUT.PUT_LINE('已修复列长度：CHANGE_TYPE -> VARCHAR2(8)');
        END IF;
    END IF;

    -- 3) 历史表索引（按存在性创建）
    IF NOT idx_exists('IDX_CUST_HIST_CARD') THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IDX_CUST_HIST_CARD ON TMM22_CUSTOMERS_HISTORY(CUSTCARD)';
    END IF;

    IF NOT idx_exists('IDX_CUST_HIST_DEVICE') THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IDX_CUST_HIST_DEVICE ON TMM22_CUSTOMERS_HISTORY(DEVICE_CHANGE_ID)';
    END IF;

    IF NOT idx_exists('IDX_CUST_HIST_STORE') THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IDX_CUST_HIST_STORE ON TMM22_CUSTOMERS_HISTORY(STORE_ID)';
    END IF;

    -- 4) TIT16 表注释（按列存在性）
    IF table_exists('TIT16_DEVICE_CHANGE') THEN
        EXECUTE IMMEDIATE 'COMMENT ON TABLE TIT16_DEVICE_CHANGE IS ''' ||
            UNISTR('\8BBE\5907\53D8\66F4\5355 - \8BB0\5F55\95E8\5E97\78C1\5361\53F7/\4FE1\606F/\8BBE\5907\53D8\66F4') || '''';

        cmt_tit16_col('DEVICE_CHANGE_ID',        UNISTR('\53D8\66F4\5355ID\FF0C\4E3B\952E'));
        cmt_tit16_col('STORE_ID',                UNISTR('\539F\95E8\5E97ID'));
        cmt_tit16_col('REQUSET_PAPER_ID',        UNISTR('\53D8\66F4\8BF7\6C42\5355ID'));
        cmt_tit16_col('CHANGE_TYPE',             UNISTR('\53D8\66F4\7C7B\578B\FF1ACK=\6539\78C1\5361\53F7, BQ=\4FE1\606F\53D8\66F4, BG=\8BBE\5907\53D8\66F4'));
        cmt_tit16_col('DEVICE_ID',               UNISTR('\6574\673AID'));
        cmt_tit16_col('NEW_CONTACTOR',           UNISTR('\53D8\66F4\8054\7CFB\4EBA'));
        cmt_tit16_col('NEW_TEL',                 UNISTR('\53D8\66F4\7535\8BDD'));
        cmt_tit16_col('NEW_ADDRESS',             UNISTR('\53D8\66F4\540E\5730\5740'));
        cmt_tit16_col('NEW_STORE_CARD',          UNISTR('\53D8\66F4\540E\95E8\5E97\78C1\5361\53F7\FF08CK\7C7B\578B\7528\FF09'));
        cmt_tit16_col('NEW_STORE_ID',            UNISTR('\53D8\66F4\540E\95E8\5E97ID\FF08\8DE8\95E8\5E97BG\7C7B\578B\7528\FF09'));
        cmt_tit16_col('IS_STORE_INSIDE_CHANGE',  UNISTR('\662F\5426\5E97\5185\79FB\673A'));
        cmt_tit16_col('REQUEST_TIME',            UNISTR('\8BF7\6C42\65F6\95F4'));
        cmt_tit16_col('EXPECTED_COMPLETION_TIME',UNISTR('\5408\540C\8981\6C42\5B8C\6210\65F6\95F4'));
        cmt_tit16_col('SHORT_DESCRIPTION',       UNISTR('\7B80\8FF0'));
        cmt_tit16_col('DETAIL_DESCRIPTION',      UNISTR('\8BE6\7EC6\63CF\8FF0'));
        cmt_tit16_col('CURRENT_STATUS',          UNISTR('\5F53\524D\72B6\6001\FF08\590D\7528\7EDF\4E00\72B6\6001\673A\FF09'));
        cmt_tit16_col('IS_SUCCESS',              UNISTR('\6210\529F\6807\5FD7'));
        cmt_tit16_col('IS_OLD',                  UNISTR('\662F\5426\8865\5355'));
        cmt_tit16_col('CREATE_TIME',             UNISTR('\521B\5EFA\65F6\95F4'));
        cmt_tit16_col('CREATOR',                 UNISTR('\521B\5EFA\4EBA'));
        cmt_tit16_col('UPDATE_TIME',             UNISTR('\66F4\65B0\65F6\95F4'));
        cmt_tit16_col('UPDATOR',                 UNISTR('\66F4\65B0\4EBA'));
        cmt_tit16_col('FIRSTOR',                 UNISTR('\7B2C\4E00\6B21\4E0A\95E8\5DE5\7A0B\5E08ID'));
        cmt_tit16_col('FIRST_TIME',              UNISTR('\7B2C\4E00\6B21\4E0A\95E8\65F6\95F4'));
        cmt_tit16_col('LEAVE_TIME',              UNISTR('\7B2C\4E00\6B21\79BB\5E97\65F6\95F4'));
        cmt_tit16_col('CLOSE_TIME',              UNISTR('\5173\5355\65F6\95F4'));
        cmt_tit16_col('REVISIT_TIME',            UNISTR('\56DE\8BBF\65F6\95F4'));
    END IF;

    -- 5) 历史表注释（中文）
    EXECUTE IMMEDIATE 'COMMENT ON TABLE TMM22_CUSTOMERS_HISTORY IS ''' ||
        UNISTR('\95E8\5E97\5BA2\6237\5386\53F2\8BB0\5F55\8868') || '''';

    cmt_hist_col('HISTORY_ID',       UNISTR('\5386\53F2\8BB0\5F55ID'));
    cmt_hist_col('CUSTCD',           UNISTR('\5BA2\6237\4EE3\7801'));
    cmt_hist_col('CUSTCARD',         UNISTR('\78C1\5361\53F7'));
    cmt_hist_col('CUSTNM',           UNISTR('\5BA2\6237\540D\79F0'));
    cmt_hist_col('STORE_ID',         UNISTR('\95E8\5E97ID'));
    cmt_hist_col('CHANGE_TYPE',      UNISTR('\53D8\66F4\7C7B\578B:CK=\78C1\5361\53F7,BQ=\4FE1\606F,BG=\8BBE\5907,INIT=\521D\59CB\5316'));
    cmt_hist_col('OLD_CUSTCARD',     UNISTR('\539F\78C1\5361\53F7\FF08\4EC5\78C1\5361\53F7\53D8\66F4\65F6\8BB0\5F55\FF09'));
    cmt_hist_col('DEVICE_CHANGE_ID', UNISTR('\5173\8054\8BBE\5907\53D8\66F4\5355ID'));
    cmt_hist_col('OPER_CD',          UNISTR('\64CD\4F5C\4EBA\4EE3\7801'));
    cmt_hist_col('USEFLG',           UNISTR('\6709\6548\6807\5FD7:1=\6709\6548,0=\65E0\6548'));
    cmt_hist_col('CREATE_TIME',      UNISTR('\521B\5EFA\65F6\95F4'));
    cmt_hist_col('UPDATE_TIME',      UNISTR('\66F4\65B0\65F6\95F4'));
    cmt_hist_col('CHANGE_REASON',    UNISTR('\53D8\66F4\539F\56E0'));
    cmt_hist_col('NEW_CUSTCARD',     UNISTR('\65B0\78C1\5361\53F7\FF08\4EC5\78C1\5361\53F7\53D8\66F4\65F6\8BB0\5F55\FF09'));
    cmt_hist_col('CHANGE_TIME',      UNISTR('\53D8\66F4\65F6\95F4'));

    -- 6) 基线初始化：仅空表执行一次
    SELECT COUNT(*) INTO v_cnt FROM TMM22_CUSTOMERS_HISTORY;
    IF v_cnt = 0 THEN
        SELECT COUNT(*) INTO v_cnt
        FROM TMM22_CUSTOMERS
        WHERE USEFLG = '1'
          AND CUSTCARD IS NULL;

        EXECUTE IMMEDIATE q'[
            INSERT INTO TMM22_CUSTOMERS_HISTORY (
                CUSTCD, CUSTCARD, CUSTNM, STORE_ID,
                CHANGE_TYPE, OLD_CUSTCARD, DEVICE_CHANGE_ID, OPER_CD,
                USEFLG, CREATE_TIME, UPDATE_TIME, CHANGE_REASON,
                NEW_CUSTCARD, CHANGE_TIME
            )
            SELECT
                CUSTCD,
                CUSTCARD,
                CUSTNM,
                CUSTCD AS STORE_ID,
                'INIT' AS CHANGE_TYPE,
                NULL AS OLD_CUSTCARD,
                NULL AS DEVICE_CHANGE_ID,
                'SYSTEM' AS OPER_CD,
                '1' AS USEFLG,
                SYSDATE AS CREATE_TIME,
                SYSDATE AS UPDATE_TIME,
                'System initialization - baseline record' AS CHANGE_REASON,
                CUSTCARD AS NEW_CUSTCARD,
                SYSDATE AS CHANGE_TIME
            FROM TMM22_CUSTOMERS
            WHERE USEFLG = '1'
              AND CUSTCARD IS NOT NULL
        ]';
        DBMS_OUTPUT.PUT_LINE('已初始化 TMM22_CUSTOMERS_HISTORY 基线数据');
        IF v_cnt > 0 THEN
            DBMS_OUTPUT.PUT_LINE('提示：因 CUSTCARD 为空被跳过的记录数=' || v_cnt);
        END IF;
    ELSE
        DBMS_OUTPUT.PUT_LINE('历史表已有数据，跳过初始化');
    END IF;

    COMMIT;
END;
/

-- 验证SQL（按需执行）
-- SELECT COUNT(*) FROM TMM22_CUSTOMERS_HISTORY;
-- SELECT COLUMN_ID, COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME='TMM22_CUSTOMERS_HISTORY' ORDER BY COLUMN_ID;
-- SELECT COLUMN_NAME, COMMENTS FROM USER_COL_COMMENTS WHERE TABLE_NAME='TMM22_CUSTOMERS_HISTORY' ORDER BY COLUMN_NAME;
-- SELECT COLUMN_NAME, COMMENTS FROM USER_COL_COMMENTS WHERE TABLE_NAME='TIT16_DEVICE_CHANGE' ORDER BY COLUMN_NAME;
