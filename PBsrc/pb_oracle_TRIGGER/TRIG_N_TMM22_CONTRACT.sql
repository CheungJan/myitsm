TRIGGER "CCGL".trig_n_tmm22_CONTRACT

  after insert  on tmm22_customers
        for each row


begin



          insert into TMM22_CONTRACT_C_LIST
          ( custcd     ,
  old_s      ,
  new_s      ,
  c_date     ,
  update_time ,
  userid     )
           values
            (:new.custcd, '',:new.is_contract ,
            sysdate,sysdate,:new.opercd);

     if    :new.is_contract ='1' then
           insert into  TMM22_CONTRACT_STATUS
           (custcd,in_date,out_date,UPLDATE_TIME)
           values
           (:new.custcd,sysdate,'',sysdate) ;
     end if ;


     if    :new.is_contract ='0' then
           insert into  TMM22_CONTRACT_STATUS
           (custcd,in_date,out_date,UPLDATE_TIME)
           values
           (:new.custcd,'','',sysdate) ;
     end if ;



  end;
