"""Eid 模型事件监听：自动写 tmm43_eid_track i/u/d 记录。

对齐 PB 触发器 TRIG_I/U/D_TMM43_TRACK：
- after_insert: type='i'，记录新值
- after_update: type='u'，记录旧/新值（仅变更字段）
- after_delete: type='d'，记录旧值

与业务语义层 C/R/T/A 互补：
- DB 操作层 i/u/d：本模块自动写，记录 tmm43_eid 的任何 INSERT/UPDATE/DELETE
- 业务语义层 C/R/T/A：由各 service 显式调用 SystemRepository.create_eid_track()
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import event, insert
from sqlalchemy import inspect as sa_inspect

logger = logging.getLogger(__name__)

# 追踪的字段列表（对齐 PB TRIG_U_TMM43_TRACK + 资产扩展字段）
_TRACKED_FIELDS: tuple[str, ...] = (
    "sflg",
    "refid",
    "qcflg",
    "whcd",
    "prddate",
    "itemtyp",
    "new_old",
    "remark",
    "manuf_seq",
    "old_degree",
    "etyp",
    "useflg",
    "asset_type",
    "recyclable",
    "recycle_status",
    "asset_owner",
    "install_date",
)

_LISTENERS_REGISTERED: bool = False


def register_eid_listeners() -> None:
    """注册 Eid 模型事件监听。

    幂等：重复调用不会重复注册。
    注册失败时记录错误日志并抛出，避免静默失效导致 i/u/d 记录丢失。
    """
    global _LISTENERS_REGISTERED
    if _LISTENERS_REGISTERED:
        return

    try:
        from app.models.master import Eid, EidTrack
    except ImportError as e:
        logger.error("注册 Eid 事件监听失败：无法导入模型 %s", e, exc_info=True)
        raise

    @event.listens_for(Eid, "after_insert")
    def _write_track_on_insert(mapper: Any, connection: Any, target: Eid) -> None:
        """INSERT 时写 type='i'（对齐 TRIG_I_TMM43_TRACK）。"""
        now = datetime.now(UTC)
        connection.execute(
            insert(EidTrack),
            {
                "type": "i",
                "change_date": now,
                "itemcd": target.itemcd,
                "eid": target.eid,
                "opercd": target.opercd or "",
                "gendate": now,
                "useflg": target.useflg or "1",
                "etyp": target.etyp,
                "sflg": target.sflg,
                "refid": target.refid,
                "qcflg": target.qcflg,
                "whcd": target.whcd,
                "prddate": target.prddate,
                "itemtyp": target.itemtyp,
                "new_old": target.new_old,
                "remark": target.remark,
                "manuf_seq": target.manuf_seq,
                "old_degree": target.old_degree,
                "asset_type": target.asset_type,
                "recyclable": _bool_to_str(target.recyclable),
                "recycle_status": target.recycle_status,
                "asset_owner": target.asset_owner,
                "install_date": target.install_date,
            },
        )

    @event.listens_for(Eid, "after_update")
    def _write_track_on_update(mapper: Any, connection: Any, target: Eid) -> None:
        """UPDATE 时写 type='u'（对齐 TRIG_U_TMM43_TRACK）。

        仅在追踪字段实际变更时写入，避免无变更的 UPDATE 产生噪声记录。
        """
        state = sa_inspect(target)
        changes: dict[str, tuple[Any, Any]] = {}
        for attr in _TRACKED_FIELDS:
            hist = state.attrs[attr].history
            if hist.has_changes():
                old_val = hist.deleted[0] if hist.deleted else None
                new_val = hist.added[0] if hist.added else None
                changes[attr] = (old_val, new_val)

        if not changes:
            return

        now = datetime.now(UTC)
        # 旧值（变更前）
        old = {attr: changes[attr][0] for attr in changes}
        # 新值（变更后）
        new = {attr: changes[attr][1] for attr in changes}

        connection.execute(
            insert(EidTrack),
            {
                "type": "u",
                "change_date": now,
                "itemcd": target.itemcd,
                "eid": target.eid,
                "opercd": target.opercd or "",
                "gendate": now,
                "useflg": target.useflg or "1",
                "etyp": old.get("etyp"),
                "sflg": old.get("sflg"),
                "refid": old.get("refid"),
                "qcflg": old.get("qcflg"),
                "whcd": old.get("whcd"),
                "prddate": old.get("prddate"),
                "itemtyp": old.get("itemtyp"),
                "new_old": old.get("new_old"),
                "remark": old.get("remark"),
                "manuf_seq": old.get("manuf_seq"),
                "old_degree": old.get("old_degree"),
                "asset_type": old.get("asset_type"),
                "recyclable": _bool_to_str(old.get("recyclable")),
                "recycle_status": old.get("recycle_status"),
                "asset_owner": old.get("asset_owner"),
                "install_date": old.get("install_date"),
                # 新值
                "n_etyp": new.get("etyp"),
                "n_sflg": new.get("sflg"),
                "n_refid": new.get("refid"),
                "n_qcflg": new.get("qcflg"),
                "n_whcd": new.get("whcd"),
                "n_prddate": new.get("prddate"),
                "n_itemtyp": new.get("itemtyp"),
                "n_new_old": new.get("new_old"),
                "n_remark": new.get("remark"),
                "n_manf_seq": new.get("manuf_seq"),
                "n_old_degree": new.get("old_degree"),
                "n_asset_type": new.get("asset_type"),
                "n_recyclable": _bool_to_str(new.get("recyclable")),
                "n_recycle_status": new.get("recycle_status"),
                "n_asset_owner": new.get("asset_owner"),
                "n_install_date": new.get("install_date"),
            },
        )

    @event.listens_for(Eid, "after_delete")
    def _write_track_on_delete(mapper: Any, connection: Any, target: Eid) -> None:
        """DELETE 时写 type='d'（对齐 TRIG_D_TMM43_TRACK）。"""
        now = datetime.now(UTC)
        connection.execute(
            insert(EidTrack),
            {
                "type": "d",
                "change_date": now,
                "itemcd": target.itemcd,
                "eid": target.eid,
                "opercd": target.opercd or "",
                "gendate": now,
                "useflg": target.useflg or "1",
                "etyp": target.etyp,
                "sflg": target.sflg,
                "refid": target.refid,
                "qcflg": target.qcflg,
                "whcd": target.whcd,
                "prddate": target.prddate,
                "itemtyp": target.itemtyp,
                "new_old": target.new_old,
                "remark": target.remark,
                "manuf_seq": target.manuf_seq,
                "old_degree": target.old_degree,
                "asset_type": target.asset_type,
                "recyclable": _bool_to_str(target.recyclable),
                "recycle_status": target.recycle_status,
                "asset_owner": target.asset_owner,
                "install_date": target.install_date,
            },
        )

    _LISTENERS_REGISTERED = True


def _bool_to_str(value: Any) -> str | None:
    """布尔值转字符串（recyclable 字段兼容）。"""
    if value is None:
        return None
    return "1" if value else "0"
