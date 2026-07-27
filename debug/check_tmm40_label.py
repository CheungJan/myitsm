#!/usr/bin/env python3
"""检查 TMM40_LABEL 表在当前数据库中的实现情况"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cheungjan@localhost:5432/myitsm")

def check_tmm40_label():
    """检查 TMM40_LABEL 表"""
    print(f"数据库连接: {DATABASE_URL}")
    print(f"检查时间: {datetime.now()}")
    print("=" * 80)
    
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 1. 检查表是否存在
        print("\n【1. 检查表是否存在】")
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'tmm40_label'
            )
        """)
        table_exists = session.execute(query).scalar()
        print(f"tmm40_label 表存在: {'是' if table_exists else '否'}")
        
        if table_exists:
            # 2. 查询表结构
            print("\n【2. 表结构】")
            query = text("""
                SELECT column_name, data_type, character_maximum_length, 
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'tmm40_label'
                ORDER BY ordinal_position
            """)
            columns = session.execute(query).fetchall()
            
            print(f"{'字段名':<20} {'数据类型':<20} {'长度':<10} {'可空':<8} {'默认值':<20}")
            print("-" * 80)
            for col in columns:
                col_name, data_type, max_length, is_nullable, default_val = col
                length = str(max_length) if max_length else ''
                print(f"{col_name:<20} {data_type:<20} {length:<10} {is_nullable:<8} {str(default_val or ''):<20}")
            
            # 3. 查询记录数
            print("\n【3. 记录统计】")
            query = text("SELECT COUNT(*) FROM tmm40_label")
            total_count = session.execute(query).scalar()
            print(f"总记录数: {total_count}")
            
            # 4. 查询示例数据
            if total_count > 0:
                print("\n【4. 示例数据】")
                query = text("SELECT * FROM tmm40_label LIMIT 5")
                sample_data = session.execute(query).fetchall()
                for row in sample_data:
                    print(row)
        else:
            print("\n【2. 表不存在】")
            print("需要创建 TMM40_LABEL 表")
        
        # 5. 检查模型定义
        print("\n【5. 检查模型定义】")
        try:
            from app.models.master import Label
            print("✅ app.models.master.Label 模型存在")
            print(f"表名: {Label.__tablename__}")
        except ImportError:
            print("❌ app.models.master.Label 模型不存在")
        
        # 6. 检查API定义
        print("\n【6. 检查API定义】")
        try:
            with open('/Users/cheungjan/myitsm/app/api/deposit.py', 'r') as f:
                content = f.read()
                if 'label' in content.lower():
                    print("✅ app/api/deposit.py 中有标签相关API")
                    # 查找标签API的具体位置
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'label' in line.lower():
                            print(f"  行 {i+1}: {line.strip()}")
                else:
                    print("❌ app/api/deposit.py 中没有标签相关API")
        except Exception as e:
            print(f"❌ 检查API时出错: {e}")
        
        session.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tmm40_label()
