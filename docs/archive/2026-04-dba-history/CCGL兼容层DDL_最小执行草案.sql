-- 文件用途：CCGL最小兼容DDL草案（仅评审/由DBA执行）
-- 目标：修复P1缺失对象 TIT01_TIMEPOINT_CUST 对历史函数的兼容
-- 风险：低（仅新增视图，不修改业务表）

-- 1) 执行DDL
CREATE OR REPLACE VIEW CCGL.TIT01_TIMEPOINT_CUST AS
SELECT c.custcd, a.timepoint, a.beforetm, a.aftertm, a.useflg
  FROM CCGL.TMM22_CUSTOMERS c
  JOIN CCGL.TIT01_TIMEPOINT_AREA a
    ON a.area = c.area
   AND a.location = c.location
 WHERE c.useflg = '1'
   AND a.useflg = '1';

-- 2) 验证SQL（只读）
SELECT COUNT(*) FROM CCGL.TIT01_TIMEPOINT_CUST WHERE ROWNUM <= 1;

-- 3) 回滚SQL
DROP VIEW CCGL.TIT01_TIMEPOINT_CUST;