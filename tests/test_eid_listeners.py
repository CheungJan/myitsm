"""11a 测试：Eid 模型事件监听自动写 tmm43_eid_track i/u/d 记录。

验证对齐 PB 触发器 TRIG_I/U/D_TMM43_TRACK 的行为：
- after_insert: type='i'
- after_update: type='u'（仅追踪字段变更时）
- after_delete: type='d'
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models.master import Eid, EidTrack


def _seed_eid(eid: str = "EIDTEST000001", itemcd: str = "IT0001") -> Eid:
    """插入测试 EID 并提交。"""
    record = Eid(
        itemcd=itemcd,
        eid=eid,
        opercd="T00001",
        gendate=datetime.now(UTC),
        useflg="1",
        sflg="8",
        whcd="W1",
    )
    db.session.add(record)
    db.session.commit()
    return record


def _tracks_for_eid(eid: str) -> list[EidTrack]:
    """查询指定 EID 的所有 track 记录。"""
    return (
        db.session.query(EidTrack)
        .filter(EidTrack.eid == eid)
        .order_by(EidTrack.seqno)
        .all()
    )


class TestEidListeners:
    """Eid 事件监听测试。"""

    def test_after_insert_writes_i_track(self, app: Flask) -> None:
        """INSERT 时写 type='i' 记录。"""
        with app.app_context():
            db.session.query(EidTrack).delete()
            db.session.query(Eid).filter(Eid.eid == "EIDTEST000001").delete()
            db.session.commit()

            _seed_eid()

            tracks = _tracks_for_eid("EIDTEST000001")
            assert len(tracks) == 1
            assert tracks[0].type == "i"
            assert tracks[0].itemcd == "IT0001"
            assert tracks[0].sflg == "8"
            assert tracks[0].whcd == "W1"

            db.session.query(EidTrack).delete()
            db.session.query(Eid).filter(Eid.eid == "EIDTEST000001").delete()
            db.session.commit()

    def test_after_update_writes_u_track(self, app: Flask) -> None:
        """UPDATE 追踪字段时写 type='u' 记录，含旧/新值。"""
        with app.app_context():
            db.session.query(EidTrack).delete()
            db.session.query(Eid).filter(Eid.eid == "EIDTEST000002").delete()
            db.session.commit()

            record = _seed_eid(eid="EIDTEST000002")
            old_sflg = record.sflg

            record.sflg = "1"
            record.whcd = "W2"
            db.session.commit()

            tracks = _tracks_for_eid("EIDTEST000002")
            assert len(tracks) == 2
            u_track = tracks[1]
            assert u_track.type == "u"
            assert u_track.sflg == old_sflg
            assert u_track.n_sflg == "1"
            assert u_track.whcd == "W1"
            assert u_track.n_whcd == "W2"

            db.session.query(EidTrack).delete()
            db.session.query(Eid).filter(Eid.eid == "EIDTEST000002").delete()
            db.session.commit()

    def test_after_update_no_tracked_change_no_track(self, app: Flask) -> None:
        """UPDATE 非追踪字段时不写 type='u' 记录。"""
        with app.app_context():
            db.session.query(EidTrack).delete()
            db.session.query(Eid).filter(Eid.eid == "EIDTEST000003").delete()
            db.session.commit()

            record = _seed_eid(eid="EIDTEST000003")
            # 仅修改非追踪字段（opercd 不在 _TRACKED_FIELDS）
            record.opercd = "T00002"
            db.session.commit()

            tracks = _tracks_for_eid("EIDTEST000003")
            assert len(tracks) == 1  # 仅 insert 的 i 记录

            db.session.query(EidTrack).delete()
            db.session.query(Eid).filter(Eid.eid == "EIDTEST000003").delete()
            db.session.commit()

    def test_after_delete_writes_d_track(self, app: Flask) -> None:
        """DELETE 时写 type='d' 记录。"""
        with app.app_context():
            db.session.query(EidTrack).delete()
            db.session.query(Eid).filter(Eid.eid == "EIDTEST000004").delete()
            db.session.commit()

            record = _seed_eid(eid="EIDTEST000004")

            db.session.delete(record)
            db.session.commit()

            tracks = _tracks_for_eid("EIDTEST000004")
            assert len(tracks) == 2
            assert tracks[0].type == "i"
            assert tracks[1].type == "d"
            assert tracks[1].sflg == "8"
            assert tracks[1].whcd == "W1"

            db.session.query(EidTrack).delete()
            db.session.commit()
