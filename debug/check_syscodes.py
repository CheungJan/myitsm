#!/usr/bin/env python3
"""检查系统字典表 TMM31_SYSCODES 的结构和数据"""

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

def check_syscodes():
    """检查系统字典表 TMM31_SYSCODES"""
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
                WHERE table_name = 'tmm31_syscodes'
            )
        """)
        table_exists = source_session.execute(query).scalar()
        print(f"源数据库 tmm31_syscodes 表存在: {'是' if table_exists else '否'}")
        
        if table_exists:
            # 查询表结构
            print("\n【2. 源数据库表结构】")
            query = text("""
                SELECT column_name, data_type, character_maximum_length, 
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'tmm31_syscodes'
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
            query = text("SELECT COUNT(*) FROM tmm31_syscodes")
            total_count = source_session.execute(query).scalar()
            print(f"源数据库总记录数: {total_count}")
            
            # 查询编码类型分布
            print("\n【4. 编码类型分布】")
            query = text("""
                SELECT codetyp, COUNT(*) as cnt
                FROM tmm31_syscodes
                GROUP BY codetyp
                ORDER BY codetyp
            """)
            codetyp_dist = source_session.execute(query).fetchall()
            print(f"{'编码类型':<15} {'数量':<10}")
            print("-" * 30)
            for row in codetyp_dist:
                codetyp, cnt = row
                print(f"{codetyp:<15} {cnt:<10}")
            
            # 查询ST类型编码（POS状态）
            print("\n【5. ST类型编码（POS状态）】")
            query = text("""
                SELECT codecd, codenm, useflg
                FROM tmm31_syscodes
                WHERE codetyp = 'ST'
                ORDER BY codecd
            """)
            st_codes = source_session.execute(query).fetchall()
            print(f"{'编码':<10} {'名称':<30} {'有效标志':<8}")
            print("-" * 50)
            for row in st_codes:
                codecd, codenm, useflg = row
                print(f"{codecd:<10} {codenm:<30} {useflg:<8}")
            
            # 查询示例数据
            print("\n【6. 源数据库示例数据】")
            query = text("SELECT * FROM tmm31_syscodes ORDER BY codetyp, codecd LIMIT 15")
            sample_data = source_session.execute(query).fetchall()
            for row in sample_data:
                print(row)
        else:
            print("\n【2. 源数据库表不存在】")
        
        source_session.close()
        
        # 连接目标数据库
        print("\n【7. 连接目标数据库 myitsm】")
        target_engine = create_engine(TARGET_DATABASE_URL)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
        
        # 检查表是否存在
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'tmm31_syscodes'
            )
        """)
        table_exists = target_session.execute(query).scalar()
        print(f"目标数据库 tmm31_syscodes 表存在: {'是' if table_exists else '否'}")
        
        if table_exists:
            # 查询记录数
            query = text("SELECT COUNT(*) FROM tmm31_syscodes")
            total_count = target_session.execute(query).scalar()
            print(f"目标数据库总记录数: {total_count}")
            
            # 查询编码类型分布
            query = text("""
                SELECT code_typ, COUNT(*) as cnt
                FROM tmm31_syscodes
                GROUP BY code_typ
                ORDER BY code_typ
            """)
            codetyp_dist = target_session.execute(query).fetchall()
            print(f"{'编码类型':<15} {'数量':<10}")
            print("-" * 30)
            for row in codetyp_dist:
                code_typ, cnt = row
                print(f"{code_typ:<15} {cnt:<10}")
        
        target_session.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_syscodes()
