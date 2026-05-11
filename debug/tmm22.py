import os
from pathlib import Path
from sqlalchemy import create_engine, text, inspect

# 加载 .env 文件
env_file = Path("/Users/cheungjan/myitsm/.env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# 数据库连接配置
source_url = os.getenv("SOURCE_DATABASE_URL", "postgresql://cheungjan@localhost:5432/ortopbitsmdb")
target_url = os.getenv("DATABASE_URL", "postgresql://cheungjan@localhost:5432/myitsm")

print(f"源数据库: {source_url}")
print(f"目标数据库: {target_url}")

# 创建引擎
src_engine = create_engine(source_url)
tgt_engine = create_engine(target_url)

def get_table_columns(engine, table_name):
    """获取表的列信息"""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return columns

def print_table_structure(db_name, engine, table_name):
    """打印表结构"""
    print(f"\n{'='*60}")
    print(f"{db_name} - {table_name} 表结构")
    print(f"{'='*60}")
    
    try:
        columns = get_table_columns(engine, table_name)
        print(f"{'字段名':<25} {'类型':<20} {'长度':<10} {'可空':<10}")
        print("-" * 80)
        for col in columns:
            length = str(col['type'].length) if hasattr(col['type'], 'length') else ''
            nullable = 'YES' if col['nullable'] else 'NO'
            print(f"{col['name']:<25} {str(col['type'])[:20]:<20} {length:<10} {nullable:<10}")
    except Exception as e:
        print(f"错误: {e}")

# 查询表结构
print_table_structure("ortopbitsmdb", src_engine, "tmm22_customers")
print_table_structure("myitsm", tgt_engine, "tmm22_customers")
print_table_structure("ortopbitsmdb", src_engine, "tmm21_custclass")
print_table_structure("myitsm", tgt_engine, "tmm21_custclass")

# 对比字段差异
print(f"\n{'='*60}")
print("字段对比分析")
print(f"{'='*60}")

def compare_columns(src_columns, tgt_columns):
    """对比字段差异"""
    src_names = {col['name'] for col in src_columns}
    tgt_names = {col['name'] for col in tgt_columns}
    
    only_in_src = src_names - tgt_names
    only_in_tgt = tgt_names - src_names
    common = src_names & tgt_names
    
    return only_in_src, only_in_tgt, common

src_customers = get_table_columns(src_engine, "tmm22_customers")
tgt_customers = get_table_columns(tgt_engine, "tmm22_customers")

only_src, only_tgt, common = compare_columns(src_customers, tgt_customers)

print("\ntmm22_customers 字段对比:")
if only_src:
    print(f"  仅在 ortopbitsmdb 中: {only_src}")
if only_tgt:
    print(f"  仅在 myitsm 中: {only_tgt}")
print(f"  共同字段数量: {len(common)}")

# 特别检查 PARENTCD/parent_cd 字段
print("\n关键字段 PARENTCD/parent_cd 检查:")
src_has_parent = any(col['name'] in ['parentcd', 'parent_cd'] for col in src_customers)
tgt_has_parent = any(col['name'] in ['parentcd', 'parent_cd'] for col in tgt_customers)
print(f"  ortopbitsmdb 有 PARENTCD/parent_cd: {src_has_parent}")
print(f"  myitsm 有 PARENTCD/parent_cd: {tgt_has_parent}")

# 查询 myitsm 中 classcd 字段的数据情况
print(f"\n{'='*60}")
print("myitsm 数据检查")
print(f"{'='*60}")

with tgt_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) as total FROM tmm22_customers"))
    total = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as null_count FROM tmm22_customers WHERE class_cd IS NULL"))
    null_count = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as has_class FROM tmm22_customers WHERE class_cd IS NOT NULL"))
    has_class = result.scalar()
    
    print(f"\ntmm22_customers class_cd 字段数据统计:")
    print(f"  总记录数: {total}")
    print(f"  class_cd 为 NULL: {null_count}")
    print(f"  class_cd 有值: {has_class}")
    
    if has_class > 0:
        result = conn.execute(text("""
            SELECT DISTINCT class_cd, COUNT(*) as count
            FROM tmm22_customers
            WHERE class_cd IS NOT NULL
            GROUP BY class_cd
            ORDER BY class_cd
            LIMIT 10
        """))
        print(f"\n  class_cd 分类分布示例:")
        for row in result:
            print(f"    {row[0]}: {row[1]} 个客户")

# 查询 ortopbitsmdb 中 parentcd 关联到 tmm21_custclass.classcd 的情况
print(f"\n{'='*60}")
print("ortopbitsmdb 数据检查")
print(f"{'='*60}")

