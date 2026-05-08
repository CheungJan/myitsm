# Oracle 原始库数据核查与导出指南

**目的**: 连接 Oracle 生产库（CCGLPDB + LGREPORTPDB），核查迁移中发现的 13 张问题表，判断是源数据问题还是合并丢失。

---

## 1. 连接 Oracle

```bash
# 方式1: sqlplus（推荐）
sqlplus username/password@host:1521/CCGLPDB

# 方式2: 如果有 tnsnames.ora
sqlplus username/password@CCGLPDB

# 方式3: Python cx_Oracle（导出数据用）
python -c "
import cx_Oracle
conn = cx_Oracle.connect('username/password@host:1521/CCGLPDB')
print('Connected')
"
```

Oracle 双库说明：
- **CCGLPDB** — 业务主库（ITSM 核心表、仓储 twh*、主数据 tmm* 等）
- **LGREPORTPDB** — 零售库（可能与 twh21/22 POS变更 相关）

---

## 2. 逐表核查 SQL（按问题类型）

### 2.1 FK 孤儿类

#### twh22_pos_change_dt — 100% 孤儿（1441行）

```sql
-- 核心核查：子表引用的 operation_id 是否在父表中存在
-- Oracle 中执行
SELECT COUNT(*) AS orphan_rows
FROM twh22_pos_change_dt dt
WHERE NOT EXISTS (
    SELECT 1 FROM twh21_pos_change pc WHERE pc.id = dt.operation_id
);

-- 分别看两个库
-- CCGLPDB:
SELECT COUNT(*) FROM twh21_pos_change;  -- 预期: 789
SELECT MIN(id), MAX(id) FROM twh21_pos_change;  -- 父表 id 范围

-- LGREPORTPDB:
SELECT COUNT(*) FROM twh21_pos_change;  -- 检查零售库是否也有数据
SELECT MIN(id), MAX(id) FROM twh21_pos_change;

-- 看子表引用了哪些不存在的 id
SELECT DISTINCT dt.operation_id 
FROM twh22_pos_change_dt dt
WHERE NOT EXISTS (
    SELECT 1 FROM twh21_pos_change pc WHERE pc.id = dt.operation_id
)
ORDER BY dt.operation_id;
-- 预期结果: 1,2,3,4,5,6,7,13 (与当前 PG 源库一致)
```

**判断**:
- 若两个库的 twh21 都无 id 1-13 → 源数据就是孤儿，合并没丢数据
- 若某个库的 twh21 有 id 1-13 → 合并时丢失了父表数据，需重新导出

#### tmm61_deposit_dtl — 381条 FK 孤儿

```sql
-- 核心核查
SELECT COUNT(*) AS orphan_rows
FROM tmm61_deposit_dtl dtl
WHERE NOT EXISTS (
    SELECT 1 FROM tmm61_deposit dep WHERE dep.custcd = dtl.custcd
);

-- 列出孤儿的 custcd
SELECT DISTINCT dtl.custcd
FROM tmm61_deposit_dtl dtl
WHERE NOT EXISTS (
    SELECT 1 FROM tmm61_deposit dep WHERE dep.custcd = dtl.custcd
)
FETCH FIRST 20 ROWS ONLY;  -- Oracle 12c+

-- 行数对照
SELECT 'tmm61_deposit' AS tbl, COUNT(*) FROM tmm61_deposit
UNION ALL SELECT 'tmm61_deposit_dtl', COUNT(*) FROM tmm61_deposit_dtl;
-- PG 源库参考: deposit=5022, deposit_dtl=6502
```

### 2.2 NULL 主键类

#### tmm61_deposit_list — id 全 NULL（6238行）

```sql
-- 核心核查：id 列是否真的全为 NULL
SELECT COUNT(*) AS total_rows,
       COUNT(id) AS non_null_ids
FROM tmm61_deposit_list;

-- 如果 Oracle 中 id 不为 NULL，说明是 PG 导出时丢失了 id 值
-- 抽样看几条
SELECT * FROM tmm61_deposit_list WHERE ROWNUM <= 5;

-- 检查 Oracle 中该表是否有触发器/序列自动生成 id
SELECT trigger_name FROM all_triggers WHERE table_name = 'TMM61_DEPOSIT_LIST';
-- 或
SELECT * FROM user_sequences WHERE sequence_name LIKE '%DEPOSIT%';
```

**判断**:
- 若 Oracle 中 id 同样全 NULL → PG 源库正确反映了原始数据
- 若 Oracle 中 id 有值 → PG 导出丢失了 id，需重新导出此表

