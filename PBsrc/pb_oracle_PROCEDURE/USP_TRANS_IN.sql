procedure usp_trans_in
( as_return out varchar2)

as

as_date date;

----
begin

as_date:=sysdate  - 30 ;

---v_type='1'  开通
insert into tmp_sm_in_open_result
(id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
select id, plan_no, case_no, cardcode, serialno, completeddate, convert(result,'zhs16gbk','utf8') result ,insert_time, syn_time, sys_status
--from  sm_in_open_result@itsm
from  sm_in_open_result
where  insert_time > as_date ;


insert into sm_in_open_result
(id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status)
select id, plan_no, case_no, cardcode, serialno, completeddate, result, insert_time, syn_time, sys_status
from    tmp_sm_in_open_result
where not exists (select * from sm_in_open_result where  sm_in_open_result.id=tmp_sm_in_open_result.id);

as_return:='开通单回单：  '||to_char(sql%rowcount)||' 条记录'||'       ';

/*for  c_1 in(select id from tmp_sm_in_open_result)
loop

update sm_in_open_result@itsm
set sys_status=2
where id=c_1.id;
end loop;
*/

/*update sm_in_open_result@itsm
set sys_status=2
where sys_status=1;
*/
--where id  in  (select id from tmp_sm_in_open_result );

---v_type='2' 配件
insert into tmp_sm_in_part_change
(id, changetype, name, serialno, model, old_name, old_serialno, old_model, case_no,
insert_time, syn_time, sys_status,OPERFLG)
select id, changetype,   convert(name,'zhs16gbk','utf8')   name, serialno,convert(model,'zhs16gbk','utf8')  model,
convert(old_name,'zhs16gbk','utf8') old_name, old_serialno,convert(old_model,'zhs16gbk','utf8') old_model, case_no,
insert_time, syn_time, sys_status,''
--from sm_in_part_change@itsm
from sm_in_part_change
where insert_time > as_date;





update tmp_sm_in_part_change
set tmp_sm_in_part_change.operflg=uf_checkperiod(old_serialno,serialno),
tmp_sm_in_part_change.memo   =uf_checkperiod_memo(old_serialno,serialno)
where tmp_sm_in_part_change.changetype =2;




update tmp_sm_in_part_change
set OPERFLG='9',memo=memo||'|'||'配件或pos机为空'
where old_serialno is null or serialno is null;

update tmp_sm_in_part_change
set memo=memo||'|'||'配件序列号不存在'
where not exists (select * from tmm43_eid where tmm43_eid.eid = tmp_sm_in_part_change.serialno);



---operflg 0 不入 1 入库
---根据原配件的质保期
insert into sm_in_part_change
(id, changetype, name, serialno, model, old_name, old_serialno, old_model, case_no,
insert_time, syn_time, sys_status,OPERFLG,memo )
select id, changetype, name, serialno, model, tmm12_items.itemnm, old_serialno,  tmm12_items.itemcd  , case_no,
insert_time, syn_time, decode(OPERFLG,'9','9', sys_status), OPERFLG , '系统:'||memo
 from tmp_sm_in_part_change
 left  outer join tmm43_eid
 on tmp_sm_in_part_change.old_serialno=tmm43_eid.eid
 left join tmm12_items
 on tmm12_items.itemcd=tmm43_eid.itemcd

 where not exists (select * from sm_in_part_change where sm_in_part_change.id=tmp_sm_in_part_change.id);

as_return:=as_return||'配件变更单：'||to_char(sql%rowcount)||' 条记录';








/*for  c_2 in(select id from tmp_sm_in_part_change)
loop

update sm_in_part_change@itsm
set sys_status=2
where id=c_2.id;
end loop;
*/


/*update sm_in_part_change@itsm a
set sys_status=2
where sys_status=1;
*/



--usp_trans_in_update(as_return) ;

-------------------------
--as_return:='OK';
-------------------



EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
