# DBA正式库执行批次清单（CCGL）

## 1. 目标与范围
- 目标：按 **P1 → P2** 分批在正式库 `CCGL` 落地兼容层，避免PB存量SQL因对象缺失报错。
- 范围：仅执行 **视图/同义词兼容** 与只读验证；不做删表、改表结构、数据迁移写入。
- 前提：`TIT01_TIMEPOINT_CUST` 已在 `CCGL_TEST` 本地测试通过。

## 2. 执行门禁（每个批次开始前必须通过）
1. 网络连通：`tnsping CCGL`
2. 会话校验（必须为 `CCGLPDB`）：
   ```sql
   SELECT SYS_CONTEXT('USERENV','SERVICE_NAME') AS service_name,
          SYS_CONTEXT('USERENV','DB_NAME')      AS db_name
   FROM dual;
   ```
3. 执行账号权限校验：具备 `CREATE VIEW` / `CREATE SYNONYM`（或由DBA执行）。
4. 变更窗口：仅在批准窗口执行，开启日志落盘（spool）。

## 3. 批次安排

### 批次P1（高优先，先落地）
- 对象：`TIT01_TIMEPOINT_CUST`
- 执行脚本：`DBA_执行_创建TIT01_TIMEPOINT_CUST.sql`
- 验证脚本：`DBA_验证_TIT01_TIMEPOINT_CUST.sql`
- 回滚脚本：`DBA_回滚_删除TIT01_TIMEPOINT_CUST.sql`
- 通过标准：对象 `VALID`、字段结构正确、可只读查询。

### 批次P2（第二批，分组执行）
建议按每组 4~6 个对象分批，单批失败可快速止损。

#### P2-A（财务/价格类）
- `TAC01_ACRECEIVE`
- `TAC11_PAYDAYS`
- `TAC12_CREDLIMIT`
- `TAC13_CREDLIMITDT`
- `TIP05_CUSTDISCOUNT`
- `TIP07_COSTPRICTRACK`
- `TIP08_MONTHCOST`

#### P2-B（销售/发票类）
- `TSL05_SLPROMPLAN`
- `TSL11_REGISTER`
- `TSL11_SLBILLITEM`
- `TSL15_PICKBILL`
- `TSL16_PICKBILLDT`
- `TSL20_INVOICE`

#### P2-C（仓储/计划类）
- `TPC01_PCPROMPLAN`
- `TPS01_PIPELINE`
- `TWH03_ROUTE`
- `TWH22_ARRTOROUTEDT`
- `TIV30_SHOPCHECKPLAN`
- `TIV33_OVBILL`

#### P2-D（基础数据/视图类）
- `TMM13_ITEMUNIT`
- `TMM14_ITEMBAR`
- `TMM15_ITEMTAXRATE`
- `TMM23_ADDRESS`
- `U_BUTTONS_V`

## 4. P2执行策略（统一）
1. 先查现状：是否已有对象/同义词（防重建）。
2. 优先同义词：若存在可复用目标对象，先 `CREATE OR REPLACE SYNONYM`。
3. 次选兼容视图：若无可复用对象，再按业务口径建兼容视图。
4. 单对象完成后立刻只读验证：对象状态、字段、`COUNT(*)`。
5. 单对象失败立即停止本批次，记录日志并回退该对象。

## 5. 推荐执行命令
```powershell
# P1
sqlplus ccgl/ccgl@CCGL @e:\project\myitsm\src\docs\DBA_执行_创建TIT01_TIMEPOINT_CUST.sql
sqlplus ccgl/ccgl@CCGL @e:\project\myitsm\src\docs\DBA_验证_TIT01_TIMEPOINT_CUST.sql

# P2（模板）
sqlplus ccgl/ccgl@CCGL @e:\project\myitsm\src\docs\DBA_P2_兼容层执行模板.sql
```

## 6. 回滚与退出条件
- 退出条件：
  - 会话非 `CCGLPDB`；
  - 对象类型冲突（非VIEW/非同义词被占用）；
  - 验证失败（状态无效、字段不匹配、关键查询报错）。
- 回滚原则：仅回滚当前批次已创建对象，不影响历史对象。

## 7. 交付记录
- 每批次输出：执行日志、验证截图/结果、异常与处理说明。
- 执行后同步更新：`数据库实体与状态码字典_优化后_最终版_utf8bom.csv` 的治理状态。
