#!/usr/bin/env python3
"""检查 tmc02_menusdt 表数据与前端菜单配置的一致性"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cheungjan@localhost:5432/myitsm")

def check_menu_data():
    """检查菜单数据"""
    print(f"数据库连接: {DATABASE_URL}")
    print(f"检查时间: {datetime.now()}")
    print("=" * 80)
    
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 1. 查询总记录数
        print("\n【1. 总记录数统计】")
        total_count = session.execute(text("SELECT COUNT(*) FROM tmc02_menusdt WHERE useflg = '1'")).scalar()
        print(f"tmc02_menusdt 表有效记录总数: {total_count}")
        print(f"前端配置的功能模块总数: 73")
        print(f"匹配状态: {'✅ 匹配' if total_count == 73 else '❌ 不匹配'}")
        
        # 2. 查询各菜单下的功能模块数量
        print("\n【2. 各菜单功能模块统计】")
        query = text("""
            SELECT menu_cd, COUNT(*) as func_count 
            FROM tmc02_menusdt 
            WHERE useflg = '1' 
            GROUP BY menu_cd 
            ORDER BY menu_cd
        """)
        results = session.execute(query).fetchall()
        
        # 前端配置的期望数量
        expected_counts = {
            'system': 6,
            'master': 7,
            'warehouse': 6,
            'procurement': 6,
            'itsm': 10,
            'sales': 4,
            'qc': 3,
            'transactions': 2,
            'portal': 3,
            'sla': 2,
            'notification': 2,
            'contract': 2,
            'billing': 2,
            'finance': 5,
            'deposit': 3,
            'attendance': 2,
            'inventory': 3,
            'mes': 4,
            'iot': 4,
            'reports': 1
        }
        
        db_counts = {row[0]: row[1] for row in results}
        
        print(f"{'菜单编码':<15} {'数据库数量':<12} {'前端配置':<12} {'匹配状态':<10}")
        print("-" * 60)
        
        match_count = 0
        mismatch_count = 0
        missing_in_db = []
        extra_in_db = []
        
        for menu_cd in sorted(expected_counts.keys()):
            db_count = db_counts.get(menu_cd, 0)
            expected_count = expected_counts[menu_cd]
            status = '✅ 匹配' if db_count == expected_count else '❌ 不匹配'
            
            if db_count == expected_count:
                match_count += 1
            elif db_count == 0:
                missing_in_db.append(menu_cd)
                mismatch_count += 1
            else:
                extra_in_db.append(menu_cd)
                mismatch_count += 1
            
            print(f"{menu_cd:<15} {db_count:<12} {expected_count:<12} {status:<10}")
        
        # 检查数据库中有多余的菜单
        for menu_cd in db_counts:
            if menu_cd not in expected_counts:
                print(f"{menu_cd:<15} {db_counts[menu_cd]:<12} {'N/A':<12} {'⚠️  额外':<10}")
                extra_in_db.append(menu_cd)
                mismatch_count += 1
        
        # 3. 详细功能模块列表
        print("\n【3. 详细功能模块列表】")
        query = text("""
            SELECT menu_cd, func_cd, func_nm 
            FROM tmc02_menusdt 
            WHERE useflg = '1' 
            ORDER BY menu_cd, func_cd
        """)
        results = session.execute(query).fetchall()
        
        current_menu = None
        for row in results:
            menu_cd, func_cd, func_nm = row
            if menu_cd != current_menu:
                if current_menu is not None:
                    print()
                print(f"\n{menu_cd}:")
                current_menu = menu_cd
            print(f"  - {func_cd}: {func_nm}")
        
        # 4. 总结
        print("\n" + "=" * 80)
        print("【4. 总结】")
        print(f"匹配菜单数: {match_count}/{len(expected_counts)}")
        print(f"不匹配菜单数: {mismatch_count}")
        if missing_in_db:
            print(f"数据库缺失菜单: {', '.join(missing_in_db)}")
        if extra_in_db:
            print(f"数据库额外菜单: {', '.join(extra_in_db)}")
        
        if total_count == 73 and mismatch_count == 0:
            print("\n✅ 数据库数据与前端配置完全匹配")
        else:
            print(f"\n❌ 数据库数据与前端配置不匹配")
            print(f"   前端配置: 73个功能模块")
            print(f"   数据库实际: {total_count}个功能模块")
            print(f"   差异: {73 - total_count}个")
        
        session.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_menu_data()
