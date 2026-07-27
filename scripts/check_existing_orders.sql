-- 检查现有订单号是否以H开头，避免冲突
SELECT 
    rgstbillid,
    LEFT(rgstbillid, 1) as first_char,
    COUNT(*) as count
FROM tpc12_register
GROUP BY LEFT(rgstbillid, 1)
ORDER BY count DESC;

-- 检查tpc01_pcplan单号分布
SELECT 
    LEFT(pcplanid, 2) as prefix,
    COUNT(*) as count
FROM tpc01_pcplan
WHERE gendate < '2026-01-01'
GROUP BY LEFT(pcplanid, 2)
ORDER BY count DESC;
