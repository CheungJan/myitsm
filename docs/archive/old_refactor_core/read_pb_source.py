# -*- coding: utf-8 -*-
"""
读取PB源码文件并提取SQL信息
"""

import re
import sys

def read_pb_file(filepath):
    """读取PB文件并返回文本内容"""
    with open(filepath, 'rb') as f:
        content = f.read()
    # 跳过文件头的二进制部分，找到$PBExportHeader$
    header_idx = content.find(b'$PBExportHeader$')
    if header_idx >= 0:
        content = content[header_idx:]
    return content.decode('utf-8', errors='ignore')

def extract_sql_from_srd(content):
    """从DataWindow文件(.srd)中提取SQL"""
    # 查找table(...)部分
    table_match = re.search(r'table\((.*?)\)', content, re.DOTALL | re.IGNORECASE)
    if table_match:
        table_section = table_match.group(1)
        # 提取SELECT语句（支持多行）
        select_match = re.search(r'select\s+.*?from\s+[\w\s\.,=:\'"()]+', table_section, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(0).strip()
        # 如果没找到完整SELECT，返回整个table部分
        return table_section[:500]
    return None

def extract_columns_from_srd(content):
    """从DataWindow文件中提取列定义"""
    columns = []
    # 查找column=(...)定义
    for match in re.finditer(r'column=\(type=(\w+)(?:\((\d+)\))?.*?name=(\w+)', content):
        col_type = match.group(1)
        col_size = match.group(2) or ''
        col_name = match.group(3)
        columns.append((col_name, col_type, col_size))
    return columns

def main():
    files_to_check = [
        # TIT15相关（itsm.pbl）- 通过Grep搜索TIT15/EQUIPMENT_RENOVATE识别的9个文件
        (r'e:\project\myitsm\src\itsm.pbl\w_r_itsm_renovate.srw', 'TIT15翻新单窗口'),
        (r'e:\project\myitsm\src\itsm.pbl\w_r_itsm_d2d.srw', 'TIT15上门服务窗口'),
        (r'e:\project\myitsm\src\itsm.pbl\u_itsm_renovate.sru', 'TIT15翻新单UserObject'),
        (r'e:\project\myitsm\src\itsm.pbl\d_renovat_report.srd', 'TIT15翻新报表'),
        (r'e:\project\myitsm\src\itsm.pbl\d_maintenance_renovate_one.srd', 'TIT15翻新单详情'),
        (r'e:\project\myitsm\src\itsm.pbl\d_maintenance_renovate_list.srd', 'TIT15翻新单列表'),
        (r'e:\project\myitsm\src\itsm.pbl\d_maintenance_renovate_free.srd', 'TIT15翻新设备查询'),
        (r'e:\project\myitsm\src\itsm.pbl\d_itsm_renovate_list.srd', 'TIT15设备列表'),
        (r'e:\project\myitsm\src\itsm.pbl\d_itsm_renovate_free.srd', 'TIT15设备查询'),
        # TIT17相关（itsm02.pbl）
        (r'e:\project\myitsm\src\itsm02.pbl\d_itsm_maintenance_daily_form.srd', 'TIT17_MAINTENANCE表单'),
        (r'e:\project\myitsm\src\itsm02.pbl\d_itsm_cust_pos_daily_form.srd', 'TIT17_CUST_POS_DAILY表单'),
        # TIT23相关（itsm02.pbl）
        (r'e:\project\myitsm\src\itsm02.pbl\d_maintenance_daily_d2d_form.srd', 'TIT23_MAINTENANCE_D2D表单'),
    ]
    
    for filepath, desc in files_to_check:
        print(f"\n{'='*60}")
        print(f"文件: {desc}")
        print(f"路径: {filepath}")
        print('='*60)
        
        try:
            content = read_pb_file(filepath)
            
            # 提取SQL
            sql = extract_sql_from_srd(content)
            if sql:
                print(f"\n[SQL]\n{sql[:500]}")
            
            # 提取列定义
            columns = extract_columns_from_srd(content)
            if columns:
                print(f"\n[列定义] ({len(columns)}列)")
                for col_name, col_type, col_size in columns[:10]:
                    size_str = f"({col_size})" if col_size else ""
                    print(f"  {col_name}: {col_type}{size_str}")
                if len(columns) > 10:
                    print(f"  ... 还有{len(columns)-10}列")
                    
        except Exception as e:
            print(f"错误: {e}")

if __name__ == '__main__':
    main()
