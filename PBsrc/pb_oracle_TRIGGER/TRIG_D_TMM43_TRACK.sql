TRIGGER "CCGL".trig_d_tmm43_track

  after delete on tmm43_eid
        for each row

        begin


  insert into tmm43_eid_track
    (seqno, type, change_date, itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, new_old, n_sflg, n_refid, n_qcflg, n_whcd, n_prddate, n_itemtyp, n_new_old)
  values
    (TMM43_seqno.Nextval , 'd', sysdate, :old.itemcd, :old.eid, :old.opercd, :old.gendate,
    :old.useflg,:old.etyp,:old.sflg, :old.refid,:old.qcflg, :old.whcd,
     :old.prddate,:old.itemtyp, :old.new_old,
      :old.sflg, :old.refid, :old.qcflg,:old.whcd, :old.prddate, :old.itemtyp,:old.new_old);




        end;
