"""数据库种子数据加载模块。

用法：
    flask seed              # 加载所有种子数据
    flask seed --check      # 仅检查，不写入
    flask seed --table tmc01_menus  # 仅加载指定表

生产部署流程：
    1. PB 数据导入 PostgreSQL
    2. flask db upgrade     # 执行 DDL + DML 迁移
    3. flask seed           # 加载种子数据（可在 upgrade 后执行，幂等）
"""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
from flask import current_app
from sqlalchemy import text

from app.extensions import db

logger = logging.getLogger(__name__)

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"

# 种子表清单及加载顺序
SEED_TABLES = [
    {
        "file": "tit04_archivecode.csv",
        "table": "tit04_archivecode",
        "columns": [
            "arch_cd", "arch_nm", "arch_group", "fault_type",
            "parent", "child_flg", "max_level", "useflg",
        ],
        "pk": "arch_cd",
        "required": True,
        "description": "故障代码树形字典（设备故障现象三级分类）",
    },
    {
        "file": "tmc01_menus.csv",
        "table": "tmc01_menus",
        "columns": [
            "menu_cd", "menu_nm", "parent_cd", "useflg",
        ],
        "pk": "menu_cd",
        "required": True,
        "description": "系统菜单定义",
    },
    {
        "file": "tmc02_menusdt.csv",
        "table": "tmc02_menusdt",
        "columns": [
            "menu_cd", "func_cd", "useflg",
        ],
        "pk": "menu_cd,func_cd",
        "required": True,
        "description": "菜单功能权限明细",
    },
]


def _load_csv(table_info: dict[str, Any]) -> int:
    """从 CSV 加载种子数据到指定表（幂等：PK 冲突则跳过）。"""
    filepath = SEED_DIR / table_info["file"]
    if not filepath.exists():
        logger.warning("种子文件不存在: %s", filepath)
        return 0

    table = table_info["table"]
    columns = table_info["columns"]
    pk_cols = [c.strip() for c in table_info["pk"].split(",")]

    rows: list[dict[str, Any]] = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 只取目标列
            clean = {c: row.get(c) for c in columns}
            rows.append(clean)

    if not rows:
        logger.info("种子文件为空: %s", filepath)
        return 0

    inserted = 0
    for row in rows:
        # 检查是否已存在
        check_sql = f"SELECT 1 FROM {table} WHERE {' AND '.join(f'{c} = :{c}' for c in pk_cols)}"
        result = db.session.execute(text(check_sql), {c: row[c] for c in pk_cols}).first()
        if result:
            continue

        # 补时间戳（TimestampMixin NOT NULL 强制要求）
        now = datetime.now(timezone.utc)
        row["created_at"] = row.get("created_at") or now
        row["updated_at"] = row.get("updated_at") or now

        cols = ", ".join(row.keys())
        placeholders = ", ".join(f":{c}" for c in row)
        sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        db.session.execute(text(sql), row)
        inserted += 1

    if inserted:
        db.session.commit()
        logger.info("种子表 %s: 新增 %d 行 (共 %d 行)", table, inserted, len(rows))
    else:
        logger.info("种子表 %s: 全部已存在 (共 %d 行)", table, len(rows))

    return inserted


def seed_table(table_name: str) -> int:
    """加载单个种子表。"""
    for t in SEED_TABLES:
        if t["table"] == table_name:
            return _load_csv(t)
    logger.warning("未知种子表: %s", table_name)
    return 0


def seed_all() -> dict[str, int]:
    """加载所有种子表。"""
    results: dict[str, int] = {}
    for t in SEED_TABLES:
        results[t["table"]] = _load_csv(t)
    return results


def check_seed() -> dict[str, dict[str, Any]]:
    """检查种子数据状态（不写入）。"""
    status: dict[str, dict[str, Any]] = {}
    for t in SEED_TABLES:
        filepath = SEED_DIR / t["file"]
        exists = filepath.exists()
        count_sql = f"SELECT COUNT(*) FROM {t['table']}"
        db_count = db.session.execute(text(count_sql)).scalar() or 0
        status[t["table"]] = {
            "file_exists": exists,
            "db_rows": db_count,
            "required": t["required"],
            "description": t["description"],
        }
    return status


# ---------------------------------------------------------------------------
# Flask CLI
# ---------------------------------------------------------------------------


@click.group("seed")
def seed_cli() -> None:
    """数据库种子数据管理。"""


@seed_cli.command("load")
@click.option("--table", "-t", default=None, help="仅加载指定表")
def seed_load(table: str | None) -> None:
    """加载种子数据（幂等）。"""
    if table:
        n = seed_table(table)
        click.echo(f"  {table}: {n} 行新增")
    else:
        results = seed_all()
        total = sum(results.values())
        for tbl, n in results.items():
            click.echo(f"  {tbl}: {n} 行新增")
        click.echo(f"总计: {total} 行新增")


@seed_cli.command("check")
def seed_check() -> None:
    """检查种子数据状态。"""
    status = check_seed()
    for tbl, info in status.items():
        flag = "✅" if info["db_rows"] > 0 else ("⚠️" if info["required"] else "⬜")
        click.echo(
            f"  {flag} {tbl}: {info['db_rows']} 行 "
            f"({'种子文件存在' if info['file_exists'] else '缺少种子文件'}) "
            f"— {info['description']}"
        )


# 注册到 Flask CLI
def init_app(app):  # type: ignore[no-untyped-def]
    app.cli.add_command(seed_cli)
