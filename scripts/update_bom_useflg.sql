-- BOM 在产状态批量更新
-- 在产白名单: 4Q4LR4, 4Q4LR6, 4Q4LRA, 4Q4010, 4Q4011, 4Q4006, 4Q4007, HS0101, PC0101, TS01
-- 其余全部设为停产(useflg=0)

BEGIN;

-- 1. 全部设为停产
UPDATE tmm41_bom SET useflg = '0', upddate = CURRENT_TIMESTAMP;

-- 2. 白名单设为在产
UPDATE tmm41_bom SET useflg = '1', upddate = CURRENT_TIMESTAMP
WHERE bomcd IN (
  '4Q4LR4',
  '4Q4LR6',
  '4Q4LRA',
  '4Q4010',
  '4Q4011',
  '4Q4006',
  '4Q4007',
  'HS0101',
  'PC0101',
  'TS01'
);

-- 3. 验证
SELECT bomcd, useflg FROM tmm41_bom WHERE useflg = '1' ORDER BY bomcd;

COMMIT;
