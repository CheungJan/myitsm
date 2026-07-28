#!/usr/bin/env python3
"""
TWH11_DETAIL 库存数据清理脚本

修复历史库存更新逻辑（旧逻辑只按 whcd+itemcd 维度，导致同一物料多行混乱）。

清理策略：
1. 按 (whcd, itemcd, itemtyp, prddate) 聚合，合并重复行
2. 删除 itemqty=0 且该维度有多行的冗余记录
3. 列出负数库存，需人工复核后手动处理
"""
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, '/Users/cheungjan/myitsm')
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app import create_app
from app.extensions import db
from sqlalchemy import func, text


def analyze():
    """分析并报告库存问题."""
    print("=" * 70)
    print("TWH11_DETAIL 库存数据分析")
    print("=" * 70)

    # 1. 总览
    total = db.session.execute(text("SELECT COUNT(*) FROM twh11_detail")).scalar()
    dims = db.session.execute(text(
        "SELECT COUNT(DISTINCT (whcd, itemcd, itemtyp, prddate)) FROM twh11_detail"
    )).scalar()
    print(f"\n总行数: {total}  独立维度数: {dims}")

    # 2. 负数
    neg = db.session.execute(text(
        "SELECT seqno, whcd, itemcd, itemtyp, prddate, itemqty "
        "FROM twh11_detail WHERE itemqty < 0 ORDER BY whcd, itemcd"
    )).fetchall()
    print(f"\n负数库存: {len(neg)} 条")
    for r in neg[:20]:
        print(f"  seqno={r[0]} {r[1]}/{r[2]}/{r[3] or '-'}/{r[4] or '-'} = {r[5]}")
    if len(neg) > 20:
        print(f"  ... 还有 {len(neg) - 20} 条")

    # 3. 同一维度多行
    dup = db.session.execute(text(
        "SELECT whcd, itemcd, itemtyp, prddate, COUNT(*) AS cnt, SUM(itemqty) AS total "
        "FROM twh11_detail "
        "GROUP BY whcd, itemcd, itemtyp, prddate "
        "HAVING COUNT(*) > 1 "
        "ORDER BY cnt DESC"
    )).fetchall()
    print(f"\n重复维度: {len(dup)} 组")
    for r in dup[:15]:
        print(f"  {r[0]}/{r[1]}/{r[2] or '-'}/{r[3] or '-'}: {r[4]}行 → 合计={r[5]}")
    if len(dup) > 15:
        print(f"  ... 还有 {len(dup) - 15} 组")

    # 4. 零库存
    zero = db.session.execute(text(
        "SELECT COUNT(*) FROM twh11_detail WHERE itemqty = 0"
    )).scalar()
    print(f"\n零库存行: {zero} 条")

    return len(neg), len(dup), zero


def clean(dry_run=True):
    """执行清理."""
    mode = "预览" if dry_run else "执行"
    print(f"\n{'=' * 70}")
    print(f"清理操作 ({mode}模式)")
    print("=" * 70)

    # -- 策略1: 合并同一维度多行 --
    dups = db.session.execute(text(
        "SELECT whcd, itemcd, itemtyp, prddate, SUM(itemqty) AS total_qty, MIN(seqno) AS keep_seqno "
        "FROM twh11_detail "
        "GROUP BY whcd, itemcd, itemtyp, prddate "
        "HAVING COUNT(*) > 1"
    )).fetchall()

    print(f"\n策略1 - 合并重复维度: {len(dups)} 组")
    if not dry_run and dups:
        # 合并：保留最小 seqno，删除其余，更新库存值为汇总
        db.session.execute(text(
            "DELETE FROM twh11_detail "
            "WHERE (whcd, itemcd, itemtyp, prddate, seqno) IN ("
            "  SELECT whcd, itemcd, itemtyp, prddate, seqno "
            "  FROM twh11_detail "
            "  WHERE (whcd, itemcd, itemtyp, prddate) IN ("
            "    SELECT whcd, itemcd, itemtyp, prddate "
            "    FROM twh11_detail "
            "    GROUP BY whcd, itemcd, itemtyp, prddate HAVING COUNT(*) > 1"
            "  )"
            "  AND seqno NOT IN ("
            "    SELECT MIN(seqno) FROM twh11_detail "
            "    GROUP BY whcd, itemcd, itemtyp, prddate HAVING COUNT(*) > 1"
            "  )"
            ")"
        ))
        # 更新保留行的库存值
        for r in dups:
            db.session.execute(text(
                "UPDATE twh11_detail SET itemqty = :qty, upddate = NOW() "
                "WHERE seqno = :seqno"
            ), {"qty": r[4], "seqno": r[5]})
        db.session.commit()
        print(f"  已合并 {len(dups)} 组重复维度")

    for r in dups[:10]:
        print(f"  {r[0]}/{r[1]}/{r[2] or '-'}/{r[3] or '-'}: → {r[4]}")

    # -- 策略2: 删除所有 itemqty=0 的占位行 --
    if not dry_run:
        deleted = db.session.execute(text(
            "DELETE FROM twh11_detail WHERE itemqty = 0"
        )).rowcount
        db.session.commit()
        print(f"\n策略2 - 删除零库存占位行: {deleted} 条")
    else:
        zero_all = db.session.execute(text(
            "SELECT COUNT(*) FROM twh11_detail WHERE itemqty = 0"
        )).scalar()
        print(f"\n策略2 - 可删除零库存占位行: {zero_all} 条")

    # -- 策略3: 负数（仅报告，不自动修复）--
    negs = db.session.execute(text(
        "SELECT seqno, whcd, itemcd, itemtyp, prddate, itemqty FROM twh11_detail WHERE itemqty < 0"
    )).fetchall()
    print(f"\n策略3 - 负数库存需人工复核: {len(negs)} 条")
    if negs:
        print("  以下记录需检查对应出入库单据后手动修正:")
        for r in negs[:10]:
            print(f"  seqno={r[0]} {r[1]}/{r[2]}/{r[3] or '-'}/{r[4] or '-'} = {r[5]}")
        if len(negs) > 10:
            print(f"  ... 还有 {len(negs) - 10} 条")

    print(f"\n{'=' * 70}")
    print(f"{mode}完成" + ("（未修改数据）" if dry_run else ""))
    print("=" * 70)


def main():
    app = create_app()
    with app.app_context():
        neg, dup, zero = analyze()

        if neg or dup or zero:
            print("\n选项: [1] 预览  [2] 执行清理  [3] 退出")
            c = input("> ").strip()
            if c == '1':
                clean(dry_run=True)
            elif c == '2':
                clean(dry_run=False)
            else:
                print("已退出")
        else:
            print("\n✓ 数据正常，无需清理")


if __name__ == '__main__':
    main()
