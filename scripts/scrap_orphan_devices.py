"""将 1,230 台 sflg='1' 无客户无 BOM 的孤儿设备按轨迹流程报废。

流程：
1. 为每台设备在 tmm43_eid_track 插入 type='u' 变更记录（sflg 1→2, whcd→NULL）
2. 更新 tmm43_eid.sflg='2', whcd=NULL
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    # 1. 查出孤儿设备
    find_sql = db.text("""
        SELECT e.eid FROM tmm43_eid e
        WHERE e.sflg = '1' AND e.useflg = '1'
          AND NOT EXISTS (SELECT 1 FROM tmm35_cust_pos_rl r WHERE r.eid = e.eid)
          AND NOT EXISTS (SELECT 1 FROM tmm44_pos_r_eid p WHERE p.eid = e.eid)
        ORDER BY e.eid
    """)
    eids = [row[0] for row in db.session.execute(find_sql).fetchall()]

    if not eids:
        print("没有找到孤儿设备")
        sys.exit(0)

    print(f"找到 {len(eids)} 台孤儿设备，准备报废...")

    # 2. 获取起始 seqno
    max_seq = db.session.execute(
        db.text("SELECT COALESCE(MAX(seqno), 0) FROM tmm43_eid_track")
    ).scalar()
    now = datetime.now()

    # 3. 逐批插入轨迹 + 更新 Eid
    insert_sql = db.text("""
        INSERT INTO tmm43_eid_track (
            seqno, type, change_date, itemcd, eid, opercd, gendate,
            useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, new_old,
            n_sflg, n_refid, n_qcflg, n_whcd, n_prddate, n_itemtyp, n_new_old,
            n_itemcd, n_etyp, n_asset_type, asset_type,
            n_recyclable, n_recycle_status, n_asset_owner, n_install_date,
            recyclable, recycle_status, asset_owner, install_date,
            old_degree, n_old_degree, manuf_seq, n_manf_seq,
            remark, n_remark, cust_cd, n_cust_cd, created_at, updated_at
        ) VALUES (
            :seqno, 'u', :change_date, :itemcd, :eid, :opercd, :gendate,
            :useflg, :etyp, :sflg, :refid, :qcflg, :whcd, :prddate, :itemtyp, :new_old,
            '2', :refid, :qcflg, NULL, :prddate, :itemtyp, :new_old,
            :itemcd, :etyp, :asset_type, :asset_type,
            :recyclable, :recycle_status, :asset_owner, :install_date,
            :recyclable, :recycle_status, :asset_owner, :install_date,
            :old_degree, :old_degree, :manuf_seq, :manuf_seq,
            NULL, NULL, NULL, NULL, now(), now()
        )
    """)

    update_sql = db.text("""
        UPDATE tmm43_eid SET sflg = '2', whcd = NULL WHERE eid = :eid
    """)

    batch_size = 200
    for i in range(0, len(eids), batch_size):
        batch = eids[i : i + batch_size]
        # 先查 Eid 详情
        rows = db.session.execute(
            db.text("SELECT * FROM tmm43_eid WHERE eid = ANY(:eids)"),
            {"eids": batch},
        ).fetchall()

        params_list = []
        for row in rows:
            max_seq += 1
            params_list.append({
                "seqno": max_seq,
                "change_date": now,
                "itemcd": row.itemcd,
                "eid": row.eid,
                "opercd": row.opercd,
                "gendate": row.gendate,
                "useflg": row.useflg,
                "etyp": row.etyp,
                "sflg": row.sflg,
                "refid": row.refid,
                "qcflg": row.qcflg,
                "whcd": row.whcd,
                "prddate": row.prddate,
                "itemtyp": row.itemtyp,
                "new_old": row.new_old,
                "asset_type": row.asset_type,
                "recyclable": "1" if row.recyclable else "0",
                "recycle_status": row.recycle_status,
                "asset_owner": row.asset_owner,
                "install_date": row.install_date,
                "old_degree": row.old_degree,
                "manuf_seq": row.manuf_seq,
            })

        for p in params_list:
            db.session.execute(insert_sql, p)
            db.session.execute(update_sql, {"eid": p["eid"]})

        db.session.commit()
        print(f"  已处理 {min(i + batch_size, len(eids))}/{len(eids)}")

    # 4. 验证
    verify = db.session.execute(
        db.text("""
            SELECT COUNT(*) FROM tmm43_eid e
            WHERE e.sflg = '1' AND e.useflg = '1'
              AND NOT EXISTS (SELECT 1 FROM tmm35_cust_pos_rl r WHERE r.eid = e.eid)
              AND NOT EXISTS (SELECT 1 FROM tmm44_pos_r_eid p WHERE p.eid = e.eid)
        """)
    ).scalar()

    print(f"\n完成！更新 {len(eids)} 台设备")
    print(f"验证：剩余孤儿设备 = {verify} (应为 0)")
