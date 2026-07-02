---
类型: 测试指南
阅读状态: 未开始
tags:
  - 仓库管理
  - 验收测试
  - 阶段AB
更新日期: 2026-05-31
创建时间: 2026-05-31
作者: CJ
版本: v1.0
---

# 仓库模块阶段 A+B 验收测试指南

## 阶段 A：自动联动

### A1. 调拨出入库联动（OV=3 → IV=4）

**测试步骤**：

1. 出库单管理 → 新建 → 出库类型选"调拨出库"
2. 选出库仓库（源仓）和目标仓库
3. 在仓库存量面板勾选商品（批次或EID模式）
4. 保存 → 审核通过
5. 验证点：
   - [ ] 入库单管理出现一条调拨入库草稿（`invtyp=4`，`whcd=目标仓`）
   - [ ] 入库草稿明细与出库单一致（含EID）
   - [ ] 源仓库存扣减正确（TWH11）
   - [ ] TWH12 有出库流水（`iotyp=0`, `itemqty`为负）
6. 入库单管理 → 找到生成的草稿 → 审核通过
7. 验证点：
   - [ ] 目标仓库存增加（TWH11）
   - [ ] TWH12 有入库流水（`iotyp=1`, `itemqty`为正）
   - [ ] EID模式：`TMM43_EID.whcd` 更新为目标仓

**备选测试（手动选择单据）**：

1. 入库单管理 → 新建 → 入库类型选"调拨入库"
2. 下拉选择调拨出库单 → 自动填充目标仓和明细
3. 保存 → 应更新已有草稿而非新建
4. 审核通过

---

### A2. 服务返还联动（ITSM → IV=3）

**前置条件**：数据库有 TIT25 记录（`operflg='1'` 且 `asset_owner != '01'`）  
当前可测数据：`MD002400` 含有 1 件自有资产待返还配件

**测试步骤**：

1. 入库单管理 → 新建 → 入库类型选"服务返还入库"
2. 检查 ITSM 工单下拉是否显示待返还数据
3. 选择 `MD002400` → 点击"一键确认入库"
4. 验证点：
   - [ ] 提示"确认入库成功"
   - [ ] 入库单管理出现服务返还入库草稿（`invtyp=3`, `whcd=""`）
   - [ ] 入库草稿明细含 EID、物料编码
5. 编辑草稿填仓库 → 审核通过
6. 验证点：
   - [ ] TWH11 库存增加
   - [ ] TMM43_EID.whcd 更新

---

### A3. 库存校验 + EID仓库校验（出库审核）

**测试步骤**：

1. 出库单管理 → 新建 → 任意手动类型 → 选仓库
2. 仓库存量面板 → EID模式 → 选一个EID添加到明细
3. 手动把仓库改成另一个仓（与EID实际所在仓不同）
4. 保存 → 审核通过
5. 验证点：
   - [ ] 审核失败，提示"EID xxx 在 X 仓，不在出库仓库 Y，请修改仓库"
6. 把仓库改回正确仓库 → 审核通过
7. 验证点：
   - [ ] 审核成功
   - [ ] TWH11 库存扣减

---

## 阶段 B：上游单据选择器

### B1. 调拨入库选择器（GET /stock-in/transferable-orders）

**前置**：有已审核的调拨出库单且未完全入库

**测试步骤**：

```bash
TOKEN=$(curl -s http://localhost:5001/api/v1/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"admin","password":"admin123"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

curl -s "http://localhost:5001/api/v1/warehouse/stock-in/transferable-orders" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

验证点：
- [ ] 返回 JSON 数组，每项含 `outbillid`, `source_whcd`, `target_whcd`, `pending`
- [ ] `pending > 0`

---

### B2. 借出归还选择器（GET /stock-in/lendable-orders）

```bash
curl -s "http://localhost:5001/api/v1/warehouse/stock-in/lendable-orders" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

验证点：
- [ ] 返回 JSON 数组（当前数据可能为空）
- [ ] 每项含 `outbillid`, `whcd`, `total_out`, `returned`, `pending`

---

### B3. 质检出库选择器（GET /stock-out/qc-pending）

```bash
curl -s "http://localhost:5001/api/v1/warehouse/stock-out/qc-pending" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

验证点：
- [ ] 返回已审核采购入库单列表，每项含 `inbillid`, `whcd`, `refbillid`

---

### B4. 质检入库选择器（GET /stock-in/qc-passed）

```bash
curl -s "http://localhost:5001/api/v1/warehouse/stock-in/qc-passed" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

验证点：
- [ ] 返回已审核质检结果单列表
- [ ] 当前数据可能为空（质检模块未启用）

---

### B5. 销售出库选择器（GET /stock-out/sales-pending）

```bash
curl -s "http://localhost:5001/api/v1/warehouse/stock-out/sales-pending" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

验证点：
- [ ] 返回已审核预计划列表，每项含 `pcplanid`, `plandate`, `memo`

---

## 辅助功能验收

### 出入库对称功能

| 功能 | 入库单 | 出库单 | 测试方法 |
|------|:--:|:--:|------|
| 审核通过 | ✓ | ✓ | 新建→审核 |
| 审核退回 | ✓ | ✓ | 审核弹窗点"审核退回" |
| 编辑 | ✓ | ✓ | 列表点"编辑"→修改→保存 |
| 作废 | ✓ | ✓ | 列表点"作废"→确认 |
| 状态筛选 | ✓ | ✓ | 搜索栏选状态→查询 |

### 特殊校验

| 场景 | 预期 |
|------|------|
| 作废已审核出入库单 | 拒绝"已审核单据不可作废" |
| 作废关联出库已审的入库单 | 拒绝"来源出库单已审核，库存已扣除，不可作废" |
| 出库填EID后数量输入框 | 锁定为1，不可修改 |
| 出库填EID后切换仓库 | 清空已选明细，重新加载新仓库存 |
| 出库选仓后库存浏览 | 批次模式显示物料+状态+数量，EID模式显示序列号+质检状态 |

---

**版本历史**：
- v1.0 (2026-05-31): 初始版本
