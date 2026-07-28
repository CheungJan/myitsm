procedure up_getitemnm
(as_eid varchar2  ,as_itemnm out varchar2)
as

v_eid varchar2(13);

v_itemnm varchar2(128);

v_sflg char(1);


begin
v_eid:=as_eid;


select b.itemnm,a.sflg into v_itemnm ,v_sflg from tmm43_eid  a
inner join tmm12_items b
on a.itemcd=b.itemcd
where a.useflg='1' and a.eid=v_eid ;
if sql%rowcount=1 then
   as_itemnm:=v_itemnm;

   if v_sflg<>'8' then
      as_itemnm:='有配件但不可用';
   end if ;
else
   as_itemnm:='没有该配件';
end if ;


-------------------------

-------------------

EXCEPTION
 when others then
   -- as_itemnm:=sqlcode||sqlerrm;
      as_itemnm:='没有该配件';

end ;

