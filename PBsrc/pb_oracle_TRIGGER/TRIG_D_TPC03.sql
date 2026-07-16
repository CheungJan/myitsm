TRIGGER "CCGL".trig_d_tpc03

  after delete on TPC03_PCPLANSTATUS
        for each row


begin


 insert into tpc03_pcplanstatus_track
   (seqno, itemcd, rgstqty, auditqty, pcqty, opercd, memo, gendate, useflg, upddate, refbillid, n_rgstqty, n_auditqty, n_pcqty, n_refbillid,status)
 values
   (tpc03_seqno.nextval , :old.itemcd, :old.rgstqty, :old.auditqty, :old.pcqty, :old.opercd, :old.memo,
    :old.gendate, :old.useflg, :old.upddate, :old.refbillid, :old.rgstqty, :old.auditqty, :old.pcqty, :old.refbillid,'d');


        end;
