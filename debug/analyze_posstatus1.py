#!/usr/bin/env python3
"""分析posstatus1字段在业务中的实际作用和必要性"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 目标数据库连接
TARGET_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cheungjan@localhost:5432/myitsm")

def analyze_posstatus1():
    """分析posstatus1字段的必要性"""
    print(f"目标数据库连接: {TARGET_DATABASE_URL}")
    print(f"检查时间: {datetime.now()}")
    print("=" * 80)
    
    try:
        target_engine = create_engine(TARGET_DATABASE_URL)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
        
        # 1. 检查D2D表中posstatus和posstatus1的数据分布
        print("\n【1. D2D表中posstatus和posstatus1的数据分布】")
        query = text("""
            SELECT posstatus, posstatus1, COUNT(*) as cnt
            FROM tit23_maintenance_d2d
            WHERE posstatus IS NOT NULL
            GROUP BY posstatus, posstatus1
            ORDER BY posstatus, posstatus1
        """)
        d2d_distribution = target_session.execute(query).fetchall()
        print(f"{'posstatus':<12} {'posstatus1':<12} {'数量':<10}")
        print("-" * 35)
        for row in d2d_distribution:
            posstatus, posstatus1, cnt = row
            posstatus_str = str(posstatus) if posstatus else 'NULL'
            posstatus1_str = str(posstatus1) if posstatus1 else 'NULL'
            cnt_str = str(cnt) if cnt else '0'
            print(f"{posstatus_str:<12} {posstatus1_str:<12} {cnt_str:<10}")
        
        # 2. 检查客户表中posstatus和posstatus1的数据分布
        print("\n【2. 客户表中posstatus和posstatus1的数据分布】")
        query = text("""
            SELECT posstatus, posstatus1, COUNT(*) as cnt
            FROM tmm22_customers
            WHERE posstatus IS NOT NULL
            GROUP BY posstatus, posstatus1
            ORDER BY posstatus, posstatus1
        """)
        cust_distribution = target_session.execute(query).fetchall()
        print(f"{'posstatus':<12} {'posstatus1':<12} {'数量':<10}")
        print("-" * 35)
        for row in cust_distribution:
            posstatus, posstatus1, cnt = row
            posstatus_str = str(posstatus) if posstatus else 'NULL'
            posstatus1_str = str(posstatus1) if posstatus1 else 'NULL'
            cnt_str = str(cnt) if cnt else '0'
            print(f"{posstatus_str:<12} {posstatus1_str:<12} {cnt_str:<10}")
        
        # 3. 分析posstatus1的独立价值
        print("\n【3. posstatus1的独立价值分析】")
        # 检查posstatus1是否总是与posstatus有固定对应关系
        query = text("""
            SELECT posstatus, COUNT(DISTINCT posstatus1) as distinct_posstatus1_count
            FROM tit23_maintenance_d2d
            WHERE posstatus IS NOT NULL
            GROUP BY posstatus
            ORDER BY posstatus
        """)
        posstatus_analysis = target_session.execute(query).fetchall()
        print(f"{'posstatus':<12} {'对应的posstatus1数量':<20}")
        print("-" * 35)
        for row in posstatus_analysis:
            posstatus, distinct_count = row
            posstatus_str = str(posstatus) if posstatus else 'NULL'
            distinct_count_str = str(distinct_count) if distinct_count else '0'
            print(f"{posstatus_str:<12} {distinct_count_str:<20}")
        
        # 4. 对比系统字典表ST类型编码
        print("\n【4. 系统字典表ST类型编码】")
        query = text("""
            SELECT code_typ, code_cd, code_nm
            FROM tmm31_syscodes
            WHERE code_typ = 'ST'
            ORDER BY code_cd
        """)
        st_codes = target_session.execute(query).fetchall()
        print(f"{'编码类型':<10} {'编码':<10} {'名称':<30}")
        print("-" * 50)
        for row in st_codes:
            code_typ, code_cd, code_nm = row
            code_typ_str = str(code_typ) if code_typ else 'NULL'
            code_cd_str = str(code_cd) if code_cd else 'NULL'
            code_nm_str = str(code_nm) if code_nm else 'NULL'
            print(f"{code_typ_str:<10} {code_cd_str:<10} {code_nm_str:<30}")
        
        # 5. 检查是否可以用单层编码替代
        print("\n【5. 单层编码替代可行性分析】")
        # 检查posstatus1的值是否可以合并到posstatus中
        query = text("""
            SELECT COUNT(DISTINCT posstatus || posstatus1) as combined_count
            FROM tit23_maintenance_d2d
            WHERE posstatus IS NOT NULL AND posstatus1 IS NOT NULL
        """)
        combined_count = target_session.execute(query).scalar()
        
        query = text("""
            SELECT COUNT(DISTINCT posstatus) as single_count
            FROM tit23_maintenance_d2d
            WHERE posstatus IS NOT NULL
        """)
        single_count = target_session.execute(query).scalar()
        
        combined_count_str = str(combined_count) if combined_count else '0'
        single_count_str = str(single_count) if single_count else '0'
        
        print(f"单层编码(posstatus)状态数: {single_count_str}")
        print(f"双层编码(posstatus+posstatus1)状态数: {combined_count_str}")
        
        if combined_count and single_count:
            print(f"双层编码增加的状态数: {combined_count - single_count}")
        
        # 6. 检查posstatus1是否真的提供额外信息
        print("\n【6. posstatus1信息价值分析】")
        query = text("""
            SELECT COUNT(*) as total_records
            FROM tit23_maintenance_d2d
            WHERE posstatus IS NOT NULL
        """)
        total_records = target_session.execute(query).scalar()
        
        query = text("""
            SELECT COUNT(*) as records_with_posstatus1
            FROM tit23_maintenance_d2d
            WHERE posstatus IS NOT NULL AND posstatus1 IS NOT NULL AND posstatus1 != ''
        """)
        records_with_posstatus1 = target_session.execute(query).scalar()
        
        total_records_str = str(total_records) if total_records else '0'
        records_with_posstatus1_str = str(records_with_posstatus1) if records_with_posstatus1 else '0'
        
        print(f"有posstatus的记录总数: {total_records_str}")
        print(f"有posstatus1的记录数: {records_with_posstatus1_str}")
        
        if total_records and records_with_posstatus1:
            percentage = (records_with_posstatus1 / total_records) * 100 if total_records > 0 else 0
            print(f"posstatus1使用率: {percentage:.2f}%")
        
        target_session.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_posstatus1()
