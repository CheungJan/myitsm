procedure usp_planstatus
 ( as_type      char,
 as_id          char,
   as_useid         char,
 as_Result    out varchar2)

AS
v_id char(8);--计划单号
v_useid varchar2(6);
v_type char(1);
v_temp integer;
v_slbillid char(8);--销售单号
begin
v_id:=as_id;
v_useid:=as_useid;
v_type:=as_type;

if v_type='1' then --新的采购计划


        --更新已有商品采购计划
        --/*+ BYPASS_UJVC */ 跳过oracle检查

       /*update (select a.rgstqty  rgstqty,a.auditqty  auditqty,a.opercd  opercd,a.upddate  upddate,b.auditqty addqty
          from tpc03_pcplanstatus a , tpc02_pcplandt b where a.itemcd=b.itemcd and  b.pcplanid=v_id and
          a.itemcd is not null
        --  exists (select * from tpc02_pcplandt where tpc03_pcplanstatus.itemcd=tpc02_pcplandt.itemcd )
           )

        set rgstqty=rgstqty+addqty ,auditqty=auditqty+addqty ,opercd=v_useid,upddate=sysdate;
       */
       --where exists (select * from tpc02_pcplandt where tpc03_pcplanstatus.itemcd=tpc02_pcplandt.itemcd  and tpc02_pcplandt.pcplanid=v_id);
        update tpc03_pcplanstatus
        set   ( rgstqty, auditqty,refbillid,upddate )=(select  nvl(tpc03_pcplanstatus.rgstqty,0) -    a.rgstqty  ,
        nvl(tpc03_pcplanstatus.auditqty,0) +   a.rgstqty ,a.pcplanid,sysdate
        from tpc02_pcplandt  a
        inner join tpc01_pcplan b on a.pcplanid=b.pcplanid
        where tpc03_pcplanstatus.itemcd=a.itemcd  and b.pcplanid=v_id)
        where exists (select * from tpc02_pcplandt  a
        inner join tpc01_pcplan b on a.pcplanid=b.pcplanid
        where tpc03_pcplanstatus.itemcd=a.itemcd  and b.pcplanid=v_id);






        ---插入没有采购计划的商品

        insert into tpc03_pcplanstatus
        (itemcd, rgstqty, auditqty, pcqty, opercd, memo, gendate, useflg, upddate,refbillid)
        select itemcd,auditqty,auditqty,0,v_useid,'',sysdate,'1',sysdate,pcplanid
        from tpc02_pcplandt
        where pcplanid=v_id  and  not exists(select * from tpc03_pcplanstatus where tpc03_pcplanstatus.itemcd=tpc02_pcplandt.itemcd) ;

        --更新销售单采购标记
        select a.slbillid into v_slbillid   from tpc01_pcplan a
        where a.pcplanid=v_id;

        update tsl10_slbill a
        set a.pcplanflg='1'
        where a.slbillid=v_slbillid and a.pcplanflg='X';


end if ;

if v_type='2' then --采购计划生成采购单
/*
update tpc03_pcplanstatus
set tpc03_pcplanstatus.pcqty=tpc03_pcplanstatus.pcqty + (select  tmp_registerdt.AUDITQTY from tmp_registerdt
  where tpc03_pcplanstatus.itemcd=tmp_registerdt.itemcd  ),
  tpc03_pcplanstatus.auditqty= tpc03_pcplanstatus.auditqty -  (select  tmp_registerdt.auditqty from tmp_registerdt
  where tpc03_pcplanstatus.itemcd=tmp_registerdt.itemcd   )

where  exists (select * from tmp_registerdt
where tpc03_pcplanstatus.itemcd= tmp_registerdt.itemcd   );
*/

update tpc03_pcplanstatus
set (tpc03_pcplanstatus.pcqty ,tpc03_pcplanstatus.auditqty,tpc03_pcplanstatus.refbillid,tpc03_pcplanstatus.upddate)
= (select tpc03_pcplanstatus.pcqty + tmp_registerdt.AUDITQTY  ,
 case when tpc03_pcplanstatus.auditqty - tmp_registerdt.auditqty>0 then
 tpc03_pcplanstatus.auditqty - tmp_registerdt.auditqty else 0 end
  ,tmp_registerdt.rgstbillid,sysdate
  from tmp_registerdt
  where tpc03_pcplanstatus.itemcd=tmp_registerdt.itemcd  )

where  exists (select * from tmp_registerdt
where tpc03_pcplanstatus.itemcd= tmp_registerdt.itemcd   );

--v_temp:=sql%rowcount;


end if ;



as_Result:='';
end ;