with src_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) as total FROM tmm22_customers"))
    total = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as null_parentcd FROM tmm22_customers WHERE parentcd IS NULL"))
    null_parentcd = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as has_parentcd FROM tmm22_customers WHERE parentcd IS NOT NULL"))
    has_parentcd = result.scalar()
    
    print(f"\ntmm22_customers parentcd 字段数据统计:")
    print(f"  总记录数: {total}")
    print(f"  parentcd 为 NULL: {null_parentcd}")
    print(f"  parentcd 有值: {has_parentcd}")
    
    if has_parentcd > 0:
        # 先查询 tmm21_custclass 的所有 classcd
        result = conn.execute(text("SELECT classcd, classnm FROM tmm21_custclass ORDER BY classcd"))
        custclass_map = {row[0]: row[1] for row in result}
        print(f"\n  tmm21_custclass 分类表内容:")
        for classcd, classnm in custclass_map.items():
            print(f"    classcd={classcd}, classnm={classnm}")
        
        # 查询 parentcd 与 classcd 的匹配情况
        result = conn.execute(text("""
            SELECT DISTINCT c.parentcd, COUNT(*) as count
            FROM tmm22_customers c
            WHERE c.parentcd IS NOT NULL
            GROUP BY c.parentcd
            ORDER BY c.parentcd
            LIMIT 15
        """))
        print(f"\n  parentcd 字段值分布:")
        for row in result:
            classnm = custclass_map.get(row[0].strip(), "未匹配")
            print(f"    parentcd={row[0]}, 分类名={classnm}, 客户数={row[1]}")
    
    # 查询 custCard 为 null 的记录
    result = conn.execute(text("SELECT COUNT(*) as null_custcard FROM tmm22_customers WHERE custcard IS NULL"))
    null_custcard = result.scalar()
    
    print(f"\n  custCard 为 NULL 的记录数: {null_custcard}")
    
    if null_custcard > 0:
        result = conn.execute(text("""
            SELECT custcd, custnm, parentcd, classcd, custcard
            FROM tmm22_customers
            WHERE custcard IS NULL
            LIMIT 10
        """))
        print(f"\n  custCard 为 NULL 的记录示例:")
        for row in result:
            print(f"    custcd={row[0]}, custnm={row[1]}, parentcd={row[2]}, classcd={row[3]}, custcard={row[4]}")

# 查询 tmm21_custclass 分类表的树状结构
print(f"\n{'='*60}")
print("客户分类表 tmm21_custclass 树状结构检查")
print(f"{'='*60}")

with src_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) as total FROM tmm21_custclass"))
    total = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as null_count FROM tmm21_custclass WHERE parent IS NULL"))
    null_count = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as percent_root FROM tmm21_custclass WHERE parent = '%'"))
    percent_root = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as has_parent FROM tmm21_custclass WHERE parent IS NOT NULL AND parent != '%'"))
    has_parent = result.scalar()
    
    print(f"\nortopbitsmdb tmm21_custclass parent 字段数据统计:")
    print(f"  总记录数: {total}")
    print(f"  parent 为 NULL: {null_count}")
    print(f"  parent = '%' (根节点): {percent_root}")
    print(f"  parent 有具体值: {has_parent}")
    
    if has_parent > 0:
        result = conn.execute(text("""
            SELECT classcd, classnm, parent 
            FROM tmm21_custclass 
            WHERE parent IS NOT NULL AND parent != '%'
            ORDER BY classcd 
            LIMIT 10
        """))
        print(f"\n  parent 有具体值的记录示例:")
        for row in result:
            print(f"    {row[0]} - {row[1]} - parent: {row[2]}")

with tgt_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) as total FROM tmm21_custclass"))
    total = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as null_count FROM tmm21_custclass WHERE parent_cd IS NULL"))
    null_count = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as has_parent FROM tmm21_custclass WHERE parent_cd IS NOT NULL"))
    has_parent = result.scalar()
    
    print(f"\nmyitsm tmm21_custclass parent_cd 字段数据统计:")
    print(f"  总记录数: {total}")
    print(f"  parent_cd 为 NULL: {null_count}")
    print(f"  parent_cd 有值: {has_parent}")
    
    if has_parent > 0:
        result = conn.execute(text("""
            SELECT class_cd, class_nm, parent_cd 
            FROM tmm21_custclass 
            WHERE parent_cd IS NOT NULL 
            ORDER BY class_cd 
            LIMIT 10
        """))
        print(f"\n  parent_cd 有值的记录示例:")
        for row in result:
            print(f"    {row[0]} - {row[1]} - parent: {row[2]}")
    else:
        print(f"\n  ⚠️ myitsm 中 tmm21_custclass 的 parent_cd 数据全部为 NULL（与物料分类表相同的问题）")

