"""检测迁移重复/丢失问题：对比源库(ortopbitsmdb)与目标库(myitsm)行数，识别目标库重复组。

使用方法：
    set -a && . .env && set +a && python debug/check_migration_duplicates.py
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

from sqlalchemy import create_engine, text

# batch_runner.py 中的全部迁移表
BATCH_TABLES: list[str] = [
    # Batch 1
    "tmc11_departments", "tmc12_groups", "tmc13_users",
    "tmm01_company", "tmm21_custclass", "tmm22_customers",
    "tmm11_itemclass", "tmm12_items",
    "tmm18_supplierclass", "tmm19_suppliers",
    "twh01_warehouse", "tmm46_area", "tmm47_commode",
    "tmm24_custitems", "tmm31_syscodes", "tmm34_idmaster",
    "tmc71_sysparm", "tmc41_acclog",
    "tmm61_deposit", "tmm61_deposit_dtl", "tmm61_deposit_io",
    "tmm61_deposit_list", "tmm61_deposit_posmodel",
    # Batch 2
    "tmc01_menus", "tmc02_menusdt",
    "tit01_timepoint_area", "tit02_liabilityreg", "tit02_liabilityregdt",
    "tit04_archivecode", "tit05_repairinfo", "tit06_userarea",
    "tmc03_usermenus", "tmc21_usergroup", "tmc22_userbusityp", "tmc31_groupright",
    "tmm35_cust_pos_rl", "tmm36_cust_ve_rl",
    # Batch 3
    "tit10_maintenanceday", "tit10_maintenance_liability",
    "tit10_main_track", "tit10_pos_detail",
    "tit11_maintenance_attc", "tit12_maintenance_archive",
    "tit13_maintenance_open", "tit14_equipment_open",
    "tit15_maintenance_renovate", "tit15_equipment_renovate",
    "tit16_device_change",
    "tit17_maintenance", "tit17_cust_pos_daily", "tit17_maintenance_plan",
    "tit18_store_close", "tit19_on_choosedt",
    "tit21_maintenance_dispatch",
    "tit23_maintenance_d2d", "tit24_maintenance_rv",
    "tit25_accessories_update", "tit26_paylist",
    "tit27_close_bills",
    "tit28_free_replace", "tit28_free_replace_dt",
    "tit29_noclose_track", "plan_cust",
    # Batch 4
    "twh11_detail", "twh12_detaildt",
    "twh13_in", "twh14_checkindt", "twh15_out",
    "twh16_outdteid", "twh16_outdtprd",
    "twh17_overlost", "twh18_overlostdt", "twh18_overlosteid",
    "twh19_asset_c_a", "twh20_asset_c_a_dtl",
    "twh21_pos_change", "twh22_pos_change_dt",
    "tpc01_pcplan", "tpc02_pcplandt", "tpc03_pcplanstatus",
    "tpc12_register", "tpc13_registerdt", "tpc14_pcbill",
    "tpc16_rpcbill", "tpc17_rpcbilldt",
    "tpc20_suppappraisal", "tpc21_suppappraisaldt",
    "tsl01_extend", "tsl02_extenddt", "tsl10_slbill",
    # Batch 5
    "tmm41_bom", "tmm42_bomdt",
    "tmm43_eid", "tmm43_eid_track",
    "tqc10_result", "tqc11_resultdt", "tqc11_resulteid",
    "tkq01_attendance", "tkq02_attendancecount",
    "tip01_price", "tip03_adjprice",
    "tht01_htgl", "tac01_fpsk",
    "ttx01_txkmg",
    "tiv01_invlimit", "tiv02_invlimit_hi",
    "tmp14_checkindt", "tmm62_asset_attrib_list",
]


def get_pk_columns(engine, table: str) -> list[str]:
    """获取表的主键列（按序）。"""
    sql = text(
        "SELECT kcu.column_name "
        "FROM information_schema.table_constraints tc "
        "JOIN information_schema.key_column_usage kcu "
        "  ON kcu.constraint_name = tc.constraint_name "
        "  AND kcu.table_schema = tc.table_schema "
        "  AND kcu.table_name = tc.table_name "
        "WHERE tc.constraint_type = 'PRIMARY KEY' "
        "  AND tc.table_schema = 'public' "
        "  AND tc.table_name = :t "
        "ORDER BY kcu.ordinal_position"
    )
    with engine.connect() as conn:
        try:
            rows = conn.execute(sql, {"t": table}).fetchall()
            return [r[0] for r in rows]
        except Exception:
            return []


def get_row_count(engine, table: str) -> int | None:
    """获取表行数，表不存在返回 None。"""
    with engine.connect() as conn:
        try:
            return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
        except Exception:
            return None


def check_duplicates(engine, table: str, pk_cols: list[str]) -> tuple[int, int]:
    """检查目标表按源库 PK 列的重复组数和重复行数。返回 (重复组数, 重复行数)。"""
    if not pk_cols:
        return (0, 0)
    cols = ", ".join(pk_cols)
    sql = text(
        f"SELECT COUNT(*) FROM (SELECT {cols} FROM {table} "
        f"GROUP BY {cols} HAVING COUNT(*) > 1) t"
    )
    with engine.connect() as conn:
        try:
            dup_groups = conn.execute(sql).scalar_one()
        except Exception:
            return (0, 0)
    if dup_groups == 0:
        return (0, 0)
    sql2 = text(
        f"SELECT COALESCE(SUM(cnt - 1), 0) FROM ("
        f"SELECT COUNT(*) AS cnt FROM {table} GROUP BY {cols} HAVING COUNT(*) > 1) t"
    )
    with engine.connect() as conn:
        try:
            dup_rows = conn.execute(sql2).scalar_one()
        except Exception:
            dup_rows = 0
    return (dup_groups, dup_rows)


def main() -> int:
    source_url = os.getenv("SOURCE_DATABASE_URL", "postgresql://cheungjan@localhost:5432/ortopbitsmdb")
    target_url = os.getenv("DATABASE_URL")
    if not target_url:
        print("ERROR: DATABASE_URL 未设置", file=sys.stderr)
        return 1

    src_engine = create_engine(source_url)
    tgt_engine = create_engine(target_url)

    print(f"{'表名':<35} {'源库':>10} {'目标库':>10} {'差值':>8} {'源PK':<25} {'重复组':>8} {'重复行':>8}")
    print("-" * 120)

    affected: list[dict] = []
    for table in BATCH_TABLES:
        src_cnt = get_row_count(src_engine, table)
        tgt_cnt = get_row_count(tgt_engine, table)
        src_pk = get_pk_columns(src_engine, table)
        tgt_pk = get_pk_columns(tgt_engine, table)

        diff = (tgt_cnt - src_cnt) if (src_cnt is not None and tgt_cnt is not None) else None
        dup_groups, dup_rows = (0, 0)
        # 只在目标库 PK 为 id 自增、源库 PK 为业务键时检查重复
        if src_pk and tgt_pk == ["id"] and table != "tmm46_area":
            dup_groups, dup_rows = check_duplicates(tgt_engine, table, src_pk)

        src_pk_str = ",".join(src_pk) if src_pk else "(无)"
        diff_str = f"{diff:+d}" if diff is not None else "?"
        print(f"{table:<35} {str(src_cnt):>10} {str(tgt_cnt):>10} {diff_str:>8} {src_pk_str:<25} {dup_groups:>8} {dup_rows:>8}")

        if (src_cnt is not None and tgt_cnt is not None and src_cnt != tgt_cnt) or dup_groups > 0:
            affected.append({
                "table": table,
                "src_cnt": src_cnt,
                "tgt_cnt": tgt_cnt,
                "diff": diff,
                "src_pk": src_pk,
                "dup_groups": dup_groups,
                "dup_rows": dup_rows,
            })

    print("-" * 120)
    print(f"\n受影响表（行数不一致 或 有重复组）：{len(affected)} 张")
    for a in affected:
        print(f"  {a['table']}: 源={a['src_cnt']} 目标={a['tgt_cnt']} 差={a['diff']} "
              f"PK=[{','.join(a['src_pk'])}] 重复组={a['dup_groups']} 重复行={a['dup_rows']}")

    src_engine.dispose()
    tgt_engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
