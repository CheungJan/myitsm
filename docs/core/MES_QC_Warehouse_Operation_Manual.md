---
类型: 操作手册
阅读状态: 已完成
tags: 操作手册, MES, QC, 仓库, 使用指南
更新日期: 2026-06-07
创建时间: 2026-06-07
---

# MES/QC/仓库联动系统操作手册

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | MES/QC/仓库联动系统操作手册 |
| 版本 | v1.0 |
| 适用角色 | 生产管理员、质检员、仓库管理员 |
| 系统版本 | myitsm |

---

## 目录

1. [快速入门](#1-快速入门)
2. [生产工单管理](#2-生产工单管理)
3. [质检流程](#3-质检流程)
4. [仓库出入库](#4-仓库出入库)
5. [库存查询与预警](#5-库存查询与预警)
6. [常见问题](#6-常见问题)

---

## 1. 快速入门

### 1.1 系统登录

1. 打开浏览器访问系统地址
2. 输入用户名和密码
3. 进入系统主界面

### 1.2 主界面导航

```
┌─────────────────────────────────────────────────────────┐
│  系统菜单                                                │
├─────────────────────────────────────────────────────────┤
│  📦 仓库管理                                              │
│     ├─ 入库管理                                          │
│     ├─ 出库管理                                          │
│     ├─ 库存查询      ← 查看实时库存和预警                 │
│     └─ 仓库报表                                          │
│  🔧 生产管理 (MES)                                        │
│     └─ 生产工单      ← 创建和管理生产任务                 │
│  ✓  质检管理 (QC)                                         │
│     └─ 质检结果      ← 质检审核和联动                     │
│  📊 报表中心                                              │
│     └─ 库存快照      ← 查看预警物料                       │
└─────────────────────────────────────────────────────────┘
```

### 1.3 操作流程总览

```
标准生产流程:
生产工单创建 → 下达 → 生产 → 完工 → 自动生成生产出库 → 质检 → 自动入库

关键联动点:
├─ 工单完工时: 自动生成 OV=8 生产出库草稿
├─ 生产出库审核: 自动扣库存 + 生成 IV=8 入库草稿
├─ QC C1合格审核: 自动激活标签 + 自动入库
└─ QC YH/PJ/C2审核: 自动生成报废/返修出库
```

---

## 2. 生产工单管理

### 2.1 创建工单

**路径**: 生产管理 → 生产工单

**操作步骤**:

1. 点击【新建】按钮
2. 填写工单信息:
   - **产品编码**: 选择要生产的产品（从BOM分类树选择）
   - **计划数量**: 输入生产数量
   - **工单类型**: 选择"新机生产"或"旧机翻新"
   - **目标仓库**: 选择完工入库仓库（可选）
   - **计划日期**: 设置计划开始和完成日期
3. 点击【创建】

**注意事项**:
- 工单编号自动生成格式: `WOYYYYMMDD-NNN`
- 草稿状态的工单可以删除，其他状态不可删除
- 产品编码必须选择最底层物料（不能在分类节点）

### 2.2 工单状态流转

```
状态流转图:

草稿(DRAFT)
    │
    ▼ 点击【下达】
已下达(RELEASED)
    │
    ▼ 点击【开始生产】
生产中(IN_PROGRESS)
    │
    ▼ 点击【完工】
已完工(COMPLETED) → 自动生成生产出库草稿
    │
    ▼ (或) 点击【取消】
已取消(CANCELLED)
```

**操作说明**:

| 当前状态 | 可操作 | 说明 |
|----------|--------|------|
| 草稿 | 下达、删除 | 可删除草稿工单 |
| 已下达 | 开始生产、取消 | 生产准备阶段 |
| 生产中 | 完工、取消 | 正在生产 |
| 已完工 | - | 终态，不可操作 |
| 已取消 | - | 终态，不可操作 |

**重要提示**:
- 完工时会自动生成 OV=8 生产出库草稿（如果该工单尚未有出库单）
- 取消操作不可逆，请谨慎使用

### 2.3 添加工序

**路径**: 生产工单详情 → 工序列表

**操作步骤**:
1. 在工单列表点击工单编号查看详情
2. 点击【添加工序】
3. 选择工序编码和序号
4. 保存

**工序状态**:
- **PENDING**: 待执行，可删除
- **IN_PROGRESS**: 执行中
- **COMPLETED**: 已完成
- **SKIPPED**: 已跳过

### 2.4 记录物料消耗

**路径**: 生产工单详情 → 物料消耗

**操作步骤**:
1. 在工单详情页查看"物料消耗"区域
2. 系统自动从 OV=8 生产出库审核时写入
3. 也可手动添加实际消耗记录

---

## 3. 质检流程

### 3.1 创建质检单

**来源方式**:
1. **从入库单创建**: 仓库 → 入库单 → 生成质检单
2. **手动创建**: 质检管理 → 新建

**操作步骤**:
1. 选择质检类型:
   - **C1**: 成品合格（自动贴标+入库）
   - **YH**: 易耗品报废（自动报废出库）
   - **PJ**: 配件（坏件返修）
   - **C2**: 成品降级（坏件返修）
2. 选择来源入库单
3. 扫描或输入设备序列号(EID)
4. 填写质检数量和结果
5. 保存

### 3.2 质检审核（关键联动）

**路径**: 质检管理 → 质检结果 → 审核

**审核前检查清单**:
- [ ] 质检单状态为"未审核"
- [ ] 已录入所有EID设备
- [ ] 质检数量与实物一致

**审核后自动触发**:

| 质检类型 | 自动执行 | 结果查看 |
|----------|----------|----------|
| **C1 合格** | 1. EID标记为"GA合格"<br>2. 自动激活标签<br>3. 自动生成生产入库单(IV=8) | 查看入库单列表 |
| **YH 报废** | 1. EID标记为"BF报废"<br>2. 自动生成报废出库单(OV=7) | 查看出库单列表，类型=7 |
| **PJ/C2 配件/降级** | 1. EID标记为"DJ待检"<br>2. 坏件(BH)自动生成返修出库(OV=9) | 查看出库单列表，类型=9 |

**操作步骤**:
1. 在质检结果列表找到要审核的单据
2. 点击【审核】按钮
3. 确认提示信息
4. 系统自动执行联动操作

**注意事项**:
- **审核后不可撤销**（业务数据已变动）
- C1审核时自动贴标，请确保标签已打印
- 坏件返修出库会自动筛选 qcflg='BH' 的设备

### 3.3 查看质检联动结果

**验证C1自动入库**:
1. 质检审核完成后
2. 进入【仓库管理 → 入库管理】
3. 查看类型为"生产入库(IV=8)"的新单据
4. 单据 refbillid 关联质检单号

**验证YH自动报废**:
1. 进入【仓库管理 → 出库管理】
2. 查看类型为"报废出库(OV=7)"的新单据
3. EID状态变为"BF报废"

---

## 4. 仓库出入库

### 4.1 入库管理

**路径**: 仓库管理 → 入库管理

**入库类型说明**:

| 类型 | 代码 | 来源 | 操作说明 |
|------|------|------|----------|
| 采购入库 | IV=1 | 采购订单 | 选择采购订单 → 确认到货 → 审核 |
| 销售退货 | IV=2 | 销售出库 | 关联销售出库单退货 |
| 生产入库 | IV=8 | QC C1合格 | **自动生成**，直接审核即可 |
| 返修入库 | IV=9 | 返修出库 | 关联返修出库单 |
| 调拨入库 | IV=4 | 调拨出库 | 关联调拨出库单 |

**标准入库流程**:
1. 创建入库单（或系统自动生成）
2. 填写入库明细（物料编码、数量、EID等）
3. 保存草稿
4. 审核入库单
5. 系统更新库存

**审核自动生成逻辑**:
- 审核 OV=3 调拨出库 → 自动生成 IV=4 调拨入库（目标仓）
- 审核 OV=9 返修出库 → 自动生成 IV=9 返修入库草稿
- 审核 OV=1 销售出库 → 自动生成 IV=2 销售退货草稿（同仓库）

### 4.2 出库管理

**路径**: 仓库管理 → 出库管理

**出库类型说明**:

| 类型 | 代码 | 用途 | 操作说明 |
|------|------|------|----------|
| 生产出库 | OV=8 | 工单领料 | 关联生产工单 |
| 返修出库 | OV=9 | 坏件返修 | **QC自动生成** |
| 报废出库 | OV=7 | 质检报废 | **QC自动生成** |
| 销售出库 | OV=1 | 销售发货 | 关联销售订单 |
| 调拨出库 | OV=3 | 仓库调拨 | 选择目标仓库 |
| 借出出库 | OV=4 | 借给客户 | 关联客户 |

**重要出库流程**:

**生产出库 (OV=8)**:
1. 系统自动生成（工单完工时）或手动创建
2. 选择工单编号
3. 系统自动带出BOM物料
4. 审核后扣减库存
5. 自动生成 IV=8 入库草稿（供返修/完工使用）

**返修出库 (OV=9)**:
1. QC PJ/C2审核时自动生成
2. 单据明细仅包含坏件(BH)设备
3. 审核后设备状态变为"返修中"
4. 自动生成 IV=9 返修入库草稿

### 4.3 单据审核

**审核前检查**:
- [ ] 单据状态为"草稿"或"未审核"
- [ ] 明细数量正确
- [ ] 仓库选择正确
- [ ] EID设备匹配

**审核操作**:
1. 在单据列表点击【审核】
2. 选择审核结果（通过/退回）
3. 填写审核备注（可选）
4. 提交审核

**审核后状态**:
- **通过**: auditflg='2'，库存变动，自动生成关联单据
- **退回**: auditflg='0'，可重新编辑

---

## 5. 库存查询与预警

### 5.1 库存查询

**路径**: 仓库管理 → 库存查询

**功能说明**:

| 功能 | 操作 | 说明 |
|------|------|------|
| **搜索物料** | 输入编码/名称 | 模糊搜索 |
| **筛选仓库** | 选择仓库 | 只看指定仓库 |
| **仅看预警** | 勾选复选框 | 只显示低于下限的物料 |
| **导出数据** | 点击导出 | CSV格式下载 |

**预警显示**:
- **红色高亮**: 库存低于下限
- **橙色高亮**: 库存超上限
- **绿色标签**: 库存正常
- **红色标签**: "低于下限"
- **橙色标签**: "超上限"
- **绿色标签**: "正常"

**查看示例**:
```
┌──────────┬──────────┬──────┬────────┬────────┬────────┬────────┐
│ 物料编码  │ 物料名称  │ 仓库  │ 库存数量│ 库存上限│ 库存下限│ 状态   │
├──────────┼──────────┼──────┼────────┼────────┼────────┼────────┤
│ IT0001   │ 主机板   │ 主仓库│   5    │   100  │   10   │ 低于下限│ ← 红色
│ IT0002   │ 显示屏   │ 主仓库│  150   │   100  │   20   │ 超上限  │ ← 橙色
│ IT0003   │ 电源线   │ 主仓库│   50   │   100  │   10   │ 正常   │ ← 绿色
└──────────┴──────────┴──────┴────────┴────────┴────────┴────────┘
```

### 5.2 库存预警看板

**路径**: 报表中心 → 库存预警

**显示内容**:
- 低于下限的物料数量（红色大数字）
- 预警物料清单
- 短缺数量计算

**预警计算**:
```
短缺数量 = 库存下限 - 当前库存
```

**响应流程**:
1. 查看预警看板
2. 点击数字查看详情
3. 创建采购计划或调拨单
4. 跟进到货

---

## 6. 常见问题

### Q1: 工单完工后没有自动生成生产出库？

**可能原因**:
- 该工单已有 OV=8 或 OV=10 出库单（系统去重）
- 工单未选择产品编码
- BOM展开无物料明细

**解决方法**:
1. 检查出库单列表是否已有该工单关联的单据
2. 手动创建 OV=8 生产出库单

### Q2: QC审核后没有看到自动入库单？

**排查步骤**:
1. 确认质检类型是 **C1**（只有C1才自动入库）
2. 检查入库单列表，筛选类型"生产入库"
3. 查看 refbillid 是否关联质检单号
4. 检查系统日志是否有错误

### Q3: 标签没有自动激活？

**可能原因**:
- Item.class_cd 为空（标签匹配需要中类编码）
- TMM40_LABEL 表没有对应 (eid, classcd) 的记录
- 标签已经是 useflg='0' 状态

**解决方法**:
1. 检查物料主数据是否有中类编码
2. 在标签管理页面手动激活
3. 联系管理员检查标签数据

### Q4: 坏件返修出库没有生成？

**排查步骤**:
1. 确认质检类型是 **PJ** 或 **C2**
2. 确认EID审核前的 qcflg='BH'（坏件）
3. 检查出库单列表，筛选类型"返修出库"

**注意**: 只有 BH 状态的EID才会触发 OV=9 生成

### Q5: 入库审核后没有看到关联出库单？

**正常情况**:
- 只有 **出库审核** 才会生成关联入库
- 入库审核不会反向生成出库

**出库→入库联动规则**:
- OV=3 → 自动生成 IV=4
- OV=9 → 自动生成 IV=9
- OV=1 → 自动生成 IV=2

### Q6: 库存预警数据不准确？

**检查项**:
1. 物料主数据是否维护 upperlimit/lowerlimit
2. 库存流水 TWH12 是否及时更新
3. 有未审核单据影响库存

**刷新库存**:
- 进入库存查询页面重新加载
- 检查是否有未审核的出入库单

---

## 附录

### A. 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+F | 页面内搜索 |
| F5 | 刷新当前页面 |
| Esc | 关闭弹窗 |

### B. 状态码速查

**工单状态**:
- 草稿 → 下达 → 生产中 → 完工/取消

**EID状态**:
- 在库(sflg=1) → 生产/翻新(sflg=7) → 合格(sflg=1) / 返修(sflg=5) / 报废(sflg=2)

**质检标志**:
- 合格(GA) / 待检(DJ) / 报废(BF) / 坏件(BH)

### C. 联系方式

- 系统管理员: admin@company.com
- 技术支持: support@company.com

---

---

## 12. 最新操作验收（2026-06-07 新增）

### 12.1 工单/工序删除

| 操作 | 预期 |
|------|------|
| 工单列表→DRAFT行→点"删除" | 确认后删除成功 |
| 工单工序→PENDING行→点"删除" | 确认后删除成功 |
| 非DRAFT工单/非PENDING工序 | 无删除按钮 |

### 12.2 库存预警

| 操作 | 预期 |
|------|------|
| 库存查询→勾选"仅看预警" | 只显示低于下限物料(红色高亮) |
| 低于下限行 | 状态列"低于下限"红色标签 |

### 12.3 报表导出

| Tab | 操作 | 预期 |
|-----|------|------|
| 收发存汇总/库存日报/库龄分析 | 点击"导出CSV" | 下载 .xlsx 文件 |

### 12.4 标签自动生成

| 操作 | 预期 |
|------|------|
| 标签管理→批量录入→"自动生成(PB规则)" | 填classcd+数量→生成 |
| 耗材(typflg=0) | classcd+YY+月后缀+4位序号 |
| 固定资产(typflg=1) | YYYYMMDD+sign+4位序号 |

### 12.5 QC C1 自动贴标验证

```sql
-- 验证标签激活
SELECT labelid, useflg, gendate, upddate FROM tmm40_label WHERE labelid = '<EID>';
-- 验证IV=6溯源
SELECT eid, itemcd, ref_eid FROM tmm43_eid WHERE ref_eid IS NOT NULL;
```

文档结束

### 附录B：数据链路验证SQL

```sql
-- ============================================
-- 出入库数据链路检查（替换占位符后执行）
-- ============================================

-- 1. 出库单
SELECT outbillid, invtyp, whcd, auditflg, refbillid, outdate, gendate
FROM twh15_out WHERE outbillid = '<出库单号>';

-- 2. 关联入库单
SELECT inbillid, invtyp, auditflg, refbillid, whcd, indate
FROM twh13_in WHERE refbillid = '<出库单号>';

-- 3. 出库明细（EID+批次逐行对比）
SELECT '出库EID' as 方向, lineno, itemcd, eid, outqty FROM twh16_outdteid WHERE outbillid = '<出库单号>'
UNION ALL SELECT '出库批次', lineno, itemcd, '', outqty FROM twh16_outdtprd WHERE outbillid = '<出库单号>'
ORDER BY 方向 DESC, lineno;

-- 4. 入库明细（按reflineno对照出库行号）
SELECT itemcd, inqty, eid, reflineno, itemtyp, to_char(prddate,'YYYY-MM-DD') as prddate
FROM twh14_checkindt WHERE inbillid = '<入库单号>';

-- 5. EID状态（出库单中的EID）
SELECT eid, itemcd, sflg, qcflg, whcd FROM tmm43_eid
WHERE eid IN (SELECT eid FROM twh16_outdteid WHERE outbillid = '<出库单号>');

-- 6. TWH12 流水
SELECT billid, iotyp, itemcd, itemqty, storeqty
FROM twh12_detaildt WHERE billid IN ('<出库单号>', '<入库单号>')
ORDER BY billid, gendate;

-- 7. TWH11 余额
SELECT itemcd, itemtyp, to_char(prddate,'YYYY-MM-DD') as prddate, itemqty
FROM twh11_detail WHERE whcd = '<仓库>' AND itemcd IN (
    SELECT itemcd FROM twh16_outdteid WHERE outbillid = '<出库单号>'
    UNION SELECT itemcd FROM twh16_outdtprd WHERE outbillid = '<出库单号>'
) ORDER BY itemcd, itemtyp;

-- 8. QC审核验证
SELECT eid, sflg, qcflg FROM tmm43_eid WHERE eid IN (SELECT eid FROM tqc11_resulteid WHERE qcbillid = '<QC单号>');
SELECT inbillid, invtyp, auditflg, refbillid FROM twh13_in WHERE refbillid = '<QC单号>';

-- 9. IV=6翻新溯源
SELECT eid, itemcd, ref_eid FROM tmm43_eid WHERE ref_eid IS NOT NULL;

-- 10. 结案验证
SELECT lineno, eid, closed_flg, closed_reason FROM twh16_outdteid WHERE outbillid = '<单号>' AND closed_flg = '1';
```

### 附录C：物料生命周期统计SQL

```sql
-- ============================================
-- 物料完整生命周期统计（替换 itemcd 后执行）
-- ============================================

-- 1. 流入流出汇总（TWH12 库存流水）
SELECT
  CASE WHEN iotyp='1' THEN '入库' WHEN iotyp='0' THEN '出库' END as 方向,
  CASE invtyp
    WHEN '1'  THEN '采购入库'
    WHEN '4'  THEN '调拨入库'
    WHEN '5'  THEN '质检出库(取样)'
    WHEN '6'  THEN '退换出库'
    WHEN '7'  THEN '报废出库'
    WHEN '8'  THEN '生产入库'
    WHEN '9'  THEN '返修出库'
    WHEN '11' THEN '质检合格入库'
    ELSE invtyp
  END as 业务类型,
  COUNT(*) as 笔数,
  SUM(itemqty) as 总数量
FROM twh12_detaildt
WHERE itemcd = '<物料编码>'
GROUP BY iotyp, invtyp
ORDER BY iotyp DESC, SUM(itemqty) DESC;

-- 2. 当前库存（批次 + EID在库）
SELECT '批次库存' as 类型, whcd, itemqty::text, itemtyp FROM twh11_detail WHERE itemcd='<物料编码>' AND itemqty>0
UNION ALL
SELECT 'EID在库', whcd, COUNT(*)::text, qcflg FROM tmm43_eid WHERE itemcd='<物料编码>' AND sflg IN ('1','3','8') GROUP BY whcd, qcflg
ORDER BY 类型, whcd;

-- 3. 汇总一句话
SELECT '批次库存' as 来源, SUM(itemqty)::text as 总量 FROM twh11_detail WHERE itemcd='<物料编码>'
UNION ALL
SELECT 'EID在库', COUNT(*)::text FROM tmm43_eid WHERE itemcd='<物料编码>' AND sflg IN ('1','3','8');

-- 4. EID 状态分布
SELECT sflg, qcflg, COUNT(*) FROM tmm43_eid WHERE itemcd='<物料编码>' GROUP BY sflg, qcflg ORDER BY sflg, qcflg;

-- 5. 不合格处理（最近30天 OV=6/7/9）
SELECT CASE o.invtyp WHEN '6' THEN '退换' WHEN '7' THEN '报废' WHEN '9' THEN '返修' END as 类型,
       o.outbillid, o.whcd, o.auditflg, d.outqty
FROM twh15_out o JOIN twh16_outdtprd d ON o.outbillid=d.outbillid
WHERE d.itemcd='<物料编码>' AND o.invtyp IN ('6','7','9') AND o.auditflg='2'
  AND o.gendate > NOW() - INTERVAL '30 days'
ORDER BY o.gendate DESC;

-- 6. 批次QC完整去向（替换批次号）
SELECT q.qcstatus as QC判定,
  CASE q.qcstatus WHEN 'GA' THEN '合格入库' WHEN 'GB' THEN '让步入库' WHEN 'BH' THEN '返修出库' WHEN 'BF' THEN '报废出库' WHEN 'TH' THEN '退换出库' END as 处理方式,
  COALESCE(d_in.eid, '批次') as EID,
  COALESCE(d_in.inqty, d_out.outqty) as 数量,
  CASE WHEN i.auditflg='2' THEN '已入正品仓' WHEN o.auditflg='2' THEN '已出库' END as 状态
FROM tqc10_result q
LEFT JOIN twh13_in i ON i.refbillid = q.qcbillid
LEFT JOIN twh14_checkindt d_in ON i.inbillid = d_in.inbillid
LEFT JOIN twh15_out o ON o.refbillid = q.qcbillid
LEFT JOIN twh16_outdtprd d_out ON o.outbillid = d_out.outbillid
WHERE q.refbillid = '<OV=5出库单号>'
ORDER BY q.qcstatus, d_in.lineno;
```

### 附录D：标签ID跨表关联运维

标签 ID（如 BS42002660001）在以下四个表中透传，修改时需同步更新：

```
TMM40_LABEL          标签主表（生成、激活状态）
    ↓ QC C1 审核激活
TMM43_EID             设备记录（sflg/qcflg/whcd）
    ↓ QC 结果录入
TQC11_RESULTEID       质检明细-按EID（qcqty/qcstatus）
    ↓ QC 审核 → IV=11
TWH14_CHECKINDT       入库明细（eid 字段）
```

**标签 ID 修复 SQL（四表同步）**：
```sql
-- 替换 <旧标签号> 和 <新标签号> 后执行
UPDATE tmm40_label      SET labelid = '<新标签号>' WHERE labelid = '<旧标签号>';
UPDATE tmm43_eid        SET eid     = '<新标签号>' WHERE eid     = '<旧标签号>';
UPDATE tqc11_resulteid  SET eid     = '<新标签号>' WHERE eid     = '<旧标签号>';
UPDATE twh14_checkindt  SET eid     = '<新标签号>' WHERE eid     = '<旧标签号>';
```

**生成规则（配件 typflg='0'）**：
```
classcd(补零至6位) + YY + 月份后缀(1-9→月份本身,10→A,11→B,12→C) + 4位序号
例：BS42 → BS4200 + 26 + 6 + 0001 → BS42002660001
```

**生成规则（成品 typflg='1'）**：
```
YYYYMMDD + sign(标识) + 4位序号
例：20260609 + L + 0001 → 20260609L0001
```

文档结束