# 分析 tmm22_customers 字段按业务语义分组（详细分类）
print(f"\n{'='*60}")
print("tmm22_customers 字段按业务语义分组（详细）")
print(f"{'='*60}")

with tgt_engine.connect() as conn:
    columns = get_table_columns(tgt_engine, "tmm22_customers")
    
    # 字段中文备注映射
    field_comments = {
        "cust_cd": "客户代码（系统主键）",
        "cust_nm": "客户名称",
        "cust_card": "客户磁卡号",
        "cust_anm": "客户简称",
        "custrnm": "客户别名",
        "store_cd": "门店编码",
        "class_cd": "客户分类",
        "area_cd": "区域编码",
        "parentcd": "上级客户编码",
        "address": "地址",
        "zipcd": "邮编",
        "phone_no": "电话",
        "faxno": "传真",
        "contactor": "联系人",
        "taxno": "税号",
        "banknm": "银行名称",
        "bankaccno": "银行账号",
        "yj_money": "预缴金额",
        "pos_n": "POS数量",
        "posstatus": "POS状态",
        "posstatus1": "POS状态1",
        "card3g": "3G卡号",
        "adr3g": "3G地址",
        "opersystem": "操作系统",
        "data_base": "数据库",
        "soft_edition": "软件版本",
        "systemcode": "内核版本",
        "ad_video": "广告视频",
        "opendate": "首次开通日期",
        "replacedate": "最近更换日期",
        "customer_status": "客户状态",
        "levels": "客户等级",
        "ordertype": "要货方式",
        "is_contract": "是否合同",
        "busi_typ": "业务类型（关联 tmm31_syscodes.code_typ='BT': code_cd → code_nm）",
        "source_type": "来源类型",
        "verified_at": "验证时间",
        "preplan_id": "预计划ID",
        "valid_until": "有效期至",
        "created_at": "创建时间",
        "updated_at": "更新时间",
        "useflg": "使用标志",
        "backup": "备份",
        "s_status": "状态",
        "location": "环线位置（1=内环, 2=中环, 3=外环）",
        "area": "行政区域（关联 tmm46_area.area_id → name）",
        "comm_mode": "通讯方式（关联 tmm47_commode.cmm_cd → cmm_nm）",
        "ppt_code": "门店属性（关联 tmm31_syscodes.code_typ='YB': code_cd → code_nm）",
        "zf_type": "支付方式（关联 tmm31_syscodes.code_typ='ZF': code_cd → code_nm）",
        "jl_contactor": "经理联系人",
        "jl_phoneno": "经理电话",
        "cust_brcd": "客户品牌代码"
    }
    
    # 按业务语义分组（基于建议的分类）
    field_groups = {
        "核心标识": ["cust_cd", "cust_nm", "cust_card", "cust_anm", "custrnm", "store_cd"],
        "分类层级": ["class_cd", "area_cd", "parentcd"],
        "联系信息": ["address", "zipcd", "phone_no", "faxno", "contactor"],
        "财务银行": ["taxno", "banknm", "bankaccno", "yj_money"],
        "POS配置": ["pos_n", "posstatus", "posstatus1", "card3g", "adr3g", "opersystem", "data_base", "soft_edition", "systemcode", "ad_video"],
        "生命周期": ["opendate", "replacedate", "customer_status", "levels", "ordertype", "is_contract"],
        "业务信息": ["busi_typ", "source_type", "verified_at", "preplan_id", "valid_until"],
        "系统字段": ["created_at", "updated_at", "useflg"],
        "其他字段": ["backup", "s_status", "location", "area", "comm_mode", "ppt_code", "zf_type", "jl_contactor", "jl_phoneno", "cust_brcd"]
    }
    
    for group_name, fields in field_groups.items():
        existing_fields = []
        for f in fields:
            for col in columns:
                if col['name'] == f:
                    existing_fields.append((col['name'], col['type'], col['nullable']))
                    break
        
        if existing_fields:
            print(f"\n{group_name} ({len(existing_fields)}个字段):")
            for field_name, field_type, nullable in existing_fields:
                nullable_str = "可空" if nullable else "非空"
                field_type_str = str(field_type) if field_type else ""
                comment = field_comments.get(field_name, "")
                print(f"  - {field_name:20} {field_type_str:20} {nullable_str:6} {comment}")
    
    print(f"\n未分类字段:")
    all_grouped_fields = [f for group in field_groups.values() for f in group]
    unclassified = []
    for col in columns:
        if col['name'] not in all_grouped_fields:
            unclassified.append((col['name'], col['type'], col['nullable']))
    
    for field_name, field_type, nullable in unclassified:
        nullable_str = "可空" if nullable else "非空"
        field_type_str = str(field_type) if field_type else ""
        comment = field_comments.get(field_name, "")
        print(f"  - {field_name:20} {field_type_str:20} {nullable_str:6} {comment}")

