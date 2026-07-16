"""
从 province-city-china 的 data.sqlite 导入国标行政区划数据到 PG。

使用方式：
    uv run python app/migration/import_geo_data.py --sqlite /path/to/data.sqlite
    uv run python app/migration/import_geo_data.py --sqlite /Users/cheungjan/Downloads/data.sqlite

支持重复执行（幂等），已存在的记录跳过。
"""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

# 确保项目根目录在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from app import create_app
from app.extensions import db
from app.models.master import GeoArea, GeoCity, GeoProvince, GeoStreet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def _bulk_upsert(session, model, rows: list[dict], pk: str) -> int:
    """批量插入，已存在则跳过，返回新增条数。"""
    if not rows:
        return 0
    existing_pks = {
        r[0]
        for r in session.query(getattr(model, pk)).filter(
            getattr(model, pk).in_([r[pk] for r in rows])
        ).all()
    }
    new_rows = [r for r in rows if r[pk] not in existing_pks]
    if new_rows:
        session.bulk_insert_mappings(model, new_rows)
    return len(new_rows)


def import_geo(sqlite_path: str) -> None:
    """主导入函数。"""
    sqlite_path = Path(sqlite_path)
    if not sqlite_path.exists():
        logger.error(f"SQLite 文件不存在：{sqlite_path}")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row

        # ── 1. 省级 ──────────────────────────────────────────
        logger.info("导入省级数据...")
        rows = [{"code": r["code"], "name": r["name"]} for r in conn.execute("SELECT code, name FROM province")]
        inserted = _bulk_upsert(db.session, GeoProvince, rows, "code")
        db.session.commit()
        logger.info(f"  省级：共 {len(rows)} 条，新增 {inserted} 条")

        # ── 2. 地级市 ─────────────────────────────────────────
        logger.info("导入地级市数据...")
        total = inserted = 0
        batch: list[dict] = []
        for r in conn.execute("SELECT code, name, provinceCode FROM city"):
            batch.append({"code": r["code"], "name": r["name"], "province_code": r["provinceCode"]})
            total += 1
            if len(batch) >= BATCH_SIZE:
                inserted += _bulk_upsert(db.session, GeoCity, batch, "code")
                db.session.commit()
                batch = []
        if batch:
            inserted += _bulk_upsert(db.session, GeoCity, batch, "code")
            db.session.commit()
        logger.info(f"  地级市：共 {total} 条，新增 {inserted} 条")

        # ── 3. 区县 ───────────────────────────────────────────
        logger.info("导入区县数据...")
        total = inserted = 0
        batch = []
        for r in conn.execute("SELECT code, name, cityCode, provinceCode FROM area"):
            batch.append({
                "code": r["code"],
                "name": r["name"],
                "city_code": r["cityCode"],
                "province_code": r["provinceCode"],
            })
            total += 1
            if len(batch) >= BATCH_SIZE:
                inserted += _bulk_upsert(db.session, GeoArea, batch, "code")
                db.session.commit()
                batch = []
        if batch:
            inserted += _bulk_upsert(db.session, GeoArea, batch, "code")
            db.session.commit()
        logger.info(f"  区县：共 {total} 条，新增 {inserted} 条")

        # ── 4. 街道/乡镇 ──────────────────────────────────────
        logger.info("导入街道数据（41352条，稍等）...")
        total = inserted = 0
        batch = []
        for r in conn.execute("SELECT code, name, areaCode, cityCode, provinceCode FROM street"):
            batch.append({
                "code": r["code"],
                "name": r["name"],
                "area_code": r["areaCode"],
                "city_code": r["cityCode"],
                "province_code": r["provinceCode"],
            })
            total += 1
            if len(batch) >= BATCH_SIZE:
                inserted += _bulk_upsert(db.session, GeoStreet, batch, "code")
                db.session.commit()
                batch = []
                if total % 5000 == 0:
                    logger.info(f"  街道进度：{total}...")
        if batch:
            inserted += _bulk_upsert(db.session, GeoStreet, batch, "code")
            db.session.commit()
        logger.info(f"  街道：共 {total} 条，新增 {inserted} 条")

        conn.close()
        logger.info("✅ 导入完成")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入国标行政区划数据到 PG")
    parser.add_argument("--sqlite", default="/Users/cheungjan/Downloads/data.sqlite", help="SQLite 文件路径")
    args = parser.parse_args()
    import_geo(args.sqlite)
