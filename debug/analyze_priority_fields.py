#!/usr/bin/env python3
"""分析tit10_maintenanceday表中servrity/emergency_level/priority字段的同步使用场景"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 目标数据库连接
TARGET_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cheungjan@localhost:5432/myitsm")

def analyze_priority_fields():
    """分析servrity/emergency_level/priority字段的同步使用场景"""
    print(f"目标数据库连接: {TARGET_DATABASE_URL}")
    print(f"检查时间: {datetime.now()}")
    print("=" * 80)
    
    try:
        target_engine = create_engine(TARGET_DATABASE_URL)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
        
        # 1. 检查三个字段的总体数据分布
        print("\n【1. 三个字段的总体数据分布】")
        
        query = text("""
            SELECT servrity, COUNT(*) as cnt
            FROM tit10_maintenanceday
            WHERE servrity IS NOT NULL
            GROUP BY servrity
            ORDER BY servrity
        """)
        servrity_dist = target_session.execute(query).fetchall()
        print(f"\n严重程度(servrity)分布:")
        print(f"{'值':<10} {'数量':<15}")
        print("-" * 25)
        for row in servrity_dist:
            val, cnt = row
            print(f"{str(val):<10} {str(cnt):<15}")
        
        query = text("""
            SELECT emergency_level, COUNT(*) as cnt
            FROM tit10_maintenanceday
            WHERE emergency_level IS NOT NULL
            GROUP BY emergency_level
            ORDER BY emergency_level
        """)
        emergency_dist = target_session.execute(query).fetchall()
        print(f"\n紧急程度(emergency_level)分布:")
        print(f"{'值':<10} {'数量':<15}")
        print("-" * 25)
        for row in emergency_dist:
            val, cnt = row
            print(f"{str(val):<10} {str(cnt):<15}")
        
        query = text("""
            SELECT priority, COUNT(*) as cnt
            FROM tit10_maintenanceday
            WHERE priority IS NOT NULL
            GROUP BY priority
            ORDER BY priority
        """)
        priority_dist = target_session.execute(query).fetchall()
        print(f"\n优先级(priority)分布:")
        print(f"{'值':<10} {'数量':<15}")
        print("-" * 25)
        for row in priority_dist:
            val, cnt = row
            print(f"{str(val):<10} {str(cnt):<15}")
        
        # 2. 检查三个字段的组合情况
        print("\n【2. 三个字段的组合情况】")
        query = text("""
            SELECT servrity, emergency_level, priority, COUNT(*) as cnt
            FROM tit10_maintenanceday
            WHERE servrity IS NOT NULL 
              AND emergency_level IS NOT NULL 
              AND priority IS NOT NULL
            GROUP BY servrity, emergency_level, priority
            ORDER BY servrity, emergency_level, priority
        """)
        combination_dist = target_session.execute(query).fetchall()
        print(f"\n{'严重程度':<12} {'紧急程度':<12} {'优先级':<12} {'数量':<15}")
        print("-" * 51)
        for row in combination_dist:
            sv, em, pr, cnt = row
            print(f"{str(sv):<12} {str(em):<12} {str(pr):<12} {str(cnt):<15}")
        
        # 3. 检查同步情况（三个值相同）
        print("\n【3. 同步情况分析（三个值相同）】")
        query = text("""
            SELECT servrity, emergency_level, priority, COUNT(*) as cnt
            FROM tit10_maintenanceday
            WHERE servrity IS NOT NULL 
              AND emergency_level IS NOT NULL 
              AND priority IS NOT NULL
              AND servrity = emergency_level 
              AND emergency_level = priority
            GROUP BY servrity, emergency_level, priority
            ORDER BY servrity
        """)
        sync_dist = target_session.execute(query).fetchall()
        
        total_sync = sum(row[3] for row in sync_dist)
        print(f"\n同步组合（三个值相同）:")
        print(f"{'严重程度':<12} {'紧急程度':<12} {'优先级':<12} {'数量':<15}")
        print("-" * 51)
        for row in sync_dist:
            sv, em, pr, cnt = row
            print(f"{str(sv):<12} {str(em):<12} {str(pr):<12} {str(cnt):<15}")
        print(f"\n同步记录总数: {total_sync}")
        
        # 4. 检查异步情况（三个值不完全相同）
        print("\n【4. 异步情况分析（三个值不完全相同）】")
        query = text("""
            SELECT COUNT(*) as total_records
            FROM tit10_maintenanceday
            WHERE servrity IS NOT NULL 
              AND emergency_level IS NOT NULL 
              AND priority IS NOT NULL
        """)
        total_records = target_session.execute(query).scalar()
        
        async_count = total_records - total_sync
        async_percentage = (async_count / total_records * 100) if total_records > 0 else 0
        sync_percentage = (total_sync / total_records * 100) if total_records > 0 else 0
        
        print(f"\n总记录数（三个字段都有值）: {total_records}")
        print(f"同步记录数（三个值相同）: {total_sync} ({sync_percentage:.2f}%)")
        print(f"异步记录数（三个值不完全相同）: {async_count} ({async_percentage:.2f}%)")
        
        # 5. 分析具体的异步组合案例
        print("\n【5. 异步组合案例（三个值不完全相同）】")
        query = text("""
            SELECT servrity, emergency_level, priority, COUNT(*) as cnt
            FROM tit10_maintenanceday
            WHERE servrity IS NOT NULL 
              AND emergency_level IS NOT NULL 
              AND priority IS NOT NULL
              AND NOT (servrity = emergency_level AND emergency_level = priority)
            GROUP BY servrity, emergency_level, priority
            ORDER BY cnt DESC
        """)
        async_dist = target_session.execute(query).fetchall()
        
        print(f"\n{'严重程度':<12} {'紧急程度':<12} {'优先级':<12} {'数量':<15}")
        print("-" * 51)
        for row in async_dist:
            sv, em, pr, cnt = row
            print(f"{str(sv):<12} {str(em):<12} {str(pr):<12} {str(cnt):<15}")
        
        # 6. 检查部分同步情况（两个值相同）
        print("\n【6. 部分同步情况分析】")
        
        query = text("""
            SELECT COUNT(*) as cnt
            FROM tit10_maintenanceday
            WHERE servrity IS NOT NULL 
              AND emergency_level IS NOT NULL 
              AND priority IS NOT NULL
              AND servrity = emergency_level 
              AND emergency_level != priority
        """)
        sv_em_sync = target_session.execute(query).scalar()
        
        query = text("""
            SELECT COUNT(*) as cnt
            FROM tit10_maintenanceday
            WHERE servrity IS NOT NULL 
              AND emergency_level IS NOT NULL 
              AND priority IS NOT NULL
              AND servrity != emergency_level 
              AND emergency_level = priority
        """)
        em_pr_sync = target_session.execute(query).scalar()
        
        query = text("""
            SELECT COUNT(*) as cnt
            FROM tit10_maintenanceday
            WHERE servrity IS NOT NULL 
              AND emergency_level IS NOT NULL 
              AND priority IS NOT NULL
              AND servrity = priority 
              AND servrity != emergency_level
        """)
        sv_pr_sync = target_session.execute(query).scalar()
        
        print(f"\n严重程度=紧急程度≠优先级: {sv_em_sync} ({sv_em_sync/total_records*100:.2f}%)" if total_records > 0 else "")
        print(f"紧急程度=优先级≠严重程度: {em_pr_sync} ({em_pr_sync/total_records*100:.2f}%)" if total_records > 0 else "")
        print(f"严重程度=优先级≠紧急程度: {sv_pr_sync} ({sv_pr_sync/total_records*100:.2f}%)" if total_records > 0 else "")
        
        # 7. 结论和建议
        print("\n【7. 结论和建议】")
        print(f"\n同步使用比例: {sync_percentage:.2f}%")
        print(f"异步使用比例: {async_percentage:.2f}%")
        
        if sync_percentage > 80:
            print("\n建议: 三个字段高度同步（同步比例>80%），可以考虑合并为单一字典类型")
        elif sync_percentage > 50:
            print("\n建议: 三个字段部分同步（同步比例50-80%），需要根据具体业务场景决定是否合并")
        else:
            print("\n建议: 三个字段主要异步使用（同步比例<50%），应保持独立的字典类型")
        
        target_session.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_priority_fields()
