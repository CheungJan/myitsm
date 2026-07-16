FUNCTION uf_sm_part_errinfo (
	v_pland    IN   varchar2
	
)
	RETURN varchar2
AS
	v_Result varchar2(500);
BEGIN
v_Result:= '----------';

for c_1 in(select  c.itemnm,a.accessories_id,case a.status when '1' then '缺失' when '2' then '型号不匹配' when '3' then '序列不匹配'  end  status
 from TIT10_POS_DETAIL a
inner join tit10_maintenanceday  b
on a.bill_id=b.maintenance_id
inner join tmm12_items c
on a.itemcd=c.itemcd
where b.requset_paper_id=v_pland and a.status <>'0')
loop

v_Result:=v_Result||chr(10)||chr(13)||c_1.itemnm||'/'||c_1.accessories_id||'/'||c_1.status;


end loop ;

return v_Result ;

	
EXCEPTION
when others then



   RETURN '-';

END uf_sm_part_errinfo;

