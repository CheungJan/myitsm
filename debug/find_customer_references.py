#!/usr/bin/env python3
"""查询关联 tmm22_customers 的表"""

from sqlalchemy import create_engine, text, inspect
from collections import defaultdict

# 数据库连接
target_url = "postgresql://cheungjan@localhost:5432/myitsm"
tgt_engine = create_engine(target_url)

print(f"{'='*60}")
print("查询关联 tmm22_customers 的表")
print(f"{'='*60}")

# 方法1：查询外键约束
print(f"\n{'='*60}")
print("方法1：查询外键约束")
print(f"{'='*60}")

with tgt_engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
        WHERE
            tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = 'tmm22_customers'
        ORDER BY tc.table_name, kcu.column_name
    """))
    
    fk_tables = set()
    for row in result:
        fk_tables.add(row[0])
        print(f"表: {row[0]}")
        print(f"  字段: {row[1]} → tmm22_customers.{row[3]}")
    
    print(f"\n通过外键约束关联的表数量: {len(fk_tables)}")

# 方法2：查询包含 cust_cd 字段的表
print(f"\n{'='*60}")
print("方法2：查询包含 cust_cd 字段的表")
print(f"{'='*60}")

with tgt_engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            table_name,
            column_name,
            data_type
        FROM
            information_schema.columns
        WHERE
            column_name = 'cust_cd'
            AND table_schema = 'public'
        ORDER BY table_name
    """))
    
    cust_cd_tables = []
    for row in result:
        cust_cd_tables.append(row[0])
        print(f"表: {row[0]}, 字段类型: {row[2]}")
    
    print(f"\n包含 cust_cd 字段的表数量: {len(cust_cd_tables)}")

# 方法3：使用 SQLAlchemy inspect
print(f"\n{'='*60}")
print("方法3：使用 SQLAlchemy inspect 查询外键")
print(f"{'='*60}")

inspector = inspect(tgt_engine)
all_tables = inspector.get_table_names()

fk_references = defaultdict(list)

for table_name in all_tables:
    try:
        foreign_keys = inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            if 'tmm22_customers' in fk.get('referred_table', ''):
                fk_references[table_name].extend(fk.get('constrained_columns', []))
    except Exception as e:
        pass

print(f"\n通过 SQLAlchemy inspect 发现的关联表:")
for table, columns in fk_references.items():
    print(f"表: {table}, 字段: {', '.join(columns)}")

# 方法4：查询包含 custcd 字段的表（兼容旧命名）
print(f"\n{'='*60}")
print("方法4：查询包含 custcd 字段的表（兼容旧命名）")
print(f"{'='*60}")

with tgt_engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            table_name,
            column_name,
            data_type
        FROM
            information_schema.columns
        WHERE
            column_name = 'custcd'
            AND table_schema = 'public'
        ORDER BY table_name
    """))
    
    custcd_tables = []
    for row in result:
        custcd_tables.append(row[0])
        print(f"表: {row[0]}, 字段类型: {row[2]}")
    
    print(f"\n包含 custcd 字段的表数量: {len(custcd_tables)}")

# 总结
print(f"\n{'='*60}")
print("总结")
print(f"{'='*60}")
print(f"通过外键约束关联的表: {len(fk_tables)}")
print(f"包含 cust_cd 字段的表: {len(cust_cd_tables)}")
print(f"包含 custcd 字段的表: {len(custcd_tables)}")

all_related_tables = set(fk_tables) | set(cust_cd_tables) | set(custcd_tables)
print(f"\n所有关联表（去重）: {len(all_related_tables)}")
print(f"\n关联表列表:")
for table in sorted(all_related_tables):
    print(f"  - {table}")

tgt_engine.dispose()
