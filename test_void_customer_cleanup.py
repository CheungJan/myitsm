#!/usr/bin/env python3
"""
测试预计划作废时的客户清理逻辑
验证：plan_cust表保留custcd，tmm22_customers表删除对应记录
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.extensions import db
from app.models.sales import PlanCust
from app.models.master import Customer
from app.services.sales_service import PlanCustService

def test_void_customer_cleanup():
    """测试预计划作废时的客户清理"""
    app = create_app()
    
    with app.app_context():
        print("=== 预计划作废客户清理测试 ===\n")
        
        # 1. 查找当前存在的孤儿预计划（plan_cust有记录但tmm22_customers没有）
        orphan_plans = db.session.execute("""
            SELECT pc.planno, pc.custcd, pc.custcard, pc.plan_status
            FROM plan_cust pc
            LEFT JOIN tmm22_customers tc ON pc.custcard = tc.cust_card
            WHERE tc.cust_card IS NULL
            AND pc.plan_status = '09'  -- 已作废的预计划
            LIMIT 5
        """).fetchall()
        
        print(f"当前已作废的孤儿预计划数量: {len(orphan_plans)}")
        
        if orphan_plans:
            print("示例孤儿预计划:")
            for plan in orphan_plans:
                print(f"  - {plan.planno}: custcd={plan.custcd}, custcard={plan.custcard}")
        
        # 2. 查找未作废的孤儿预计划
        active_orphan_plans = db.session.execute("""
            SELECT pc.planno, pc.custcd, pc.custcard, pc.plan_status
            FROM plan_cust pc
            LEFT JOIN tmm22_customers tc ON pc.custcard = tc.cust_card
            WHERE tc.cust_card IS NULL
            AND pc.plan_status != '09'  -- 未作废的预计划
            LIMIT 3
        """).fetchall()
        
        print(f"\n当前未作废的孤儿预计划数量: {len(active_orphan_plans)}")
        
        if active_orphan_plans:
            print("示例未作废孤儿预计划:")
            for plan in active_orphan_plans:
                print(f"  - {plan.planno}: custcd={plan.custcd}, custcard={plan.custcard}")
                
                # 检查客户状态
                customer = db.session.get(Customer, plan.custcd)
                if customer:
                    print(f"    客户状态: {customer.customer_status}, useflg: {customer.useflg}")
                else:
                    print(f"    客户记录: 不存在")
        
        # 3. 模拟作废一个预计划（如果有的话）
        if active_orphan_plans:
            test_plan = active_orphan_plans[0]
            print(f"\n=== 测试作废预计划 {test_plan.planno} ===")
            
            # 检查作废前的状态
            customer_before = db.session.get(Customer, test_plan.custcd)
            if customer_before:
                print(f"作废前客户状态: {customer_before.customer_status}")
            
            # 执行作废
            result = PlanCustService.void(test_plan.planno, "test_operator", "测试作废")
            print(f"作废结果: {result}")
            
            # 检查作废后的状态
            customer_after = db.session.get(Customer, test_plan.custcd)
            if customer_after:
                print(f"作废后客户状态: {customer_after.customer_status}")
            else:
                print("作废后客户记录: 已删除")
        else:
            print("\n没有可测试的预计划")
        
        print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_void_customer_cleanup()
