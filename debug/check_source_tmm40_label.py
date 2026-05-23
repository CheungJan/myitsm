#!/usr/bin/env python3
"""检查源数据库 ortopbitsmdb 中 TMM40_LABEL 表的结构"""

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

def check_source_tmm40_label():
    """检查源数据库中的 TMM40_LABEL 表"""
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
                WHERE table_name = 'tmm40_label'
            )
        """)
        table_exists = source_session.execute(query).scalar()
        print(f"源数据库 tmm40_label 表存在: {'是' if table_exists else '否'}")
        
        if table_exists:
            # 查询表结构
            print("\n【2. 源数据库表结构】")
            query = text("""
                SELECT column_name, data_type, character_maximum_length, 
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'tmm40_label'
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
            query = text("SELECT COUNT(*) FROM tmm40_label")
            total_count = source_session.execute(query).scalar()
            print(f"源数据库总记录数: {total_count}")
            
            # 查询示例数据
            if total_count > 0:
                print("\n【4. 源数据库示例数据】")
                query = text("SELECT * FROM tmm40_label LIMIT 3")
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
                WHERE table_name = 'tmm40_label'
            )
        """)
        table_exists = target_session.execute(query).scalar()
        print(f"目标数据库 tmm40_label 表存在: {'是' if table_exists else '否'}")
        
        target_session.close()
        
        # 检查数据迁移配置
        print("\n【6. 检查数据迁移配置】")
        try:
            from app.migration.batch_runner import TABLE_MAPPINGS
            if 'tmm40_label' in TABLE_MAPPINGS:
                print(f"✅ tmm40_label 在迁移配置中")
                print(f"   映射: {TABLE_MAPPINGS['tmm40_label']}")
            else:
                print(f"❌ tmm40_label 不在迁移配置中")
        except Exception as e:
            print(f"❌ 检查迁移配置时出错: {e}")
        
        # 检查迁移脚本
        print("\n【7. 检查迁移脚本】")
        migration_files = []
        try:
            import os
            migrations_dir = '/Users/cheungjan/myitsm/migrations/versions'
            for filename in os.listdir(migrations_dir):
                if filename.endswith('.py') and filename != '__init__.py':
                    filepath = os.path.join(migrations_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'tmm40_label' in content.lower():
                            migration_files.append(filename)
            
            if migration_files:
                print(f"✅ 找到 {len(migration_files)} 个迁移脚本包含 tmm40_label:")
                for filename in migration_files:
                    print(f"   - {filename}")
            else:
                print(f"❌ 没有迁移脚本包含 tmm40_label")
        except Exception as e:
            print(f"❌ 检查迁移脚本时出错: {e}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_source_tmm40_label()
