-- 文件说明：DBA验证脚本（只读）
-- 目标对象：CCGL.TIT01_TIMEPOINT_CUST
-- 用途：验证兼容视图已可访问、字段结构符合预期。

-- 1) 对象是否存在
SELECT object_name, object_type, status
FROM all_objects
WHERE owner = 'CCGL'
  AND object_name = 'TIT01_TIMEPOINT_CUST';

-- 2) 字段结构检查
SELECT column_id, column_name, data_type, data_length, nullable
FROM all_tab_columns
WHERE owner = 'CCGL'
  AND table_name = 'TIT01_TIMEPOINT_CUST'
ORDER BY column_id;

-- 3) 数据可读性检查（只读）
SELECT COUNT(*) AS total_rows
FROM CCGL.TIT01_TIMEPOINT_CUST;

SELECT *
FROM (
    SELECT custcd, timepoint, beforetm, aftertm, useflg
    FROM CCGL.TIT01_TIMEPOINT_CUST
    ORDER BY custcd
)
WHERE ROWNUM <= 20;