### 2.3 PK 重复类

#### twh19_asset_c_a — 唯一值 69 但总行 179

```sql
-- 核心核查：Oracle 中是否也允许 opbillid 重复
SELECT opbillid, COUNT(*) AS cnt
FROM twh19_asset_c_a
GROUP BY opbillid
HAVING COUNT(*) > 1
ORDER BY cnt DESC
FETCH FIRST 10 ROWS ONLY;

-- 如果 Oracle 同样允许重复 → 原系统设计就如此，需要确认迁移策略
-- (保留最新？保留全部？合并？)

-- 行数对比
SELECT COUNT(*) AS total, COUNT(DISTINCT opbillid) AS unique_opbillid
FROM twh19_asset_c_a;
-- PG 源: total=179, unique=69
```

#### tmm61_deposit_dtl — 89 个重复 id

```sql
-- 找出重复 id
SELECT id, COUNT(*) AS cnt
FROM tmm61_deposit_dtl
GROUP BY id
HAVING COUNT(*) > 1
ORDER BY cnt DESC
FETCH FIRST 10 ROWS ONLY;

-- 抽样看重复行的完整数据（确认是否真重复还是数据录入错误）
SELECT * FROM tmm61_deposit_dtl 
WHERE id IN (
    SELECT id FROM tmm61_deposit_dtl 
    GROUP BY id HAVING COUNT(*) > 1
) AND ROWNUM <= 20
ORDER BY id;

-- 总行数 vs 唯一 id 数
SELECT COUNT(*) AS total, COUNT(DISTINCT id) AS unique_ids
FROM tmm61_deposit_dtl;
-- PG 源: total=6502, unique=6413
```

### 2.4 微小差异类（<1%，选查）

这些表差异极小（最多差 280 行），可能是迁移时个别行因类型转换/约束冲突被跳过。Oracle 中主要核查是否有更完整的行数：

```sql
-- 逐表行数对比（在 Oracle 中执行，记录结果回去和 PG 源库对比）
SELECT 'tit10_maintenance_liability' AS tbl, COUNT(*) FROM tit10_maintenance_liability
UNION ALL SELECT 'tit10_pos_detail', COUNT(*) FROM tit10_pos_detail
UNION ALL SELECT 'tmm22_customers', COUNT(*) FROM tmm22_customers
UNION ALL SELECT 'tmm35_cust_pos_rl', COUNT(*) FROM tmm35_cust_pos_rl
UNION ALL SELECT 'tmm42_bomdt', COUNT(*) FROM tmm42_bomdt
UNION ALL SELECT 'tmm43_eid_track', COUNT(*) FROM tmm43_eid_track
UNION ALL SELECT 'twh12_detaildt', COUNT(*) FROM twh12_detaildt;
```

参考值：

| 表 | PG 源库行数 | 迁移后行数 | Oracle 期望值 |
|---|---|---|---|
| tit10_maintenance_liability | 16,399 | 16,398 | ? |
| tit10_pos_detail | 34,481 | 34,468 | ? |
| tmm22_customers | 11,047 | 11,046 | ? |
| tmm35_cust_pos_rl | 16,912 | 16,902 | ? |
| tmm42_bomdt | 1,272 | 1,268 | ? |
| tmm43_eid_track | 1,022,481 | 1,022,462 | ? |
| twh12_detaildt | 265,579 | 265,299 | ? |

---

## 3. 数据导出操作

### 3.1 Oracle 导出整表为 CSV

```bash
# 用 sqlplus 的 spool 功能
sqlplus username/password@CCGLPDB << 'SQLEOF'
SET PAGESIZE 0
SET LINESIZE 5000
SET FEEDBACK OFF
SET HEADING OFF
SET TRIMSPOOL ON
SET COLSEP ','
SPOOL /tmp/twh22_pos_change_dt.csv

SELECT id, operation_id, poseid, changetype, old_eid, new_eid, 
       opercd, upddate, useflg, remark
FROM twh22_pos_change_dt;

SPOOL OFF
EXIT
SQLEOF
```

### 3.2 用 Python 导（推荐，处理编码更好）

