TRIGGER "CCGL".trig_u_plan_status

  after update  of status on plan_cust
        for each row


begin
 /*when '00' then '（计划中）'
      when '01' then '（计划完成）'
        when '02' then '（分派中）'
          when '03' then '（实施完成）'
            when '04' then '（实施中）'
              when '08' then '（计划退回）'
 */
      if :new.status='01' then

        insert into PLAN_F_TIME
        (PLANID,UPDATE_TIME,C_STAUS)
         values
          (:new.planno,sysdate,:old.status||'/'||:new.status);


       end if ;

  end;
