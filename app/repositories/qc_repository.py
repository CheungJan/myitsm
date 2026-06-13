"""质检管理数据访问层。"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import g
from sqlalchemy import func, or_

from app.extensions import db
from app.models.warehouse import QcResult, QcResultDt, QcResultEid


def _gen_qc_id() -> str:
    """生成质检单号 (QC + YYMMDD + 3位序号)。"""
    today = datetime.now(timezone.utc).strftime("%y%m%d")
    prefix = f"QC{today}"
    row = db.session.execute(
        db.text(
            "SELECT COALESCE(MAX(qcbillid), :prefix) FROM tqc10_result "
            "WHERE qcbillid LIKE :pattern"
        ),
        {"prefix": prefix, "pattern": f"{prefix}%"},
    ).fetchone()
    last_id = row[0] if row else prefix
    seq = int(last_id[len(prefix):] or "0") + 1
    return f"{prefix}{seq:03d}"


def _gen_batch_id() -> str:
    """生成批次号 (BAT + YYMMDD + 3位序号)。"""
    today = datetime.now(timezone.utc).strftime("%y%m%d")
    prefix = f"BAT{today}"
    row = db.session.execute(
        db.text(
            "SELECT COALESCE(MAX(batch_id), :prefix) FROM tqc10_result "
            "WHERE batch_id LIKE :pattern"
        ),
        {"prefix": prefix, "pattern": f"{prefix}%"},
    ).fetchone()
    last_id = row[0] if row else prefix
    seq = int(last_id[len(prefix):] or "0") + 1
    return f"{prefix}{seq:03d}"


class QcRepository:
    """质检结果数据访问。"""

    @staticmethod
    def find_draft_by_refbillid(refbillid: str) -> QcResult | None:
        """查询同一来源单是否有未审核/已退回的 QC 记录。"""
        if not refbillid:
            return None
        return db.session.query(QcResult).filter(
            QcResult.refbillid == refbillid,
            QcResult.auditflg.in_(["0", "8"]),
            QcResult.useflg == "1",
        ).first()

    @staticmethod
    def list_results(
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
    ) -> tuple[list[QcResult], int]:
        q = db.session.query(QcResult)
        if search:
            q = q.filter(
                db.or_(
                    QcResult.qcbillid.ilike(f"%{search}%"),
                    QcResult.refbillid.ilike(f"%{search}%"),
                    QcResult.itemcd.ilike(f"%{search}%"),
                    QcResult.eid.ilike(f"%{search}%"),
                )
            )
        q = q.order_by(QcResult.gendate.desc())
        total = q.count()
        rows = q.offset((page - 1) * per_page).limit(per_page).all()
        return rows, total

    @staticmethod
    def get_result(qcbillid: str) -> QcResult | None:
        return db.session.get(QcResult, qcbillid)

    @staticmethod
    def list_details(qcbillid: str) -> list[QcResultDt]:
        return list(
            db.session.query(QcResultDt)
            .filter(QcResultDt.qcbillid == qcbillid)
            .order_by(QcResultDt.lineno)
            .all()
        )

    @staticmethod
    def list_eid_details(qcbillid: str) -> list[QcResultEid]:
        return list(
            db.session.query(QcResultEid)
            .filter(QcResultEid.qcbillid == qcbillid)
            .order_by(QcResultEid.lineno)
            .all()
        )

    @staticmethod
    def create(data: dict[str, object]) -> QcResult:
        qc = QcResult(**data)
        qc.qcbillid = _gen_qc_id()
        if not qc.batch_id:
            qc.batch_id = _gen_batch_id()
        qc.opercd = g.get("current_user", "")
        qc.gendate = datetime.now(timezone.utc)
        qc.auditflg = "0"
        db.session.add(qc)
        db.session.commit()
        return qc

    @staticmethod
    def add_detail(
        qcbillid: str,
        lineno: int,
        data: dict[str, object],
    ) -> QcResultDt:
        data.pop("lineno", None)
        detail = QcResultDt(qcbillid=qcbillid, lineno=lineno, **data)
        db.session.add(detail)
        return detail

    @staticmethod
    def add_eid_detail(
        qcbillid: str,
        lineno: int,
        data: dict[str, object],
    ) -> QcResultEid:
        data.pop("lineno", None)
        detail = QcResultEid(qcbillid=qcbillid, lineno=lineno, **data)
        db.session.add(detail)
        return detail

    @staticmethod
    def audit(qc: QcResult, auditor: str, auditflg: str = "1", checkmemo: str | None = None) -> QcResult:
        qc.auditflg = auditflg
        qc.auditman = auditor
        qc.auditdate = datetime.now(timezone.utc)
        if checkmemo:
            qc.memo = (qc.memo or "") + f" [审核备注: {checkmemo}]"
        db.session.commit()
        return qc

    @staticmethod
    def void(qc: QcResult, operator: str) -> QcResult:
        qc.auditflg = "V"
        qc.opercd = operator
        qc.upddate = datetime.now(timezone.utc)
        db.session.commit()
        return qc

    @staticmethod
    def list_batches(
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        auditflg: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        eid: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """按批次聚合查询 QC 结果。"""
        from sqlalchemy import text

        eid_join = "LEFT JOIN tqc11_resulteid eid ON q.qcbillid = eid.qcbillid" if eid else ""
        eid_filter = "AND eid.eid LIKE :eid" if eid else ""

        sql = text(f"""
            SELECT
                q.batch_id,
                MIN(q.refbillid) as refbillid,
                MIN(q.gendate) as gendate,
                MIN(q.opercd) as opercd,
                MIN(q.auditflg) as auditflg,
                MIN(q.draft_type) as draft_type,
                COUNT(DISTINCT q.qcbillid) as total_count,
                SUM(CASE WHEN q.qcstatus = 'GA' THEN 1 ELSE 0 END) as ga_count,
                SUM(CASE WHEN q.qcstatus = 'GB' THEN 1 ELSE 0 END) as gb_count,
                SUM(CASE WHEN q.qcstatus = 'GC' THEN 1 ELSE 0 END) as gc_count,
                SUM(CASE WHEN q.qcstatus = 'BF' THEN 1 ELSE 0 END) as bf_count,
                SUM(CASE WHEN q.qcstatus = 'BH' THEN 1 ELSE 0 END) as bh_count,
                SUM(CASE WHEN q.qcstatus = 'TH' THEN 1 ELSE 0 END) as th_count,
                CASE WHEN EXISTS (
                    SELECT 1 FROM tqc10_result q2
                    JOIN tqc11_resultdt dt ON q2.qcbillid = dt.qcbillid
                    WHERE q2.batch_id = q.batch_id AND dt.replenish_status = 'pending'
                ) OR EXISTS (
                    SELECT 1 FROM tqc10_result q3
                    JOIN tqc11_resulteid eid2 ON q3.qcbillid = eid2.qcbillid
                    WHERE q3.batch_id = q.batch_id AND eid2.replenish_status = 'pending'
                ) THEN 1 ELSE 0 END AS has_pending_replenish
            FROM tqc10_result q
            {eid_join}
            WHERE q.useflg = '1' AND q.batch_id IS NOT NULL
            AND (:search IS NULL OR q.batch_id LIKE :search OR q.refbillid LIKE :search)
            AND (:start_date IS NULL OR q.gendate >= CAST(:start_date AS TIMESTAMP))
            AND (:end_date IS NULL OR q.gendate < CAST(:end_date AS TIMESTAMP) + INTERVAL '1 day')
            {eid_filter}
            GROUP BY q.batch_id
            HAVING (:auditflg IS NULL OR MIN(q.auditflg) = :auditflg)
            ORDER BY MIN(q.gendate) DESC
            LIMIT :per_page OFFSET :offset
        """)
        offset = (page - 1) * per_page
        params: dict[str, Any] = {
            "search": f"%{search}%" if search else None,
            "auditflg": auditflg,
            "start_date": start_date,
            "end_date": end_date,
            "eid": f"%{eid}%" if eid else None,
            "per_page": per_page,
            "offset": offset,
        }
        rows = db.session.execute(sql, params).fetchall()

        eid_count_join = "LEFT JOIN tqc11_resulteid eid ON q.qcbillid = eid.qcbillid" if eid else ""
        eid_count_filter = "AND eid.eid LIKE :eid" if eid else ""
        count_sql = text(f"""
            SELECT COUNT(*) FROM (
                SELECT q.batch_id
                FROM tqc10_result q
                {eid_count_join}
                WHERE q.useflg = '1' AND q.batch_id IS NOT NULL
                AND (:search IS NULL OR q.batch_id LIKE :search OR q.refbillid LIKE :search)
                AND (:start_date IS NULL OR q.gendate >= CAST(:start_date AS TIMESTAMP))
                AND (:end_date IS NULL OR q.gendate < CAST(:end_date AS TIMESTAMP) + INTERVAL '1 day')
                {eid_count_filter}
                GROUP BY q.batch_id
                HAVING (:auditflg IS NULL OR MIN(q.auditflg) = :auditflg)
            ) sub
        """)
        total = db.session.execute(count_sql, params).scalar() or 0

        batches: list[dict[str, Any]] = []
        for r in rows:
            batches.append({
                "batch_id": r.batch_id,
                "refbillid": r.refbillid or "",
                "gendate": r.gendate.isoformat() if r.gendate else "",
                "opercd": r.opercd or "",
                "auditflg": r.auditflg or "0",
                "total_count": r.total_count,
                "ga_count": r.ga_count or 0,
                "gb_count": r.gb_count or 0,
                "gc_count": r.gc_count or 0,
                "bf_count": r.bf_count or 0,
                "bh_count": r.bh_count or 0,
                "th_count": r.th_count or 0,
            })
        return batches, total

    @staticmethod
    def get_batch_details(batch_id: str) -> list[QcResult]:
        """获取批次下所有子记录。"""
        return db.session.query(QcResult).filter(
            QcResult.batch_id == batch_id,
            QcResult.useflg == "1",
        ).all()

    @staticmethod
    def batch_audit(
        batch_id: str, auditor: str, auditflg: str = "1",
        checkmemo: str | None = None,
    ) -> list[QcResult]:
        """批次审核（批量更新所有子记录）。"""
        qcs = QcRepository.get_batch_details(batch_id)
        for qc in qcs:
            qc.auditflg = auditflg
            qc.auditman = auditor
            qc.auditdate = datetime.now(timezone.utc)
            if checkmemo:
                qc.memo = (qc.memo or "") + f" [审核备注: {checkmemo}]"
        db.session.commit()
        return qcs

    @staticmethod
    def batch_delete(batch_id: str) -> None:
        """删除批次下所有子记录及明细（用于重新编辑时覆盖）。"""
        qcs = QcRepository.get_batch_details(batch_id)
        for qc in qcs:
            db.session.query(QcResultDt).filter(QcResultDt.qcbillid == qc.qcbillid).delete()
            db.session.query(QcResultEid).filter(QcResultEid.qcbillid == qc.qcbillid).delete()
            db.session.delete(qc)
        db.session.commit()

    @staticmethod
    def batch_void(batch_id: str, operator: str) -> list[QcResult]:
        """批次作废（所有子记录统一作废）。"""
        qcs = QcRepository.get_batch_details(batch_id)
        for qc in qcs:
            if qc.auditflg == "1":
                raise ValueError("批次包含已审核记录，不可作废")
            qc.auditflg = "V"
            qc.opercd = operator
            qc.upddate = datetime.now(timezone.utc)
        db.session.commit()
        return qcs

    @staticmethod
    def get_eids_by_refbillid(refbillid: str) -> list[QcResultEid]:
        """获取指定来源单据的所有已审核EID记录（用于FQC回显IPQC的配件EID）。"""
        return list(
            db.session.query(QcResultEid)
            .join(QcResult, QcResultEid.qcbillid == QcResult.qcbillid)
            .filter(
                QcResult.refbillid == refbillid,
                QcResult.auditflg == "1",
                QcResult.useflg == "1",
            )
            .order_by(QcResultEid.lineno)
            .all()
        )

    @staticmethod
    def get_non_pass_details(batch_id: str) -> tuple[list[QcResultDt], list[QcResultEid]]:
        """获取批次中所有 BF/BH/TH 且未补料的明细行。"""
        qcs = QcRepository.get_batch_details(batch_id)
        qcbillids = [q.qcbillid for q in qcs]
        if not qcbillids:
            return [], []
        prd_rows = db.session.query(QcResultDt).filter(
            QcResultDt.qcbillid.in_(qcbillids),
            QcResultDt.qcstatus.in_(["BF", "BH", "TH"]),
            db.or_(
                QcResultDt.replenish_ov_billid == "",
                QcResultDt.replenish_ov_billid.is_(None),
            ),
        ).all()
        eid_rows = db.session.query(QcResultEid).filter(
            QcResultEid.qcbillid.in_(qcbillids),
            QcResultEid.qcstatus.in_(["BF", "BH", "TH"]),
            db.or_(
                QcResultEid.replenish_ov_billid == "",
                QcResultEid.replenish_ov_billid.is_(None),
            ),
        ).all()
        return list(prd_rows), list(eid_rows)

    @staticmethod
    def mark_details_replenished(batch_id: str, replenish_ov_billid: str) -> int:
        """标记批次中所有非合格行为已申请补料，返回更新的行数。"""
        qcs = QcRepository.get_batch_details(batch_id)
        qcbillids = [q.qcbillid for q in qcs]
        if not qcbillids:
            return 0
        count = 0
        count += db.session.query(QcResultDt).filter(
            QcResultDt.qcbillid.in_(qcbillids),
            QcResultDt.qcstatus.in_(["BF", "BH", "TH"]),
            db.or_(
                QcResultDt.replenish_ov_billid == "",
                QcResultDt.replenish_ov_billid.is_(None),
            ),
        ).update(
            {"replenish_status": "pending", "replenish_ov_billid": replenish_ov_billid},
            synchronize_session=False,
        )
        count += db.session.query(QcResultEid).filter(
            QcResultEid.qcbillid.in_(qcbillids),
            QcResultEid.qcstatus.in_(["BF", "BH", "TH"]),
            db.or_(
                QcResultEid.replenish_ov_billid == "",
                QcResultEid.replenish_ov_billid.is_(None),
            ),
        ).update(
            {"replenish_status": "pending", "replenish_ov_billid": replenish_ov_billid},
            synchronize_session=False,
        )
        return count

    @staticmethod
    def get_stats() -> list[dict[str, object]]:
        """按质检状态统计。"""
        rows = (
            db.session.query(
                QcResult.qcstatus,
                func.count(QcResult.qcbillid).label("cnt"),
            )
            .group_by(QcResult.qcstatus)
            .order_by(QcResult.qcstatus)
            .all()
        )
        return [{"qcstatus": r.qcstatus or "未知", "cnt": r.cnt} for r in rows]

    @staticmethod
    def get_ov5_completion() -> dict[str, Any]:
        """OV=5 质检出库 QC 完成情况 + 下游单据统计。"""
        from app.models.warehouse import StockOut, StockOutDetailPrd, StockIn as SIN
        from sqlalchemy import text

        # OV=5 总数
        total_ov5 = db.session.query(func.count(StockOut.outbillid)).filter(
            StockOut.invtyp == "5", StockOut.auditflg == "2"
        ).scalar() or 0

        # 已完成QC的OV=5（所有出库行都已QC审核）
        done_sql = text("""
            SELECT COUNT(*) FROM (
                SELECT o.outbillid,
                       COALESCE(SUM(d.outqty), 0) as total_out,
                       COALESCE(qc_done.qc_qty, 0) as qc_done_qty
                FROM twh15_out o
                JOIN twh16_outdtprd d ON o.outbillid = d.outbillid
                LEFT JOIN (
                    SELECT q.refbillid, SUM(COALESCE(dt.qcqty, 0) + COALESCE(eid.qcqty, 0)) as qc_qty
                    FROM tqc10_result q
                    LEFT JOIN tqc11_resultdt dt ON q.qcbillid = dt.qcbillid
                    LEFT JOIN tqc11_resulteid eid ON q.qcbillid = eid.qcbillid
                    WHERE q.auditflg = '1'
                    GROUP BY q.refbillid
                ) qc_done ON o.outbillid = qc_done.refbillid
                WHERE o.invtyp = '5' AND o.auditflg = '2'
                GROUP BY o.outbillid, qc_done.qc_qty
                HAVING COALESCE(SUM(d.outqty), 0) <= COALESCE(qc_done.qc_qty, 0)
            ) sub
        """)
        done_count = db.session.execute(done_sql).scalar() or 0

        # 下游单据统计
        in_count = db.session.query(func.count(SIN.inbillid)).filter(
            SIN.invtyp == "11", SIN.refbillid.like("QC%")
        ).scalar() or 0

        out_count = db.session.query(func.count(StockOut.outbillid)).filter(
            StockOut.invtyp.in_(["6", "7", "9"]), StockOut.refbillid.like("QC%"),
            StockOut.auditflg != "V"
        ).scalar() or 0

        return {
            "total_ov5": total_ov5,
            "done_ov5": done_count,
            "pending_ov5": total_ov5 - done_count,
            "iv11_count": in_count,
            "ov_out_count": out_count,
        }
