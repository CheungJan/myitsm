TRIGGER "CCGL".trig_u_sm_part_status

  after update  of sys_status on sm_in_part_change
        for each row


begin

      if :new.sys_status='2' then

          insert into SM_part_f_time
          (PLANID,UPDATE_TIME,C_STAUS)
           values
            (:new.case_no,sysdate,:old.sys_status||'/'||:new.sys_status);


         end if ;

  end;
