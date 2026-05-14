"""BOM 管理数据访问层。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import g

from app.extensions import db
from app.models.master import Bom, BomDt


class BomRepository:
    """BOM 数据访问。"""

    @staticmethod
    def list_boms(page: int = 1, per_page: int = 20, search: str | None = None,
                  class_cd: str | None = None) -> tuple[list[Bom], int]:
        from app.models.master import Item
        from app.repositories.system_repository import SystemRepository
        q = db.session.query(Bom).join(Item, Bom.bomcd == Item.item_cd).filter(Item.typflg == "1")
        if search:
            q = q.filter(db.or_(Bom.bomcd.ilike(f"%{search}%"), Bom.bomnm.ilike(f"%{search}%")))
        if class_cd:
            cds = SystemRepository._get_descendant_class_cds(class_cd)
            item_cds = [r[0] for r in db.session.query(Item.item_cd).filter(
                Item.class_cd.in_(cds)).all()]
            if item_cds:
                q = q.filter(Bom.bomcd.in_(item_cds))
            else:
                return [], 0
        q = q.order_by(Bom.bomcd)
        total = q.count()
        return q.offset((page - 1) * per_page).limit(per_page).all(), total

    @staticmethod
    def get_bom(bomcd: str) -> Bom | None:
        return db.session.get(Bom, bomcd)

    @staticmethod
    def create_bom(data: dict[str, Any]) -> Bom:
        bom = Bom(**data)
        bom.opercd = g.get("user_cd", "")
        bom.gendate = datetime.now(timezone.utc)
        bom.upddate = datetime.now(timezone.utc)
        db.session.add(bom)
        db.session.commit()
        return bom

    @staticmethod
    def update_bom(bom: Bom, data: dict[str, Any]) -> Bom:
        for k, v in data.items():
            setattr(bom, k, v)
        bom.upddate = datetime.now(timezone.utc)
        db.session.commit()
        return bom

    @staticmethod
    def delete_bom(bom: Bom) -> None:
        db.session.delete(bom)
        db.session.commit()

    @staticmethod
    def list_details(bomcd: str) -> list[BomDt]:
        return list(db.session.query(BomDt).filter(BomDt.bomcd == bomcd).order_by(BomDt.itemcd).all())

    @staticmethod
    def get_detail(bomcd: str, itemcd: str) -> BomDt | None:
        return db.session.get(BomDt, (bomcd, itemcd))

    @staticmethod
    def add_detail(data: dict[str, Any]) -> BomDt:
        dt = BomDt(**data)
        dt.opercd = g.get("user_cd", "")
        dt.gendate = datetime.now(timezone.utc)
        dt.upddate = datetime.now(timezone.utc)
        db.session.add(dt)
        db.session.commit()
        return dt

    @staticmethod
    def update_detail(dt: BomDt, data: dict[str, Any]) -> BomDt:
        for k, v in data.items():
            setattr(dt, k, v)
        dt.upddate = datetime.now(timezone.utc)
        db.session.commit()
        return dt

    @staticmethod
    def delete_detail(dt: BomDt) -> None:
        db.session.delete(dt)
        db.session.commit()
