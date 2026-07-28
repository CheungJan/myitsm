TRIGGER "CCGL".trig_u_tpc03

  after update on TPC03_PCPLANSTATUS
        for each row


begin


 insert into tpc03_pcplanstatus_track
   (seqno, itemcd, rgstqty, auditqty, pcqty, opercd, memo, gendate, useflg, upddate, refbillid, n_rgstqty, n_auditqty, n_pcqty, n_refbillid,status)
 values
   (tpc03_seqno.nextval , :new.itemcd, :old.rgstqty, :old.auditqty, :old.pcqty, :new.opercd, :new.memo,
    :new.gendate, :new.useflg, :new.upddate, :new.refbillid, :new.rgstqty, :new.auditqty, :new.pcqty, :new.refbillid,'u');


        end;
