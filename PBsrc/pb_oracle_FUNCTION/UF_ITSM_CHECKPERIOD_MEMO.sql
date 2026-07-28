FUNCTION uf_itsm_checkperiod_memo (
  v_eid    IN   varCHAR2, -- eid
  v_newid  in varCHAR2,
  v_mid in varCHAR2
)
  RETURN varchar2
AS

v_enddate date;
v_custclass varchar2(10);
v_busityp  varchar2(10);
v_message varchar2(256);
v_newflg varchar2(1) ;
BEGIN

if v_newid is null then
  return '配件入库返修';
end if;

if v_eid is null then
  return '配件返修完成 到店安装';
end if;

-----捷强直属全部调换
if not v_eid is null then

  select c.classcd,c.busityp into v_custclass,  v_busityp from tmm44_pos_r_eid a
  inner join tmm35_cust_pos_rl b
  on a.posid=b.eid
  inner join tmm22_customers c
  on b.custcd=c.custcd
  where a.eid=v_eid  and a.useflg='1' and b.useflg='1' ;

  if v_custclass='08' and v_busityp='ZS' then

     return '捷强';

  end if ;

end if;

if not v_newid is null then
  SELECT IS_NEW  INTO v_newflg
  FROM TIT25_ACCESSORIES_UPDATE
  WHERE new_accessories_id = v_newid and maintenance_id = v_mid /*AND auditflg = '1'*/;

  if v_newflg = '2' then
     return '销售旧品，原配件入库！';
  end if ;
end if;

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
  where a.eid=v_eid and a.useflg='1';

return v_message ;


EXCEPTION
 when others then
     return  'error';


END uf_itsm_checkperiod_memo;
