procedure usp_tsl10_status
(as_opbillid char, as_slbillid char  ,as_return out varchar2)

as
v_opbillid char(8);
V_slbillid char(8);

begin

v_opbillid:=as_opbillid;
V_slbillid:=as_slbillid;


update tsl10_slbill
set tsl10_slbill.planqty= tsl10_slbill.planqty+(
select sum(tsl02_extenddt.planqty) from tsl02_extenddt  where  tsl02_extenddt.opbillid=v_opbillid)
where slbillid=v_slbillid;





-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