# 分析 ortopbitsmdb tmm22_customers 字段按业务语义分组
print(f"\n{'='*60}")
print("ortopbitsmdb tmm22_customers 字段按业务语义分组（详细）")
print(f"{'='*60}")

with src_engine.connect() as conn:
    columns = get_table_columns(src_engine, "tmm22_customers")
    
    # ortopbitsmdb 字段中文备注映射（使用原字段名）
    ortop_field_comments = {
        "custcd": "客户代码（系统主键）",
        "custnm": "客户名称",
        "custanm": "客户简称",
        "custbrcd": "客户品牌代码",
        "classcd": "客户分类",
        "busityp": "业务类型",
        "address": "地址",
        "zipcd": "邮编",
        "phoneno": "电话",
        "faxno": "传真",
        "contactor": "联系人",
        "taxno": "税号",
        "banknm": "银行名称",
        "bankaccno": "银行账号",
        "opercd": "操作员代码",
        "gendate": "生成日期",
        "upddate": "更新日期",
        "useflg": "使用标志",
        "parentcd": "上级客户编码",
        "custcard": "客户磁卡号",
        "backup": "备份",
        "location": "位置",
        "area": "区域",
        "pos_n": "POS数量",
        "whtransflg": "仓储传输标志",
        "sttransflg": "门店传输标志",
        "opersystem": "操作系统",
        "data_base": "数据库",
        "soft_edition": "软件版本",
        "s_status": "状态",
        "ad_video": "广告视频",
        "commmode": "通讯方式",
        "card3g": "3G卡号",
        "adr3g": "3G地址",
        "systemcode": "内核版本",
        "custrnm": "客户别名",
        "opendate": "首次开通日期",
        "replacedate": "最近更换日期",
        "levels": "客户等级",
        "ordertype": "要货方式",
        "pptcode": "门店属性",
        "jl_contactor": "经理联系人",
        "jl_phoneno": "经理电话"
    }
    
    # ortopbitsmdb 字段分组（使用原字段名）
    ortop_field_groups = {
        "核心标识": ["custcd", "custnm", "custcard", "custanm", "custrnm", "custbrcd"],
        "分类层级": ["classcd", "parentcd"],
        "联系信息": ["address", "zipcd", "phoneno", "faxno", "contactor"],
        "财务银行": ["taxno", "banknm", "bankaccno"],
        "POS配置": ["pos_n", "card3g", "adr3g", "opersystem", "data_base", "soft_edition", "systemcode", "ad_video"],
        "生命周期": ["opendate", "replacedate", "levels", "ordertype"],
        "业务信息": ["busityp"],
        "系统字段": ["opercd", "gendate", "upddate", "useflg"],
        "其他字段": ["backup", "location", "area", "whtransflg", "sttransflg", "s_status", "commmode", "pptcode", "jl_contactor", "jl_phoneno"]
    }
    
    for group_name, fields in ortop_field_groups.items():
        existing_fields = []
        for f in fields:
            for col in columns:
                if col['name'] == f:
                    existing_fields.append((col['name'], col['type'], col['nullable']))
                    break
        
        if existing_fields:
            print(f"\n{group_name} ({len(existing_fields)}个字段):")
            for field_name, field_type, nullable in existing_fields:
                nullable_str = "可空" if nullable else "非空"
                field_type_str = str(field_type) if field_type else ""
                comment = ortop_field_comments.get(field_name, "")
                print(f"  - {field_name:20} {field_type_str:20} {nullable_str:6} {comment}")
    
    print(f"\n未分类字段:")
    all_grouped_fields = [f for group in ortop_field_groups.values() for f in group]
    unclassified = []
    for col in columns:
        if col['name'] not in all_grouped_fields:
            unclassified.append((col['name'], col['type'], col['nullable']))
    
    for field_name, field_type, nullable in unclassified:
        nullable_str = "可空" if nullable else "非空"
        field_type_str = str(field_type) if field_type else ""
        comment = ortop_field_comments.get(field_name, "")
        print(f"  - {field_name:20} {field_type_str:20} {nullable_str:6} {comment}")

# 关闭连接
src_engine.dispose()
tgt_engine.dispose()