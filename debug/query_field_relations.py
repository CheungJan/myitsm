#!/usr/bin/env python3
"""查询 tmm22_customers 字段的关联表信息"""

from sqlalchemy import create_engine, text

# 数据库连接
target_url = "postgresql://cheungjan@localhost:5432/myitsm"
tgt_engine = create_engine(target_url)

print(f"{'='*60}")
print("查询 tmm22_customers 字段的关联表信息")
print(f"{'='*60}")

# 需要查询的字段及其可能的关联表
field_relations = {
    "zf_type": "支付方式",
    "comm_mode": "通讯方式", 
    "area": "区域",
    "location": "位置",
    "ppt_code": "门店属性"
}

with tgt_engine.connect() as conn:
    # 1. 查询 tmm31_syscodes 表结构（系统编码表）
    print(f"\n{'='*60}")
    print("tmm31_syscodes 表结构")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'tmm31_syscodes'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]:20} {row[1]:20} {row[2] if row[2] else ''}")
    
    # 2. 查询 tmm31_syscodes 中的代码类型
    print(f"\n{'='*60}")
    print("tmm31_syscodes 代码类型分布")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT code_typ, COUNT(*) as cnt
        FROM tmm31_syscodes
        GROUP BY code_typ
        ORDER BY code_typ
    """))
    for row in result:
        print(f"  代码类型: {row[0]:10} 数量: {row[1]}")
    
    # 3. 查询 ZF 类型代码（支付方式）
    print(f"\n{'='*60}")
    print("ZF 类型代码（支付方式）")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT code_cd, code_nm
        FROM tmm31_syscodes
        WHERE code_typ = 'ZF'
        ORDER BY code_cd
    """))
    for row in result:
        print(f"  {row[0]:10} {row[1]}")
    
    # 4. 查询 YB 类型代码（门店属性）
    print(f"\n{'='*60}")
    print("YB 类型代码（门店属性）")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT code_cd, code_nm
        FROM tmm31_syscodes
        WHERE code_typ = 'YB'
        ORDER BY code_cd
    """))
    for row in result:
        print(f"  {row[0]:10} {row[1]}")
    
    # 5. 查询 tmm47_commode 表结构（通讯方式）
    print(f"\n{'='*60}")
    print("tmm47_commode 表结构（通讯方式）")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'tmm47_commode'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]:20} {row[1]:20} {row[2] if row[2] else ''}")
    
    # 6. 查询通讯方式数据
    print(f"\n{'='*60}")
    print("tmm47_commode 数据示例")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT cmm_cd, cmm_nm
        FROM tmm47_commode
        ORDER BY cmm_cd
        LIMIT 10
    """))
    for row in result:
        print(f"  {row[0]:10} {row[1]}")
    
    # 7. 查询 tmm46_area 表结构（区域）
    print(f"\n{'='*60}")
    print("tmm46_area 表结构（区域）")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'tmm46_area'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]:20} {row[1]:20} {row[2] if row[2] else ''}")
    
    # 8. 查询区域数据
    print(f"\n{'='*60}")
    print("tmm46_area 数据示例")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT area_cd, area_nm
        FROM tmm46_area
        ORDER BY area_cd
        LIMIT 10
    """))
    for row in result:
        print(f"  {row[0]:10} {row[1]}")
    
    # 9. 查询 tmm31_syscodes 中的业务类型代码
    print(f"\n{'='*60}")
    print("业务类型代码（假设是 BT 类型）")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT code_cd, code_nm
        FROM tmm31_syscodes
        WHERE code_typ = 'BT'
        ORDER BY code_cd
    """))
    for row in result:
        print(f"  {row[0]:10} {row[1]}")
    
    # 10. 查询所有可能的业务类型代码类型
    print(f"\n{'='*60}")
    print("可能的业务类型代码类型")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT code_typ, COUNT(*) as cnt
        FROM tmm31_syscodes
        WHERE code_typ LIKE '%B%' OR code_typ LIKE '%T%'
        GROUP BY code_typ
        ORDER BY code_typ
    """))
    for row in result:
        print(f"  代码类型: {row[0]:10} 数量: {row[1]}")
    
    # 11. 查询 tmm22_customers 中的 busi_typ 值分布
    print(f"\n{'='*60}")
    print("tmm22_customers 中 busi_typ 值分布")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT busi_typ, COUNT(*) as cnt
        FROM tmm22_customers
        WHERE busi_typ IS NOT NULL
        GROUP BY busi_typ
        ORDER BY busi_typ
    """))
    for row in result:
        print(f"  {row[0]:10} 数量: {row[1]}")
    
    # 12. 查询 tmm22_customers 中的 area 值分布
    print(f"\n{'='*60}")
    print("tmm22_customers 中 area 值分布")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT area, COUNT(*) as cnt
        FROM tmm22_customers
        WHERE area IS NOT NULL
        GROUP BY area
        ORDER BY area
        LIMIT 20
    """))
    for row in result:
        print(f"  {row[0]:10} 数量: {row[1]}")
    
    # 13. 查询 tmm46_area 的完整数据
    print(f"\n{'='*60}")
    print("tmm46_area 完整数据")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT area_id, area_cd, area_nm, name
        FROM tmm46_area
        ORDER BY area_id
    """))
    for row in result:
        area_id = row[0] if row[0] is not None else ""
        area_cd = row[1] if row[1] is not None else ""
        area_nm = row[2] if row[2] is not None else ""
        name = row[3] if row[3] is not None else ""
        print(f"  area_id: {area_id:5} area_cd: {area_cd:10} area_nm: {area_nm:20} name: {name}")
    
    # 14. 查询 tmm22_customers 中的 location 值分布
    print(f"\n{'='*60}")
    print("tmm22_customers 中 location 值分布")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT location, COUNT(*) as cnt
        FROM tmm22_customers
        WHERE location IS NOT NULL
        GROUP BY location
        ORDER BY location
    """))
    for row in result:
        print(f"  {row[0]:10} 数量: {row[1]}")
    
    # 15. 查询 tmm22_customers 中的 posstatus 值分布
    print(f"\n{'='*60}")
    print("tmm22_customers 中 posstatus 值分布")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT posstatus, COUNT(*) as cnt
        FROM tmm22_customers
        WHERE posstatus IS NOT NULL
        GROUP BY posstatus
        ORDER BY posstatus
    """))
    for row in result:
        print(f"  {row[0]:10} 数量: {row[1]}")
    
    # 16. 查询 tmm22_customers 中的 posstatus1 值分布
    print(f"\n{'='*60}")
    print("tmm22_customers 中 posstatus1 值分布")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT posstatus1, COUNT(*) as cnt
        FROM tmm22_customers
        WHERE posstatus1 IS NOT NULL
        GROUP BY posstatus1
        ORDER BY posstatus1
    """))
    for row in result:
        print(f"  {row[0]:10} 数量: {row[1]}")
    
    # 17. 查询 tmm31_syscodes 中可能的 POS 状态代码类型
    print(f"\n{'='*60}")
    print("可能的 POS 状态代码类型")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT code_typ, COUNT(*) as cnt
        FROM tmm31_syscodes
        WHERE code_typ LIKE '%P%' OR code_typ LIKE '%S%' OR code_typ LIKE '%O%'
        GROUP BY code_typ
        ORDER BY code_typ
    """))
    for row in result:
        print(f"  代码类型: {row[0]:10} 数量: {row[1]}")
    
    # 18. 查询 tmm52_posstatus 表结构
    print(f"\n{'='*60}")
    print("tmm52_posstatus 表结构")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'tmm52_posstatus'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]:20} {row[1]:20} {row[2] if row[2] else ''}")
    
    # 19. 查询幽灵用户优化字段的值分布
    print(f"\n{'='*60}")
    print("幽灵用户优化字段值分布")
    print(f"{'='*60}")
    
    # customer_status
    print("\ncustomer_status 值分布:")
    result = conn.execute(text("""
        SELECT customer_status, COUNT(*) as cnt
        FROM tmm22_customers
        WHERE customer_status IS NOT NULL
        GROUP BY customer_status
        ORDER BY customer_status
    """))
    for row in result:
        print(f"  {row[0]:20} 数量: {row[1]}")
    
    # source_type
    print("\nsource_type 值分布:")
    result = conn.execute(text("""
        SELECT source_type, COUNT(*) as cnt
        FROM tmm22_customers
        WHERE source_type IS NOT NULL
        GROUP BY source_type
        ORDER BY source_type
    """))
    for row in result:
        print(f"  {row[0]:20} 数量: {row[1]}")
    
    # verified_at
    print("\nverified_at 值分布（有值的记录数）:")
    result = conn.execute(text("""
        SELECT COUNT(*) as cnt
        FROM tmm22_customers
        WHERE verified_at IS NOT NULL
    """))
    for row in result:
        print(f"  有值的记录数: {row[0]}")
    
    # preplan_id
    print("\npreplan_id 值分布:")
    result = conn.execute(text("""
        SELECT preplan_id, COUNT(*) as cnt
        FROM tmm22_customers
        WHERE preplan_id IS NOT NULL
        GROUP BY preplan_id
        ORDER BY preplan_id
        LIMIT 10
    """))
    for row in result:
        print(f"  {row[0]:30} 数量: {row[1]}")
    
    # valid_until
    print("\nvalid_until 值分布（有值的记录数）:")
    result = conn.execute(text("""
        SELECT COUNT(*) as cnt
        FROM tmm22_customers
        WHERE valid_until IS NOT NULL
    """))
    for row in result:
        print(f"  有值的记录数: {row[0]}")
    
    # 20. 查询 tmm21_custclass 表结构和数据（分析层级关系问题）
    print(f"\n{'='*60}")
    print("tmm21_custclass 表结构")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'tmm21_custclass'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]:20} {row[1]:20} {row[2] if row[2] else ''}")
    
    print(f"\n{'='*60}")
    print("tmm21_custclass 数据（含父子关系）")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT class_cd, class_nm, parent_cd, useflg
        FROM tmm21_custclass
        ORDER BY class_cd
    """))
    for row in result:
        class_cd = row[0] if row[0] is not None else ""
        class_nm = row[1] if row[1] is not None else ""
        parent_cd = row[2] if row[2] is not None else ""
        useflg = row[3] if row[3] is not None else ""
        print(f"  class_cd: {class_cd:10} class_nm: {class_nm:20} parent_cd: {parent_cd:10} useflg: {useflg}")
    
    print(f"\n{'='*60}")
    print("测试和耳机目录的父子关系")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT 
            c1.class_cd as 子目录代码,
            c1.class_nm as 子目录名称,
            c1.parent_cd as 父目录代码,
            c2.class_nm as 父目录名称
        FROM tmm21_custclass c1
        LEFT JOIN tmm21_custclass c2 ON c1.parent_cd = c2.class_cd
        WHERE c1.class_nm LIKE '%测试%' OR c1.class_nm LIKE '%耳机%'
        ORDER BY c1.class_cd
    """))
    for row in result:
        子目录代码 = row[0] if row[0] is not None else ""
        子目录名称 = row[1] if row[1] is not None else ""
        父目录代码 = row[2] if row[2] is not None else ""
        父目录名称 = row[3] if row[3] is not None else ""
        print(f"  子目录: {子目录代码:10} {子目录名称:20} 父目录: {父目录代码:10} {父目录名称:20}")
    
    # 21. 查询关联到耳机目录的客户数据
    print(f"\n{'='*60}")
    print("关联到耳机目录（tt02）的客户数据")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT 
            cust_cd,
            cust_nm,
            class_cd,
            parentcd
        FROM tmm22_customers
        WHERE class_cd = 'tt02'
        ORDER BY cust_cd
    """))
    for row in result:
        cust_cd = row[0] if row[0] is not None else ""
        cust_nm = row[1] if row[1] is not None else ""
        class_cd = row[2] if row[2] is not None else ""
        parentcd = row[3] if row[3] is not None else ""
        print(f"  客户代码: {cust_cd:10} 客户名称: {cust_nm:20} 分类: {class_cd:10} 上级: {parentcd}")
    
    # 22. 查询关联到test一级目录（tt）的客户数据
    print(f"\n{'='*60}")
    print("关联到test一级目录（tt）的客户数据")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT 
            cust_cd,
            cust_nm,
            class_cd,
            parentcd
        FROM tmm22_customers
        WHERE class_cd = 'tt'
        ORDER BY cust_cd
    """))
    for row in result:
        cust_cd = row[0] if row[0] is not None else ""
        cust_nm = row[1] if row[1] is not None else ""
        class_cd = row[2] if row[2] is not None else ""
        parentcd = row[3] if row[3] is not None else ""
        print(f"  客户代码: {cust_cd:10} 客户名称: {cust_nm:20} 分类: {class_cd:10} 上级: {parentcd}")
    
    # 23. 查询通过 tmm21_custclass 关联的父子关系（用户的期望逻辑）
    print(f"\n{'='*60}")
    print("通过 tmm21_custclass 关联的父子关系（用户期望逻辑）")
    print(f"{'='*60}")
    result = conn.execute(text("""
        SELECT 
            c.cust_cd as 客户代码,
            c.cust_nm as 客户名称,
            c.class_cd as 客户分类代码,
            cc.class_nm as 客户分类名称,
            cc.parent_cd as 父分类代码,
            pcc.class_nm as 父分类名称
        FROM tmm22_customers c
        LEFT JOIN tmm21_custclass cc ON c.class_cd = cc.class_cd
        LEFT JOIN tmm21_custclass pcc ON cc.parent_cd = pcc.class_cd
        WHERE c.class_cd IN ('tt', 'tt02')
        ORDER BY c.cust_cd
    """))
    for row in result:
        客户代码 = row[0] if row[0] is not None else ""
        客户名称 = row[1] if row[1] is not None else ""
        客户分类代码 = row[2] if row[2] is not None else ""
        客户分类名称 = row[3] if row[3] is not None else ""
        父分类代码 = row[4] if row[4] is not None else ""
        父分类名称 = row[5] if row[5] is not None else ""
        print(f"  客户: {客户代码:10} {客户名称:20}")
        print(f"    分类: {客户分类代码:10} {客户分类名称:20}")
        print(f"    父分类: {父分类代码:10} {父分类名称:20}")
    
    # 24. 查询地理区域表是否存在（tmm01-tmm05）
    print(f"\n{'='*60}")
    print("地理区域表检查（国家→省份→城市→城镇）")
    print(f"{'='*60}")
    
    tables = ['tmm01_continent', 'tmm02_country', 'tmm03_province', 'tmm04_city', 'tmm05_town']
    for table in tables:
        try:
            result = conn.execute(text(f"""
                SELECT COUNT(*) FROM {table}
            """))
            count = result.scalar()
            print(f"  {table:20} 存在，记录数: {count}")
        except Exception as e:
            print(f"  {table:20} 不存在或无法访问")
    
    # 25. 查询客户表中是否有地理区域相关字段
    print(f"\n{'='*60}")
    print("客户表中地理区域相关字段")
    print(f"{'='*60}")
    try:
        result = conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'tmm22_customers'
              AND (column_name LIKE '%cd%'
                   OR column_name LIKE '%country%'
                   OR column_name LIKE '%province%'
                   OR column_name LIKE '%city%'
                   OR column_name LIKE '%town%')
            ORDER BY column_name
        """))
        for row in result:
            print(f"  {row[0]:20} {row[1]:20}")
    except Exception as e:
        print(f"  查询出错: {e}")

tgt_engine.dispose()
