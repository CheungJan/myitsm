"""单表重迁移脚本：TRUNCATE 目标表后从源库重新迁移。

使用方法：
    set -a && . .env && set +a && \
    /Users/cheungjan/myitsm/.venv/bin/python \
    /Users/cheungjan/myitsm/debug/remigrate_table.py tit23_maintenance_d2d

用于修复分页 ORDER BY 不稳定导致的重复/丢失数据问题。
"""
from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, text

# 复用 batch_runner 的迁移逻辑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.migration.field_mapper import (  # noqa: E402
    build_mapping,
    get_row_count,
    sync_sequence,
    truncate_table,
    write_target_rows,
)


def remigrate(table_name: str, batch_size: int = 5000) -> None:
    """TRUNCATE 目标表后从源库重新迁移。"""
    source_url = os.getenv("SOURCE_DATABASE_URL", "postgresql://cheungjan@localhost:5432/ortopbitsmdb")
    target_url = os.getenv("DATABASE_URL")
    if not target_url:
        raise SystemExit("DATABASE_URL 未设置")

    src_engine = create_engine(source_url, pool_size=1)
    tgt_engine = create_engine(target_url, pool_size=5)

    src_count = get_row_count(src_engine, table_name)
    print(f"源库 {table_name}: {src_count} 行")

    mapping = build_mapping(src_engine, tgt_engine, table_name, table_name, batch=3)
    if not mapping.common_columns and not mapping.rename_map:
        print("无映射列，退出")
        return

    print(f"公共列({len(mapping.common_columns)}): {mapping.common_columns[:5]}...")
    if mapping.rename_map:
        print(f"重命名列: {mapping.rename_map}")

    # 1. 清空目标表
    print(f"TRUNCATE {table_name} ...")
    truncate_table(tgt_engine, table_name)

    # 2. 分批读取源库并写入目标库
    total = 0
    offset = 0
    while offset < src_count:
        rows = _read_batch(src_engine, mapping, offset, batch_size)
        if not rows:
            break
        inserted = write_target_rows(tgt_engine, mapping, rows)
        total += inserted
        offset += batch_size
        print(f"  进度: {min(offset, src_count)} / {src_count} (插入 {inserted})")

    # 3. 同步序列
    sync_sequence(tgt_engine, table_name)

    print(f"完成: {total} 行 (源 {src_count} 行)")

    # 4. 验证重复
    with tgt_engine.connect() as conn:
        dup = conn.execute(text(
            f"SELECT COUNT(*) FROM (SELECT maintenance_id, business_operation_id "
            f"FROM {table_name} GROUP BY maintenance_id, business_operation_id "
            f"HAVING COUNT(*) > 1) t"
        )).scalar_one()
        tgt_cnt = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one()
    print(f"目标库 {table_name}: {tgt_cnt} 行, 重复组: {dup}")

    src_engine.dispose()
    tgt_engine.dispose()


def _read_batch(engine, mapping, offset: int, limit: int):
    """从源库读取一批行（全列 ORDER BY 确保分页确定性）。"""
    from app.migration.field_mapper import read_source_rows
    return read_source_rows(engine, mapping, offset, limit)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: remigrate_table.py <table_name>", file=sys.stderr)
        sys.exit(1)
    remigrate(sys.argv[1])
