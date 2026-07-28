"""11f 资产编辑接口写 type='A'（属性变更）测试。"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.master import Eid, EidTrack
from app.services.system_service import SystemService


def _seed_eid(itemcd: str = "IT00A", eid_val: str = "EID00A0000001") -> None:
    """插入测试 EID（幂等，先清后插）。"""
    db.session.query(EidTrack).filter(EidTrack.eid == eid_val).delete(synchronize_session=False)
    db.session.query(Eid).filter(Eid.eid == eid_val).delete(synchronize_session=False)
    db.session.add(
        Eid(
            itemcd=itemcd,
            eid=eid_val,
            opercd="T00001",
            gendate=datetime.now(UTC),
            useflg="1",
            sflg="8",
            whcd="W1",
            asset_type="01",
            asset_owner="CUSTOMER",
            recyclable=False,
            install_date=None,
        )
    )
    db.session.commit()


class TestUpdateEid11f:
    """11f：资产编辑接口写 type='A'（属性变更）。"""

    def test_update_asset_type_writes_a_track(self, app: Flask) -> None:
        """更新 asset_type 应写 type='A' 记录，含变更前后值。"""
        with app.app_context():
            _seed_eid()
            svc = SystemService()

            result = svc.update_eid(
                "IT00A",
                "EID00A0000001",
                {
                    "asset_type": "02",
                    "opercd": "T00001",
                },
            )

            assert result is not None
            assert result["asset_type"] == "02"

            # 11f: 业务语义层 type='A'
            a_tracks = (
                db.session.query(EidTrack)
                .filter(EidTrack.eid == "EID00A0000001", EidTrack.type == "A")
                .all()
            )
            assert len(a_tracks) >= 1, "11f: 缺少 type='A' 记录"
            track = a_tracks[-1]
            assert "asset_type" in track.remark
            assert "01" in track.remark  # 旧值
            assert "02" in track.remark  # 新值

    def test_update_no_asset_change_no_a_track(self, app: Flask) -> None:
        """更新非资产属性字段（如 remark）也应写 A 记录（remark 在白名单内）。"""
        with app.app_context():
            _seed_eid()
            svc = SystemService()

            svc.update_eid(
                "IT00A",
                "EID00A0000001",
                {
                    "remark": "测试备注",
                    "opercd": "T00001",
                },
            )

            a_tracks = (
                db.session.query(EidTrack)
                .filter(EidTrack.eid == "EID00A0000001", EidTrack.type == "A")
                .all()
            )
            assert len(a_tracks) >= 1, "remark 在白名单内，应写 A 记录"

    def test_update_no_change_no_a_track(self, app: Flask) -> None:
        """无实际变更时不写 A 记录（避免噪声）。"""
        with app.app_context():
            _seed_eid()
            svc = SystemService()

            # 传入与当前值相同的 asset_type
            svc.update_eid(
                "IT00A",
                "EID00A0000001",
                {
                    "asset_type": "01",
                    "opercd": "T00001",
                },
            )

            a_tracks = (
                db.session.query(EidTrack)
                .filter(EidTrack.eid == "EID00A0000001", EidTrack.type == "A")
                .all()
            )
            assert len(a_tracks) == 0, "无变更不应写 A 记录"

    def test_update_eid_not_found_returns_none(self, app: Flask) -> None:
        """EID 不存在时返回 None，不写 A 记录。"""
        with app.app_context():
            _seed_eid()
            svc = SystemService()

            result = svc.update_eid(
                "IT00A",
                "EID_NOT_EXIST",
                {
                    "asset_type": "02",
                    "opercd": "T00001",
                },
            )

            assert result is None
            a_tracks = (
                db.session.query(EidTrack)
                .filter(EidTrack.eid == "EID_NOT_EXIST", EidTrack.type == "A")
                .all()
            )
            assert len(a_tracks) == 0

    def test_update_writes_both_a_and_u(self, app: Flask) -> None:
        """资产编辑同时写业务语义层 A 和 DB 操作层 u（11a 事件监听）。"""
        with app.app_context():
            _seed_eid()
            svc = SystemService()

            svc.update_eid(
                "IT00A",
                "EID00A0000001",
                {
                    "asset_type": "03",
                    "opercd": "T00001",
                },
            )

            all_tracks = db.session.query(EidTrack).filter(EidTrack.eid == "EID00A0000001").all()
            types = {t.type for t in all_tracks}
            assert "A" in types, "11f: 缺少业务语义层 type='A'"
            assert "u" in types, "11a: 缺少 DB 操作层 type='u'"
