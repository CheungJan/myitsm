"""一次性迁移脚本: DepositPosModel 机型级押金 → tip01_price busityp=40。

映射:
  单屏/双屏/4Q → 4Q4 开头 BOM,押金 3000
  7Q           → 7Q 开头 BOM,押金 3000
  海晟         → HS 开头 BOM,押金 0(跳过)

迁移后 DepositPosModel 标记弃用,保留表结构供历史追溯。
"""
import os
from app import create_app
from app.extensions import db

os.environ.setdefault("DATABASE_URL", "postgresql://cheungjan@localhost:5432/myitsm")


def main() -> None:
    app = create_app()
    with app.app_context():
        for prefix in ("4Q4", "7Q"):
            boms = db.session.execute(
                db.text("SELECT bomcd FROM tmm41_bom WHERE bomcd LIKE :p || '%'"),
                {"p": prefix},
            ).all()
            for (bomcd,) in boms:
                existing = db.session.execute(
                    db.text("SELECT 1 FROM tip01_price WHERE itemcd=:i AND busityp='40'"),
                    {"i": bomcd},
                ).first()
                if not existing:
                    db.session.execute(
                        db.text(
                            "INSERT INTO tip01_price "
                            "(itemcd, busityp, itemprice, opercd, gendate, upddate, "
                            "useflg, is_current, created_at, updated_at) "
                            "VALUES (:i, '40', 3000, 'SYSTEM', NOW(), NOW(), '1', true, NOW(), NOW())"
                        ),
                        {"i": bomcd},
                    )
        db.session.commit()
        rows = db.session.execute(
            db.text(
                "SELECT itemcd, itemprice FROM tip01_price "
                "WHERE busityp='40' AND (itemcd LIKE '4Q4%' OR itemcd LIKE '7Q%') "
                "ORDER BY itemcd"
            )
        ).all()
        print(f"busityp=40 押金 {len(rows)} 条")
        for r in rows[:3]:
            print(f"  {r[0]} | {float(r[1])}")
        if len(rows) > 3:
            print(f"  ... 共 {len(rows)} 条")


if __name__ == "__main__":
    main()
