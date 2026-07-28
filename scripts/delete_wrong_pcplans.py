#!/usr/bin/env python3
"""
删除错误的需求单号记录
包括：1832D5FB, 79184E44, 2DB56F0B

需要删除的表：
- tpc01_pcplan (主表)
- tpc02_pcplandt (明细表) - 有外键级联删除
- tpc20_requisition_order_link (需求-订单关联表) - 如果有的话
"""

import sys
sys.path.insert(0, '/Users/cheungjan/myitsm')

from app.extensions import db
from app.models.procurement import PurchasePlan, PurchasePlanDt, RequisitionOrderLink

# 需要删除的错误单号
WRONG_PCPLAN_IDS = ['1832D5FB', '79184E44', '2DB56F0B']


def delete_pcplan(pcplanid: str, dry_run: bool = True):
    """删除单个需求单及其关联数据。
    
    Args:
        pcplanid: 需求单号
        dry_run: 是否为预览模式（只查询不删除）
    """
    print(f"\n处理单号: {pcplanid}")
    
    # 1. 检查关联表 tpc20_requisition_order_link
    link_count = db.session.query(RequisitionOrderLink).filter(
        RequisitionOrderLink.pcplanid == pcplanid
    ).count()
    
    if link_count > 0:
        print(f"  - 关联表记录: {link_count} 条")
        if not dry_run:
            db.session.query(RequisitionOrderLink).filter(
                RequisitionOrderLink.pcplanid == pcplanid
            ).delete(synchronize_session=False)
            print(f"    ✅ 已删除")
    else:
        print(f"  - 关联表无记录")
    
    # 2. 检查/删除明细表 tpc02_pcplandt
    dt_count = db.session.query(PurchasePlanDt).filter(
        PurchasePlanDt.pcplanid == pcplanid
    ).count()
    
    if dt_count > 0:
        print(f"  - 明细表记录: {dt_count} 条")
        if not dry_run:
            db.session.query(PurchasePlanDt).filter(
                PurchasePlanDt.pcplanid == pcplanid
            ).delete(synchronize_session=False)
            print(f"    ✅ 已删除")
    else:
        print(f"  - 明细表无记录")
    
    # 3. 检查/删除主表 tpc01_pcplan
    plan = db.session.get(PurchasePlan, pcplanid)
    if plan:
        print(f"  - 主表记录: 存在 (审核状态: {plan.auditflg}, 生成日期: {plan.gendate})")
        if not dry_run:
            db.session.delete(plan)
            print(f"    ✅ 已标记删除")
    else:
        print(f"  - ⚠️ 主表记录不存在")
        return False
    
    return True


def main():
    """主函数。"""
    print("=" * 60)
    print("删除错误需求单号记录")
    print("=" * 60)
    print(f"目标单号: {', '.join(WRONG_PCPLAN_IDS)}")
    print("\n⚠️  第一步：预览模式（只查询不删除）")
    
    found_count = 0
    not_found = []
    
    # 第一步：预览
    for pcplanid in WRONG_PCPLAN_IDS:
        if delete_pcplan(pcplanid, dry_run=True):
            found_count += 1
        else:
            not_found.append(pcplanid)
    
    if found_count == 0:
        print(f"\n{'=' * 60}")
        print("⚠️  没有找到任何可删除的记录")
        print(f"{'=' * 60}")
        return
    
    print(f"\n{'=' * 60}")
    print(f"找到 {found_count} 个可删除的需求单")
    if not_found:
        print(f"未找到: {', '.join(not_found)}")
    print(f"{'=' * 60}")
    
    # 第二步：确认
    confirm = input(f"\n确认删除以上 {found_count} 个需求单及其关联记录? [yes/no]: ")
    if confirm.lower() != 'yes':
        print("\n❌ 已取消删除")
        return
    
    # 第三步：执行删除
    print("\n" + "=" * 60)
    print("执行删除...")
    print("=" * 60)
    
    deleted_count = 0
    try:
        for pcplanid in WRONG_PCPLAN_IDS:
            if pcplanid not in not_found:
                if delete_pcplan(pcplanid, dry_run=False):
                    deleted_count += 1
        
        db.session.commit()
        print(f"\n{'=' * 60}")
        print(f"✅ 成功删除 {deleted_count} 个需求单及其关联记录")
        print(f"{'=' * 60}")
            
    except Exception as e:
        db.session.rollback()
        print(f"\n{'=' * 60}")
        print(f"❌ 删除失败，已回滚: {e}")
        print(f"{'=' * 60}")
        raise


if __name__ == '__main__':
    main()
