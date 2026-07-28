FUNCTION uf_checkperiod (
  v_eid    IN   varCHAR2, -- eid
  v_newid  in varCHAR2
)
  RETURN char
AS

v_enddate date;
v_custclass varchar2(10);
v_busityp  varchar2(10);
v_message varchar2(256);
v_typ number ;
BEGIN


-----捷强直属全部调换

select c.classcd,c.busityp into v_custclass,  v_busityp from tmm44_pos_r_eid a
inner join tmm35_cust_pos_rl b
on a.posid=b.eid
inner join tmm22_customers c
on b.custcd=c.custcd
where a.eid=v_eid and a.useflg='1' and b.useflg='1' ;

if v_custclass='08' and v_busityp='ZS' then

   return '1';

end if ;
----
/*select "old_degree" into v_typ from data_asset_item@itsm
where  serial = v_newid and ENABLED=1;*/
select "old_degree" into v_typ from
(select * from data_asset_item@itsm
where  serial = v_newid and ENABLED=1 order by id desc) where rownum = 1;


update tmm43_eid
set old_degree=v_typ
where eid= v_newid;



if v_typ=3 then  ---3旧品  12新品
   return '1';
end if ;
-----捷强延伸 过保卖 保内换 延保


  select decode(c.qcflg,'GA', a.gendate + b.newperiod  ,
   'GB'  ,  a.gendate + b.newperiod  ,
   'GC',  a.gendate + b.oldperiod   , sysdate ) ,


   '起始时间：'||nvl(to_char(a.gendate,'yyyy-mm-dd'),'无') ||';'||'配件状态：'||nvl(c.qcflg,'无')||';'||'出保时间：' ||
to_char(decode(c.qcflg,'GA', a.gendate + b.newperiod  ,
   'GB'  ,  a.gendate + b.newperiod  ,
   'GC',  a.gendate + b.oldperiod   , sysdate ) ,'yyyy-mm-dd')


   into v_enddate ,v_message



  from tmm44_pos_r_eid a
  inner join tmm12_items b
  on a.itemcd=b.itemcd
  inner join tmm43_eid c
  on a.eid=c.eid
  where a.eid=v_eid and a.useflg='1' ;

---update  tmp_sm_in_part_change
--set CASE_NO=v_message
---where id=v_id;



  if trunc(v_enddate,'dd')<=trunc(sysdate,'dd') then
     --超质保
      RETURN   '0';

  else
      --质保内
      return  '1' ;

  end if ;




EXCEPTION
 when others then
     return  '9';


END uf_checkperiod;
