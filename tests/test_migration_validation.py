"""全量迁移校验：逐表行数对比。"""
import os
import pytest
from sqlalchemy import create_engine, text


def _get_tables(engine):
    """获取库中所有表名。"""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE' "
                "AND table_name NOT LIKE 'mig_%' "
                "ORDER BY table_name"
            )
        ).fetchall()
    return [row[0] for row in rows]


def _get_common_tables(src_engine, tgt_engine):
    """获取两库共有的表。"""
    src_tables = set(_get_tables(src_engine))
    tgt_tables = set(_get_tables(tgt_engine))
    return sorted(src_tables & tgt_tables)


@pytest.fixture(scope="module")
def engines():
    source_url = os.getenv("SOURCE_DATABASE_URL")
    target_url = os.getenv("DATABASE_URL")
    if not source_url or not target_url:
        pytest.skip("需要 SOURCE_DATABASE_URL 和 DATABASE_URL")
    src = create_engine(source_url)
    tgt = create_engine(target_url)
    yield src, tgt
    src.dispose()
    tgt.dispose()


def test_source_accessible(engines):
    src, _ = engines
    tables = _get_tables(src)
    assert len(tables) > 0, "源库无表"


def test_target_accessible(engines):
    _, tgt = engines
    tables = _get_tables(tgt)
    assert len(tables) > 50, f"目标库表数异常: {len(tables)}"


def test_row_count_comparison(engines):
    """逐表对比源库和目标库行数。"""
    src, tgt = engines
    common = _get_common_tables(src, tgt)
    assert len(common) > 50, f"两库共同表不足: {len(common)}"

    mismatches = []
    ok_count = 0
    total_src_rows = 0
    total_tgt_rows = 0

    with src.connect() as sc, tgt.connect() as tc:
        for tbl in common:
            src_count = sc.execute(
                text(f"SELECT COUNT(*) FROM {tbl}")
            ).scalar()
            tgt_count = tc.execute(
                text(f"SELECT COUNT(*) FROM {tbl}")
            ).scalar()
            total_src_rows += src_count
            total_tgt_rows += tgt_count

            if src_count == 0 and tgt_count == 0:
                continue
            if src_count == tgt_count:
                ok_count += 1
            else:
                pct = (tgt_count / src_count * 100) if src_count > 0 else 0
                mismatches.append((tbl, src_count, tgt_count, pct))

    print(f"\n逐表行数校验:")
    print(f"  完全匹配: {ok_count} 表")
    print(f"  有差异: {len(mismatches)} 表")
    print(f"  源库总行数: {total_src_rows:,}")
    print(f"  目标库总行数: {total_tgt_rows:,}")
    print(f"  总体完整率: {total_tgt_rows/total_src_rows*100:.1f}%")

    for tbl, s, t, pct in mismatches:
        print(f"  {tbl}: 源{s} → 目标{t} ({pct:.1f}%)")

    assert len(mismatches) == 0, f"{len(mismatches)} 张表行数不一致"


@pytest.mark.parametrize("table_name", [
    "tmm22_customers",
    "tit10_maintenanceday",
    "tit23_maintenance_d2d",
    "tmm43_eid",
    "twH13_in",
    "twH15_out",
    "tmm12_items",
    "tmc13_users",
    "tkq01_attendance",
    "tht01_htgl",
    "tac01_fpsk",
])
def test_key_table_data_exists(engines, table_name):
    """验证核心业务表有数据。"""
    _, tgt = engines
    with tgt.connect() as conn:
        count = conn.execute(
            text(f"SELECT COUNT(*) FROM {table_name}")
        ).scalar()
        assert count > 0, f"核心表 {table_name} 为空!"
