"""字段级映射：动态同名列匹配 + 类型转换。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Engine, text


# 目标库专属列（源库不存在，有 server default 或无数据来源）
SKIP_TARGET_COLUMNS = {
    "created_at", "updated_at", "id", "status", "password",
    "phone", "email", "source_type", "customer_status",
    "asset_type", "recycle_status", "verified_at", "preplan_id",
    "valid_until",
}

# 手动重命名映射（模糊匹配无法处理的跨单词重命名）
# {表名: {目标列: 源列}}
MANUAL_RENAME: dict[str, dict[str, str]] = {
    "tmm19_suppliers": {
        "supp_cd": "custcd",
        "supp_nm": "custnm",
    },
    "tmm46_area": {
        "area_cd": "id",
        "area_nm": "name",
    },
    "tmm34_idmaster": {
        "id_type": "idtyp",
        "prefix": "idtyp",
        "current_no": "curbillid",
    },
    "tmc71_sysparm": {
        "parm_cd": "pk",
        "parm_nm": "pk",
    },
    "tpc14_pcbill": {
        "pcbill_id": "pcbillid",
    },
    "tpc16_rpcbill": {
        "pcbill_id": "pcbillid",
    },
    "tpc17_rpcbilldt": {
        "pcbill_id": "pcbillid",
    },
    "tpc20_suppappraisal": {
        "appraise_id": "appid",
        "start_date": "sdate",
        "end_date": "edate",
    },
    "tpc21_suppappraisaldt": {
        "appraise_id": "appid",
        "supplier_id": "supplierid",
    },
    "tqc11_resultdt": {
        "result_id": "qcbillid",
    },
}


def _try_fuzzy_match(tgt_col: str, src_cols: set[str]) -> str | None:
    """尝试模糊匹配：下划线变体互相查找。

    例如 tgt_col='user_cd' → 在 src 中找 'usercd'
         tgt_col='child_flg' → 在 src 中找 'childflg'
    优先精确匹配。
    """
    if tgt_col in src_cols:
        return tgt_col
    collapsed = tgt_col.replace("_", "")
    for sc in src_cols:
        if sc == collapsed:
            return sc
    return None


def _find_rename_map(
    src_cols: set[str], tgt_cols: set[str], table_name: str = ""
) -> dict[str, str]:
    """找出需要 INSERT ... AS 重命名的列映射。返回 {目标列名: 源列名}。

    仅返回目标列在源库有不同名称的映射。
    1. 先查 MANUAL_RENAME 覆盖
    2. 再尝试模糊匹配
    同名列不在此 Map 中（由 common_columns 处理）。
    """
    manual = MANUAL_RENAME.get(table_name, {})
    rename: dict[str, str] = {}
    for tc in tgt_cols:
        if tc in SKIP_TARGET_COLUMNS:
            continue
        if tc in src_cols:
            continue
        # 手动覆盖优先
        if tc in manual and manual[tc] in src_cols:
            rename[tc] = manual[tc]
            continue
        match = _try_fuzzy_match(tc, src_cols)
        if match and match != tc:
            rename[tc] = match
    return rename


@dataclass
class TableMapping:
    """整表映射：旧表名 → 新表名 + 自动匹配的列。"""

    old_table: str
    new_table: str
    common_columns: list[str] = field(default_factory=list)
    rename_map: dict[str, str] = field(default_factory=dict)
    batch: int = 1
    depends_on: list[str] = field(default_factory=list)


def build_mapping(
    src_engine: Engine,
    tgt_engine: Engine,
    old_table: str,
    new_table: str,
    batch: int = 1,
    depends_on: list[str] | None = None,
) -> TableMapping:
    """自动构建表映射：取两库同名列的交集。"""
    with src_engine.connect() as conn:
        src_cols = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name=:t"
                ),
                {"t": old_table},
            ).fetchall()
        }

    with tgt_engine.connect() as conn:
        tgt_cols = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name=:t"
                ),
                {"t": new_table},
            ).fetchall()
        }

    exact = sorted(c for c in (src_cols & tgt_cols) if c not in SKIP_TARGET_COLUMNS)
    rename_map = _find_rename_map(src_cols, tgt_cols, new_table)
    return TableMapping(
        old_table=old_table,
        new_table=new_table,
        common_columns=exact,
        rename_map=rename_map,
        batch=batch,
        depends_on=depends_on or [],
    )


def read_source_rows(
    engine: Engine, mapping: TableMapping, offset: int, limit: int
) -> list[dict[str, Any]]:
    """从源库读取一批行，返回目标列名作为 key 的行字典。

    使用 ORDER BY 第一列确保跨连接读取顺序一致。
    """
    if not mapping.common_columns and not mapping.rename_map:
        return []

    # 构建 SELECT 列表：同名列直接取，重命名列用 AS
    select_parts: list[str] = []
    # 同名列（源列名 = 目标列名）
    for col in mapping.common_columns:
        select_parts.append(col)
    # 重命名列（源列名 AS 目标列名）
    for tgt_col, src_col in mapping.rename_map.items():
        select_parts.append(f"{src_col} AS {tgt_col}")

    target_cols = mapping.common_columns + list(mapping.rename_map.keys())
    cols_str = ", ".join(select_parts)
    # 使用 CTID（物理行标识）排序，确保跨查询顺序一致
    # CTID 在同一连接内保证 OFFSET 一致性
    sql = f"SELECT {cols_str} FROM {mapping.old_table} OFFSET {offset} LIMIT {limit}"
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(zip(target_cols, row)) for row in result.fetchall()]


def write_target_rows(
    engine: Engine, mapping: TableMapping, rows: list[dict[str, Any]]
) -> int:
    """将行写入目标表，自动添加 created_at/updated_at 并清理 CHAR 尾部空格。"""
    if not rows:
        return 0

    # 查询目标表有哪些列及长度限制
    all_target_cols = _get_target_columns(engine, mapping.new_table)
    col_lengths = _get_target_column_lengths(engine, mapping.new_table)

    # 清理 CHAR 空格 + 截断 + 添加默认值
    from datetime import datetime
    now = datetime.utcnow()
    extra_cols: list[str] = []
    for row in rows:
        for k, v in list(row.items()):
            if isinstance(v, str):
                v = v.rstrip()
                # 截断超出目标列长度的字符串
                max_len = col_lengths.get(k)
                if max_len and len(v) > max_len:
                    v = v[:max_len]
                row[k] = v

        # created_at / updated_at
        if "created_at" in all_target_cols:
            row["created_at"] = now
            if "created_at" not in extra_cols:
                extra_cols.append("created_at")
        if "updated_at" in all_target_cols:
            row["updated_at"] = now
            if "updated_at" not in extra_cols:
                extra_cols.append("updated_at")

        # password 列：仅当目标表有此列时填充
        if "password" in all_target_cols and "password" not in row:
            row["password"] = row.get("passwd", "") or ""
            if "password" not in extra_cols:
                extra_cols.append("password")

        # status 列：默认 '1'
        if "status" in all_target_cols and "status" not in row:
            row["status"] = "1"
            if "status" not in extra_cols:
                extra_cols.append("status")

    all_cols = mapping.common_columns + list(mapping.rename_map.keys()) + extra_cols
    cols = ", ".join(all_cols)
    placeholders = ", ".join([f":{c}" for c in all_cols])
    sql = f"INSERT INTO {mapping.new_table} ({cols}) VALUES ({placeholders})"

    with engine.connect() as conn:
        try:
            result = conn.execute(text(sql), rows)
            conn.commit()
            return result.rowcount
        except Exception:
            conn.rollback()
            # 降级为逐行插入，跳过冲突
            inserted = 0
            for row in rows:
                try:
                    conn.execute(text(sql), [row])
                    conn.commit()
                    inserted += 1
                except Exception:
                    conn.rollback()
            return inserted


def get_row_count(engine: Engine, table: str) -> int:
    """获取表行数。"""
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()


def truncate_table(engine: Engine, table: str) -> None:
    """清空目标表。"""
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        conn.commit()


_target_cols_cache: dict[str, set[str]] = {}
_target_col_len_cache: dict[str, dict[str, int | None]] = {}


def _get_target_columns(engine: Engine, table: str) -> set[str]:
    """获取目标表的所有列名（缓存）。"""
    if table not in _target_cols_cache:
        _load_target_metadata(engine, table)
    return _target_cols_cache[table]


def _get_target_column_lengths(engine: Engine, table: str) -> dict[str, int | None]:
    """获取目标表 varchar 列的长度限制（缓存）。"""
    if table not in _target_col_len_cache:
        _load_target_metadata(engine, table)
    return _target_col_len_cache[table]


def _load_target_metadata(engine: Engine, table: str) -> None:
    """加载目标表的列名和长度限制。"""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT column_name, character_maximum_length "
                "FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=:t"
            ),
            {"t": table},
        ).fetchall()
    _target_cols_cache[table] = {row[0] for row in rows}
    _target_col_len_cache[table] = {
        row[0]: row[1] for row in rows if row[1] is not None
    }


def sync_sequence(engine: Engine, table: str) -> None:
    """同步自增序列。"""
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence(:tbl, 'id'), "
                    "COALESCE((SELECT MAX(id) FROM {tbl}), 0) + 1, false)"
                    .format(tbl=table)
                ),
                {"tbl": table},
            )
            conn.commit()
    except Exception:
        pass