```python
"""导出 Oracle 问题表数据到 CSV，用于和 PG 源库对比。"""
import csv
import cx_Oracle

TABLES = [
    ("CCGLPDB", "twh22_pos_change_dt"),
    ("CCGLPDB", "twh21_pos_change"),
    ("CCGLPDB", "tmm61_deposit_list"),
    ("CCGLPDB", "tmm61_deposit_dtl"),
    ("CCGLPDB", "tmm61_deposit"),
    ("CCGLPDB", "twh19_asset_c_a"),
    # 如果 LGREPORTPDB 也有相关表:
    ("LGREPORTPDB", "twh21_pos_change"),
]

# Oracle 连接信息（替换为实际值）
CONNS = {
    "CCGLPDB": "username/password@host:1521/CCGLPDB",
    "LGREPORTPDB": "username/password@host:1521/LGREPORTPDB",
}

for db_name, table_name in TABLES:
    conn = cx_Oracle.connect(CONNS[db_name])
    cursor = conn.cursor()
    
    # 获取列名
    cursor.execute(f"SELECT * FROM {table_name} WHERE ROWNUM = 0")
    columns = [d[0] for d in cursor.description]
    
    output = f"/tmp/oracle_{db_name}_{table_name}.csv"
    cursor.execute(f"SELECT * FROM {table_name}")
    
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)  # 表头
        writer.writerows(cursor)
    
    row_count = cursor.rowcount
    print(f"{db_name}.{table_name}: {row_count} 行 → {output}")
    
    cursor.close()
    conn.close()
```

### 3.3 导出后和 PG 源库对比

```bash
# 对比行数
echo "Oracle: $(wc -l < /tmp/oracle_CCGLPDB_twh22_pos_change_dt.csv)"
echo "PG源库:"
psql -U cheungjan -d ortopbitsmdb -c "SELECT count(*) FROM twh22_pos_change_dt;"

# 对比内容（关键列）
# 导出 PG 源库数据
psql -U cheungjan -d ortopbitsmdb -c "\COPY (
  SELECT operation_id, count(*) FROM twh22_pos_change_dt 
  GROUP BY operation_id ORDER BY operation_id
) TO '/tmp/pg_twh22_opid.csv' CSV HEADER;"

# 在 Oracle 侧同样导出
# 然后用 diff 对比
diff <(sort /tmp/oracle_twh22_opid.csv) <(sort /tmp/pg_twh22_opid.csv)
```

---

## 4. 核查结论记录模板

核查完后，对每个问题表填写：

| 表 | Oracle行数 | PG源库行数 | 一致? | 根因 |
|---|---|---|---|---|
| twh22_pos_change_dt | ? | 1441 | | |
| twh21_pos_change | ? | 789 | | |
| tmm61_deposit_list (id=NULL?) | ? | 6238 | | |
| tmm61_deposit_dtl | ? | 6502 | | |
| tmm61_deposit | ? | 5022 | | |
| twh19_asset_c_a | ? | 179(69唯) | | |

**根因分类**：
- A: Oracle 与 PG 源库一致 → 源数据问题，迁移正确
- B: Oracle 有但 PG 源库没有 → Oracle→PG 合并丢失，需重新导出该表
- C: Oracle 也没有 → 可能查看的是错误的 Oracle schema/库

---

## 5. 如果确实有合并丢失

如果发现 Oracle 数据比 PG 源库多，则需要针对性地重新导出该表：

```bash
# 方式1: Oracle SQL Developer → 右键表 → Export → CSV/INSERT statements
# 方式2: Oracle Data Pump
expdp username/password@CCGLPDB \
  tables=twh21_pos_change,twh22_pos_change_dt \
  directory=EXPORT_DIR \
  dumpfile=missing_tables.dmp

# 方式3: Python 导为 INSERT SQL 直接可执行
python << 'PYEOF'
import cx_Oracle
conn = cx_Oracle.connect('username/password@host:1521/CCGLPDB')
cursor = conn.cursor()

tables = ["twh21_pos_change"]
for tbl in tables:
    cursor.execute(f"SELECT * FROM {tbl}")
    cols = [d[0] for d in cursor.description]
    with open(f"/tmp/{tbl}.sql", "w") as f:
        for row in cursor:
            vals = []
            for v in row:
                if v is None: vals.append("NULL")
                elif isinstance(v, (int, float)): vals.append(str(v))
                else: vals.append(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'")
            f.write(f"INSERT INTO {tbl} ({','.join(cols)}) VALUES ({','.join(vals)});\n")
    print(f"{tbl}: {cursor.rowcount} rows exported")

cursor.close()
conn.close()
PYEOF

# 导入到 PG 源库
psql -U cheungjan -d ortopbitsmdb -f /tmp/twh21_pos_change.sql
```
