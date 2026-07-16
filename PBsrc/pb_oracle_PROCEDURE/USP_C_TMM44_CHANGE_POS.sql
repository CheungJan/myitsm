procedure usp_c_tmm44_change_pos
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



-------------------------
as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
