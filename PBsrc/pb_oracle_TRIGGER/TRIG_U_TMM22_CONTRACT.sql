TRIGGER "CCGL".trig_u_tmm22_CONTRACT

  after update  of is_CONTRACT on tmm22_customers
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
            (:new.custcd, :old.is_contract,:new.is_contract ,
            sysdate,sysdate,:new.opercd);


            if :old.is_contract='0' and :new.is_contract='1' then -----入网

               update TMM22_CONTRACT_status
                      set in_date=sysdate , out_date=''
                      where custcd=:new.custcd ;

            end if ;


             if :old.is_contract='1' and :new.is_contract='0' then -----退网

               update TMM22_CONTRACT_status
                      set  out_date=sysdate
                      where custcd=:new.custcd ;

            end if ;


  end;
