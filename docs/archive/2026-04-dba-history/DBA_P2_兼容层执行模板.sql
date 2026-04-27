-- 文件说明：P2批次兼容层执行模板（正式库CCGL）
-- 用途：按对象逐条创建同义词/视图并做最小只读验证
-- 注意：请在变更窗口执行；每处理1个对象即提交日志并确认结果

SET DEFINE OFF;
SET SERVEROUTPUT ON;
SET LINESIZE 200;
SET PAGESIZE 200;

PROMPT === [0] 会话安全校验 ===
COLUMN service_name FORMAT A30;
COLUMN db_name FORMAT A20;
SELECT SYS_CONTEXT('USERENV','SERVICE_NAME') AS service_name,
       SYS_CONTEXT('USERENV','DB_NAME')      AS db_name
FROM dual;

PROMPT === [1] 对象处理模板（请逐条替换并执行） ===
-- 模板变量说明：
--   <OBJ_NAME>      缺失对象名（大写）
--   <TARGET_OWNER>  目标对象Owner（如CCGL）
--   <TARGET_NAME>   可复用目标对象名（大写）

-- 1.1 先看现状：对象/同义词是否已存在
-- SELECT owner, object_name, object_type, status
-- FROM all_objects
-- WHERE object_name = '<OBJ_NAME>'
-- ORDER BY owner;
--
-- SELECT owner, synonym_name, table_owner, table_name
-- FROM all_synonyms
-- WHERE synonym_name = '<OBJ_NAME>'
-- ORDER BY owner;

-- 1.2 路径A：存在可复用对象时，优先创建同义词（推荐）
-- CREATE OR REPLACE SYNONYM CCGL.<OBJ_NAME> FOR <TARGET_OWNER>.<TARGET_NAME>;

-- 1.3 路径B：无可复用对象时，创建兼容视图（需按业务SQL补齐）
-- CREATE OR REPLACE VIEW CCGL.<OBJ_NAME> AS
-- SELECT ...
-- FROM ...
-- WHERE ...;

-- 1.4 最小验证（只读）
-- SELECT object_name, object_type, status
-- FROM all_objects
-- WHERE owner = 'CCGL'
--   AND object_name = '<OBJ_NAME>';
--
-- SELECT COUNT(*) AS total_rows
-- FROM CCGL.<OBJ_NAME>;

PROMPT === [2] 建议执行顺序（与批次清单一致） ===
PROMPT P2-A: TAC01_ACRECEIVE, TAC11_PAYDAYS, TAC12_CREDLIMIT, TAC13_CREDLIMITDT, TIP05_CUSTDISCOUNT, TIP07_COSTPRICTRACK, TIP08_MONTHCOST
PROMPT P2-B: TSL05_SLPROMPLAN, TSL11_REGISTER, TSL11_SLBILLITEM, TSL15_PICKBILL, TSL16_PICKBILLDT, TSL20_INVOICE
PROMPT P2-C: TPC01_PCPROMPLAN, TPS01_PIPELINE, TWH03_ROUTE, TWH22_ARRTOROUTEDT, TIV30_SHOPCHECKPLAN, TIV33_OVBILL
PROMPT P2-D: TMM13_ITEMUNIT, TMM14_ITEMBAR, TMM15_ITEMTAXRATE, TMM23_ADDRESS, U_BUTTONS_V

PROMPT === [3] 回滚模板（按对象） ===
-- DROP VIEW CCGL.<OBJ_NAME>;
-- DROP SYNONYM CCGL.<OBJ_NAME>;

PROMPT === 完成：请将每个对象执行结果回写到治理字典 ===
