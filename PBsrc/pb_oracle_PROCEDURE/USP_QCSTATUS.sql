procedure usp_qcstatus
 ( as_type      char,
 as_id          char,
   as_useid         char,
   as_refbillid  char,
 as_Result    out varchar2)

AS
v_id char(8);--质检结果单号
v_useid varchar2(6);
v_type char(2);--类型
v_temp integer;
v_refbillid char(8);
v_eid char(13);--pos eid
v_poscd char(8);
begin
v_id:=as_id;
v_useid:=as_useid;
v_type:=as_type;
v_refbillid :=as_refbillid;

if v_type='YH' then  --易耗品

update twh16_outdtprd
set qcqty=qcqty+(select qcqty from tqc11_resultdt  where  qcbillid=v_id   and  itemcd= twh16_outdtprd.itemcd
and  itemtyp= twh16_outdtprd.itemtyp  and  prddate= twh16_outdtprd.prddate )
where outbillid=v_refbillid ;



as_Result:='';
end if ;

if v_type='PJ' then  --配件

--批次出库
update twh16_outdtprd
set qcqty=nvl(qcqty,0)+ nvl((select sum(qcqty) from tqc11_resulteid
where  qcbillid=v_id   and  itemcd= twh16_outdtprd.itemcd and   prddate= twh16_outdtprd.prddate    ),0)
where outbillid=v_refbillid ;
--按id出库

update twh16_outdteid
set qcqty=nvl(qcqty,0)+ nvl((select qcqty from tqc11_resulteid  where  qcbillid=v_id
and  itemcd= twh16_outdteid.itemcd  and twh16_outdteid.eid =tqc11_resulteid.eid  ),0)
where outbillid=v_refbillid  ;


-----质检结果更新设备IDtmm43_eid
--sflg 0：新品已检验1：已使用2：已报废3：待检4：已退回5已检验  6检验中 7 生产中
update tmm43_eid
set (sflg,refid,gendate,opercd,qcflg,manuf_seq)=
(select '5',v_refbillid,sysdate,v_useid,qcstatus,manuf_seq from tqc11_resulteid
where  qcbillid=v_id and tmm43_eid.eid=tqc11_resulteid.eid)

where exists (select * from tqc11_resulteid
 where tqc11_resulteid.eid=tmm43_eid.eid  and  tqc11_resulteid.qcbillid=v_id);





---质检结果创建新设备ID

--Etyp	Char(1)	设备类型	0：配件1：主机
--Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验 6:检验中 7:生产中 8:在库

insert into tmm43_eid
(itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp,new_old,manuf_seq)
select a.itemcd,a.eid,v_useid,sysdate,'1',  decode(b.typflg, '1','1','0','0' )    ,  '0'   ,
v_refbillid,a.qcstatus,'',a.prddate,a.itemtyp,'1',manuf_seq
from tqc11_resulteid  a
inner join tmm12_items b
on  a.itemcd=b.itemcd
where  a.qcbillid=v_id  and  not exists
(select * from tmm43_eid where    a.eid= tmm43_eid.eid  );

--回写标签表
update tmm40_label
set useflg='1'
where exists (select * from tqc11_resulteid  where  tqc11_resulteid.qcbillid=v_id  and tmm40_label.labelid=tqc11_resulteid.eid );




as_Result:='';
end if ;


if v_type='C1' then  --成品


--按id出库 回写生产出库单状态
/*
update twh16_outdteid
set qcqty=qcqty+(select qcqty from tqc11_resulteid  where  qcbillid=v_id
and  itemcd= twh16_outdteid.itemcd  and twh16_outdteid.eid =tqc11_resulteid.eid  )
where  ;
*/
update twh16_outdteid
set qcqty=1
where qcqty=0 and exists (select eid from tqc11_resulteid where   twh16_outdteid.eid =tqc11_resulteid.eid  and tqc11_resulteid.qcbillid=v_id );


---质检结果创建新pos设备ID

--Etyp	Char(1)	设备类型	0：配件1：主机
--Sflg	Char(1)	状态标志	0：新品 已检验  1：已使用  2：已报废  3：待检  4：已退回 5: 已检验

insert into tmm43_eid
(itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp,new_old)
select a.itemcd,a.eid,v_useid,sysdate,'0',  '1'   ,  '0'   ,
v_id,qcstatus  ,'','','','1'
from tqc10_result  a
where  a.qcbillid=v_id  and  not exists
(select * from tmm43_eid where    a.eid= tmm43_eid.eid  );


--回写标签表
update tmm40_label
set useflg='1'
where exists (select * from tqc10_result  where   tmm40_label.labelid=tqc10_result.eid and tqc10_result.qcbillid=v_id );





-----质检结果更新设备IDtmm43_eid

update tmm43_eid
set (sflg,refid,gendate,opercd,QCflg)=
(select '1',v_id,sysdate,v_useid,qcstatus from tqc11_resulteid
where  qcbillid=v_id and tmm43_eid.eid=tqc11_resulteid.eid)

where exists (select * from tqc11_resulteid
 where tqc11_resulteid.eid=tmm43_eid.eid  and  tqc11_resulteid.qcbillid=v_id);


--构建pos配件清单关系
insert into tmm44_pos_r_eid
( posid, itemcd, eid, opercd, gendate, upddate ,useflg)
select a.eid ,b.itemcd,b.eid,v_useid,sysdate,sysdate,'1'
from tqc10_result a
right outer  join tqc11_resulteid b
on a.qcbillid=b.qcbillid
where a.qcbillid=v_id ;


as_Result:='';
end if ;


if v_type='C2' then  --成品转配件

--按id出库 回写生产出库单状态

select itemcd ,eid

into v_poscd ,v_eid
from tqc10_result
where qcbillid=v_id;

/*update twh16_outdteid
set qcqty=1
where outbillid=v_refbillid  and eid=v_eid ;
*/

update twh16_outdteid
set qcqty=1
where twh16_outdteid.outbillid||twh16_outdteid.eid in
 (select tqc10_result.refbillid||tqc10_result.eid  from tqc10_result
  where    tqc10_result.qcbillid=v_id )      ;

--更新tmm43_eid主机
update tmm43_eid
set  opercd=v_useid,    gendate=sysdate ,
 sflg='2' , refid=v_id , qcflg='BF', whcd='', prddate='', itemtyp=''
where eid=v_eid;


--更新tmm43_eid配件

 update  tmm43_eid
            set (sflg,refid, whcd, prddate, itemtyp)=
            (select '7',v_id,'' ,tqc11_resulteid.prddate,tqc11_resulteid.itemtyp
             from tqc11_resulteid where tqc11_resulteid.eid= tmm43_eid.eid   and tqc11_resulteid.qcbillid=v_id )
            where eid in (select eid from tqc11_resulteid    where qcbillid=v_id );
  ---pos关系表
         update tmm44_pos_r_eid
         set    useflg='0'
         where posid=v_eid;


as_Result:='';
end if ;


as_Result:='';

-------------------

EXCEPTION
 when others then
    as_Result:=sqlcode||sqlerrm;

end ;
