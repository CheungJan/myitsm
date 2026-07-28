#!/usr/bin/env python3
"""查询 ortopbitsmdb 和 myitsm 中 tmm11_itemclass 和 tmm12_items 的表结构对比"""

import os
from pathlib import Path
from sqlalchemy import create_engine, text, inspect

# 加载 .env 文件
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# 数据库连接配置
source_url = os.getenv("SOURCE_DATABASE_URL")
target_url = os.getenv("DATABASE_URL")

if not target_url:
    print("错误：DATABASE_URL 环境变量未设置")
    exit(1)

print(f"目标数据库 (myitsm): {target_url}")

if not source_url:
    print("警告：SOURCE_DATABASE_URL 环境变量未设置，仅查询 myitsm")
    print("请在 .env 文件中添加：SOURCE_DATABASE_URL=postgresql://user:pass@host:5432/ortopbitsmdb")
    src_engine = None
else:
    print(f"源数据库 (ortopbitsmdb): {source_url}")

# 创建引擎
if source_url:
    src_engine = create_engine(source_url)
tgt_engine = create_engine(target_url)

def get_table_columns(engine, table_name):
    """获取表的列信息"""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return columns

def print_table_structure(db_name, engine, table_name):
    """打印表结构"""
    print(f"\n{'='*60}")
    print(f"{db_name} - {table_name} 表结构")
    print(f"{'='*60}")
    
    try:
        columns = get_table_columns(engine, table_name)
        print(f"{'字段名':<20} {'类型':<20} {'长度':<10} {'可空':<10} {'默认值'}")
        print("-" * 80)
        for col in columns:
            length = str(col['type'].length) if hasattr(col['type'], 'length') else ''
            nullable = 'YES' if col['nullable'] else 'NO'
            default = str(col['default']) if col['default'] else ''
            print(f"{col['name']:<20} {str(col['type'])[:20]:<20} {length:<10} {nullable:<10} {default}")
    except Exception as e:
        print(f"错误: {e}")

# 查询 myitsm 表结构
print_table_structure("myitsm", tgt_engine, "tmm11_itemclass")
print_table_structure("myitsm", tgt_engine, "tmm12_items")

# 如果有源数据库，则对比
if src_engine:
    print_table_structure("ortopbitsmdb", src_engine, "tmm11_itemclass")
    print_table_structure("ortopbitsmdb", src_engine, "tmm12_items")
    
    # 对比字段差异
    print(f"\n{'='*60}")
    print("字段对比分析")
    print(f"{'='*60}")

    def compare_columns(src_columns, tgt_columns):
        """对比字段差异"""
        src_names = {col['name'] for col in src_columns}
        tgt_names = {col['name'] for col in tgt_columns}
        
        only_in_src = src_names - tgt_names
        only_in_tgt = tgt_names - src_names
        common = src_names & tgt_names
        
        return only_in_src, only_in_tgt, common

    # 对比 tmm11_itemclass
    src_itemclass = get_table_columns(src_engine, "tmm11_itemclass")
    tgt_itemclass = get_table_columns(tgt_engine, "tmm11_itemclass")

    only_src, only_tgt, common = compare_columns(src_itemclass, tgt_itemclass)

    print("\ntmm11_itemclass 字段对比:")
    if only_src:
        print(f"  仅在 ortopbitsmdb 中: {only_src}")
    if only_tgt:
        print(f"  仅在 myitsm 中: {only_tgt}")
    print(f"  共同字段: {common}")

    # 特别检查 PARENT/parent_cd 字段
    print("\n关键字段 PARENT/parent_cd 检查:")
    src_has_parent = any(col['name'] in ['parent', 'parent_cd'] for col in src_itemclass)
    tgt_has_parent = any(col['name'] in ['parent', 'parent_cd'] for col in tgt_itemclass)
    print(f"  ortopbitsmdb 有 PARENT/parent_cd: {src_has_parent}")
    print(f"  myitsm 有 PARENT/parent_cd: {tgt_has_parent}")

    # 对比 tmm12_items
    src_items = get_table_columns(src_engine, "tmm12_items")
    tgt_items = get_table_columns(tgt_engine, "tmm12_items")

    only_src, only_tgt, common = compare_columns(src_items, tgt_items)

    print("\ntmm12_items 字段对比:")
    if only_src:
        print(f"  仅在 ortopbitsmdb 中: {only_src}")
    if only_tgt:
        print(f"  仅在 myitsm 中: {only_tgt}")
    print(f"  共同字段: {common}")

    # 关闭连接
    src_engine.dispose()

