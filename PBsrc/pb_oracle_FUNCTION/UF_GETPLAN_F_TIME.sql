FUNCTION uf_getplan_f_time(
  v_palnid    IN   varCHAR2 -- 预计话单号

)
  RETURN date
AS

  ld_return      date ;
BEGIN

--c_type, requset_paper_id ,current_status,is_success,request_time,close_time
select nvl(plan_f_time.update_time,sysdate)

into ld_return

 from plan_cust left outer join   plan_f_time
 on plan_cust.planno=plan_f_time.planid
where plan_cust.planno=v_palnid ;

        return ld_return ;

EXCEPTION
when others then



   RETURN sysdate;
END uf_getplan_f_time;
