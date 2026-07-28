TRIGGER "CCGL".trig_u_sm_open_status

  after update  of sys_status on sm_in_open_result
        for each row


begin

      if :new.sys_status='2' then

          insert into SM_OPEN_F_TIME
          (PLANID,UPDATE_TIME,C_STAUS)
           values
            (:new.plan_no,sysdate,:old.sys_status||'/'||:new.sys_status);


         end if ;

  end;
