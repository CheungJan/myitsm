procedure usp_c_tmm44
(as_return out varchar2)

as
v_posid varchar2(50);
v_pos number(5);
v_str1 varchar2(500);
v_str2 varchar2(500);
v_tftype  varchar2(10);
v_itemcd varchar2(100);
----资产表
begin

delete from o_tf_in_asset
where sys_status=1;



delete from o_tf_in_part
where sys_status=1;

------------------是否增加时间段 缩小范围?

for    sm_open in
(
select plan_no , cardcode,serialno,COMPLETEDDATE ,id
  from sm_in_open_result
  where sys_status=2)loop

          select  sltyp ,itemcd into v_tftype ,v_itemcd
          from tsl01_extend b
          where opbillid=sm_open.plan_no;
         --GX BQ CK GB  BG

          --门店开通
          if v_tftype='XZ' or v_tftype='GX' then

        --根据itsm返回的开通单
        --sys_status  '1'=新接收数据 '2'=已确认数据 已更新tmm44表

                      v_str1:=sm_open.serialno;

                 v_pos:=instr(v_str1,',');


                     if v_pos=0 then --只有一个posid
                        insert into TMP_TMM43_EID
                          ( itemcd, eid, opercd, gendate, useflg,
                           etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, id )
                          select   itemcd, eid, opercd, gendate, useflg,
                           etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, sm_open.id
                            from TMM43_EID
                          --where etyp='1';
                          where eid =v_str1;



                     end if ;



         -------------循环
                 while  v_pos<>0  loop

                       v_str2:=substr(v_str1,1,v_pos -1 );
                          insert into TMP_TMM43_EID
                          ( itemcd, eid, opercd, gendate, useflg,
                           etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, id )
                          select   itemcd, eid, opercd, gendate, useflg,
                           etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, sm_open.id
                            from TMM43_EID
                          --where etyp='1';
                          where eid =v_str2;




                       v_str1:=substr(v_str1,v_pos+1);

                       v_pos:=instr(v_str1,',');

                           if v_pos=0 then
                                  insert into TMP_TMM43_EID
                                    ( itemcd, eid, opercd, gendate, useflg,
                                     etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, id )
                                    select   itemcd, eid, opercd, gendate, useflg,
                                     etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, sm_open.id
                                      from TMM43_EID
                                    --where etyp='1';
                                    where eid =v_str1;

                           end if ;

                 end  loop;
        ------------------------
           end if ;

end loop;


---old_degree	int	设备 新旧度  3:旧 12:新

insert into o_tf_in_asset
( sm_no, serialno, name, model, cost, old_degree, enabled_date, repair_date, description, insert_time,
syn_time, sys_status,checkflg,cardcode,id)

select lpad(to_char(tf_seqid.nextval),10,0),a.eid,b.itemnm,a.itemcd,0,12,c.startdate,c.startdate+b.newperiod,'',sysdate,'',1,'0',d.custcard,id
from TMP_TMM43_EID a
inner join tmm12_items b
on a.itemcd=b.itemcd
inner join tmm35_cust_pos_rl c
on a.eid=c.eid
inner join tmm22_customers d
on c.custcd=d.custcd
;

--old_degree	int	配件新旧度 3:旧 12:新
insert into o_tf_in_part
( sm_no, asset_serialno, asset_model, name, part_serialno, part_model, old_degree,
enabled_date, repair_date, cost, deliverno, receiptno,
description, insert_time, syn_time, sys_status,checkflg)


select lpad(to_char(tf_seqid.nextval),10,0),a.posid,a.itemcd,c.itemnm,b.eid,c.itemcd,12,
a.gendate,a.gendate+c.newperiod,'','','',
'',sysdate,'',1,'0'
from tmm43_eid b
inner join tmm12_items c
on b.itemcd=c.itemcd

inner join tmm44_pos_r_eid a
on a.eid=b.eid

where exists (select * from TMP_TMM43_EID  where a.posid=TMP_TMM43_EID.EID);


----------------
update sm_in_open_result
set sys_status='3'
where exists (select * from TMP_TMM43_EID  where TMP_TMM43_EID.Refid=sm_in_open_result.plan_no);





-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
