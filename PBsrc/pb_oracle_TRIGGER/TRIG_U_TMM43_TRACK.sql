TRIGGER "CCGL".trig_u_tmm43_track

  after update on tmm43_eid
        for each row


begin


  insert into tmm43_eid_track
    (seqno, type, change_date, itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, new_old, n_sflg, n_refid, n_qcflg, n_whcd, n_prddate, n_itemtyp, n_new_old,
     n_itemcd, n_etyp, remark, n_remark, manuf_seq, n_manf_seq, old_degree, n_old_degree )
  values
    (TMM43_seqno.Nextval , 'u', sysdate, :new.itemcd, :new.eid, :new.opercd, :new.gendate,
    :new.useflg,:new.etyp,:old.sflg, :old.refid,:old.qcflg, :old.whcd,
     :old.prddate,:old.itemtyp, :old.new_old,
      :new.sflg, :new.refid, :new.qcflg,:new.whcd, :new.prddate, :new.itemtyp,:new.new_old,
      :new.itemcd,:new.etyp,:old.remark,:new.remark,:old.manuf_seq,:new.manuf_seq,:old.old_degree,:new.old_degree);




        end;
