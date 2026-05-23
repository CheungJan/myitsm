#!/usr/bin/env python3
"""检查菜单表结构：tmc01_menus 和 tmc02_menusdt 的关系"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cheungjan@localhost:5432/myitsm")

def check_menu_structure():
    """检查菜单表结构"""
    print(f"数据库连接: {DATABASE_URL}")
    print(f"检查时间: {datetime.now()}")
    print("=" * 80)
    
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 1. 查询 tmc01_menus 表（一级菜单）
        print("\n【1. tmc01_menus 表数据（一级菜单）】")
        query = text("""
            SELECT menu_cd, menu_nm, menu_order, useflg 
            FROM tmc01_menus 
            WHERE useflg = '1' 
            ORDER BY menu_order
        """)
        results = session.execute(query).fetchall()
        
        print(f"一级菜单总数: {len(results)}")
        print(f"{'menu_cd':<15} {'menu_nm':<20} {'menu_order':<10} {'useflg':<8}")
        print("-" * 60)
        for row in results:
            menu_cd, menu_nm, menu_order, useflg = row
            print(f"{menu_cd:<15} {menu_nm:<20} {menu_order or '':<10} {useflg:<8}")
        
        # 2. 查询 tmc02_menusdt 表（菜单明细）
        print("\n【2. tmc02_menusdt 表数据（菜单明细）】")
        query = text("""
            SELECT menu_cd, func_cd, func_nm, useflg 
            FROM tmc02_menusdt 
            WHERE useflg = '1' 
            ORDER BY menu_cd, func_cd
        """)
        results = session.execute(query).fetchall()
        
        print(f"菜单明细总数: {len(results)}")
        print(f"{'menu_cd':<20} {'func_cd':<15} {'func_nm':<20} {'useflg':<8}")
        print("-" * 80)
        
        # 按menu_cd分组统计
        from collections import defaultdict
        menu_groups = defaultdict(list)
        for row in results:
            menu_cd, func_cd, func_nm, useflg = row
            menu_groups[menu_cd].append((func_cd, func_nm))
        
        for menu_cd in sorted(menu_groups.keys()):
            print(f"\n{menu_cd} ({len(menu_groups[menu_cd])} 个操作):")
            for func_cd, func_nm in menu_groups[menu_cd]:
                print(f"  - {func_cd}: {func_nm}")
        
        # 3. 分析表结构关系
        print("\n【3. 表结构关系分析】")
        print("tmc01_menus (一级菜单表)")
        print("  - menu_cd: 菜单编码（如system, master）")
        print("  - menu_nm: 菜单名称")
        print("  - menu_ord: 排序号")
        print("  - 关联: tmc02_menusdt.menu_cd (外键)")
        
        print("\ntmc02_menusdt (菜单明细表)")
        print("  - menu_cd: 菜单编码（外键关联 tmc01_menus.menu_cd）")
        print("  - func_cd: 功能编码/操作编码（如view, create, edit, delete）")
        print("  - func_nm: 功能名称/操作名称")
        print("  - useflg: 有效标志")
        
        print("\n【4. 前端配置 vs 数据库结构对比】")
        print("前端配置结构:")
        print("  - 一级菜单: menu_cd, menu_nm, children[]")
        print("  - 二级菜单: menu_cd, menu_nm, path")
        print("  - 总计: 21个一级菜单 + 73个二级菜单")
        
        print("\n数据库表结构:")
        print("  - tmc01_menus: 一级菜单表")
        print("  - tmc02_menusdt: 菜单明细表（存储每个菜单的操作权限）")
        print("  - 当前数据: ?个一级菜单 + 135个操作权限")
        
        print("\n【5. 结论】")
        print("数据库表设计与前端配置结构不同：")
        print("- 数据库: 菜单 -> 操作权限（细粒度权限控制）")
        print("- 前端: 菜单 -> 子菜单（页面导航结构）")
        print("两者不是一一对应关系，需要重新设计对比逻辑")
        
        session.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_menu_structure()
