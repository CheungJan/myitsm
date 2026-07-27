#!/usr/bin/env python3
"""检查源数据库中TIT03_SYSCODES表的ST类型数据"""

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

def check_tit03_syscodes():
    """检查TIT03_SYSCODES表的ST类型数据"""
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
                WHERE table_name = 'tit03_syscodes'
            )
        """)
        table_exists = source_session.execute(query).scalar()
        print(f"源数据库 tit03_syscodes 表存在: {'是' if table_exists else '否'}")
        
        if table_exists:
            # 查询ST类型数据
            print("\n【2. 源数据库ST类型数据】")
            query = text("""
                SELECT codecd, codenm, useflg
                FROM tit03_syscodes
                WHERE codetyp = 'ST'
                ORDER BY codecd
            """)
            st_codes = source_session.execute(query).fetchall()
            print(f"{'编码':<10} {'名称':<30} {'有效标志':<8}")
            print("-" * 50)
            for row in st_codes:
                codecd, codenm, useflg = row
                print(f"{codecd:<10} {codenm:<30} {useflg:<8}")
            
            print(f"\n源数据库ST类型编码总数: {len(st_codes)}")
        
        source_session.close()
        
        # 连接目标数据库
        print("\n【3. 连接目标数据库 myitsm】")
        target_engine = create_engine(TARGET_DATABASE_URL)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
        
        # 检查表是否存在
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'tit03_syscodes'
            )
        """)
        table_exists = target_session.execute(query).scalar()
        print(f"目标数据库 tit03_syscodes 表存在: {'是' if table_exists else '否'}")
        
        if table_exists:
            # 查询ST类型数据
            print("\n【4. 目标数据库ST类型数据】")
            query = text("""
                SELECT codecd, codenm, useflg
                FROM tit03_syscodes
                WHERE codetyp = 'ST'
                ORDER BY codecd
            """)
            st_codes = target_session.execute(query).fetchall()
            print(f"{'编码':<10} {'名称':<30} {'有效标志':<8}")
            print("-" * 50)
            for row in st_codes:
                codecd, codenm, useflg = row
                print(f"{codecd:<10} {codenm:<30} {useflg:<8}")
            
            print(f"\n目标数据库ST类型编码总数: {len(st_codes)}")
        
        target_session.close()
        
        # 对比分析
        print("\n【5. PB源码中的使用方式】")
        print("PB源码中的SQL查询：")
        print("SELECT A.id AS ID,A.codecd AS codecd, B.codenm AS NAME,A.codenm AS codenm")
        print("FROM tmm52_posstatus a, TIT03_SYSCODES b")
        print("WHERE a.codecd = b.codecd AND b.CODETYP = 'ST' AND A.useflg= '1'")
        print("ORDER BY A.id")
        print("\n这说明：")
        print("- TMM52_POSSTATUS的codecd字段关联TIT03_SYSCODES表的codecd字段")
        print("- 状态名称从TIT03_SYSCODES表的codenm字段获取")
        print("- TMM52_POSSTATUS的codecd1字段可能是冗余字段")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tit03_syscodes()
