#!/usr/bin/env python3
"""检查源数据库 ortopbitsmdb 中 TMM52_POSSTATUS 表的结构"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 源数据库连接
SOURCE_DATABASE_URL = os.getenv("SOURCE_DATABASE_URL", "postgresql://cheungjan@localhost:5432/ortopbitsmdb")
TARGET_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cheungjan@localhost:5432/myitsm")

def check_source_tmm52():
    """检查源数据库中的 TMM52_POSSTATUS 表"""
    print(f"源数据库连接: {SOURCE_DATABASE_URL}")
    print(f"目标数据库连接: {TARGET_DATABASE_URL}")
    print(f"检查时间: {datetime.now()}")
    print("=" * 80)
    
    try:
        # 连接源数据库
        print("\n【1. 连接源数据库 ortopbitsmdb】")
        source_engine = create_engine(SOURCE_DATABASE_URL)
        SourceSession = sessionmaker(bind=source_engine)
        source_session = SourceSession()
        
        # 检查表是否存在
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'tmm52_posstatus'
            )
        """)
        table_exists = source_session.execute(query).scalar()
        print(f"源数据库 tmm52_posstatus 表存在: {'是' if table_exists else '否'}")
        
        if table_exists:
            # 查询表结构
            print("\n【2. 源数据库表结构】")
            query = text("""
                SELECT column_name, data_type, character_maximum_length, 
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'tmm52_posstatus'
                ORDER BY ordinal_position
            """)
            columns = source_session.execute(query).fetchall()
            
            print(f"{'字段名':<20} {'数据类型':<20} {'长度':<10} {'可空':<8} {'默认值':<20}")
            print("-" * 80)
            for col in columns:
                col_name, data_type, max_length, is_nullable, default_val = col
                length = str(max_length) if max_length else ''
                print(f"{col_name:<20} {data_type:<20} {length:<10} {is_nullable:<8} {str(default_val or ''):<20}")
            
            # 查询记录数
            print("\n【3. 源数据库记录统计】")
            query = text("SELECT COUNT(*) FROM tmm52_posstatus")
            total_count = source_session.execute(query).scalar()
            print(f"源数据库总记录数: {total_count}")
            
            # 查询示例数据
            if total_count > 0:
                print("\n【4. 源数据库示例数据】")
                query = text("SELECT * FROM tmm52_posstatus ORDER BY id LIMIT 10")
                sample_data = source_session.execute(query).fetchall()
                for row in sample_data:
                    print(row)
        else:
            print("\n【2. 源数据库表不存在】")
        
        source_session.close()
        
        # 连接目标数据库
        print("\n【5. 连接目标数据库 myitsm】")
        target_engine = create_engine(TARGET_DATABASE_URL)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
        
        # 检查表是否存在
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'tmm52_posstatus'
            )
        """)
        table_exists = target_session.execute(query).scalar()
        print(f"目标数据库 tmm52_posstatus 表存在: {'是' if table_exists else '否'}")
        
        target_session.close()
        
        # 检查其他表中的posstatus字段
        print("\n【6. 检查其他表中的posstatus字段】")
        source_engine = create_engine(SOURCE_DATABASE_URL)
        SourceSession = sessionmaker(bind=source_engine)
        source_session = SourceSession()
        
        query = text("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE column_name IN ('posstatus', 'posstatus1')
            ORDER BY table_name, column_name
        """)
        posstatus_fields = source_session.execute(query).fetchall()
        
        print(f"{'表名':<30} {'字段名':<15} {'数据类型':<20}")
        print("-" * 80)
        for row in posstatus_fields:
            table_name, column_name, data_type = row
            print(f"{table_name:<30} {column_name:<15} {data_type:<20}")
        
        source_session.close()
        
        # 检查数据迁移配置
        print("\n【7. 检查数据迁移配置】")
        try:
            from app.migration.batch_runner import BATCH_TABLES
            found_in_batch = False
            for batch, tables in BATCH_TABLES.items():
                if 'tmm52_posstatus' in tables:
                    print(f"✅ tmm52_posstatus 在迁移配置中，批次: {batch}")
                    found_in_batch = True
                    break
            if not found_in_batch:
                print(f"❌ tmm52_posstatus 不在迁移配置中")
        except Exception as e:
            print(f"❌ 检查迁移配置时出错: {e}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_source_tmm52()
