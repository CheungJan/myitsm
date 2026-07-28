TRIGGER "CCGL".trig_i_tmm43_track

  after insert on tmm43_eid
        for each row

        begin


  insert into tmm43_eid_track
    (seqno, type, change_date, itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, new_old, n_sflg, n_refid, n_qcflg, n_whcd, n_prddate, n_itemtyp, n_new_old)
  values
    (TMM43_seqno.Nextval , 'i', sysdate, :new.itemcd, :new.eid, :new.opercd, :new.gendate,
    :new.useflg,:new.etyp,:new.sflg, :new.refid,:new.qcflg, :new.whcd,
     :new.prddate,:new.itemtyp, :new.new_old,
      :new.sflg, :new.refid, :new.qcflg,:new.whcd, :new.prddate, :new.itemtyp,:new.new_old);




        end;
