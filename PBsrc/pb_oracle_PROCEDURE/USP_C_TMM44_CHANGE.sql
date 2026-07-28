procedure usp_c_tmm44_change
(as_eid varchar2,  as_return out varchar2)

as
v_eid varchar2(13);
----资产表
begin
v_eid:=as_eid;

--delete from o_tf_in_asset
--where sys_status=1;



--delete from o_tf_in_part
--where sys_status=1;


delete from TMP_TMM43_EID;

insert into TMP_TMM43_EID
select itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, 1
 from tmm43_eid
 where eid=v_eid;


insert into TMP_TMM43_EID
select itemcd, eid, opercd, gendate, useflg, etyp, sflg, refid, qcflg, whcd, prddate, itemtyp, 1
 from tmm43_eid
 where eid in (select eid from tmm44_pos_r_eid where posid= v_eid);

---old_degree  int  设备 新旧度  3:旧 12:新

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

--old_degree  int  配件新旧度 3:旧 12:新
/*insert into o_tf_in_part
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
*/

----------------
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

where exists (select * from TMP_TMM43_EID  where a.eid=TMP_TMM43_EID.EID) and a.useflg='1';


-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
