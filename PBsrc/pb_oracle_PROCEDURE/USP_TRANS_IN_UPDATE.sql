procedure usp_trans_in_update
(  as_return out varchar2)

as

v_date date;

begin
v_date:=sysdate;

for  c_1 in(select id from tmp_sm_in_open_result)
loop

update sm_in_open_result@itsm
set sys_status=2
where id=c_1.id;
end loop;


for  c_2 in(select id from tmp_sm_in_part_change)
loop

update sm_in_part_change@itsm
set sys_status=2
where id=c_2.id;
end loop;


-------------------------
as_return:='OK';
-------------------

EXCEPTION
 when others then
    as_return:=sqlcode||sqlerrm;


    end ;