tgt_engine.dispose()

# 查询 myitsm 中 parent_cd 字段的数据情况
print(f"\n{'='*60}")
print("myitsm 数据检查")
print(f"{'='*60}")

from sqlalchemy import text

# 检查 tmm11_itemclass 的 parent_cd 数据
with tgt_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) as total FROM tmm11_itemclass"))
    total = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as null_count FROM tmm11_itemclass WHERE parent_cd IS NULL"))
    null_count = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as has_parent FROM tmm11_itemclass WHERE parent_cd IS NOT NULL"))
    has_parent = result.scalar()
    
    print(f"\ntmm11_itemclass parent_cd 字段数据统计:")
    print(f"  总记录数: {total}")
    print(f"  parent_cd 为 NULL: {null_count}")
    print(f"  parent_cd 有值: {has_parent}")
    
    if has_parent > 0:
        result = conn.execute(text("""
            SELECT class_cd, class_nm, parent_cd 
            FROM tmm11_itemclass 
            WHERE parent_cd IS NOT NULL 
            ORDER BY class_cd 
            LIMIT 10
        """))
        print(f"\n  parent_cd 有值的记录示例:")
        for row in result:
            print(f"    {row[0]} - {row[1]} - parent: {row[2]}")
    
    # 检查编码长度分布
    result = conn.execute(text("""
        SELECT LENGTH(class_cd) as cd_len, COUNT(*) as count
        FROM tmm11_itemclass
        GROUP BY LENGTH(class_cd)
        ORDER BY cd_len
    """))
    print(f"\n  class_cd 编码长度分布:")
    for row in result:
        print(f"    长度 {row[0]}: {row[1]} 条")

# 查询 ortopbitsmdb 中 parent 字段的数据情况
if src_engine:
    print(f"\n{'='*60}")
    print("ortopbitsmdb 数据检查")
    print(f"{'='*60}")
    
    with src_engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) as total FROM tmm11_itemclass"))
        total = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(*) as null_count FROM tmm11_itemclass WHERE parent IS NULL"))
        null_count = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(*) as percent_root FROM tmm11_itemclass WHERE parent = '%'"))
        percent_root = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(*) as has_parent FROM tmm11_itemclass WHERE parent IS NOT NULL AND parent != '%'"))
        has_parent = result.scalar()
        
        print(f"\ntmm11_itemclass parent 字段数据统计:")
        print(f"  总记录数: {total}")
        print(f"  parent 为 NULL: {null_count}")
        print(f"  parent = '%' (根节点): {percent_root}")
        print(f"  parent 有具体值: {has_parent}")
        
        if has_parent > 0:
            result = conn.execute(text("""
                SELECT classcd, classnm, parent 
                FROM tmm11_itemclass 
                WHERE parent IS NOT NULL AND parent != '%'
                ORDER BY classcd 
                LIMIT 10
            """))
            print(f"\n  parent 有具体值的记录示例:")
            for row in result:
                print(f"    {row[0]} - {row[1]} - parent: {row[2]}")
        
        if percent_root > 0:
            result = conn.execute(text("""
                SELECT classcd, classnm, parent 
                FROM tmm11_itemclass 
                WHERE parent = '%'
                ORDER BY classcd 
                LIMIT 10
            """))
            print(f"\n  parent = '%' (根节点) 记录示例:")
            for row in result:
                print(f"    {row[0]} - {row[1]} - parent: {row[2]}")
        
        # 检查编码长度分布
        result = conn.execute(text("""
            SELECT LENGTH(classcd) as cd_len, COUNT(*) as count
            FROM tmm11_itemclass
            GROUP BY LENGTH(classcd)
            ORDER BY cd_len
        """))
        print(f"\n  classcd 编码长度分布:")
        for row in result:
            print(f"    长度 {row[0]}: {row[1]} 条")
