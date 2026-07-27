procedure up_getdata
(v_itemcd varchar2 , v_cur_result OUT SYS_REFCURSOR)
as

as_itemcd varchar2(10);


begin

as_itemcd:=v_itemcd;--||'%';

open v_cur_result for
select itemcd||itemnm,whnm,itemqty from  ccgl.v_getdata
where itemcd like as_itemcd;


-------------------------
--v_result:='OK';
-------------------

--EXCEPTION
-- when others then
 --  v_result:=sqlcode||sqlerrm;


end ;
