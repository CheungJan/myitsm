#!/usr/bin/env python3
"""重新确认TMM52_POSSTATUS和TMM40_LABEL表的存在状态和数据"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 目标数据库连接
TARGET_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cheungjan@localhost:5432/myitsm")

def recheck_tables():
    """重新确认表状态"""
    print(f"目标数据库连接: {TARGET_DATABASE_URL}")
    print(f"检查时间: {datetime.now()}")
    print("=" * 80)
    
    try:
        target_engine = create_engine(TARGET_DATABASE_URL)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
        
        # 检查TMM52_POSSTATUS表
        print("\n【1. 检查TMM52_POSSTATUS表】")
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'tmm52_posstatus'
            )
        """)
        table_exists = target_session.execute(query).scalar()
        print(f"TMM52_POSSTATUS表存在: {'是' if table_exists else '否'}")
        
        if table_exists:
            # 查询表结构
            query = text("""
                SELECT column_name, data_type, character_maximum_length, 
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'tmm52_posstatus'
                ORDER BY ordinal_position
            """)
            columns = target_session.execute(query).fetchall()
            
            print(f"{'字段名':<20} {'数据类型':<20} {'长度':<10} {'可空':<8} {'默认值':<20}")
            print("-" * 80)
            for col in columns:
                col_name, data_type, max_length, is_nullable, default_val = col
                length = str(max_length) if max_length else ''
                print(f"{col_name:<20} {data_type:<20} {length:<10} {is_nullable:<8} {str(default_val or ''):<20}")
            
            # 查询记录数
            query = text("SELECT COUNT(*) FROM tmm52_posstatus")
            total_count = target_session.execute(query).scalar()
            print(f"总记录数: {total_count}")
            
            # 查询示例数据
            if total_count > 0:
                query = text("SELECT * FROM tmm52_posstatus ORDER BY id LIMIT 10")
                sample_data = target_session.execute(query).fetchall()
                print("示例数据:")
                for row in sample_data:
                    print(row)
        
        # 检查TMM40_LABEL表
        print("\n【2. 检查TMM40_LABEL表】")
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'tmm40_label'
            )
        """)
        table_exists = target_session.execute(query).scalar()
        print(f"TMM40_LABEL表存在: {'是' if table_exists else '否'}")
        
        if table_exists:
            # 查询表结构
            query = text("""
                SELECT column_name, data_type, character_maximum_length, 
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'tmm40_label'
                ORDER BY ordinal_position
            """)
            columns = target_session.execute(query).fetchall()
            
            print(f"{'字段名':<20} {'数据类型':<20} {'长度':<10} {'可空':<8} {'默认值':<20}")
            print("-" * 80)
            for col in columns:
                col_name, data_type, max_length, is_nullable, default_val = col
                length = str(max_length) if max_length else ''
                print(f"{col_name:<20} {data_type:<20} {length:<10} {is_nullable:<8} {str(default_val or ''):<20}")
            
            # 查询记录数
            query = text("SELECT COUNT(*) FROM tmm40_label")
            total_count = target_session.execute(query).scalar()
            print(f"总记录数: {total_count}")
            
            # 查询示例数据
            if total_count > 0:
                query = text("SELECT * FROM tmm40_label ORDER BY labelid LIMIT 5")
                sample_data = target_session.execute(query).fetchall()
                print("示例数据:")
                for row in sample_data:
                    print(row)
        
        # 对比系统字典表ST编码
        print("\n【3. 系统字典表ST类型编码】")
        query = text("""
            SELECT code_typ, code_cd, code_nm, useflg
            FROM tmm31_syscodes
            WHERE code_typ = 'ST'
            ORDER BY code_cd
        """)
        st_codes = target_session.execute(query).fetchall()
        print(f"{'编码类型':<10} {'编码':<10} {'名称':<30} {'有效标志':<8}")
        print("-" * 60)
        for row in st_codes:
            code_typ, code_cd, code_nm, useflg = row
            print(f"{code_typ:<10} {code_cd:<10} {code_nm:<30} {useflg:<8}")
        
        print(f"\nST类型编码总数: {len(st_codes)}")
        
        target_session.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recheck_tables()
