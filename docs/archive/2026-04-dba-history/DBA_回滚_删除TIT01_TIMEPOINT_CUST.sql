-- 文件说明：DBA回滚脚本（删除兼容视图）
-- 目标对象：CCGL.TIT01_TIMEPOINT_CUST
-- 使用场景：验证失败或业务回退。

DROP VIEW CCGL.TIT01_TIMEPOINT_CUST;

-- 回滚后建议：确认对象已删除
SELECT object_name, object_type, status
FROM all_objects
WHERE owner = 'CCGL'
  AND object_name = 'TIT01_TIMEPOINT_CUST';
